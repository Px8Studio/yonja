# src/ALİM/agent/memory.py
"""🌾 ALİM — LangGraph checkpointer factory for session persistence.

Supports multiple backends (NO automatic fallback - explicit selection):
- 🔴 Redis (fastest) - via langgraph-checkpoint-redis
- 🐘 PostgreSQL (production) - via langgraph-checkpoint-postgres
- 💾 In-Memory (dev only) - via MemorySaver

Best Practice: Let LangGraph handle checkpointing internally.
Don't reinvent the wheel - use the official checkpointers.

Windows Note: psycopg requires SelectorEventLoop, not ProactorEventLoop.
Call configure_windows_event_loop() before using PostgreSQL checkpointer.
"""

import asyncio
import sys
from typing import Literal, Union

import structlog
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from alim.config import settings

log = structlog.get_logger()

# Service emoji constants for consistent branding
EMOJI_ALİM = "🌾"
EMOJI_REDIS = "🔴"
EMOJI_POSTGRES = "🐘"
EMOJI_MEMORY = "💾"
EMOJI_ERROR = "❌"
EMOJI_SUCCESS = "✅"

# Flag to track if Windows event loop has been configured
_windows_event_loop_configured = False


def configure_windows_event_loop() -> bool:
    """Configure Windows event loop for psycopg compatibility.

    psycopg (used by LangGraph PostgreSQL checkpointer) requires
    SelectorEventLoop on Windows, not the default ProactorEventLoop.

    This should be called early in application startup.

    Returns:
        True if configuration was applied, False otherwise.
    """
    global _windows_event_loop_configured

    if _windows_event_loop_configured:
        return False

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        _windows_event_loop_configured = True
        log.debug(f"{EMOJI_ALİM} Windows SelectorEventLoop configured for psycopg")
        return True

    return False


# Type for checkpointer backend preference
CheckpointerBackend = Literal["redis", "postgres", "memory", "auto"]

# Try to import Redis checkpointer from official package
# NOTE: LangGraph 1.x uses langgraph.checkpoint.redis (not langgraph_checkpoint_redis)
try:
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver

    REDIS_CHECKPOINTER_AVAILABLE = True
    log.debug(f"{EMOJI_ALİM} {EMOJI_REDIS} langgraph-checkpoint-redis available")
except ImportError:
    REDIS_CHECKPOINTER_AVAILABLE = False
    AsyncRedisSaver = None  # type: ignore
    log.debug(f"{EMOJI_ALİM} {EMOJI_REDIS} langgraph-checkpoint-redis not installed")

# Try to import PostgreSQL checkpointer from official package
# NOTE: LangGraph 1.x uses langgraph.checkpoint.postgres (not langgraph_checkpoint_postgres)
try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    POSTGRES_CHECKPOINTER_AVAILABLE = True
    log.debug(f"{EMOJI_ALİM} {EMOJI_POSTGRES} langgraph-checkpoint-postgres available")
except ImportError:
    POSTGRES_CHECKPOINTER_AVAILABLE = False
    AsyncPostgresSaver = None  # type: ignore
    log.debug(f"{EMOJI_ALİM} {EMOJI_POSTGRES} langgraph-checkpoint-postgres not installed")


# Type alias for checkpointer types
CheckpointerType = Union[MemorySaver, "AsyncRedisSaver", "AsyncPostgresSaver"]

# Singleton instance
_checkpointer: BaseCheckpointSaver | None = None


