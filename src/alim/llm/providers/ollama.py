# src/ALİM/llm/providers/ollama.py
"""Ollama LLM provider for local inference.

Connects to a local Ollama server for LLM inference.
Supports both qwen3 and atllama (imported GGUF) models.
"""

import json
from collections.abc import AsyncIterator

import httpx

from alim.llm.http_pool import HTTPClientPool
from alim.observability.banner import print_connection_failure

from .base import LLMMessage, LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference.

    Example:
        ```python
        async with OllamaProvider(model="qwen3:4b") as llm:
            response = await llm.generate([
                LLMMessage.system("You are a helpful assistant."),
                LLMMessage.user("Salam!")
            ])
            print(response.content)
        ```
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:4b",
        timeout: float = 120.0,
    ):
        """Initialize Ollama provider.

        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Model name (e.g., "qwen3:4b", "atllama")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self.model

    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client from the shared connection pool."""
        return await HTTPClientPool.get_pool(
            provider="ollama",
            base_url=self.base_url,
            headers={"Content-Type": "application/json", "X-Sovereign-Data": "sovereign-local"},
        )

    async def __aenter__(self) -> "OllamaProvider":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Connection pool cleanup is handled by HTTPClientPool.close_all()."""
        pass

    async def close(self) -> None:
        """Connection pool cleanup is handled by HTTPClientPool.close_all()."""
        pass

    def _format_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Convert LLMMessage list to Ollama format."""
        return [{"role": m.role.value, "content": m.content} for m in messages]

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate a response from Ollama.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse with the generated content.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        client = await self._get_client()

        payload = {
            "model": self.model,
            "messages": self._format_messages(messages),
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }

        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
        except httpx.ConnectError as e:
            print_connection_failure("Ollama", str(e))
            raise
        except httpx.HTTPError:
            raise

        data = response.json()

        return LLMResponse(
            content=data["message"]["content"],
            model=self.model,
            tokens_used=data.get("eval_count", 0),
            finish_reason=data.get("done_reason", "stop"),
            metadata={
                "total_duration": data.get("total_duration"),
                "load_duration": data.get("load_duration"),
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
            },
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Stream a response from Ollama.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.

        Yields:
            String chunks of the generated response.
        """
        client = await self._get_client()

        payload = {
            "model": self.model,
            "messages": self._format_messages(messages),
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": True,
        }

        try:
            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            content = data["message"]["content"]
                            if content:
                                yield content
        except httpx.ConnectError as e:
            print_connection_failure("Ollama", str(e))
            raise
        except httpx.HTTPError:
            raise

    async def health_check(self) -> bool:
        """Check if Ollama server is healthy.

        Returns:
            True if Ollama is reachable and the model is available.
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            if response.status_code != 200:
                return False

            # Check if our model is available
            data = response.json()
            available_models = [m["name"] for m in data.get("models", [])]

            # Match model name (with or without tag)
            model_base = self.model.split(":")[0]
            return any(m == self.model or m.startswith(f"{model_base}:") for m in available_models)
        except httpx.HTTPError:
            return False

    async def list_models(self) -> list[str]:
        """List available models in Ollama.

        Returns:
            List of model names.
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except httpx.HTTPError:
            return []
