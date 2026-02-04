# src/ALİM/data/cache.py
"""Redis caching layer for repositories.

Provides cached access to frequently-used data:
- User profiles and contexts
- Farm profiles and contexts
- NDVI readings

Implements cache-aside pattern with configurable TTL.
"""

import json
from typing import Any

from alim.data.redis_client import get_redis


class CacheKeys:
    """Cache key patterns."""

    USER_CONTEXT = "user:context:{user_id}"
    FARM_CONTEXT = "farm:context:{farm_id}"
    USER_FARMS = "user:farms:{user_id}"
    FARM_NDVI = "farm:ndvi:{farm_id}"
    FARM_CROPS = "farm:crops:{farm_id}"

    @classmethod
    def user_context(cls, user_id: str) -> str:
        return cls.USER_CONTEXT.format(user_id=user_id)

    @classmethod
    def farm_context(cls, farm_id: str) -> str:
        return cls.FARM_CONTEXT.format(farm_id=farm_id)

    @classmethod
    def user_farms(cls, user_id: str) -> str:
        return cls.USER_FARMS.format(user_id=user_id)

    @classmethod
    def farm_ndvi(cls, farm_id: str) -> str:
        return cls.FARM_NDVI.format(farm_id=farm_id)

    @classmethod
    def farm_crops(cls, farm_id: str) -> str:
        return cls.FARM_CROPS.format(farm_id=farm_id)


class RepositoryCache:
    """Caching layer for repository data.

    Implements cache-aside pattern:
    1. Check cache first
    2. If miss, query database
    3. Store result in cache
    4. Return result

    TTL defaults:
    - User context: 1 hour
    - Farm context: 30 minutes (more dynamic)
    - NDVI data: 15 minutes (frequently updated)
    """

    # TTL in seconds
    TTL_USER_CONTEXT = 3600  # 1 hour
    TTL_FARM_CONTEXT = 1800  # 30 minutes
    TTL_NDVI = 900  # 15 minutes
    TTL_CROPS = 1800  # 30 minutes

    @classmethod
    async def get_user_context(cls, user_id: str) -> dict | None:
        """Get cached user context.

        Args:
            user_id: User ID

        Returns:
            Cached context dict or None if not cached
        """
        async with get_redis() as redis:
            key = CacheKeys.user_context(user_id)
            data = await redis.get(key)
            if data:
                return json.loads(data)
            return None

    @classmethod
    async def set_user_context(cls, user_id: str, context: dict) -> None:
        """Cache user context.

        Args:
            user_id: User ID
            context: Context dict to cache
        """
        async with get_redis() as redis:
            key = CacheKeys.user_context(user_id)
            await redis.set(key, json.dumps(context), ex=cls.TTL_USER_CONTEXT)

    @classmethod
    async def invalidate_user_context(cls, user_id: str) -> None:
        """Invalidate cached user context.

        Args:
            user_id: User ID
        """
        async with get_redis() as redis:
            key = CacheKeys.user_context(user_id)
            await redis.delete(key)

    @classmethod
    async def get_farm_context(cls, farm_id: str) -> dict | None:
        """Get cached farm context.

        Args:
            farm_id: Farm ID

        Returns:
            Cached context dict or None if not cached
        """
        async with get_redis() as redis:
            key = CacheKeys.farm_context(farm_id)
            data = await redis.get(key)
            if data:
                return json.loads(data)
            return None

    @classmethod
    async def set_farm_context(cls, farm_id: str, context: dict) -> None:
        """Cache farm context.

        Args:
            farm_id: Farm ID
            context: Context dict to cache
        """
        async with get_redis() as redis:
            key = CacheKeys.farm_context(farm_id)
            await redis.set(key, json.dumps(context), ex=cls.TTL_FARM_CONTEXT)

    @classmethod
    async def invalidate_farm_context(cls, farm_id: str) -> None:
        """Invalidate cached farm context.

        Args:
            farm_id: Farm ID
        """
        async with get_redis() as redis:
            key = CacheKeys.farm_context(farm_id)
            await redis.delete(key)

    @classmethod
    async def get_farm_ndvi(cls, farm_id: str) -> list | None:
        """Get cached NDVI readings.

        Args:
            farm_id: Farm ID

        Returns:
            Cached NDVI list or None if not cached
        """
        async with get_redis() as redis:
            key = CacheKeys.farm_ndvi(farm_id)
            data = await redis.get(key)
            if data:
                return json.loads(data)
            return None

    @classmethod
    async def set_farm_ndvi(cls, farm_id: str, readings: list) -> None:
        """Cache NDVI readings.

        Args:
            farm_id: Farm ID
            readings: List of NDVI reading dicts
        """
        async with get_redis() as redis:
            key = CacheKeys.farm_ndvi(farm_id)
            await redis.set(key, json.dumps(readings), ex=cls.TTL_NDVI)

    @classmethod
    async def get_farm_crops(cls, farm_id: str) -> list | None:
        """Get cached active crops.

        Args:
            farm_id: Farm ID

        Returns:
            Cached crops list or None if not cached
        """
        async with get_redis() as redis:
            key = CacheKeys.farm_crops(farm_id)
            data = await redis.get(key)
            if data:
                return json.loads(data)
            return None

    @classmethod
    async def set_farm_crops(cls, farm_id: str, crops: list) -> None:
        """Cache active crops.

        Args:
            farm_id: Farm ID
            crops: List of active crop dicts
        """
        async with get_redis() as redis:
            key = CacheKeys.farm_crops(farm_id)
            await redis.set(key, json.dumps(crops), ex=cls.TTL_CROPS)

    @classmethod
    async def invalidate_all_for_user(cls, user_id: str) -> None:
        """Invalidate all caches for a user.

        Args:
            user_id: User ID
        """
        async with get_redis() as redis:
            # Delete user context
            await redis.delete(CacheKeys.user_context(user_id))

            # Delete user farms list
            farms_key = CacheKeys.user_farms(user_id)
            farms_data = await redis.get(farms_key)
            if farms_data:
                farm_ids = json.loads(farms_data)
                # Delete each farm's context
                for farm_id in farm_ids:
                    await redis.delete(CacheKeys.farm_context(farm_id))
                    await redis.delete(CacheKeys.farm_ndvi(farm_id))
                    await redis.delete(CacheKeys.farm_crops(farm_id))
            await redis.delete(farms_key)

    @classmethod
    async def cache_user_farms(cls, user_id: str, farm_ids: list[str]) -> None:
        """Cache list of farm IDs for a user.

        Args:
            user_id: User ID
            farm_ids: List of farm IDs
        """
        async with get_redis() as redis:
            key = CacheKeys.user_farms(user_id)
            await redis.set(key, json.dumps(farm_ids), ex=cls.TTL_USER_CONTEXT)


