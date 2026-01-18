# demo-ui/services/yonca_client.py
"""HTTP client for the Yonca API.

Used for the API client pattern when the demo UI talks to the
backend via REST instead of direct LangGraph integration.
"""

import httpx
from typing import Any, AsyncIterator
import structlog

logger = structlog.get_logger(__name__)


class YoncaClientError(Exception):
    """Error from the Yonca API."""
    
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class YoncaClient:
    """Async HTTP client for the Yonca API.
    
    Example:
        ```python
        async with YoncaClient("http://localhost:8000") as client:
            response = await client.chat(
                message="Pomidorları nə vaxt suvarmalıyam?",
                session_id="session_123",
            )
            print(response["content"])
        ```
    """
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        timeout: float = 60.0,
    ):
        """Initialize the client.
        
        Args:
            base_url: Base URL of the Yonca API.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self) -> "YoncaClient":
        """Enter async context."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, raising if not initialized."""
        if self._client is None:
            raise RuntimeError("YoncaClient not initialized. Use 'async with' context.")
        return self._client
    
    async def health_check(self) -> dict[str, Any]:
        """Check API health.
        
        Returns:
            Health status dictionary.
        """
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()
    
    async def chat(
        self,
        message: str,
        session_id: str | None = None,
        farm_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a chat message.
        
        Args:
            message: User message in Azerbaijani.
            session_id: Session ID for conversation continuity.
            farm_id: Optional farm context ID.
            stream: Whether to stream the response.
            
        Returns:
            Response dictionary with 'content' and metadata.
        """
        payload = {
            "message": message,
            "language": "az",
        }
        
        if session_id:
            payload["session_id"] = session_id
        if farm_id:
            payload["farm_id"] = farm_id
        
        try:
            response = await self.client.post(
                "/api/v1/chat",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "API request failed",
                status_code=e.response.status_code,
                detail=e.response.text,
            )
            raise YoncaClientError(
                f"API error: {e.response.text}",
                status_code=e.response.status_code,
            ) from e
    
    async def chat_stream(
        self,
        message: str,
        session_id: str | None = None,
        farm_id: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream a chat response token by token.
        
        Args:
            message: User message in Azerbaijani.
            session_id: Session ID for conversation continuity.
            farm_id: Optional farm context ID.
            
        Yields:
            Response tokens as they arrive.
        """
        payload = {
            "message": message,
            "language": "az",
            "stream": True,
        }
        
        if session_id:
            payload["session_id"] = session_id
        if farm_id:
            payload["farm_id"] = farm_id
        
        async with self.client.stream(
            "POST",
            "/api/v1/chat/stream",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    token = line[6:]  # Remove "data: " prefix
                    if token != "[DONE]":
                        yield token
    
    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get session information.
        
        Args:
            session_id: The session ID.
            
        Returns:
            Session data including conversation history.
        """
        response = await self.client.get(f"/api/v1/session/{session_id}")
        response.raise_for_status()
        return response.json()
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session.
        
        Args:
            session_id: The session ID to delete.
        """
        response = await self.client.delete(f"/api/v1/session/{session_id}")
        response.raise_for_status()
