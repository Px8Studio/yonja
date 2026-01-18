# tests/conftest.py
"""Pytest fixtures and configuration for Yonca AI tests."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from yonca.llm.providers.base import LLMMessage, LLMProvider, LLMResponse, MessageRole


# ============================================================
# Mock LLM Provider
# ============================================================

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(
        self,
        provider_name: str = "mock",
        model_name: str = "mock-model",
        response_content: str = "Mock response",
        should_fail: bool = False,
        stream_chunks: list[str] | None = None,
    ):
        self._provider_name = provider_name
        self._model_name = model_name
        self._response_content = response_content
        self._should_fail = should_fail
        self._stream_chunks = stream_chunks or ["Mock ", "streaming ", "response"]
        self.generate_calls: list[dict[str, Any]] = []
        self.stream_calls: list[dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        self.generate_calls.append({
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        
        if self._should_fail:
            raise RuntimeError("Mock provider failed")
        
        return LLMResponse(
            content=self._response_content,
            model=self._model_name,
            tokens_used=len(self._response_content.split()),
            finish_reason="stop",
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        self.stream_calls.append({
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        
        if self._should_fail:
            raise RuntimeError("Mock provider failed")
        
        for chunk in self._stream_chunks:
            yield chunk

    async def health_check(self) -> bool:
        return not self._should_fail


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def mock_llm_provider_factory():
    """Factory fixture to create mock providers with custom settings."""
    def factory(**kwargs) -> MockLLMProvider:
        return MockLLMProvider(**kwargs)
    return factory


# ============================================================
# Sample Messages
# ============================================================

@pytest.fixture
def sample_messages() -> list[LLMMessage]:
    """Sample conversation messages for testing."""
    return [
        LLMMessage.system("Sən Yonca AI kənd təsərrüfatı köməkçisisən."),
        LLMMessage.user("Buğda əkmək üçün ən yaxşı vaxt nədir?"),
    ]


@pytest.fixture
def sample_multi_turn_messages() -> list[LLMMessage]:
    """Multi-turn conversation messages for testing."""
    return [
        LLMMessage.system("Sən Yonca AI kənd təsərrüfatı köməkçisisən."),
        LLMMessage.user("Pomidorlarım saraldı."),
        LLMMessage.assistant("Bu çox güman ki, azot çatışmazlığıdır. Torpağınız necədir?"),
        LLMMessage.user("Torpaq qurudur."),
    ]


# ============================================================
# HTTP Mocking
# ============================================================

@pytest_asyncio.fixture
async def mock_httpx_client():
    """Create a mock httpx AsyncClient."""
    client = AsyncMock()
    client.post = AsyncMock()
    client.get = AsyncMock()
    return client


# ============================================================
# Environment Overrides
# ============================================================

@pytest.fixture
def clean_env(monkeypatch):
    """Clear LLM-related environment variables."""
    monkeypatch.delenv("YONCA_GROQ_API_KEY", raising=False)
    monkeypatch.delenv("YONCA_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("YONCA_OLLAMA_BASE_URL", raising=False)


@pytest.fixture
def mock_groq_env(monkeypatch):
    """Set up mock Groq environment."""
    monkeypatch.setenv("YONCA_GROQ_API_KEY", "test-groq-api-key")
    monkeypatch.setenv("YONCA_LLM_PROVIDER", "groq")


@pytest.fixture
def mock_gemini_env(monkeypatch):
    """Set up mock Gemini environment."""
    monkeypatch.setenv("YONCA_GEMINI_API_KEY", "test-gemini-api-key")
    monkeypatch.setenv("YONCA_LLM_PROVIDER", "gemini")


@pytest.fixture
def mock_ollama_env(monkeypatch):
    """Set up mock Ollama environment."""
    monkeypatch.setenv("YONCA_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("YONCA_LLM_PROVIDER", "ollama")
