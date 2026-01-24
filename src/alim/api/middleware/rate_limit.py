# src/ALİM/api/middleware/rate_limit.py
"""Rate limiting middleware using Redis sliding window.

Provides distributed rate limiting for multi-user scalability.
Uses Redis for state storage to work across multiple API instances.
"""

import time
from collections.abc import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from alim.config import settings
from alim.data.redis_client import get_redis


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Çox sayda sorğu göndərdiniz. Zəhmət olmasa bir az gözləyin.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )


class RateLimiter:
    """Redis-based sliding window rate limiter.

    Uses sorted sets for accurate sliding window counting.
    Supports different limits for different endpoints/users.

    Algorithm:
        1. Remove expired entries (outside window)
        2. Count remaining entries in window
        3. If under limit, add new entry and allow
        4. If at/over limit, reject request

    Example:
        ```python
        limiter = RateLimiter(requests_per_minute=30)
        if not await limiter.is_allowed("user:123"):
            raise RateLimitExceeded()
        ```
    """

    # Key prefix for rate limit data
    RATE_LIMIT_PREFIX = "alim:ratelimit:"

    def __init__(
        self,
        requests_per_minute: int | None = None,
        burst_limit: int | None = None,
        window_seconds: int = 60,
    ):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute (uses config default).
            burst_limit: Max burst size (uses config default).
            window_seconds: Sliding window size in seconds.
        """
        self.requests_per_minute = requests_per_minute or settings.rate_limit_requests_per_minute
        self.burst_limit = burst_limit or settings.rate_limit_burst
        self.window_seconds = window_seconds

    def _key(self, identifier: str) -> str:
        """Generate Redis key for rate limit tracking."""
        return f"{self.RATE_LIMIT_PREFIX}{identifier}"

    async def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """Check if request is allowed under rate limit.

        Args:
            identifier: Unique identifier (IP, user_id, API key).

        Returns:
            Tuple of (allowed: bool, info: dict with limit details).
        """
        now = time.time()
        window_start = now - self.window_seconds
        key = self._key(identifier)

        async with get_redis() as client:
            pipe = client.pipeline()

            # Remove entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count entries in current window
            pipe.zcard(key)

            # Add current request timestamp
            pipe.zadd(key, {str(now): now})

            # Set key expiration (cleanup)
            pipe.expire(key, self.window_seconds + 1)

            results = await pipe.execute()
            current_count = results[1]  # zcard result

        allowed = current_count < self.requests_per_minute
        remaining = max(0, self.requests_per_minute - current_count - 1)

        # Calculate retry-after if limited
        retry_after = 0
        if not allowed:
            async with get_redis() as client:
                # Get oldest entry in window
                oldest = await client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int(oldest_time + self.window_seconds - now) + 1

        info = {
            "limit": self.requests_per_minute,
            "remaining": remaining,
            "reset": int(now + self.window_seconds),
            "retry_after": retry_after,
        }

        return allowed, info

    async def get_usage(self, identifier: str) -> dict:
        """Get current rate limit usage for an identifier.

        Args:
            identifier: Unique identifier.

        Returns:
            Dict with usage statistics.
        """
        now = time.time()
        window_start = now - self.window_seconds
        key = self._key(identifier)

        async with get_redis() as client:
            # Clean and count
            await client.zremrangebyscore(key, 0, window_start)
            count = await client.zcard(key)

        return {
            "requests_used": count,
            "requests_limit": self.requests_per_minute,
            "requests_remaining": max(0, self.requests_per_minute - count),
            "window_seconds": self.window_seconds,
            "reset_at": int(now + self.window_seconds),
        }


def get_client_identifier(request: Request) -> str:
    """Extract client identifier from request.

    Priority:
        1. Authenticated user ID (from JWT/header)
        2. API key
        3. X-Forwarded-For (behind proxy)
        4. Client IP address

    Args:
        request: FastAPI request object.

    Returns:
        Unique client identifier string.
    """
    # Check for authenticated user
    if hasattr(request.state, "user_id") and request.state.user_id:
        return f"user:{request.state.user_id}"

    # Check for API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key[:16]}"  # Use prefix for privacy

    # Use IP address
    # Check X-Forwarded-For for requests behind proxy/load balancer
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take first IP in chain (original client)
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return f"ip:{client_ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting.

    Applies sliding window rate limiting to all requests.
    Adds rate limit headers to responses.

    Headers added:
        - X-RateLimit-Limit: Max requests per window
        - X-RateLimit-Remaining: Requests remaining
        - X-RateLimit-Reset: Unix timestamp when limit resets
        - Retry-After: Seconds to wait (when limited)
    """

    # Paths exempt from rate limiting
    EXEMPT_PATHS = {
        "/health",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    def __init__(self, app, limiter: RateLimiter | None = None):
        super().__init__(app)
        self.limiter = limiter or RateLimiter()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Skip rate limiting for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get client identifier
        identifier = get_client_identifier(request)

        try:
            # Check rate limit
            allowed, info = await self.limiter.is_allowed(identifier)

            if not allowed:
                # Rate limited - return 429
                raise RateLimitExceeded(retry_after=info["retry_after"])

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset"])

            return response

        except RateLimitExceeded:
            raise
        except Exception:
            # If Redis is down, allow request (fail open)
            # Log this in production
            return await call_next(request)


# ============================================================
# Endpoint-specific rate limiters
# ============================================================

# Standard rate limiter for most endpoints
standard_limiter = RateLimiter()

# Stricter limiter for chat endpoints (LLM calls are expensive)
chat_limiter = RateLimiter(
    requests_per_minute=20,  # Lower limit for expensive LLM calls
    burst_limit=30,
)

# More lenient limiter for read-only endpoints
read_limiter = RateLimiter(
    requests_per_minute=100,
    burst_limit=150,
)


async def check_rate_limit(
    request: Request,
    limiter: RateLimiter = standard_limiter,
) -> dict:
    """Dependency for checking rate limits in route handlers.

    Use this for fine-grained control over rate limiting per endpoint.

    Example:
        ```python
        @router.post("/chat")
        async def chat(
            request: Request,
            rate_info: dict = Depends(lambda r: check_rate_limit(r, chat_limiter))
        ):
            # rate_info contains limit, remaining, reset
            pass
        ```
    """
    identifier = get_client_identifier(request)
    allowed, info = await limiter.is_allowed(identifier)

    if not allowed:
        raise RateLimitExceeded(retry_after=info["retry_after"])

    return info
