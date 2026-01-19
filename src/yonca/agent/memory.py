# src/yonca/agent/memory.py
"""LangGraph checkpointer factory for session persistence.

Uses the official langgraph-checkpoint-redis package for Redis persistence,
with automatic fallback to in-memory storage for development.

Best Practice: Let LangGraph handle checkpointing internally.
Don't reinvent the wheel - use the official AsyncRedisSaver.
"""

from typing import Optional, Union

import structlog
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver

from yonca.config import settings


log = structlog.get_logger()

# Try to import Redis checkpointer from official package
try:
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver
    REDIS_CHECKPOINTER_AVAILABLE = True
except ImportError:
    REDIS_CHECKPOINTER_AVAILABLE = False
    AsyncRedisSaver = None  # type: ignore
    log.warning("langgraph-checkpoint-redis not installed, Redis persistence unavailable")


# Type alias for checkpointer types
CheckpointerType = Union[MemorySaver, "AsyncRedisSaver"]

# Singleton instance
_checkpointer: Optional[BaseCheckpointSaver] = None


async def get_checkpointer_async(
    redis_url: Optional[str] = None, 
    use_singleton: bool = True
) -> BaseCheckpointSaver:
    """Get a LangGraph-compatible checkpointer (async version).
    
    This version properly initializes AsyncRedisSaver within an async context.
    
    Args:
        redis_url: Redis connection URL. If None, reads from settings.redis_url
        use_singleton: Whether to cache and reuse the checkpointer instance
        
    Returns:
        AsyncRedisSaver if Redis is available, otherwise MemorySaver
    """
    global _checkpointer
    
    # Return cached instance if singleton mode
    if use_singleton and _checkpointer is not None:
        return _checkpointer
    
    # Get Redis URL from param or settings
    url = redis_url or settings.redis_url
    
    checkpointer: BaseCheckpointSaver
    
    if url and REDIS_CHECKPOINTER_AVAILABLE and AsyncRedisSaver is not None:
        try:
            # Use direct instantiation - AsyncRedisSaver manages its own lifecycle
            checkpointer = AsyncRedisSaver(redis_url=url)
            # Setup indexes (required on first use)
            await checkpointer.asetup()
            log.info("Using Redis checkpointer for session persistence", redis_url=url)
        except Exception as e:
            log.warning("Failed to create Redis checkpointer, falling back to memory", error=str(e))
            checkpointer = MemorySaver()
            log.info("Using in-memory checkpointer (no persistence across restarts)")
    else:
        checkpointer = MemorySaver()
        log.info("Using in-memory checkpointer (no persistence across restarts)")
    
    if use_singleton:
        _checkpointer = checkpointer
    
    return checkpointer


def get_checkpointer(
    redis_url: Optional[str] = None, 
    use_singleton: bool = True
) -> BaseCheckpointSaver:
    """Get a LangGraph-compatible checkpointer (sync version with MemorySaver fallback).
    
    Note: For Redis support in async contexts, use get_checkpointer_async() instead.
    This sync version will always return MemorySaver since AsyncRedisSaver 
    requires an async context for initialization.
    
    Args:
        redis_url: Redis connection URL (ignored in sync version)
        use_singleton: Whether to cache and reuse the checkpointer instance
        
    Returns:
        Cached checkpointer if available, otherwise MemorySaver
        
    Usage:
        # In async code (preferred for Redis support):
        checkpointer = await get_checkpointer_async()
        
        # In sync code (MemorySaver only):
        checkpointer = get_checkpointer()
    """
    global _checkpointer
    
    # Return cached instance if available (might be AsyncRedisSaver from async init)
    if use_singleton and _checkpointer is not None:
        return _checkpointer
    
    # In sync context, we can only use MemorySaver
    # For Redis, use get_checkpointer_async() in an async context
    checkpointer = MemorySaver()
    log.info("Using in-memory checkpointer (use get_checkpointer_async for Redis)")
    
    if use_singleton:
        _checkpointer = checkpointer
    
    return checkpointer


def reset_checkpointer() -> None:
    """Reset the singleton checkpointer (useful for testing)."""
    global _checkpointer
    _checkpointer = None
