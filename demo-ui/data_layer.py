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
