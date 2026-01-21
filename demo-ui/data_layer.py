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
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import chainlit as cl
import structlog
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.step import Step
from chainlit.user import PersistedUser, User
from sqlalchemy import text

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
    """Extended data layer with Yonca-specific functionality.

    Adds:
    - ChatSettings persistence in user metadata
    - Link to existing user_profiles table
    - Logging for debugging
    """

    async def get_user(self, identifier: str) -> PersistedUser | None:
        """Get user by identifier (email from OAuth).

        Also loads their persisted ChatSettings from metadata.
        """
        user = await super().get_user(identifier)
        if user:
            logger.debug(
                "user_loaded",
                identifier=identifier,
                has_metadata=bool(user.metadata),
            )
        return user

    async def create_user(self, user: User) -> PersistedUser | None:
        """Override to use proper UUID and ISO string for createdAt."""
        try:
            async with self.async_session() as session:
                # Use ISO string for createdAt (Chainlit uses TEXT column)
                created_at = datetime.utcnow().isoformat()

                # Generate proper UUID for id column
                user_uuid = str(uuid.uuid4())

                # Convert metadata to proper JSON string (not Python repr!)
                if isinstance(user.metadata, str):
                    metadata_json = user.metadata
                elif user.metadata is None:
                    metadata_json = "{}"
                else:
                    metadata_json = json.dumps(user.metadata)

                await session.execute(
                    text(
                        """
                        INSERT INTO users ("id", "identifier", "createdAt", "metadata")
                        VALUES (:id, :identifier, :created_at, :metadata)
                        ON CONFLICT ("identifier") DO UPDATE SET
                            "metadata" = :metadata
                    """
                    ),
                    {
                        "id": user_uuid,
                        "identifier": user.identifier,
                        "created_at": created_at,
                        "metadata": metadata_json,
                    },
                )
                await session.commit()

                logger.info(
                    "user_created_or_updated",
                    identifier=user.identifier,
                    has_metadata=bool(metadata_json and metadata_json != "{}"),
                )

                # Fetch and return
                return await self.get_user(user.identifier)

        except Exception as e:
            logger.error("create_user_failed", identifier=user.identifier, error=str(e))
            return None

    async def update_user_metadata(
        self,
        identifier: str,
        metadata: dict,
    ) -> bool:
        """Update user metadata (used for persisting ChatSettings).

        This is called when user changes settings in the sidebar.

        Args:
            identifier: User's email (from OAuth)
            metadata: Updated metadata dict including chat_settings

        Returns:
            True if update succeeded
        """
        try:
            # Get existing user
            user = await self.get_user(identifier)
            if not user:
                logger.warning("update_metadata_user_not_found", identifier=identifier)
                return False

            # Merge metadata (keep existing, update with new)
            existing_metadata = user.metadata if isinstance(user.metadata, dict) else {}
            merged_metadata = {**existing_metadata, **metadata}

            # Convert to proper JSON string
            metadata_json = json.dumps(merged_metadata)

            # Use SQLAlchemy to update
            async with self.async_session() as session:
                await session.execute(
                    text("UPDATE users SET metadata = :metadata WHERE identifier = :identifier"),
                    {"metadata": metadata_json, "identifier": identifier},
                )
                await session.commit()

            logger.info(
                "user_metadata_updated",
                identifier=identifier,
                settings_keys=list(metadata.get("chat_settings", {}).keys()),
            )
            return True

        except Exception as e:
            logger.error("update_metadata_error", error=str(e), identifier=identifier)
            return False

    async def upsert_step(self, step: "Step"):
        """Serialize tags to JSON string for JSONB column compatibility with asyncpg."""
        if isinstance(step.tags, list):
            # asyncpg requires JSON-serialized string for JSONB columns, not Python list
            step.tags = json.dumps(step.tags) if step.tags else "[]"
        elif step.tags is None:
            step.tags = "[]"
        return await super().upsert_step(step)


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
    user_id: str,
    thread_id: str,
    context: dict,
) -> bool:
    """Persist conversation context to database.

    Stores the conversation parameters that define agent behavior:
    crop type, region, expertise level, etc. These are NOT physical
    farm plans but rather agent acting instructions.

    Called when chat settings change to track conversation evolution.

    Args:
        user_id: User identifier (email)
        thread_id: Chainlit thread ID
        context: ConversationContext dict with parameters

    Returns:
        True if saved successfully
    """
    data_layer = get_data_layer()
    if not data_layer:
        logger.debug("save_context_skipped_no_datalayer")
        return False

    try:
        async with data_layer.async_session() as session:
            # Generate UUID for new context
            scenario_id = str(uuid.uuid4())

            # Insert into conversation_contexts (or view for backward compat)
            await session.execute(
                text(
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
                ),
                {
                    "scenario_id": scenario_id,
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "crop_category": context.get("crop_category"),
                    "specific_crop": context.get("specific_crop"),
                    "region": context.get("region"),
                    "farm_size_ha": context.get("farm_size_ha"),
                    "experience_level": context.get("experience_level"),
                    "soil_type": context.get("soil_type"),
                    "irrigation_type": context.get("irrigation_type"),
                    "current_month": context.get("current_month"),
                    "action_categories": json.dumps(context.get("action_categories", [])),
                    "expertise_areas": json.dumps(context.get("expertise_areas", [])),
                    "smart_question": context.get("smart_question"),
                    "user_confirmed": context.get("user_confirmed", False),
                    "conversation_stage": context.get("conversation_stage", "initial"),
                    "settings_version": context.get("settings_version", 1),
                },
            )
            await session.commit()

            logger.info(
                "conversation_context_saved",
                scenario_id=scenario_id,
                user_id=user_id,
                thread_id=thread_id,
                crop=context.get("specific_crop"),
                stage=context.get("conversation_stage"),
            )
            return True

    except Exception as e:
        logger.error("save_scenario_error", error=str(e), exc_info=True)
        return False


