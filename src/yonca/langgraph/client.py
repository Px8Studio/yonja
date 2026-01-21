"""Async client for the LangGraph development server."""
from __future__ import annotations

import inspect
import json
from collections.abc import AsyncIterator
from typing import Any

import httpx


class LangGraphClientError(Exception):
    """Error raised when the LangGraph Dev Server request fails."""


class LangGraphClient:
    """LangGraph async client for invoking graphs."""

    def __init__(
        self,
        base_url: str = "http://localhost:2024",
        graph_id: str = "yonca_agent",
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ):
        """Initialize LangGraph client.

        Args:
            base_url: LangGraph server base URL (default: http://localhost:2024)
            graph_id: Graph ID to invoke (default: yonca_agent)
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

    async def health(self) -> dict[str, Any]:
        """Check Dev Server health (best-effort)."""
        try:
            response = await self.client.get("/health")
            await _await_if_needed(response.raise_for_status())
            return await _await_if_needed(response.json())
        except Exception as exc:  # noqa: BLE001
            raise LangGraphClientError(str(exc)) from exc

    async def ensure_thread(
        self, thread_id: str | None, metadata: dict[str, Any] | None = None
    ) -> str:
        """Return an existing thread_id or create a new one."""
        if thread_id:
            return thread_id

        try:
            response = await self.client.post("/threads", json={"metadata": metadata or {}})
            await _await_if_needed(response.raise_for_status())
            data = await _await_if_needed(response.json())
            return self._coerce_thread_id(data)
        except Exception as exc:  # noqa: BLE001
            raise LangGraphClientError(f"Failed to create thread: {exc}") from exc

    async def invoke(
        self,
        message: str,
        thread_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        language: str = "az",
    ) -> dict:
        """Invoke the LangGraph agent."""
        import uuid

        from yonca.agent.state import create_initial_state

        # Create or use thread ID
        if thread_id is None:
            thread_id = f"thread_{uuid.uuid4().hex[:12]}"

        # Create initial state
        initial_state = create_initial_state(
            thread_id=thread_id,
            user_input=message,
            user_id=user_id,
            session_id=session_id,
            language=language,
        )

        # Prepare config and payload
        config = {"configurable": {"thread_id": thread_id}}
        payload = {
            "graph_id": self.graph_id,
            "input": dict(initial_state),
            "config": config,
            "stream": False,
        }

        # Build endpoint URL
        url = f"{self.base_url}/runs/stream"

        async with httpx.AsyncClient(transport=self._transport, timeout=self.timeout) as client:
            response = await client.post(url, json=payload, timeout=self.timeout)

            # Handle sync httpx.Response and AsyncMock in tests
            await _await_if_needed(response.raise_for_status())
            return await _await_if_needed(response.json())

    async def stream(
        self,
        input_state: dict[str, Any],
        *,
        thread_id: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream graph execution events as dicts."""
        thread = await self.ensure_thread(thread_id, metadata=(config or {}).get("metadata"))
        payload: dict[str, Any] = {"input": input_state}
        if config:
            payload["config"] = config

        try:
            async with self.client.stream(
                "POST",
                f"/threads/{thread}/runs",
                params={"graph": self.graph_id, "stream": "true"},
                headers={"Accept": "text/event-stream"},
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data:"):
                        chunk = line[5:].strip()
                        if chunk == "[DONE]":
                            break
                        try:
                            yield json.loads(chunk)
                        except json.JSONDecodeError:
                            yield {"data": chunk, "thread_id": thread}
        except Exception as exc:  # noqa: BLE001
            raise LangGraphClientError(f"Graph stream failed: {exc}") from exc

    @staticmethod
    def _coerce_thread_id(payload: dict[str, Any]) -> str:
        for key in ("thread_id", "id"):
            if key in payload:
                return str(payload[key])
        thread_obj = payload.get("thread") if isinstance(payload, dict) else None
        if isinstance(thread_obj, dict):
            if "id" in thread_obj:
                return str(thread_obj["id"])
            if "thread_id" in thread_obj:
                return str(thread_obj["thread_id"])
        raise LangGraphClientError("Dev server did not return a thread_id")


async def _await_if_needed(value):
    """Await value if it is awaitable (supports AsyncMock in tests)."""
    if inspect.isawaitable(value):
        return await value
    return value
