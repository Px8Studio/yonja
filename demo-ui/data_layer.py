# demo-ui/data_layer.py
"""Chainlit Data Layer for ALİM.

This module implements Chainlit's SQLAlchemy data layer to persist:
- Users (linked to Google OAuth identity)
- Threads (conversation history)
- Steps (individual messages)
- User settings (via metadata JSONB)

Uses the SAME Postgres database as the main Yonca API, adding
Chainlit-specific tables alongside your existing user_profiles, farms, etc.

Architecture:
    Google OAuth → cl.User(identifier=email) → Chainlit users table
                                               ↓
                         users.metadata stores ChatSettings (persisted)
                                               ↓
                         Link to user_profiles via email for farm data
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chainlit.data.storage_clients.base import BaseStorageClient
    from chainlit.types import StepDict

import chainlit as cl
import structlog
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

# Initialize logger FIRST
logger = structlog.get_logger(__name__)

# Module-level singleton
_data_layer: AlimDataLayer | None = None


def get_database_url() -> str:
    """Get async database URL for Chainlit data layer.

    Chainlit's SQLAlchemy layer requires asyncpg for Postgres.
    Converts standard postgres:// URLs to postgresql+asyncpg://

    Returns:
        Async-compatible database URL
    """
    # Try demo-ui specific setting first, then fall back to main app
    db_url = os.getenv(
        "CHAINLIT_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/yonca.db")
    )

    # Convert postgres:// to postgresql+asyncpg:// for async support
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return db_url


class AlimDataLayer(SQLAlchemyDataLayer):
    """Custom data layer with JSONB serialization fix for PostgreSQL.

    Chainlit's default SQLAlchemyDataLayer has a bug where it passes tags as a
    Python list directly to asyncpg, but PostgreSQL TEXT columns need JSON strings.

    The parent class serializes `metadata` with json.dumps() but NOT `tags`.
    This subclass fixes that by serializing tags to JSON before the SQL query.

    CRITICAL: The parent SQLAlchemyDataLayer.update_thread() uses UPSERT
    (INSERT ON CONFLICT UPDATE) so there is NO create_thread() method.
    Always use update_thread() for both create and update operations.
    """

    def __init__(
        self,
        conninfo: str,
        storage_provider: BaseStorageClient | None = None,
    ):
        """Initialize with connection string and optional storage provider.

        Args:
            conninfo: Database connection string (e.g., postgresql+asyncpg://...)
            storage_provider: Optional storage client for file elements (images, docs, etc.)
        """
        super().__init__(conninfo=conninfo, storage_provider=storage_provider)
        # REMOVED: show_logger parameter (deprecated in newer Chainlit versions)

    async def update_thread(
        self,
        thread_id: str,
        name: str | None = None,
        user_id: str | None = None,
        metadata: dict | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Override to serialize tags to JSON string for PostgreSQL.

        The parent class passes tags directly to SQL, but asyncpg can't encode
        Python lists. We serialize to JSON string before calling parent.

        Args:
            thread_id: Thread ID (required)
            name: Thread display name
            user_id: User ID who owns the thread
            metadata: Thread metadata dict
            tags: Thread tags list (will be serialized to JSON string)
        """
        # CRITICAL FIX: Parent class does NOT serialize tags, only metadata.
        # asyncpg throws "list object has no attribute 'encode'" if we pass a list.
        # Serialize tags to JSON string for PostgreSQL TEXT column compatibility.
        serialized_tags = _serialize_tags(tags) if tags else None

        # We can't call super() because it expects List[str] but we have a string.
        # Instead, we implement the same logic with our fix applied.
        await self._update_thread_with_serialized_tags(
            thread_id=thread_id,
            name=name,
            user_id=user_id,
            metadata=metadata,
            tags_json=serialized_tags,
        )

    async def _update_thread_with_serialized_tags(
        self,
        thread_id: str,
        name: str | None = None,
        user_id: str | None = None,
        metadata: dict | None = None,
        tags_json: str | None = None,
    ) -> None:
        """Internal method that handles serialized tags properly.

        This is a copy of parent's update_thread() but with tags already serialized.
        """
        user_identifier = None
        if user_id:
            user_identifier = await self._get_user_identifer_by_id(user_id)

        if metadata is not None:
            existing = await self.execute_sql(
                query='SELECT "metadata" FROM threads WHERE "id" = :id',
                parameters={"id": thread_id},
            )
            base = {}
            if isinstance(existing, list) and existing:
                raw = existing[0].get("metadata") or {}
                if isinstance(raw, str):
                    try:
                        base = json.loads(raw)
                    except json.JSONDecodeError:
                        base = {}
                elif isinstance(raw, dict):
                    base = raw
            incoming = {k: v for k, v in metadata.items() if v is not None}
            metadata = {**base, **incoming}

        name_value = name
        if name_value is None and metadata:
            name_value = metadata.get("name")
        created_at_value = await self.get_current_timestamp() if metadata is None else None

        data = {
            "id": thread_id,
            "createdAt": created_at_value,
            "name": name_value,
            "userId": user_id,
            "userIdentifier": user_identifier,
            "tags": tags_json,  # Already serialized to JSON string!
            "metadata": json.dumps(metadata) if metadata else None,
        }
        parameters = {key: value for key, value in data.items() if value is not None}
        columns = ", ".join(f'"{key}"' for key in parameters.keys())
        values = ", ".join(f":{key}" for key in parameters.keys())
        updates = ", ".join(
            f'"{key}" = EXCLUDED."{key}"' for key in parameters.keys() if key != "id"
        )
        query = f"""
            INSERT INTO threads ({columns})
            VALUES ({values})
            ON CONFLICT ("id") DO UPDATE
            SET {updates};
        """
        await self.execute_sql(query=query, parameters=parameters)

    async def create_step(self, step: StepDict | None = None, **kwargs) -> str:
        """Override to serialize tags before DB insert."""
        step_dict = step if step is not None else kwargs.get("step_dict", kwargs)

        if isinstance(step_dict, dict) and "tags" in step_dict:
            step_dict["tags"] = _serialize_tags(step_dict["tags"])

        return await super().create_step(step_dict)

    async def update_step(self, step: StepDict | None = None, **kwargs) -> None:
        """Override to serialize tags before DB update."""
        step_dict = step if step is not None else kwargs.get("step_dict", kwargs)

        if isinstance(step_dict, dict) and "tags" in step_dict:
            step_dict["tags"] = _serialize_tags(step_dict["tags"])

        return await super().update_step(step_dict)

    async def create_user(self, user: cl.User) -> cl.PersistedUser | None:
        """Override to handle unique constraint violations gracefully.

        The parent implementation has a race condition where concurrent requests
        (e.g., multiple browser tabs logging in simultaneously) can cause
        UniqueViolationError. This implementation uses UPSERT to handle it.

        Args:
            user: Chainlit User object from OAuth callback

        Returns:
            PersistedUser if created/updated successfully, None on error
        """
        import json
        import uuid
        from datetime import datetime

        try:
            # Use UPSERT (INSERT ... ON CONFLICT DO UPDATE) to handle race conditions
            user_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat() + "Z"
            metadata_json = json.dumps(user.metadata) if user.metadata else "{}"

            # PostgreSQL UPSERT query - creates user if not exists, updates metadata if exists
            query = """
                INSERT INTO users ("id", "identifier", "createdAt", "metadata")
                VALUES (:id, :identifier, :createdAt, :metadata)
                ON CONFLICT ("identifier") DO UPDATE
                SET "metadata" = EXCLUDED."metadata"
                RETURNING "id", "identifier", "createdAt", "metadata"
            """
            parameters = {
                "id": user_id,
                "identifier": user.identifier,
                "createdAt": created_at,
                "metadata": metadata_json,
            }

            result = await self.execute_sql(query=query, parameters=parameters)

            if result and isinstance(result, list) and len(result) > 0:
                row = result[0]
                # Parse metadata back from JSON string if needed
                metadata = row.get("metadata", {})
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)

                logger.info(
                    "user_upserted_successfully",
                    identifier=user.identifier,
                    user_id=row["id"],
                )

                return cl.PersistedUser(
                    id=row["id"],
                    identifier=row["identifier"],
                    createdAt=row["createdAt"],
                    metadata=metadata,
                )

            # Fallback: if RETURNING didn't work, fetch the user
            logger.debug("create_user_upsert_no_return_fetching", identifier=user.identifier)
            return await self.get_user(user.identifier)

        except Exception as e:
            logger.error("create_user_error", identifier=user.identifier, error=str(e))
            # Last resort: try to fetch existing user (might work if user was created by another request)
            try:
                return await self.get_user(user.identifier)
            except Exception:
                return None


