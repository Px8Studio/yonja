# src/ALİM/data/redis_client.py
"""Redis client for session storage, caching, and rate limiting.

Provides async Redis connection management with connection pooling
for multi-user scalability.
"""

import json
from contextlib import asynccontextmanager
from datetime import UTC

import redis.asyncio as redis
from alim.config import settings
from redis.asyncio.connection import ConnectionPool


class RedisClient:
    """Async Redis client with connection pooling.

    Designed for 100+ concurrent users with proper connection management.

    Example:
        ```python
        async with get_redis() as client:
            await client.set("key", "value", ex=3600)
            value = await client.get("key")
        ```
    """

    _pool: ConnectionPool | None = None
    _client: redis.Redis | None = None

    @classmethod
    async def get_pool(cls) -> ConnectionPool:
        """Get or create the connection pool (singleton)."""
        if cls._pool is None:
            cls._pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=True,
            )
        return cls._pool

    @classmethod
    async def get_client(cls) -> redis.Redis:
        """Get or create the Redis client."""
        if cls._client is None:
            pool = await cls.get_pool()
            cls._client = redis.Redis(connection_pool=pool)
        return cls._client

    @classmethod
    async def close(cls) -> None:
        """Close the Redis connection pool."""
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None
        if cls._pool is not None:
            await cls._pool.disconnect()
            cls._pool = None

    @classmethod
    async def health_check(cls) -> bool:
        """Check Redis connectivity."""
        try:
            client = await cls.get_client()
            await client.ping()
            return True
        except Exception:
            return False


@asynccontextmanager
async def get_redis():
    """Context manager for Redis operations.

    Example:
        ```python
        async with get_redis() as client:
            await client.set("key", "value")
        ```
    """
    client = await RedisClient.get_client()
    try:
        yield client
    finally:
        # Connection is returned to pool, not closed
        pass


# ============================================================
# Session Storage Operations
# ============================================================


class SessionStorage:
    """Redis-backed session storage for conversation history.

    Stores per-user conversation state with automatic expiration.
    Designed for multi-turn conversations across 100+ users.

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
    """

    # Key prefix for session data
    SESSION_PREFIX = "ALİM:session:"

    # Default session TTL: 1 hour (3600 seconds)
    DEFAULT_TTL = 3600

    # Maximum messages per session to prevent memory bloat
    MAX_MESSAGES = 50

    @classmethod
    def _session_key(cls, session_id: str) -> str:
        """Generate Redis key for a session."""
        return f"{cls.SESSION_PREFIX}{session_id}"

    @classmethod
    async def get(cls, session_id: str) -> dict | None:
        """Get session data by ID.

        Args:
            session_id: The session UUID.

        Returns:
            Session data dict or None if not found.
        """
        async with get_redis() as client:
            data = await client.get(cls._session_key(session_id))
            if data:
                return json.loads(data)
            return None

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
        from datetime import datetime

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "metadata": metadata or {},
        }

        async with get_redis() as client:
            await client.setex(
                cls._session_key(session_id),
                ttl or cls.DEFAULT_TTL,
                json.dumps(session_data),
            )

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
        return await cls.create(session_id, user_id, metadata)

    @classmethod
    async def add_message(
        cls,
        session_id: str,
        role: str,
        content: str,
        ttl: int | None = None,
    ) -> dict:
        """Add a message to the session history.

        Automatically creates session if it doesn't exist.
        Trims old messages if exceeding MAX_MESSAGES.

        Args:
            session_id: The session UUID.
            role: Message role (user/assistant/system).
            content: Message content.
            ttl: Time-to-live in seconds.

        Returns:
            Updated session data.
        """
        from datetime import datetime

        session = await cls.get_or_create(session_id)

        # Add new message
        session["messages"].append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # Trim old messages if exceeding limit (keep system messages)
        if len(session["messages"]) > cls.MAX_MESSAGES:
            # Keep first message if it's a system message, trim from middle
            messages = session["messages"]
            if messages and messages[0].get("role") == "system":
                # Keep system message + last (MAX_MESSAGES - 1) messages
                session["messages"] = [messages[0]] + messages[-(cls.MAX_MESSAGES - 1) :]
            else:
                # Keep last MAX_MESSAGES messages
                session["messages"] = messages[-cls.MAX_MESSAGES :]

        session["updated_at"] = datetime.now(UTC).isoformat()

        async with get_redis() as client:
            await client.setex(
                cls._session_key(session_id),
                ttl or cls.DEFAULT_TTL,
                json.dumps(session),
            )

        return session

    @classmethod
    async def get_messages(cls, session_id: str) -> list[dict]:
        """Get all messages from a session.

        Args:
            session_id: The session UUID.

        Returns:
            List of message dicts or empty list.
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
        async with get_redis() as client:
            result = await client.delete(cls._session_key(session_id))
            return result > 0

    @classmethod
    async def extend_ttl(cls, session_id: str, ttl: int | None = None) -> bool:
        """Extend session TTL (refresh expiration).

        Args:
            session_id: The session UUID.
            ttl: New TTL in seconds.

        Returns:
            True if extended, False if session not found.
        """
        async with get_redis() as client:
            return await client.expire(
                cls._session_key(session_id),
                ttl or cls.DEFAULT_TTL,
            )

    @classmethod
    async def clear_all(cls) -> int:
        """Clear all sessions (use with caution!).

        Returns:
            Number of sessions deleted.
        """
        async with get_redis() as client:
            keys = []
            async for key in client.scan_iter(f"{cls.SESSION_PREFIX}*"):
                keys.append(key)
            if keys:
                return await client.delete(*keys)
            return 0
