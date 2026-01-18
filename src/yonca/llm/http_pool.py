# src/yonca/llm/http_pool.py
"""HTTP connection pool manager for LLM providers.

Provides centralized connection pool management for multi-user scalability.
Ensures proper connection limits, timeouts, and lifecycle management.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import ClassVar

import httpx


@dataclass
class PoolConfig:
    """Configuration for HTTP connection pool."""
    
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 30.0
    connect_timeout: float = 10.0
    read_timeout: float = 60.0
    write_timeout: float = 30.0
    pool_timeout: float = 10.0


class HTTPClientPool:
    """Centralized HTTP client pool manager.
    
    Manages connection pools for different LLM providers with proper
    limits and lifecycle handling for 100+ concurrent users.
    
    Design principles:
        - Shared pool per provider (not per request)
        - Configurable limits to prevent connection exhaustion
        - Automatic connection reuse and keepalive
        - Graceful shutdown with cleanup
    
    Example:
        ```python
        # Get a client for Groq API
        async with HTTPClientPool.get_client("groq") as client:
            response = await client.post("/chat/completions", json=payload)
        ```
    """
    
    # Default pool configuration
    DEFAULT_CONFIG = PoolConfig()
    
    # Provider-specific configurations
    PROVIDER_CONFIGS: ClassVar[dict[str, PoolConfig]] = {
        "groq": PoolConfig(
            max_connections=50,
            max_keepalive_connections=10,
            read_timeout=30.0,  # Groq is fast
        ),
        "gemini": PoolConfig(
            max_connections=50,
            max_keepalive_connections=10,
            read_timeout=60.0,  # Gemini may be slower
        ),
        "ollama": PoolConfig(
            max_connections=20,  # Local, fewer needed
            max_keepalive_connections=5,
            read_timeout=120.0,  # Local models can be slow
        ),
    }
    
    # Shared client pools (singleton per provider)
    _pools: ClassVar[dict[str, httpx.AsyncClient]] = {}
    
    @classmethod
    def _get_config(cls, provider: str) -> PoolConfig:
        """Get configuration for a provider."""
        return cls.PROVIDER_CONFIGS.get(provider, cls.DEFAULT_CONFIG)
    
    @classmethod
    def _create_limits(cls, config: PoolConfig) -> httpx.Limits:
        """Create httpx Limits from config."""
        return httpx.Limits(
            max_connections=config.max_connections,
            max_keepalive_connections=config.max_keepalive_connections,
            keepalive_expiry=config.keepalive_expiry,
        )
    
    @classmethod
    def _create_timeout(cls, config: PoolConfig) -> httpx.Timeout:
        """Create httpx Timeout from config."""
        return httpx.Timeout(
            connect=config.connect_timeout,
            read=config.read_timeout,
            write=config.write_timeout,
            pool=config.pool_timeout,
        )
    
    @classmethod
    async def get_pool(
        cls,
        provider: str,
        base_url: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.AsyncClient:
        """Get or create a connection pool for a provider.
        
        Args:
            provider: Provider name (groq, gemini, ollama).
            base_url: Optional base URL for the client.
            headers: Optional default headers.
            
        Returns:
            Shared AsyncClient instance for the provider.
        """
        pool_key = f"{provider}:{base_url or 'default'}"
        
        if pool_key not in cls._pools:
            config = cls._get_config(provider)
            cls._pools[pool_key] = httpx.AsyncClient(
                base_url=base_url,
                headers=headers or {},
                limits=cls._create_limits(config),
                timeout=cls._create_timeout(config),
            )
        
        return cls._pools[pool_key]
    
    @classmethod
    @asynccontextmanager
    async def get_client(
        cls,
        provider: str,
        base_url: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """Context manager for getting a client from the pool.
        
        The client is borrowed from the pool and returned after use.
        Does NOT close the client - it's managed by the pool.
        
        Args:
            provider: Provider name.
            base_url: Optional base URL.
            headers: Optional headers.
            
        Yields:
            httpx.AsyncClient from the pool.
        """
        client = await cls.get_pool(provider, base_url, headers)
        try:
            yield client
        finally:
            # Client is returned to pool, not closed
            pass
    
    @classmethod
    async def close_pool(cls, provider: str, base_url: str | None = None) -> None:
        """Close a specific provider's connection pool.
        
        Args:
            provider: Provider name.
            base_url: Optional base URL.
        """
        pool_key = f"{provider}:{base_url or 'default'}"
        if pool_key in cls._pools:
            await cls._pools[pool_key].aclose()
            del cls._pools[pool_key]
    
    @classmethod
    async def close_all(cls) -> None:
        """Close all connection pools (for shutdown)."""
        for client in cls._pools.values():
            await client.aclose()
        cls._pools.clear()
    
    @classmethod
    def get_pool_stats(cls) -> dict:
        """Get statistics about active pools.
        
        Returns:
            Dict with pool information.
        """
        stats = {}
        for key, client in cls._pools.items():
            # httpx doesn't expose internal pool stats directly
            # but we can track the pools we've created
            stats[key] = {
                "active": not client.is_closed,
                "base_url": str(client.base_url) if client.base_url else None,
            }
        return stats


# ============================================================
# Convenience functions
# ============================================================

async def get_groq_client(api_key: str, base_url: str = "https://api.groq.com/openai/v1"):
    """Get a Groq API client from the pool.
    
    Args:
        api_key: Groq API key.
        base_url: API base URL.
        
    Returns:
        Context manager yielding httpx.AsyncClient.
    """
    return HTTPClientPool.get_client(
        provider="groq",
        base_url=base_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )


async def get_gemini_client():
    """Get a Gemini API client from the pool.
    
    Note: Gemini uses query params for auth, not headers.
    
    Returns:
        Context manager yielding httpx.AsyncClient.
    """
    return HTTPClientPool.get_client(
        provider="gemini",
        headers={
            "Content-Type": "application/json",
        },
    )


async def get_ollama_client(base_url: str = "http://localhost:11434"):
    """Get an Ollama API client from the pool.
    
    Args:
        base_url: Ollama server URL.
        
    Returns:
        Context manager yielding httpx.AsyncClient.
    """
    return HTTPClientPool.get_client(
        provider="ollama",
        base_url=base_url,
        headers={
            "Content-Type": "application/json",
        },
    )