# Add tag serialization helper
def _serialize_tags(tags: list | str | None) -> str | None:
    """Convert tags list to JSON string for PostgreSQL TEXT column.

    Chainlit's SQLAlchemy layer passes tags as Python lists,
    but PostgreSQL TEXT columns need JSON strings.

    Args:
        tags: List of tag strings or already-serialized JSON

    Returns:
        JSON string or None
    """
    if tags is None:
        return None

    if isinstance(tags, str):
        # Already serialized
        return tags

    if isinstance(tags, list):
        # Serialize list to JSON
        try:
            return json.dumps(tags)
        except (TypeError, ValueError):
            logger.warning("failed_to_serialize_tags", tags=tags)
            return json.dumps([])

    return None


# Patch Chainlit's SQLAlchemyDataLayer to serialize tags
_original_create_step = None


def _patch_chainlit_step_serialization():
    """Patch Chainlit's create_step to serialize tags before DB insert."""
    global _original_create_step

    from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

    if _original_create_step is not None:
        return  # Already patched

    _original_create_step = SQLAlchemyDataLayer.create_step

    async def create_step_patched(self, step_dict: dict) -> str:
        """Patched create_step with tag serialization."""
        # Serialize tags if present
        if "tags" in step_dict and isinstance(step_dict["tags"], list):
            step_dict["tags"] = _serialize_tags(step_dict["tags"])

        # Call original method
        return await _original_create_step(self, step_dict)

    SQLAlchemyDataLayer.create_step = create_step_patched
    logger.info("chainlit_step_serialization_patched")