async def get_checkpointer_async(
    redis_url: str | None = None,
    postgres_url: str | None = None,
    backend: CheckpointerBackend = "auto",
    use_singleton: bool = True,
) -> BaseCheckpointSaver:
    """Get a LangGraph-compatible checkpointer (async version).

    Supports multiple backends with automatic fallback:
    - "redis": Force Redis (fastest, requires Redis Stack)
    - "postgres": Force PostgreSQL (production, uses existing DB)
    - "memory": Force in-memory (dev only, no persistence)
    - "auto": Try Redis → PostgreSQL → Memory (default)

    Args:
        redis_url: Redis connection URL. If None, reads from settings.redis_url
        postgres_url: PostgreSQL URL. If None, reads from settings.database_url
        backend: Which backend to use ("redis", "postgres", "memory", "auto")
        use_singleton: Whether to cache and reuse the checkpointer instance

    Returns:
        Checkpointer instance based on backend preference and availability
    """
    global _checkpointer

    # Return cached instance if singleton mode
    if use_singleton and _checkpointer is not None:
        return _checkpointer

    # Get URLs from params or settings
    redis = redis_url or settings.redis_url
    postgres = postgres_url or settings.database_url

    checkpointer: BaseCheckpointSaver

    # Backend selection logic
    # PRIORITY: Postgres (persistent) > Redis (fast but ephemeral) > Memory (dev only)
    # NOTE: On Windows, psycopg requires SelectorEventLoop, not ProactorEventLoop
    #       This means Postgres checkpointer may fail on Windows dev environments.
    #       Redis or Memory will be used as fallback.

    # 1. Try PostgreSQL first (persistent across restarts)
    if backend == "postgres" or (backend == "auto" and postgres):
        if postgres and POSTGRES_CHECKPOINTER_AVAILABLE and AsyncPostgresSaver is not None:
            try:
                # Convert asyncpg URL to psycopg format if needed
                pg_url = postgres.replace("postgresql+asyncpg://", "postgresql://")
                log.debug(f"Attempting PostgreSQL checkpointer with: {pg_url[:50]}...")

                # v3.x API: from_conn_string is an async context manager
                # We need to enter the context and keep the reference
                async_cm = AsyncPostgresSaver.from_conn_string(pg_url)
                checkpointer = await async_cm.__aenter__()

                # Setup tables (required on first use)
                await checkpointer.setup()

                log.info(
                    f"{EMOJI_ALİM} {EMOJI_POSTGRES} Using PostgreSQL checkpointer (persistent)"
                )
                if use_singleton:
                    _checkpointer = checkpointer
                return checkpointer
            except Exception as e:
                # On Windows, this commonly fails due to event loop incompatibility
                error_str = str(e)
                if "ProactorEventLoop" in error_str:
                    log.info(
                        f"{EMOJI_ALİM} PostgreSQL checkpointer not available on Windows "
                        "(ProactorEventLoop incompatibility), using Redis fallback"
                    )
                else:
                    log.warning(
                        f"{EMOJI_ALİM} {EMOJI_ERROR} PostgreSQL checkpointer failed, will try Redis",
                        error=error_str,
                    )
                if backend == "postgres":
                    raise  # Don't fallback if explicitly requested
        else:
            reasons = []
            if not postgres:
                reasons.append("no postgres_url")
            if not POSTGRES_CHECKPOINTER_AVAILABLE:
                reasons.append("langgraph-checkpoint-postgres not installed")
            log.debug(f"Skipping PostgreSQL checkpointer: {', '.join(reasons)}")

    # 2. Try Redis (fast but data lost on restart)
    if backend == "redis" or (backend == "auto" and redis):
        if redis and REDIS_CHECKPOINTER_AVAILABLE and AsyncRedisSaver is not None:
            try:
                checkpointer = AsyncRedisSaver(redis_url=redis)
                await checkpointer.asetup()
                log.info(f"{EMOJI_ALİM} {EMOJI_REDIS} Using Redis checkpointer (fast, ephemeral)")
                if use_singleton:
                    _checkpointer = checkpointer
                return checkpointer
            except Exception as e:
                log.warning(
                    f"{EMOJI_ALİM} {EMOJI_ERROR} Failed to create Redis checkpointer", error=str(e)
                )
                if backend == "redis":
                    raise  # Don't fallback if explicitly requested

    # 3. Fallback to in-memory (no persistence)
    checkpointer = MemorySaver()
    log.info(f"{EMOJI_ALİM} {EMOJI_MEMORY} Using in-memory checkpointer (no persistence)")

    if use_singleton:
        _checkpointer = checkpointer

    return checkpointer


def get_checkpointer(
    redis_url: str | None = None, use_singleton: bool = True
) -> BaseCheckpointSaver:
    """Get a LangGraph-compatible checkpointer (sync version).

    Note: For Redis/PostgreSQL support, use get_checkpointer_async() instead.
    This sync version always returns MemorySaver since async checkpointers
    require an async context for initialization.

    Args:
        redis_url: Ignored in sync version
        use_singleton: Whether to cache and reuse the checkpointer instance

    Returns:
        Cached checkpointer if available, otherwise MemorySaver

    Usage:
        # In async code (preferred for persistent storage):
        checkpointer = await get_checkpointer_async()

        # In sync code (MemorySaver only):
        checkpointer = get_checkpointer()
    """
    global _checkpointer

    # Return cached instance if available (might be from async init)
    if use_singleton and _checkpointer is not None:
        return _checkpointer

    # In sync context, we can only use MemorySaver
    checkpointer = MemorySaver()
    log.info("Using in-memory checkpointer (use get_checkpointer_async for Redis/Postgres)")

    if use_singleton:
        _checkpointer = checkpointer

    return checkpointer


def reset_checkpointer() -> None:
    """Reset the singleton checkpointer (useful for testing)."""
    global _checkpointer
    _checkpointer = None
