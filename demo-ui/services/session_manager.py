"""Session state management with database persistence.

This module ensures that user preferences, farm context, and expertise areas
survive page refreshes and browser restarts by persisting to PostgreSQL.

Architectural Role:
    Chainlit's data layer handles *storage* (saving to DB), but it does **not**
    automatically load that data back into the active session (`cl.user_session`)
    when a user logs in. `SessionManager` performs this critical "hydration" step
    (User Metadata → Active Session). Without it, this logic would clutter `app.py`.

Architecture:
    - Store session data in Chainlit's data layer (PostgreSQL)
    - Load on @cl.on_chat_start
    - Update whenever user makes changes
    - Fallback to in-memory if DB unavailable
"""

import logging
from typing import Any

import chainlit as cl

logger = logging.getLogger(__name__)


class SessionManager:
    """Unified session state management with database persistence."""

    # Schema key for storing preferences in Chainlit metadata
    PREFERENCES_KEY = "yonca_preferences"
    FARM_CONTEXT_KEY = "yonca_farm_context"
    EXPERTISE_KEY = "yonca_expertise"

    @staticmethod
    async def load_user_preferences(user_id: str) -> dict[str, Any]:
        """Load persisted user preferences from database.

        Args:
            user_id: User identifier (email for OAuth users)

        Returns:
            Dict with saved preferences or empty dict if not found
        """
        try:
            # Try to load from Chainlit's data layer if available
            from data_layer import get_data_layer

            data_layer = get_data_layer()
            if not data_layer:
                # If data layer is expected but missing, this is weird, but maybe not fatal if in-memory
                # But if we are in persistence mode, this should probably be an error.
                # For now, we log usage.
                logger.debug("session_load_no_datalayer")
                return {}

            # Query user from database
            user = await data_layer.get_user(user_id)
            if not user:
                logger.debug(f"Session load user not found: user_id={user_id}")
                return {}

            # Extract preferences from user metadata
            # Handle both Pydantic object (PersistedUser) and dict (legacy)
            if hasattr(user, "metadata"):
                metadata = user.metadata
            else:
                metadata = user.get("metadata")

            if not metadata:
                metadata = {}

            if isinstance(metadata, str):
                import json

                try:
                    metadata = json.loads(metadata) if metadata.strip() else {}
                except Exception:
                    # corrupted metadata json is bad, but maybe recoverable by resetting?
                    # Strict mode: warn deeply
                    logger.warning(f"Corrupted metadata JSON for user {user_id}")
                    metadata = {}

            preferences = metadata.get(SessionManager.PREFERENCES_KEY, {})
            logger.info(
                "session_preferences_loaded",
                user_id=user_id,
                keys=list(preferences.keys()),
            )
            return preferences

        except Exception as e:
            # STRICT MODE: Do not swallow DB errors.
            logger.error(f"❌ Session load CRITICAL FAILURE: user_id={user_id}", exc_info=True)
            raise e

    @staticmethod
    async def save_user_preferences(user_id: str, preferences: dict[str, Any]) -> bool:
        """Persist user preferences to database.

        Args:
            user_id: User identifier (email for OAuth users)
            preferences: Dict of preferences to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            from data_layer import get_data_layer

            data_layer = get_data_layer()
            if not data_layer:
                logger.debug("session_save_no_datalayer")
                return False

            # Get current user
            user = await data_layer.get_user(user_id)
            if not user:
                logger.warning(f"Session save user not found: user_id={user_id}")
                return False

            # Merge into metadata
            # Handle both Pydantic object (PersistedUser) and dict (legacy)
            if hasattr(user, "metadata"):
                metadata = user.metadata
            else:
                metadata = user.get("metadata")

            if not metadata:
                metadata = {}
            if isinstance(metadata, str):
                import json

                try:
                    metadata = json.loads(metadata) if metadata.strip() else {}
                except Exception:
                    metadata = {}

            metadata[SessionManager.PREFERENCES_KEY] = preferences

            # Save back to database
            import json

            await data_layer.update_user(
                user_id=user_id,
                metadata=json.dumps(metadata),  # Metadata must be JSON string
            )

            logger.info(
                "session_preferences_saved",
                user_id=user_id,
                keys=list(preferences.keys()),
            )
            return True

        except Exception as e:
            # STRICT MODE: Do not swallow save errors.
            logger.error(f"❌ Session save CRITICAL FAILURE: user_id={user_id}", exc_info=True)
            raise e

    @staticmethod
    async def restore_session(user_id: str) -> None:
        """Restore user session state from database on page refresh.

        Populates cl.user_session with persisted values:
        - Chat profile (mode selection)
        - Farm selection
        - Expertise areas
        - Custom preferences (language, detail level, etc.)

        Call this in @cl.on_chat_start AFTER loading authentication.

        Args:
            user_id: User identifier (email for OAuth users)
        """
        try:
            preferences = await SessionManager.load_user_preferences(user_id)

            if not preferences:
                logger.debug(f"Session restore no preferences: user_id={user_id}")
                return

            # Restore session state
            restored_keys = []

            # Chat profile (interaction mode: Ask/Plan/Agent)
            if "chat_profile" in preferences:
                cl.user_session.set("chat_profile", preferences["chat_profile"])
                restored_keys.append("chat_profile")

            # Farm selection
            if "farm_id" in preferences:
                cl.user_session.set("farm_id", preferences["farm_id"])
                restored_keys.append("farm_id")

            # Expertise areas (for prompt customization)
            if "expertise_areas" in preferences:
                cl.user_session.set("expertise_areas", preferences["expertise_areas"])
                restored_keys.append("expertise_areas")

            # Custom settings
            if "language" in preferences:
                cl.user_session.set(
                    "user_preferences",
                    {
                        **cl.user_session.get("user_preferences", {}),
                        "language": preferences["language"],
                    },
                )
                restored_keys.append("language")

            if "detail_level" in preferences:
                cl.user_session.set(
                    "user_preferences",
                    {
                        **cl.user_session.get("user_preferences", {}),
                        "detail_level": preferences["detail_level"],
                    },
                )
                restored_keys.append("detail_level")

            logger.info(
                "session_restored",
                user_id=user_id,
                restored_keys=restored_keys,
            )

        except Exception as e:
            logger.warning(f"Session restore failed: user_id={user_id}, error={str(e)}")

    @staticmethod
    async def save_interaction_mode(user_id: str, mode: str) -> bool:
        """Save selected interaction mode (Ask/Plan/Agent).

        Called when user changes the chat profile dropdown.

        Args:
            user_id: User identifier
            mode: Mode name (Ask, Plan, or Agent)

        Returns:
            True if saved successfully
        """
        try:
            preferences = await SessionManager.load_user_preferences(user_id)
            preferences["chat_profile"] = mode
            return await SessionManager.save_user_preferences(user_id, preferences)
        except Exception as e:
            logger.warning(
                f"Session save mode failed: user_id={user_id}, mode={mode}, error={str(e)}"
            )
            return False

    @staticmethod
    async def save_farm_selection(user_id: str, farm_id: str) -> bool:
        """Save selected farm for this user.

        Called when user changes the farm selector.

        Args:
            user_id: User identifier
            farm_id: Selected farm ID

        Returns:
            True if saved successfully
        """
        try:
            preferences = await SessionManager.load_user_preferences(user_id)
            preferences["farm_id"] = farm_id
            return await SessionManager.save_user_preferences(user_id, preferences)
        except Exception as e:
            logger.warning(
                "session_save_farm_failed", user_id=user_id, farm_id=farm_id, error=str(e)
            )
            return False

    @staticmethod
    async def save_expertise_areas(user_id: str, expertise_areas: list[str]) -> bool:
        """Save user's selected expertise areas for prompt customization.

        Called when user changes expertise selection in chat settings.

        Args:
            user_id: User identifier
            expertise_areas: List of expertise area IDs

        Returns:
            True if saved successfully
        """
        try:
            preferences = await SessionManager.load_user_preferences(user_id)
            preferences["expertise_areas"] = expertise_areas
            return await SessionManager.save_user_preferences(user_id, preferences)
        except Exception as e:
            logger.warning(
                "session_save_expertise_failed",
                user_id=user_id,
                expertise_count=len(expertise_areas),
                error=str(e),
            )
            return False

    @staticmethod
    async def save_custom_preferences(
        user_id: str,
        language: str | None = None,
        detail_level: str | None = None,
        show_thinking_steps: bool | None = None,
        enable_feedback: bool | None = None,
    ) -> bool:
        """Save various user preference settings from chat settings panel.

        Args:
            user_id: User identifier
            language: Language preference (Azərbaycanca, English, Русский)
            detail_level: Response detail level (Qısa, Orta, Ətraflı)
            show_thinking_steps: Whether to show thinking steps
            enable_feedback: Whether to show feedback buttons

        Returns:
            True if saved successfully
        """
        try:
            preferences = await SessionManager.load_user_preferences(user_id)

            if language:
                preferences["language"] = language
            if detail_level:
                preferences["detail_level"] = detail_level
            if show_thinking_steps is not None:
                preferences["show_thinking_steps"] = show_thinking_steps
            if enable_feedback is not None:
                preferences["enable_feedback"] = enable_feedback

            return await SessionManager.save_user_preferences(user_id, preferences)

        except Exception as e:
            logger.warning(f"Session save preferences failed: user_id={user_id}, error={str(e)}")
            return False

    @staticmethod
    def get_session_state(key: str, default: Any = None) -> Any:
        """Get value from in-memory session (wrapper for cl.user_session.get).

        Use this for consistent session access across the app.

        Args:
            key: Session key
            default: Default value if not found

        Returns:
            Session value or default
        """
        try:
            return cl.user_session.get(key, default)
        except Exception:
            return default

    @staticmethod
    def set_session_state(key: str, value: Any) -> None:
        """Set value in in-memory session (wrapper for cl.user_session.set).

        Use this for consistent session access across the app.

        Args:
            key: Session key
            value: Value to store
        """
        try:
            cl.user_session.set(key, value)
        except Exception as e:
            logger.warning(f"Session set failed: key={key}, error={str(e)}")


# ============================================
# INITIALIZATION HOOK
# ============================================
# Call this in @cl.on_chat_start AFTER user authentication


async def initialize_session_with_persistence(user_id: str, user_email: str | None = None):
    """Complete initialization: restore persisted data + set up defaults.

    This function:
    1. Loads user's previous preferences from database
    2. Restores session state from previous sessions
    3. Falls back to smart defaults if no persisted data
    4. Logs initialization results

    Call in @cl.on_chat_start after user authentication.

    Args:
        user_id: User identifier (email for OAuth users, or "anonymous")
        user_email: User's email (for database queries, optional)
    """
    logger.info(f"Session initialization start: user_id={user_id}, user_email={user_email}")

    # If authenticated, restore from database
    if user_id != "anonymous" and user_email:
        await SessionManager.restore_session(user_email)

    # Log what's in the session now
    session_state = {
        "farm_id": SessionManager.get_session_state("farm_id"),
        "chat_profile": SessionManager.get_session_state("chat_profile"),
        "expertise_areas": SessionManager.get_session_state("expertise_areas"),
        "thread_id": SessionManager.get_session_state("thread_id"),
    }

    logger.info(f"Session initialization complete: user_id={user_id}, session={session_state}")
