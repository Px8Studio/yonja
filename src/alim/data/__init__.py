# src/ALİM/data/__init__.py
"""Data layer with database, Redis, and caching.

Provides:
- Async SQLAlchemy database with connection pooling
- Redis client with session storage
- Repository pattern for clean data access
- Caching layer for frequently-used data
- Azerbaijani Faker providers for synthetic data
"""

from alim.data.cache import (
    CachedFarmRepository,
    CachedUserRepository,
    RepositoryCache,
)
from alim.data.database import (
    Base,
    close_db,
    get_db_session,
    get_session,
    init_db,
)
from alim.data.redis_client import (
    RedisClient,
    SessionStorage,
    get_redis,
)

__all__ = [
    # Database
    "Base",
    "init_db",
    "close_db",
    "get_db_session",
    "get_session",
    # Redis
    "RedisClient",
    "SessionStorage",
    "get_redis",
    # Caching
    "RepositoryCache",
    "CachedUserRepository",
    "CachedFarmRepository",
]
