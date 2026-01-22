# demo-ui/data_layer.py
"""Chainlit Data Layer for ALEM.

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

import json
import os
from typing import TYPE_CHECKING, Optional

import chainlit as cl
import structlog
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

if TYPE_CHECKING:
    pass  # Type hints already imported above

logger = structlog.get_logger(__name__)

# Module-level singleton
_data_layer: Optional["YoncaDataLayer"] = None


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


class YoncaDataLayer(SQLAlchemyDataLayer):
    """Custom data layer with JSONB serialization fix.

    Chainlit's default SQLAlchemy layer has a bug where it tries to
    JSON-serialize already-serialized strings in JSONB columns (tags, metadata).

    This subclass fixes that by checking if the value is already a string
    before attempting JSON serialization.
    """

    def __init__(self, conninfo: str):
        """Initialize with connection string only.

        Args:
            conninfo: Database connection string (e.g., postgresql+asyncpg://...)
        """
        super().__init__(conninfo=conninfo)
        # REMOVED: show_logger parameter (deprecated in newer Chainlit versions)

    async def create_step(self, step_dict: dict) -> str:
        """Override to serialize tags before DB insert."""
        # Serialize tags to JSON string
        if "tags" in step_dict:
            step_dict["tags"] = _serialize_tags(step_dict["tags"])

        return await super().create_step(step_dict)

    async def update_step(self, step_dict: dict) -> None:
        """Override to serialize tags before DB update."""
        if "tags" in step_dict:
            step_dict["tags"] = _serialize_tags(step_dict["tags"])

        return await super().update_step(step_dict)


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


def get_data_layer() -> YoncaDataLayer | None:
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
        _data_layer = YoncaDataLayer(conninfo=db_url)
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