# ============================================
# USER PROVISIONING HELPERS
# ============================================


async def ensure_user_persisted(user: cl.User) -> bool:
    """Ensure user from OAuth is persisted to database.

    Called after OAuth login to ensure the Chainlit user exists in DB.
    This is CRITICAL before creating related records (personas, threads, etc)
    to avoid foreign key constraint violations.

    Args:
        user: Authenticated Chainlit user from OAuth

    Returns:
        True if user exists or was created successfully
    """
    if not user:
        logger.warning("ensure_user_persisted_no_user")
        return False

    data_layer = get_data_layer()
    if not data_layer:
        logger.warning("ensure_user_persisted_no_datalayer")
        return False

    try:
        # Check if user exists
        persisted_user = await data_layer.get_user(user.identifier)

        if persisted_user:
            logger.debug("user_already_exists", identifier=user.identifier)
            return True

        # Create user if not exists - CRITICAL for foreign key constraints
        created_user = await data_layer.create_user(user)

        if created_user:
            logger.info(
                "user_created_successfully",
                identifier=user.identifier,
                has_metadata=bool(user.metadata),
            )
            return True
        else:
            logger.error("user_creation_returned_none", identifier=user.identifier)
            return False

    except Exception as e:
        logger.error("ensure_user_error", identifier=user.identifier, error=str(e))
        return False


# ============================================
# DATA LAYER FACTORY
# ============================================


