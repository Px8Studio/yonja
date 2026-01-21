# tests/unit/test_auth.py
"""Tests for JWT authentication middleware."""

import time
from unittest.mock import MagicMock

import pytest
from yonca.api.middleware.auth import (
    AuthenticatedUser,
    JWTAuthenticator,
    TokenPayload,
    create_token,
)


class TestTokenCreation:
    """Test token creation utility."""

    def test_create_token_basic(self):
        """Creates valid JWT token."""
        token = create_token("user123")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT format: header.payload.signature
        assert token.count(".") == 2

    def test_create_token_custom_tier(self):
        """Creates token with custom tier."""
        token = create_token("user123", tier="premium")

        # Decode without verification to check claims
        import jwt

        decoded = jwt.decode(token, options={"verify_signature": False})

        assert decoded["tier"] == "premium"

    def test_create_token_custom_scopes(self):
        """Creates token with custom scopes."""
        token = create_token("user123", scopes=["custom:read", "custom:write"])

        import jwt

        decoded = jwt.decode(token, options={"verify_signature": False})

        assert "custom:read" in decoded["scope"]
        assert "custom:write" in decoded["scope"]

    def test_create_token_expiry(self):
        """Creates token with correct expiry."""
        token = create_token("user123", expires_in_hours=1)

        import jwt

        decoded = jwt.decode(token, options={"verify_signature": False})

        # Should expire in ~1 hour
        expected_exp = time.time() + 3600
        assert abs(decoded["exp"] - expected_exp) < 5


