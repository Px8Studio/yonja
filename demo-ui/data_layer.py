# demo-ui/data_layer.py
"""Chainlit Data Layer for Yonca AI.

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

import os
from typing import TYPE_CHECKING

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
import structlog

if TYPE_CHECKING:
    from chainlit.user import PersistedUser

logger = structlog.get_logger(__name__)


def get_database_url() -> str:
    """Get async database URL for Chainlit data layer.
    
    Chainlit's SQLAlchemy layer requires asyncpg for Postgres.
    Converts standard postgres:// URLs to postgresql+asyncpg://
    
    Returns:
        Async-compatible database URL
    """
    # Try demo-ui specific setting first, then fall back to main app
    db_url = os.getenv(
        "CHAINLIT_DATABASE_URL",
        os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/yonca.db")
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
    
    async def get_user(self, identifier: str) -> "PersistedUser | None":
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
    
    async def create_user(self, user: cl.User) -> "PersistedUser | None":
        """Create a new user from OAuth callback.
        
        Initializes default ChatSettings in metadata.
        """
        # Ensure metadata exists and has default settings
        if user.metadata is None:
            user.metadata = {}
        
        # Initialize default ChatSettings if not present
        if "chat_settings" not in user.metadata:
            user.metadata["chat_settings"] = {
                "language": "Azərbaycanca",
                "detail_level": "Orta",
                "units": "Metrik (ha, kg)",
                "notifications": True,
                "show_sources": False,
            }
        
        created_user = await super().create_user(user)
        
        if created_user:
            logger.info(
                "user_created",
                identifier=user.identifier,
                provider=user.metadata.get("provider"),
            )
        
        return created_user
    
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
            merged_metadata = {**user.metadata, **metadata}
            
            # Use SQLAlchemy to update
            async with self.async_session() as session:
                from sqlalchemy import text
                await session.execute(
                    text(
                        'UPDATE users SET metadata = :metadata WHERE identifier = :identifier'
                    ),
                    {"metadata": merged_metadata, "identifier": identifier}
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
# DATA LAYER FACTORY
# ============================================

_data_layer: YoncaDataLayer | None = None


def get_data_layer() -> YoncaDataLayer:
    """Get or create the data layer singleton.
    
    This is called by Chainlit via the @cl.data_layer decorator.
    """
    global _data_layer
    
    if _data_layer is None:
        db_url = get_database_url()
        
        # Only create if we have a real database (not SQLite for now)
        # SQLite support would require different handling
        if "sqlite" in db_url:
            logger.warning(
                "sqlite_not_supported_for_persistence",
                message="Using SQLite - data persistence disabled. Use Postgres for full persistence.",
            )
            # Return None to disable persistence (Chainlit will work without it)
            return None  # type: ignore
        
        logger.info(
            "initializing_data_layer",
            db_url=db_url.split("@")[-1] if "@" in db_url else "local",  # Hide credentials
        )
        
        _data_layer = YoncaDataLayer(
            conninfo=db_url,
            # No storage provider for now (files stored locally)
            # Add Azure/S3 storage_provider here if needed for file uploads
        )
    
    return _data_layer


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
