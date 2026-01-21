# src/yonca/api/middleware/__init__.py
"""FastAPI middleware for multi-user scalability.

Provides:
- Rate limiting with Redis-backed sliding window
- Request throttling for expensive LLM operations
- Client identification for per-user limits
- JWT authentication with mock mode for development
"""

from yonca.api.middleware.auth import (
    AuthenticatedUser,
    JWTAuthenticator,
    TokenPayload,
    create_token,
    get_authenticator,
    optional_auth,
    require_auth,
)
from yonca.api.middleware.rate_limit import (
    RateLimiter,
    RateLimitExceeded,
    RateLimitMiddleware,
    chat_limiter,
    check_rate_limit,
    get_client_identifier,
    read_limiter,
    standard_limiter,
)

__all__ = [
    # Rate limiting
    "RateLimitMiddleware",
    "RateLimiter",
    "RateLimitExceeded",
    "chat_limiter",
    "standard_limiter",
    "read_limiter",
    "check_rate_limit",
    "get_client_identifier",
    # Authentication
    "JWTAuthenticator",
    "AuthenticatedUser",
    "TokenPayload",
    "require_auth",
    "optional_auth",
    "create_token",
    "get_authenticator",
]