class TestJWTAuthenticator:
    """Test JWT authenticator."""

    @pytest.fixture
    def authenticator(self) -> JWTAuthenticator:
        """Create authenticator instance with mock mode disabled."""
        return JWTAuthenticator(
            secret="test-secret-key-for-testing",  # pragma: allowlist secret
            mock_mode=False,
        )

    @pytest.fixture
    def mock_authenticator(self) -> JWTAuthenticator:
        """Create authenticator in mock mode."""
        return JWTAuthenticator(mock_mode=True)

    def test_validate_valid_token(self, authenticator: JWTAuthenticator):
        """Validates legitimate token."""
        # Create token with matching secret
        import jwt

        payload = {
            "sub": "user123",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "scope": "yonca:read yonca:chat",
            "tier": "standard",
        }
        token = jwt.encode(payload, "test-secret-key-for-testing", algorithm="HS256")

        result = authenticator.validate_token(token)

        assert isinstance(result, TokenPayload)
        assert result.user_id == "user123"
        assert result.tier == "standard"

    def test_validate_expired_token(self, authenticator: JWTAuthenticator):
        """Rejects expired token."""
        import jwt
        from fastapi import HTTPException

        payload = {
            "sub": "user123",
            "iat": int(time.time()) - 7200,
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        }
        token = jwt.encode(payload, "test-secret-key-for-testing", algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            authenticator.validate_token(token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_validate_invalid_signature(self, authenticator: JWTAuthenticator):
        """Rejects token with wrong signature."""
        import jwt
        from fastapi import HTTPException

        payload = {
            "sub": "user123",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            authenticator.validate_token(token)

        assert exc_info.value.status_code == 401

    def test_validate_future_issued_token(self, authenticator: JWTAuthenticator):
        """Rejects token issued in future."""
        import jwt
        from fastapi import HTTPException

        payload = {
            "sub": "user123",
            "iat": int(time.time()) + 3600,  # Issued 1 hour in future
            "exp": int(time.time()) + 7200,
        }
        token = jwt.encode(payload, "test-secret-key-for-testing", algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            authenticator.validate_token(token)

        assert exc_info.value.status_code == 401
        # JWT library returns "not yet valid" for iat in future
        assert (
            "not yet valid" in exc_info.value.detail.lower()
            or "future" in exc_info.value.detail.lower()
        )

    def test_token_caching(self, authenticator: JWTAuthenticator):
        """Caches validated tokens."""
        import jwt

        payload = {
            "sub": "user123",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "scope": "yonca:read yonca:chat",
        }
        token = jwt.encode(payload, "test-secret-key-for-testing", algorithm="HS256")

        # First validation
        result1 = authenticator.validate_token(token)

        # Second validation should use cache
        result2 = authenticator.validate_token(token)

        assert result1.user_id == result2.user_id

    def test_mock_user_creation(self, mock_authenticator: JWTAuthenticator):
        """Creates mock user for development."""
        user = mock_authenticator.create_mock_user("test_user")

        assert isinstance(user, AuthenticatedUser)
        assert user.user_id == "test_user"
        assert user.is_mock
        assert "yonca:read" in user.scopes


class TestTokenPayload:
    """Test TokenPayload model."""

    def test_user_id_alias(self):
        """user_id is alias for sub."""
        payload = TokenPayload(
            sub="user123",
            exp=int(time.time()) + 3600,
            iat=int(time.time()),
        )

        assert payload.user_id == "user123"
        assert payload.user_id == payload.sub

    def test_is_expired_false(self):
        """is_expired returns False for valid token."""
        payload = TokenPayload(
            sub="user123",
            exp=int(time.time()) + 3600,
            iat=int(time.time()),
        )

        assert not payload.is_expired

    def test_is_expired_true(self):
        """is_expired returns True for expired token."""
        payload = TokenPayload(
            sub="user123",
            exp=int(time.time()) - 100,  # Expired
            iat=int(time.time()) - 200,
        )

        assert payload.is_expired


class TestAuthenticatedUser:
    """Test AuthenticatedUser model."""

    def test_authenticated_user_creation(self):
        """Creates authenticated user."""
        user = AuthenticatedUser(
            user_id="user123",
            tier="premium",
            scopes=["read", "write"],
            is_mock=False,
        )

        assert user.user_id == "user123"
        assert user.tier == "premium"
        assert "read" in user.scopes
        assert not user.is_mock

    def test_authenticated_user_defaults(self):
        """Uses default values."""
        user = AuthenticatedUser(user_id="user123")

        assert user.tier == "standard"
        assert user.scopes == []
        assert not user.is_mock


class TestAuthDependencies:
    """Test FastAPI auth dependencies."""

    @pytest.mark.asyncio
    async def test_get_current_user_mock_mode(self):
        """Returns mock user in mock mode."""
        from unittest.mock import MagicMock

        authenticator = JWTAuthenticator(mock_mode=True)

        # Create mock request
        request = MagicMock()
        request.state = MagicMock()

        user = await authenticator.get_current_user(
            request=request,
            credentials=None,
            api_key=None,
        )

        assert isinstance(user, AuthenticatedUser)
        assert user.is_mock
        # Should set request state
        assert hasattr(request.state, "user_id")

    @pytest.mark.asyncio
    async def test_get_current_user_with_token(self):
        """Validates bearer token."""
        import jwt
        from fastapi.security import HTTPAuthorizationCredentials

        authenticator = JWTAuthenticator(
            secret="test-secret",  # pragma: allowlist secret
            mock_mode=False,
        )

        # Create valid token with required scopes
        payload = {
            "sub": "user123",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "scope": "yonca:read yonca:chat",
            "tier": "premium",
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        # Create mock request and credentials
        request = MagicMock()
        request.state = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        user = await authenticator.get_current_user(
            request=request,
            credentials=credentials,
            api_key=None,
        )

        assert user.user_id == "user123"
        # Tier comes from the token payload
        assert not user.is_mock

    @pytest.mark.asyncio
    async def test_get_current_user_insufficient_scopes(self):
        """Rejects token with insufficient scopes."""
        import jwt
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        authenticator = JWTAuthenticator(
            secret="test-secret",  # pragma: allowlist secret
            mock_mode=False,
        )

        # Token without required scopes
        payload = {
            "sub": "user123",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "scope": "other:read",  # Missing yonca scopes
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        request = MagicMock()
        request.state = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        with pytest.raises(HTTPException) as exc_info:
            await authenticator.get_current_user(
                request=request,
                credentials=credentials,
                api_key=None,
            )

        assert exc_info.value.status_code == 403
        assert "scopes" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_no_auth(self):
        """Raises 401 when no authentication provided."""
        from fastapi import HTTPException

        authenticator = JWTAuthenticator(mock_mode=False)

        request = MagicMock()
        request.state = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await authenticator.get_current_user(
                request=request,
                credentials=None,
                api_key=None,
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_optional_user_no_auth(self):
        """Returns None when no auth in optional mode."""
        authenticator = JWTAuthenticator(mock_mode=False)

        request = MagicMock()
        request.state = MagicMock()

        user = await authenticator.get_optional_user(
            request=request,
            credentials=None,
            api_key=None,
        )

        assert user is None
