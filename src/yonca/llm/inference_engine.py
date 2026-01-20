"""Central InferenceEngine for ALEM.

Supports three drivers:
- GroqCloud (open-source models via Groq API)
- AzInTelecomVLLM (self-hosted vLLM OpenAI-compatible)
- LocalOllama (offline-capable)
"""

from typing import AsyncIterator

from yonca.config import LLMProvider as LLMProviderEnum, settings
from .factory import (
    create_groq_provider,
    create_ollama_provider,
    create_vllm_provider,
)
from .providers.base import LLMMessage, LLMProvider, LLMResponse


class InferenceEngine:
    """Selects and wraps the configured LLM driver."""

    def __init__(self) -> None:
        self.provider: LLMProvider = self._select_provider()

    def _select_provider(self) -> LLMProvider:
        if settings.llm_provider == LLMProviderEnum.GROQ:
            return create_groq_provider()
        if settings.llm_provider == LLMProviderEnum.VLLM:
            return create_vllm_provider()
        return create_ollama_provider()

    @property
    def driver_name(self) -> str:
        mapping = {
            "groq": "GroqCloud",
            "vllm": "AzInTelecomVLLM",
            "ollama": "LocalOllama",
        }
        return mapping.get(self.provider.provider_name, self.provider.provider_name)

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        return await self.provider.generate(messages, temperature=temperature, max_tokens=max_tokens)

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        async for chunk in self.provider.stream(messages, temperature=temperature, max_tokens=max_tokens):
            yield chunk
