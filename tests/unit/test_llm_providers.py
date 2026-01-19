# tests/unit/test_llm_providers.py
"""Unit tests for LLM providers.

Tests the LLM provider interfaces, message formatting, and response handling.
Mocks external HTTP calls to ensure fast, reliable tests.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from yonca.llm.providers.base import LLMMessage, LLMResponse, MessageRole
from yonca.llm.providers.ollama import OllamaProvider
from yonca.llm.providers.gemini import GeminiProvider
from yonca.llm.providers.groq import GroqProvider, strip_thinking_tags


# ============================================================
# Base Provider Tests
# ============================================================

class TestLLMMessage:
    """Test LLMMessage model."""

    def test_create_system_message(self):
        """Test creating a system message."""
        msg = LLMMessage.system("You are a helpful assistant.")
        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "You are a helpful assistant."

    def test_create_user_message(self):
        """Test creating a user message."""
        msg = LLMMessage.user("Hello!")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello!"

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = LLMMessage.assistant("Hi there!")
        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Hi there!"

    def test_azerbaijani_content(self):
        """Test handling Azerbaijani text."""
        msg = LLMMessage.user("Buğda əkmək üçün ən yaxşı vaxt nədir?")
        assert "Buğda" in msg.content
        assert "ə" in msg.content


class TestLLMResponse:
    """Test LLMResponse model."""

    def test_response_with_all_fields(self):
        """Test creating a full response."""
        response = LLMResponse(
            content="Test response",
            model="test-model",
            tokens_used=10,
            finish_reason="stop",
            metadata={"key": "value"},
        )
        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.tokens_used == 10
        assert response.finish_reason == "stop"
        assert response.metadata["key"] == "value"

    def test_response_with_defaults(self):
        """Test response with default values."""
        response = LLMResponse(content="Test", model="model")
        assert response.tokens_used == 0
        assert response.finish_reason == "stop"
        assert response.metadata == {}


# ============================================================
# Ollama Provider Tests
# ============================================================

class TestOllamaProvider:
    """Test OllamaProvider implementation."""

    def test_provider_name(self):
        """Test provider name property."""
        provider = OllamaProvider(model="qwen3:4b")
        assert provider.provider_name == "ollama"

    def test_model_name(self):
        """Test model name property."""
        provider = OllamaProvider(model="atllama")
        assert provider.model_name == "atllama"

    def test_format_messages(self, sample_messages):
        """Test message formatting for Ollama API."""
        provider = OllamaProvider()
        formatted = provider._format_messages(sample_messages)
        
        assert len(formatted) == 2
        assert formatted[0]["role"] == "system"
        assert formatted[1]["role"] == "user"
        assert "Yonca AI" in formatted[0]["content"]

    @pytest.mark.asyncio
    async def test_generate_success(self, sample_messages):
        """Test successful generation."""
        provider = OllamaProvider(model="qwen3:4b")
        
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Buğda payızda əkilir."},
            "eval_count": 5,
            "done_reason": "stop",
            "total_duration": 1000000,
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(provider, "_get_client", return_value=mock_client):
            response = await provider.generate(sample_messages)
        
        assert response.content == "Buğda payızda əkilir."
        assert response.model == "qwen3:4b"
        assert response.tokens_used == 5
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check when Ollama is healthy."""
        provider = OllamaProvider(model="qwen3:4b")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "qwen3:4b"}, {"name": "atllama"}]
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(provider, "_get_client", return_value=mock_client):
            is_healthy = await provider.health_check()
        
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_model_not_found(self):
        """Test health check when model is not available."""
        provider = OllamaProvider(model="nonexistent:latest")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "qwen3:4b"}]
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(provider, "_get_client", return_value=mock_client):
            is_healthy = await provider.health_check()
        
        assert is_healthy is False


# ============================================================
# Groq Provider Tests
# ============================================================

