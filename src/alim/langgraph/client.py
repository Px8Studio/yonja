"""Async client for the LangGraph development server.

LangGraph Dev Server API Reference (v1.x):
- POST /threads - Create a new thread
- POST /threads/{thread_id}/runs - Execute graph run
- POST /threads/{thread_id}/runs/stream - Stream graph execution
- GET /threads/{thread_id}/state - Get current thread state
- GET /health - Health check
"""
from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LangGraphClientError(Exception):
    """Error raised when the LangGraph Dev Server request fails."""


class LangGraphClient:
    """Async client for LangGraph Dev Server.

    This client provides a clean interface for invoking LangGraph graphs
    deployed via `langgraph dev` or `langgraph up`.

    Usage:
        async with LangGraphClient() as client:
            # Create thread and invoke
            thread_id = await client.create_thread()
            result = await client.invoke(
                input_state={"messages": [{"role": "user", "content": "Hello"}]},
                thread_id=thread_id,
            )

            # Or stream the response
            async for event in client.stream(input_state, thread_id=thread_id):
                print(event)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:2024",
        graph_id: str = "alim_agent",
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ):
        """Initialize LangGraph client.

        Args:
            base_url: LangGraph server base URL (default: http://localhost:2024)
            graph_id: Graph ID to invoke (from langgraph.json)
            timeout: Request timeout in seconds (default: 120.0)
            transport: Optional httpx transport for custom HTTP behavior
        """
        self.base_url = base_url.rstrip("/")
        self.graph_id = graph_id
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._transport = transport

    async def __aenter__(self) -> LangGraphClient:
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self._transport,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("LangGraphClient not initialized. Use 'async with'.")
        return self._client

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    # ============================================================
    # Health & Status
    # ============================================================

    async def health(self) -> dict[str, Any]:
        """Check Dev Server health.

        Returns:
            Health status dict with 'status' key.
        """
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise LangGraphClientError(f"Health check failed: {exc.response.status_code}") from exc
        except Exception as exc:
            raise LangGraphClientError(f"Health check error: {exc}") from exc

    async def is_healthy(self) -> bool:
        """Quick health check returning boolean."""
        try:
            health = await self.health()
            return health.get("status") == "ok"
        except LangGraphClientError:
            return False

    # ============================================================
    # Thread Management
    # ============================================================

    async def create_thread(self, metadata: dict[str, Any] | None = None) -> str:
        """Create a new conversation thread.

        Args:
            metadata: Optional metadata to attach to thread

        Returns:
            Thread ID string
        """
        try:
            response = await self.client.post(
                "/threads",
                json={"metadata": metadata or {}},
            )
            response.raise_for_status()
            data = response.json()
            return self._extract_thread_id(data)
        except httpx.HTTPStatusError as exc:
            raise LangGraphClientError(
                f"Failed to create thread: {exc.response.status_code}"
            ) from exc
        except Exception as exc:
            raise LangGraphClientError(f"Thread creation error: {exc}") from exc

    async def ensure_thread(
        self, thread_id: str | None, metadata: dict[str, Any] | None = None
    ) -> str:
        """Return existing thread_id or create a new one.

        Args:
            thread_id: Existing thread ID (if any)
            metadata: Metadata for new thread (if creating)

        Returns:
            Valid thread ID
        """
        if thread_id:
            return thread_id
        return await self.create_thread(metadata)

    async def get_thread_state(self, thread_id: str) -> dict[str, Any]:
        """Get the current state of a thread.

        Args:
            thread_id: Thread ID

        Returns:
            Current thread state dict
        """
        try:
            response = await self.client.get(f"/threads/{thread_id}/state")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise LangGraphClientError(f"Thread not found: {thread_id}") from exc
            raise LangGraphClientError(
                f"Failed to get thread state: {exc.response.status_code}"
            ) from exc
        except Exception as exc:
            raise LangGraphClientError(f"Get state error: {exc}") from exc

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread and its history.

        Args:
            thread_id: Thread ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            response = await self.client.delete(f"/threads/{thread_id}")
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return False  # Already deleted
            raise LangGraphClientError(
                f"Failed to delete thread: {exc.response.status_code}"
            ) from exc
        except Exception as exc:
            raise LangGraphClientError(f"Delete thread error: {exc}") from exc

    # ============================================================
    # Graph Invocation
    # ============================================================

    async def invoke(
        self,
        input_state: dict[str, Any],
        thread_id: str | None = None,
        config: dict[str, Any] | None = None,
        *,
        wait: bool = True,
    ) -> dict[str, Any]:
        """Invoke the graph and wait for completion.

        Args:
            input_state: Input state dict (must match graph's state schema)
            thread_id: Thread ID (creates new if None)
            config: Optional config dict with metadata, callbacks, etc.
            wait: If True, wait for run completion (default: True)

        Returns:
            Final state after graph execution
        """
        thread = await self.ensure_thread(thread_id)

        # Build run payload - assistant_id must be in body for LangGraph API >= 0.7.x
        payload: dict[str, Any] = {
            "input": input_state,
            "assistant_id": self.graph_id,
        }
        if config:
            payload["config"] = config

        # wait param is still a query param
        params = {}
        if wait:
            params["wait"] = "true"

        try:
            response = await self.client.post(
                f"/threads/{thread}/runs",
                params=params if params else None,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            # If wait=True, result is the final state
            # If wait=False, result is the run info
            return result

        except httpx.HTTPStatusError as exc:
            error_detail = ""
            try:
                error_detail = exc.response.text[:500]
            except Exception:
                pass
            raise LangGraphClientError(
                f"Graph invocation failed ({exc.response.status_code}): {error_detail}"
            ) from exc
        except Exception as exc:
            raise LangGraphClientError(f"Invoke error: {exc}") from exc

    async def stream(
        self,
        input_state: dict[str, Any],
        thread_id: str | None = None,
        config: dict[str, Any] | None = None,
        *,
        stream_mode: str = "values",
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream graph execution events.

        Args:
            input_state: Input state dict
            thread_id: Thread ID (creates new if None)
            config: Optional config dict
            stream_mode: What to stream - "values", "updates", "messages", "events"
                - "values": Stream full state after each node
                - "updates": Stream only state updates (delta)
                - "messages": Stream LLM messages/tokens
                - "events": Stream all events (most verbose)

        Yields:
            Event dicts with structure depending on stream_mode
        """
        thread = await self.ensure_thread(thread_id)

        # Build run payload - assistant_id must be in body for LangGraph API >= 0.7.x
        payload: dict[str, Any] = {
            "input": input_state,
            "assistant_id": self.graph_id,
            "stream_mode": stream_mode,
        }
        if config:
            payload["config"] = config

        try:
            async with self.client.stream(
                "POST",
                f"/threads/{thread}/runs/stream",
                headers={"Accept": "text/event-stream"},
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    # Skip empty lines and comments
                    if not line or line.startswith(":"):
                        continue

                    # Parse SSE data lines
                    if line.startswith("data:"):
                        data = line[5:].strip()

                        # Check for stream end
                        if data == "[DONE]":
                            break

                        # Parse JSON event
                        try:
                            event = json.loads(data)
                            yield event
                        except json.JSONDecodeError:
                            # Non-JSON data, wrap it
                            yield {"raw_data": data, "thread_id": thread}

                    # Handle event type lines (SSE standard)
                    elif line.startswith("event:"):
                        event_type = line[6:].strip()
                        yield {"event_type": event_type}

        except httpx.HTTPStatusError as exc:
            raise LangGraphClientError(f"Stream failed ({exc.response.status_code})") from exc
        except Exception as exc:
            raise LangGraphClientError(f"Stream error: {exc}") from exc

    # ============================================================
    # Convenience Methods
    # ============================================================

    async def chat(
        self,
        message: str,
        thread_id: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """High-level chat interface.

        Wraps message in standard format and invokes graph.

        Args:
            message: User message text
            thread_id: Thread ID (creates new if None)
            user_id: Optional user ID for tracking
            **kwargs: Additional config options

        Returns:
            Graph response state
        """
        input_state = {
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
        }

        config = kwargs.pop("config", {})
        if user_id:
            config.setdefault("configurable", {})["user_id"] = user_id

        return await self.invoke(
            input_state=input_state,
            thread_id=thread_id,
            config=config if config else None,
            **kwargs,
        )

    async def stream_chat(
        self,
        message: str,
        thread_id: str | None = None,
        user_id: str | None = None,
        stream_mode: str = "messages",
    ) -> AsyncIterator[dict[str, Any]]:
        """High-level streaming chat interface.

        Args:
            message: User message text
            thread_id: Thread ID (creates new if None)
            user_id: Optional user ID
            stream_mode: Stream mode (default: "messages" for token streaming)

        Yields:
            Stream events
        """
        input_state = {
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
        }

        config = {}
        if user_id:
            config["configurable"] = {"user_id": user_id}

        async for event in self.stream(
            input_state=input_state,
            thread_id=thread_id,
            config=config if config else None,
            stream_mode=stream_mode,
        ):
            yield event

    # ============================================================
    # Helpers
    # ============================================================

    @staticmethod
    def _extract_thread_id(data: dict[str, Any]) -> str:
        """Extract thread ID from API response."""
        # Try common response formats
        for key in ("thread_id", "id"):
            if key in data:
                return str(data[key])

        # Try nested thread object
        thread_obj = data.get("thread")
        if isinstance(thread_obj, dict):
            for key in ("id", "thread_id"):
                if key in thread_obj:
                    return str(thread_obj[key])

        raise LangGraphClientError(f"Could not extract thread_id from response: {data}")

    @staticmethod
    def generate_thread_id() -> str:
        """Generate a new thread ID locally."""
        return f"thread_{uuid.uuid4().hex[:12]}"
