# src/yonca/api/routes/auth.py
"""Authentication and authorization routes for Yonca AI."""


from fastapi import APIRouter, Header
from pydantic import BaseModel

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


class AuthTestRequest(BaseModel):
    """Test authentication request."""

    test_token: str | None = None


class AuthTestResponse(BaseModel):
    """Authentication test response."""

    authenticated: bool
    token_valid: bool
    user_id: str | None = None
    message: str


@router.post("/test", response_model=AuthTestResponse)
async def test_authentication(
    request: AuthTestRequest,
    authorization: str | None = Header(None),
):
    """Test endpoint for Yonca Mobile to verify authentication.

    This minimal endpoint allows partners to quickly verify:
    - Bearer token format
    - JWT signature validation (when implemented)
    - User identification

    Example:
        ```bash
        curl -X POST \\
          -H "Authorization: Bearer <token>" \\
          -d '{"test_token": "optional"}' \\
          http://localhost:8000/api/v1/auth/test
        ```

    Returns:
        AuthTestResponse with token validation status
    """
    if not authorization:
        return AuthTestResponse(
            authenticated=False,
            token_valid=False,
            message="No Authorization header provided. Use 'Authorization: Bearer <token>'",
        )

    if not authorization.startswith("Bearer "):
        return AuthTestResponse(
            authenticated=False,
            token_valid=False,
            message="Invalid Authorization header format. Use 'Bearer <token>'",
        )

    token = authorization.replace("Bearer ", "")

    # TODO: When SİMA/ASAN integration is live, validate JWT here
    # For now, accept any Bearer token for testing
    if len(token) > 10:  # Minimal validation
        return AuthTestResponse(
            authenticated=True,
            token_valid=True,
            user_id="demo-user",
            message="✅ Authentication successful (dev mode). Production will validate JWT with SİMA/ASAN.",
        )
    else:
        return AuthTestResponse(
            authenticated=False,
            token_valid=False,
            message="Token too short. Provide a valid JWT token.",
        )