def get_data_layer() -> AlimDataLayer | None:
    """Get or create the data layer singleton."""
    global _data_layer

    if _data_layer is not None:
        return _data_layer

    from config import settings as demo_settings

    if not demo_settings.data_persistence_enabled:
        logger.info("data_persistence_disabled")
        return None

    db_url = demo_settings.effective_database_url

    logger.info(
        "initializing_data_layer",
        db_url=db_url.split("@")[-1] if "@" in db_url else "local",
    )

    try:
        _data_layer = AlimDataLayer(conninfo=db_url)
        return _data_layer
    except Exception as e:
        logger.error("data_layer_init_failed", error=str(e))
        return None


# ============================================
# SETTINGS PERSISTENCE HELPERS
# ============================================


async def load_user_settings(user: cl.User | None) -> dict:
    """Load persisted ChatSettings for a user.

    Called at session start to restore user's preferences.

    Args:
        user: Authenticated Chainlit user (from OAuth)

    Returns:
        ChatSettings dict, or defaults if not found
    """
    defaults = {
        "language": "Azərbaycanca",
        "detail_level": "Orta",
        "units": "Metrik (ha, kg)",
        "notifications": True,
        "show_sources": False,
    }

    if not user:
        return defaults

    data_layer = get_data_layer()
    if not data_layer:
        return defaults

    try:
        persisted_user = await data_layer.get_user(user.identifier)
        if persisted_user and persisted_user.metadata:
            return persisted_user.metadata.get("chat_settings", defaults)
    except Exception as e:
        logger.error("load_settings_error", error=str(e))

    return defaults


async def save_user_settings(user: cl.User | None, settings: dict) -> bool:
    """Persist ChatSettings for a user.

    Called when user changes settings in the sidebar.

    Args:
        user: Authenticated Chainlit user
        settings: Updated ChatSettings dict

    Returns:
        True if saved successfully
    """
    if not user:
        logger.debug("save_settings_skipped_no_user")
        return False

    data_layer = get_data_layer()
    if not data_layer:
        logger.debug("save_settings_skipped_no_datalayer")
        return False

    try:
        return await data_layer.update_user_metadata(
            identifier=user.identifier,
            metadata={"chat_settings": settings},
        )
    except Exception as e:
        logger.error("save_settings_error", error=str(e))
        return False