class CachedUserRepository:
    """Cached wrapper for UserRepository.

    Provides cache-aside pattern for user context queries.
    """

    def __init__(self, repo: Any):
        """Initialize with underlying repository.

        Args:
            repo: UserRepository instance
        """
        self.repo = repo

    async def get_context_for_ai(self, user_id: str) -> dict | None:
        """Get user context with caching.

        Args:
            user_id: User ID

        Returns:
            User context dict
        """
        # Check cache first
        cached = await RepositoryCache.get_user_context(user_id)
        if cached is not None:
            return cached

        # Cache miss - query database
        context = await self.repo.get_context_for_ai(user_id)

        if context is not None:
            # Store in cache
            await RepositoryCache.set_user_context(user_id, context)

            # Also cache farm IDs for invalidation
            await RepositoryCache.cache_user_farms(
                user_id,
                context.get("farm_ids", []),
            )

        return context


class CachedFarmRepository:
    """Cached wrapper for FarmRepository.

    Provides cache-aside pattern for farm context queries.
    """

    def __init__(self, repo: Any):
        """Initialize with underlying repository.

        Args:
            repo: FarmRepository instance
        """
        self.repo = repo

    async def get_context_for_ai(self, farm_id: str) -> dict | None:
        """Get farm context with caching.

        Args:
            farm_id: Farm ID

        Returns:
            Farm context dict
        """
        # Check cache first
        cached = await RepositoryCache.get_farm_context(farm_id)
        if cached is not None:
            return cached

        # Cache miss - query database
        context = await self.repo.get_context_for_ai(farm_id)

        if context is not None:
            # Store in cache
            await RepositoryCache.set_farm_context(farm_id, context)

        return context

    async def get_active_crops(self, farm_id: str) -> list:
        """Get active crops with caching.

        Args:
            farm_id: Farm ID

        Returns:
            List of active crop dicts
        """
        # Check cache first
        cached = await RepositoryCache.get_farm_crops(farm_id)
        if cached is not None:
            return cached

        # Cache miss - query database
        crops = await self.repo.get_active_crops(farm_id)

        if crops:
            # Store in cache
            await RepositoryCache.set_farm_crops(farm_id, crops)

        return crops

    async def get_recent_ndvi(self, farm_id: str, days: int = 30) -> list:
        """Get recent NDVI with caching.

        Args:
            farm_id: Farm ID
            days: Number of days to look back

        Returns:
            List of NDVI reading dicts
        """
        # Check cache first
        cached = await RepositoryCache.get_farm_ndvi(farm_id)
        if cached is not None:
            return cached

        # Cache miss - query database
        readings = await self.repo.get_recent_ndvi(farm_id, days)

        if readings:
            # Store in cache
            await RepositoryCache.set_farm_ndvi(farm_id, readings)

        return readings
