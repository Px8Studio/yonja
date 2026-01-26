from alim.config import settings
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

api_key_header_scheme = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def get_api_key(api_key: str = Security(api_key_header_scheme)):
    """Validate API Key for third-party access."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != settings.api_key_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )

    return api_key