async def save_conversation_context(
    user: cl.User | None,
    thread_id: str,
    scenario_context: dict | None,
) -> bool:
    """Save conversation context to database.

    Args:
        user: Chainlit user
        thread_id: Thread/conversation ID
        scenario_context: Scenario parameters dict

    Returns:
        True if saved successfully
    """
    if not user or not scenario_context:
        return False

    data_layer = get_data_layer()
    if not data_layer or not data_layer.engine:
        logger.warning("save_context_no_datalayer")
        return False

    try:
        from sqlalchemy import text

        # Serialize list fields to JSON
        action_categories = json.dumps(scenario_context.get("action_categories", []))
        expertise_areas = json.dumps(scenario_context.get("expertise_areas", []))

        stmt = text(
            """
                    INSERT INTO conversation_contexts (
                        scenario_id, user_id, thread_id,
                        crop_category, specific_crop, region,
                        farm_size_ha, experience_level,
                        soil_type, irrigation_type, current_month,
                        action_categories, expertise_areas,
                        smart_question, user_confirmed,
                        conversation_stage, settings_version
                    ) VALUES (
                        :scenario_id, :user_id, :thread_id,
                        :crop_category, :specific_crop, :region,
                        :farm_size_ha, :experience_level,
                        :soil_type, :irrigation_type, :current_month,
                        :action_categories, :expertise_areas,
                        :smart_question, :user_confirmed,
                        :conversation_stage, :settings_version
                    )
                    ON CONFLICT (user_id, thread_id)
                    DO UPDATE SET
                        crop_category = EXCLUDED.crop_category,
                        specific_crop = EXCLUDED.specific_crop,
                        region = EXCLUDED.region,
                        farm_size_ha = EXCLUDED.farm_size_ha,
                        experience_level = EXCLUDED.experience_level,
                        soil_type = EXCLUDED.soil_type,
                        irrigation_type = EXCLUDED.irrigation_type,
                        current_month = EXCLUDED.current_month,
                        action_categories = EXCLUDED.action_categories,
                        expertise_areas = EXCLUDED.expertise_areas,
                        smart_question = EXCLUDED.smart_question,
                        conversation_stage = EXCLUDED.conversation_stage,
                        settings_version = EXCLUDED.settings_version,
                        updated_at = CURRENT_TIMESTAMP
                    """
        )

        async with data_layer.engine.begin() as conn:
            await conn.execute(
                stmt,
                {
                    "scenario_id": f"{user.identifier}:{thread_id}",
                    "user_id": user.identifier,
                    "thread_id": thread_id,
                    "crop_category": scenario_context.get("crop_category"),
                    "specific_crop": scenario_context.get("specific_crop"),
                    "region": scenario_context.get("region"),
                    "farm_size_ha": scenario_context.get("farm_size_ha"),
                    "experience_level": scenario_context.get("experience_level"),
                    "soil_type": scenario_context.get("soil_type"),
                    "irrigation_type": scenario_context.get("irrigation_type"),
                    "current_month": scenario_context.get("current_month"),
                    "action_categories": action_categories,
                    "expertise_areas": expertise_areas,
                    "smart_question": scenario_context.get("smart_question"),
                    "user_confirmed": scenario_context.get("user_confirmed", False),
                    "conversation_stage": scenario_context.get("conversation_stage"),
                    "settings_version": scenario_context.get("settings_version", 1),
                },
            )

        logger.info("conversation_context_saved", user_id=user.identifier, thread_id=thread_id)
        return True

    except Exception as e:
        logger.error("save_context_error", error=str(e), user_id=user.identifier)
        return False


async def load_conversation_context(user_id: str, thread_id: str) -> dict | None:
    """Load conversation context from database.

    Args:
        user_id: User identifier
        thread_id: Thread/conversation ID

    Returns:
        Scenario context dict or None if not found
    """
    data_layer = get_data_layer()
    if not data_layer or not data_layer.engine:
        logger.warning("load_context_no_datalayer")
        return None

    try:
        from sqlalchemy import text

        stmt = text(
            """
            SELECT crop_category, specific_crop, region,
                   farm_size_ha, experience_level,
                   soil_type, irrigation_type, current_month,
                   action_categories, expertise_areas,
                   smart_question, user_confirmed,
                   conversation_stage, settings_version
            FROM conversation_contexts
            WHERE user_id = :user_id AND thread_id = :thread_id
        """
        )

        async with data_layer.engine.begin() as conn:
            result = await conn.execute(
                stmt,
                {"user_id": user_id, "thread_id": thread_id},
            )
            row = result.first()

            if not row:
                return None

            return {
                "crop_category": row[0],
                "specific_crop": row[1],
                "region": row[2],
                "farm_size_ha": row[3],
                "experience_level": row[4],
                "soil_type": row[5],
                "irrigation_type": row[6],
                "current_month": row[7],
                "action_categories": json.loads(row[8]) if row[8] else [],
                "expertise_areas": json.loads(row[9]) if row[9] else [],
                "smart_question": row[10],
                "user_confirmed": row[11],
                "conversation_stage": row[12],
                "settings_version": row[13],
            }
    except Exception as e:
        logger.error("load_context_error", error=str(e), user_id=user_id)
        return None


# Patch on module load
_patch_chainlit_step_serialization()


# Backward compatibility aliases
async def save_farm_scenario(user_id: str, thread_id: str, scenario: dict) -> bool:
    """Deprecated: Use save_conversation_context instead."""
    return await save_conversation_context(user_id, thread_id, scenario)


async def load_farm_scenario(user_id: str, thread_id: str) -> dict | None:
    """Deprecated: Use load_conversation_context instead."""
    return await load_conversation_context(user_id, thread_id)
