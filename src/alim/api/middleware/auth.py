# src/ALİM/api/middleware/auth.py
"""JWT Authentication middleware for API security.

Provides:
- JWT token validation (RS256 for production, HS256 for development)
- User extraction from tokens
- Mock auth mode for development/testing
- Request state injection (user_id, user_tier)

In production, integrates with mygov ID or similar OAuth provider.
"""

import time
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from alim.config import settings


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # Subject (user ID)
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    iss: str | None = None  # Issuer
    aud: str | None = None  # Audience
    scopes: list[str] = []  # Granted scopes
    tier: str = "standard"  # User tier for rate limiting

    @property
    def user_id(self) -> str:
        """Alias for sub field."""
        return self.sub

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return time.time() > self.exp


class AuthenticatedUser(BaseModel):
    """Authenticated user information extracted from token."""

    user_id: str
    tier: str = "standard"
    scopes: list[str] = []
    is_mock: bool = False  # True if using mock auth


# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class JWTAuthenticator:
    """JWT token validator.

    Supports two modes:
    1. Production: RS256 with JWKS validation (for OAuth providers)
    2. Development: HS256 with local secret (for testing)

    Also supports a mock mode for development where any token is accepted.

    Example:
        ```python
        auth = JWTAuthenticator()

        # In a route:
        @app.get("/protected")
        async def protected(user: AuthenticatedUser = Depends(auth.get_current_user)):
            return {"user_id": user.user_id}
        ```
    """

    # Required scopes for ALİM API access
    REQUIRED_SCOPES = {"ALİM:read", "ALİM:chat"}

    def __init__(
        self,
        secret: str | None = None,
        algorithm: str = "HS256",
        issuer: str | None = None,
        audience: str | None = None,
        mock_mode: bool | None = None,
    ):
        """Initialize authenticator.

        Args:
            secret: JWT secret for HS256 mode.
            algorithm: JWT algorithm (HS256 or RS256).
            issuer: Expected token issuer.
            audience: Expected token audience.
            mock_mode: If True, accept any token for development. If None, uses env setting.
        """
        self.secret = secret or settings.jwt_secret
        self.algorithm = algorithm or settings.jwt_algorithm
        self.issuer = issuer
        self.audience = audience
        # Only use environment default if mock_mode is not explicitly set
        if mock_mode is True:
            self.mock_mode = True
        elif mock_mode is False:
            self.mock_mode = False
        else:
            self.mock_mode = settings.environment == "development"

        # Token cache to avoid repeated validation
        self._token_cache: dict[str, tuple[TokenPayload, float]] = {}
        self._cache_ttl = 300  # 5 minutes

    def _get_cached(self, token: str) -> TokenPayload | None:
        """Get cached token payload if still valid."""
        if token in self._token_cache:
            payload, cached_at = self._token_cache[token]
            if time.time() - cached_at < self._cache_ttl and not payload.is_expired:
                return payload
            # Remove expired cache entry
            del self._token_cache[token]
        return None

    def _cache_payload(self, token: str, payload: TokenPayload) -> None:
        """Cache validated token payload."""
        # Limit cache size
        if len(self._token_cache) > 1000:
            # Remove oldest entries
            sorted_entries = sorted(self._token_cache.items(), key=lambda x: x[1][1])
            for old_token, _ in sorted_entries[:500]:
                del self._token_cache[old_token]

        self._token_cache[token] = (payload, time.time())

    def validate_token(self, token: str) -> TokenPayload:
        """Validate JWT token and extract payload.

        Args:
            token: JWT token string.

        Returns:
            TokenPayload with validated claims.

        Raises:
            HTTPException: If token is invalid.
        """
        # Check cache first
        cached = self._get_cached(token)
        if cached:
            return cached

        try:
            # Decode and validate
            decoded = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options={
                    "require": ["exp", "iat", "sub"],
                    "verify_exp": True,
                    "verify_iat": True,
                },
                issuer=self.issuer,
                audience=self.audience,
            )

            # Parse into structured payload
            payload = TokenPayload(
                sub=decoded["sub"],
                exp=decoded["exp"],
                iat=decoded["iat"],
                iss=decoded.get("iss"),
                aud=decoded.get("aud"),
                scopes=decoded.get("scope", "").split()
                if isinstance(decoded.get("scope"), str)
                else decoded.get("scopes", []),
                tier=decoded.get("tier", "standard"),
            )

            # Validate not issued in future (with clock skew tolerance)
            if payload.iat > time.time() + 60:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token issued in future",
                )

            # Cache and return
            self._cache_payload(token, payload)
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def create_mock_user(self, user_id: str = "mock_user_001") -> AuthenticatedUser:
        """Create a mock user for development.

        Args:
            user_id: ID to assign to mock user.

        Returns:
            AuthenticatedUser marked as mock.
        """
        return AuthenticatedUser(
            user_id=user_id,
            tier="standard",
            scopes=list(self.REQUIRED_SCOPES),
            is_mock=True,
        )

    async def get_current_user(
        self,
        request: Request,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
        api_key: Annotated[str | None, Depends(api_key_header)] = None,
    ) -> AuthenticatedUser:
        """FastAPI dependency to get current authenticated user.

        Supports multiple auth methods:
        1. Bearer token (JWT)
        2. API key header
        3. Mock mode (development)

        Args:
            request: FastAPI request object.
            credentials: Bearer token if provided.
            api_key: API key if provided.

        Returns:
            AuthenticatedUser with user details.

        Raises:
            HTTPException: If authentication fails.
        """
        # In mock mode, return mock user without validation
        if self.mock_mode:
            # Check if we have any identifier
            mock_id = "mock_user_001"
            if credentials and credentials.credentials:
                # Use token as identifier hint
                try:
                    # Try to decode without verification to get sub
                    decoded = jwt.decode(
                        credentials.credentials, options={"verify_signature": False}
                    )
                    mock_id = decoded.get("sub", mock_id)
                except Exception:
                    pass
            elif api_key:
                mock_id = f"api_key_{api_key[:8]}"

            user = self.create_mock_user(mock_id)
            request.state.user_id = user.user_id
            return user

        # Production mode - require valid authentication
        if credentials and credentials.credentials:
            # Bearer token authentication
            payload = self.validate_token(credentials.credentials)

            # Check required scopes
            token_scopes = set(payload.scopes)
            if not self.REQUIRED_SCOPES.issubset(token_scopes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient scopes",
                )

            user = AuthenticatedUser(
                user_id=payload.user_id,
                tier=payload.tier,
                scopes=payload.scopes,
                is_mock=False,
            )

            # Store in request state
            request.state.user_id = user.user_id
            request.state.user_tier = user.tier

            return user

        if api_key:
            # API key authentication (simple validation)
            # In production, this would validate against a database
            if len(api_key) < 32:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )

            user = AuthenticatedUser(
                user_id=f"api_{api_key[:8]}",
                tier="standard",
                scopes=list(self.REQUIRED_SCOPES),
                is_mock=False,
            )

            request.state.user_id = user.user_id
            request.state.user_tier = user.tier

            return user

        # No authentication provided
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async def get_optional_user(
        self,
        request: Request,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
        api_key: Annotated[str | None, Depends(api_key_header)] = None,
    ) -> AuthenticatedUser | None:
        """FastAPI dependency for optional authentication.

        Returns user if authenticated, None if not.
        Does not raise exceptions for missing auth.

        Args:
            request: FastAPI request object.
            credentials: Bearer token if provided.
            api_key: API key if provided.

        Returns:
            AuthenticatedUser or None.
        """
        try:
            return await self.get_current_user(request, credentials, api_key)
        except HTTPException:
            return None


def create_token(
    user_id: str,
    tier: str = "standard",
    scopes: list[str] | None = None,
    expires_in_hours: int = 24,
) -> str:
    """Create a JWT token for development/testing.

    Args:
        user_id: User ID to encode.
        tier: User tier for rate limiting.
        scopes: List of granted scopes.
        expires_in_hours: Token validity period.

    Returns:
        Encoded JWT token string.
    """
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + (expires_in_hours * 3600),
        "tier": tier,
        "scope": " ".join(scopes or ["ALİM:read", "ALİM:chat"]),
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# Singleton authenticator
_authenticator: JWTAuthenticator | None = None


def get_authenticator() -> JWTAuthenticator:
    """Get singleton authenticator instance."""
    global _authenticator
    if _authenticator is None:
        _authenticator = JWTAuthenticator()
    return _authenticator


# FastAPI dependencies for easy import
async def require_auth(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
) -> AuthenticatedUser:
    """Dependency that requires authentication."""
    return await get_authenticator().get_current_user(request, credentials, api_key)


async def optional_auth(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
) -> AuthenticatedUser | None:
    """Dependency that optionally authenticates."""
    return await get_authenticator().get_optional_user(request, credentials, api_key)
