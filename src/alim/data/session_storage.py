# src/ALİM/data/session_storage.py
"""🌾 ALİM — In-memory session storage for conversation history.

Provides thread-safe session management with automatic expiration.
For single-instance deployments - no Redis required.

Note: For multi-instance (scaled) deployments, implement PostgreSQL-backed
sessions using the ALİM database.
"""

import asyncio
from datetime import UTC, datetime


class SessionStorage:
    """🌾 ALİM — In-memory session storage for conversations.

    Thread-safe implementation using asyncio locks.
    Includes automatic cleanup of expired sessions.

    Session data structure:
        {
            "session_id": "uuid",
            "user_id": "optional-user-id",
            "messages": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ],
            "created_at": "iso-timestamp",
            "updated_at": "iso-timestamp",
            "metadata": {...}
        }

    Example:
        ```python
        session = await SessionStorage.get_or_create("session-123", user_id="user-1")
        await SessionStorage.add_message("session-123", "user", "Salam!")
        messages = await SessionStorage.get_messages("session-123")
        ```
    """

    # Default session TTL: 1 hour (3600 seconds)
    DEFAULT_TTL = 3600

    # Maximum messages per session to prevent memory bloat
    MAX_MESSAGES = 50

    # In-memory storage: {session_id: {"data": {...}, "expires_at": timestamp}}
    _sessions: dict[str, dict] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get(cls, session_id: str) -> dict | None:
        """Get session data by ID.

        Args:
            session_id: The session UUID.

        Returns:
            Session data dict or None if not found/expired.
        """
        async with cls._lock:
            entry = cls._sessions.get(session_id)
            if entry is None:
                return None

            # Check expiration
            if datetime.now(UTC).timestamp() > entry["expires_at"]:
                del cls._sessions[session_id]
                return None

            return entry["data"]

    @classmethod
    async def create(
        cls,
        session_id: str,
        user_id: str | None = None,
        metadata: dict | None = None,
        ttl: int | None = None,
    ) -> dict:
        """Create a new session.

        Args:
            session_id: The session UUID.
            user_id: Optional user identifier.
            metadata: Optional metadata dict.
            ttl: Time-to-live in seconds (default: 1 hour).

        Returns:
            The created session data.
        """
        now = datetime.now(UTC)

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "metadata": metadata or {},
        }

        async with cls._lock:
            cls._sessions[session_id] = {
                "data": session_data,
                "expires_at": now.timestamp() + (ttl or cls.DEFAULT_TTL),
            }

        return session_data

    @classmethod
    async def get_or_create(
        cls,
        session_id: str,
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Get existing session or create new one.

        Args:
            session_id: The session UUID.
            user_id: Optional user identifier.
            metadata: Optional metadata dict.

        Returns:
            Session data dict.
        """
        existing = await cls.get(session_id)
        if existing:
            return existing

        return await cls.create(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata,
        )

    @classmethod
    async def update(
        cls,
        session_id: str,
        metadata: dict | None = None,
        extend_ttl: bool = True,
    ) -> dict | None:
        """Update session metadata and optionally extend TTL.

        Args:
            session_id: The session UUID.
            metadata: Metadata to merge into existing.
            extend_ttl: Whether to extend session TTL.

        Returns:
            Updated session data or None if not found.
        """
        async with cls._lock:
            entry = cls._sessions.get(session_id)
            if entry is None:
                return None

            now = datetime.now(UTC)

            # Update metadata if provided
            if metadata:
                entry["data"]["metadata"].update(metadata)

            entry["data"]["updated_at"] = now.isoformat()

            # Extend TTL if requested
            if extend_ttl:
                entry["expires_at"] = now.timestamp() + cls.DEFAULT_TTL

            return entry["data"]

    @classmethod
    async def add_message(
        cls,
        session_id: str,
        role: str,
        content: str,
        extend_ttl: bool = True,
    ) -> bool:
        """Add a message to session history.

        Args:
            session_id: The session UUID.
            role: Message role ("user" or "assistant").
            content: Message content.
            extend_ttl: Whether to extend session TTL.

        Returns:
            True if message was added, False if session not found.
        """
        async with cls._lock:
            entry = cls._sessions.get(session_id)
            if entry is None:
                return False

            now = datetime.now(UTC)

            # Add message
            entry["data"]["messages"].append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": now.isoformat(),
                }
            )

            # Trim old messages if over limit
            if len(entry["data"]["messages"]) > cls.MAX_MESSAGES:
                entry["data"]["messages"] = entry["data"]["messages"][-cls.MAX_MESSAGES :]

            entry["data"]["updated_at"] = now.isoformat()

            # Extend TTL if requested
            if extend_ttl:
                entry["expires_at"] = now.timestamp() + cls.DEFAULT_TTL

            return True

    @classmethod
    async def get_messages(cls, session_id: str) -> list[dict]:
        """Get all messages for a session.

        Args:
            session_id: The session UUID.

        Returns:
            List of message dicts or empty list if not found.
        """
        session = await cls.get(session_id)
        if session:
            return session.get("messages", [])
        return []

    @classmethod
    async def delete(cls, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: The session UUID.

        Returns:
            True if deleted, False if not found.
        """
        async with cls._lock:
            if session_id in cls._sessions:
                del cls._sessions[session_id]
                return True
            return False

    @classmethod
    async def cleanup_expired(cls) -> int:
        """Clean up all expired sessions.

        Call this periodically (e.g., every 5 minutes) to prevent memory growth.

        Returns:
            Number of sessions cleaned up.
        """
        now = datetime.now(UTC).timestamp()
        cleaned = 0

        async with cls._lock:
            expired_ids = [sid for sid, entry in cls._sessions.items() if now > entry["expires_at"]]
            for sid in expired_ids:
                del cls._sessions[sid]
                cleaned += 1

        return cleaned

    @classmethod
    async def count_active(cls) -> int:
        """Get count of active (non-expired) sessions.

        Returns:
            Number of active sessions.
        """
        now = datetime.now(UTC).timestamp()

        async with cls._lock:
            return sum(1 for entry in cls._sessions.values() if now <= entry["expires_at"])

    @classmethod
    async def clear_all(cls) -> int:
        """Clear all sessions (use for testing).

        Returns:
            Number of sessions cleared.
        """
        async with cls._lock:
            count = len(cls._sessions)
            cls._sessions.clear()
            return count
