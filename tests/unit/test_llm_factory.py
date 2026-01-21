# tests/unit/test_llm_factory.py
"""Unit tests for LLM provider factory."""

from unittest.mock import MagicMock, patch

import pytest
from yonca.config import LLMProvider as LLMProviderEnum
from yonca.llm.factory import (
    LLMProviderError,
    create_groq_provider,
    create_llm_provider,
    create_ollama_provider,
)


class TestCreateGroqProvider:
    """Test Groq provider creation."""

    def test_create_with_explicit_key(self):
        """Test creating provider with explicit API key."""
        provider = create_groq_provider(api_key="test_key_12345")  # pragma: allowlist secret
        assert provider.provider_name == "groq"
        assert provider.api_key == "test_key_12345"  # pragma: allowlist secret

    def test_create_with_custom_model(self):
        """Test creating provider with custom model."""
        provider = create_groq_provider(
            api_key="test_key_12345",  # pragma: allowlist secret
            model="llama-3.3-70b-versatile",
        )
        assert provider.model_name == "llama-3.3-70b-versatile"

    def test_explicit_key_overrides_settings(self):
        """Test that explicit API key takes precedence over settings."""
        provider = create_groq_provider(api_key="explicit-key")  # pragma: allowlist secret
        # Should use the explicit key, not the one from settings
        assert provider.api_key == "explicit-key"


class TestCreateOllamaProvider:
    """Test Ollama provider creation."""

    def test_create_with_defaults(self):
        """Test creating provider with default settings."""
        provider = create_ollama_provider()
        assert provider.provider_name == "ollama"

    def test_create_with_custom_url(self):
        """Test creating provider with custom URL."""
        provider = create_ollama_provider(base_url="http://gpu-server:11434")
        assert provider.base_url == "http://gpu-server:11434"

    def test_create_with_custom_model(self):
        """Test creating provider with custom model."""
        provider = create_ollama_provider(model="atllama")
        assert provider.model_name == "atllama"


class TestCreateLLMProvider:
    """Test factory function for creating providers."""

    def test_create_ollama_provider(self):
        """Test creating Ollama provider via factory."""
        provider = create_llm_provider(
            provider_type=LLMProviderEnum.OLLAMA,
            model="qwen3:4b",
        )
        assert provider.provider_name == "ollama"

    def test_create_groq_provider(self):
        """Test creating Groq provider via factory."""
        provider = create_llm_provider(
            provider_type=LLMProviderEnum.GROQ,
            api_key="test-key",  # pragma: allowlist secret
        )
        assert provider.provider_name == "groq"

    def test_invalid_provider_type(self):
        """Test that invalid provider type raises error."""
        with pytest.raises(LLMProviderError, match="Unknown LLM provider"):
            create_llm_provider(provider_type="invalid")


class TestProviderHealthCheck:
    """Test provider health check functionality."""

    @pytest.mark.asyncio
    async def test_check_llm_health_ollama(self, mock_ollama_env):
        """Test health check for Ollama provider."""
        from yonca.llm.factory import get_llm_provider

        # Clear the cached provider
        get_llm_provider.cache_clear()

        provider = create_ollama_provider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "qwen3:4b"}]}

        from unittest.mock import AsyncMock

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch.object(provider, "_get_client", return_value=mock_client):
            is_healthy = await provider.health_check()

        assert is_healthy is True