class TestGroqProvider:
    """Test GroqProvider implementation."""

    def test_provider_name(self):
        """Test provider name property."""
        provider = GroqProvider(api_key="test-key")
        assert provider.provider_name == "groq"

    def test_model_name_default(self):
        """Test default model name (Maverick)."""
        provider = GroqProvider(api_key="test-key")
        assert "maverick" in provider.model_name.lower()

    def test_requires_api_key(self):
        """Test that API key is required."""
        with pytest.raises(ValueError, match="API key is required"):
            GroqProvider(api_key="")

    def test_format_messages(self, sample_messages):
        """Test message formatting for OpenAI-compatible API."""
        provider = GroqProvider(api_key="test-key")
        formatted = provider._format_messages(sample_messages)
        
        assert len(formatted) == 2
        assert formatted[0]["role"] == "system"
        assert formatted[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_success(self, sample_messages):
        """Test successful generation."""
        provider = GroqProvider(api_key="test-key", model="llama-3.1-8b-instant")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Cavab burada."},
                "finish_reason": "stop",
            }],
            "usage": {"total_tokens": 15},
            "model": "llama-3.1-8b-instant",
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(provider, "_get_client", return_value=mock_client):
            response = await provider.generate(sample_messages)
        
        assert response.content == "Cavab burada."
        assert response.tokens_used == 15


class TestStripThinkingTags:
    """Test Qwen3 thinking tag stripping."""

    def test_strip_thinking_tags_basic(self):
        """Test stripping basic thinking tags."""
        text = "<think>Let me think about this...</think>The answer is 42."
        result = strip_thinking_tags(text)
        assert result == "The answer is 42."

    def test_strip_multiline_thinking(self):
        """Test stripping multiline thinking tags."""
        text = """<think>
First, I need to consider...
Then, I should analyze...
</think>
Here is my response."""
        result = strip_thinking_tags(text)
        assert result == "Here is my response."

    def test_no_thinking_tags(self):
        """Test text without thinking tags."""
        text = "This is a normal response."
        result = strip_thinking_tags(text)
        assert result == "This is a normal response."

    def test_azerbaijani_content(self):
        """Test with Azerbaijani content."""
        text = "<think>Düşünürəm...</think>Buğda payızda əkilir."
        result = strip_thinking_tags(text)
        assert result == "Buğda payızda əkilir."


# ============================================================
# Gemini Provider Tests
# ============================================================

class TestGeminiProvider:
    """Test GeminiProvider implementation."""

    def test_provider_name(self):
        """Test provider name property."""
        provider = GeminiProvider(api_key="test-key")
        assert provider.provider_name == "gemini"

    def test_model_name_default(self):
        """Test default model name."""
        provider = GeminiProvider(api_key="test-key")
        assert "gemini" in provider.model_name.lower()

    def test_requires_api_key(self):
        """Test that API key is required."""
        with pytest.raises(ValueError, match="API key is required"):
            GeminiProvider(api_key="")

    def test_format_messages_with_system(self, sample_messages):
        """Test message formatting extracts system instruction."""
        provider = GeminiProvider(api_key="test-key")
        system_instruction, contents = provider._format_messages(sample_messages)
        
        assert system_instruction is not None
        assert "Yonca AI" in system_instruction
        assert len(contents) == 1
        assert contents[0]["role"] == "user"

    def test_format_messages_role_mapping(self, sample_multi_turn_messages):
        """Test that assistant role maps to 'model' for Gemini."""
        provider = GeminiProvider(api_key="test-key")
        _, contents = provider._format_messages(sample_multi_turn_messages)
        
        # Should have user, model, user (system is extracted)
        roles = [c["role"] for c in contents]
        assert roles == ["user", "model", "user"]

    @pytest.mark.asyncio
    async def test_generate_success(self, sample_messages):
        """Test successful generation."""
        provider = GeminiProvider(api_key="test-key")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Gemini cavabı."}]
                },
                "finishReason": "STOP",
            }],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 5,
                "totalTokenCount": 15,
            },
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(provider, "_get_client", return_value=mock_client):
            response = await provider.generate(sample_messages)
        
        assert response.content == "Gemini cavabı."
        assert response.tokens_used == 15


# ============================================================
# HTTP Pool Tests
# ============================================================

class TestHTTPClientPool:
    """Test HTTP connection pool management."""

    def test_pool_config_defaults(self):
        """Test default pool configuration."""
        from yonca.llm.http_pool import PoolConfig
        
        config = PoolConfig()
        assert config.max_connections == 100
        assert config.max_keepalive_connections == 20

    def test_provider_specific_configs(self):
        """Test provider-specific configurations."""
        from yonca.llm.http_pool import HTTPClientPool
        
        groq_config = HTTPClientPool._get_config("groq")
        ollama_config = HTTPClientPool._get_config("ollama")
        
        # Groq should be faster timeout
        assert groq_config.read_timeout < ollama_config.read_timeout
        # Ollama needs fewer connections (local)
        assert ollama_config.max_connections < groq_config.max_connections
