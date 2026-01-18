# src/yonca/api/middleware/__init__.py
"""FastAPI middleware for multi-user scalability.

Provides:
- Rate limiting with Redis-backed sliding window
- Request throttling for expensive LLM operations
- Client identification for per-user limits
- JWT authentication with mock mode for development
"""

from yonca.api.middleware.rate_limit import (
    RateLimitMiddleware,
    RateLimiter,
    RateLimitExceeded,
    chat_limiter,
    standard_limiter,
    read_limiter,
    check_rate_limit,
    get_client_identifier,
)
from yonca.api.middleware.auth import (
    JWTAuthenticator,
    AuthenticatedUser,
    TokenPayload,
    require_auth,
    optional_auth,
    create_token,
    get_authenticator,
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