async def load_conversation_context(user_id: str, thread_id: str) -> dict | None:
    """Load conversation context from database.

    Retrieves the conversation parameters that define agent behavior.
    These parameters include crop type, region, expertise level, etc.

    Called on chat resume to restore conversation context.

    Args:
        user_id: User identifier (email)
        thread_id: Chainlit thread ID

    Returns:
        ConversationContext dict or None if not found
    """
    data_layer = get_data_layer()
    if not data_layer:
        return None

    try:
        async with data_layer.async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT
                        crop_category, specific_crop, region,
                        farm_size_ha, experience_level,
                        soil_type, irrigation_type, current_month,
                        action_categories, expertise_areas,
                        smart_question, user_confirmed,
                        conversation_stage, settings_version
                    FROM conversation_contexts
                    WHERE user_id = :user_id AND thread_id = :thread_id
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """
                ),
                {"user_id": user_id, "thread_id": thread_id},
            )
            row = result.fetchone()

            if not row:
                logger.debug("no_context_found", user_id=user_id, thread_id=thread_id)
                return None

            # Convert Row to dict
            context = {
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

            logger.info(
                "conversation_context_loaded",
                user_id=user_id,
                thread_id=thread_id,
                crop=context["specific_crop"],
                stage=context["conversation_stage"],
            )
            return context

    except Exception as e:
        logger.error("load_context_error", error=str(e), exc_info=True)
        return None


# Backward compatibility aliases
async def save_farm_scenario(user_id: str, thread_id: str, scenario: dict) -> bool:
    """Deprecated: Use save_conversation_context instead."""
    return await save_conversation_context(user_id, thread_id, scenario)


async def load_farm_scenario(user_id: str, thread_id: str) -> dict | None:
    """Deprecated: Use load_conversation_context instead."""
    return await load_conversation_context(user_id, thread_id)
