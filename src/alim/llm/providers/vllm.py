"""vLLM provider for self-hosted OpenAI-compatible inference.

Used for sovereign deployments (AzInTelecom/DigiRella) exposing a vLLM server
with OpenAI-compatible `chat/completions` endpoints.
"""

from collections.abc import AsyncIterator

import httpx

from alim.config import settings
from alim.llm.http_pool import HTTPClientPool

from .base import LLMMessage, LLMProvider, LLMResponse


class VLLMProvider(LLMProvider):
    """Self-hosted vLLM provider (OpenAI-compatible)."""

    DEFAULT_BASE_URL = "http://localhost:8000/v1"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        api_key: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.vllm_base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.model = model or settings.vllm_model
        self.timeout = timeout
        self.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "vllm"

    @property
    def model_name(self) -> str:
        return self.model

    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client from the shared connection pool."""
        headers = {"Content-Type": "application/json", "X-Sovereign-Data": "sovereign-cloud"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return await HTTPClientPool.get_pool(
            provider="vllm",
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
        )

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        client = await self._get_client()
        payload = {
            "model": self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = await client.post(
            "/chat/completions" if not self.base_url.endswith("/v1") else "/v1/chat/completions",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            tokens_used=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
            metadata={
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "id": data.get("id"),
            },
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        payload = {
            "model": self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        url = "/chat/completions" if not self.base_url.endswith("/v1") else "/v1/chat/completions"
        async with client.stream("POST", url, json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    chunk = line[6:].strip()
                    yield chunk

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            url = "/models" if not self.base_url.endswith("/v1") else "/v1/models"
            resp = await client.get(url)
            return resp.status_code == 200
        except Exception:
            return False
