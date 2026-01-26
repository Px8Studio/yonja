# tests/integration/test_llm_integration.py
"""Integration tests for LLM providers.

These tests verify actual API connectivity and response handling.
Marked with pytest markers to allow selective execution:

    # Run only unit tests (fast, mocked)
    pytest tests/unit -v

    # Run integration tests (requires API keys or local Ollama)
    pytest tests/integration -v -m "integration"

    # Run Ollama integration tests only (requires local Ollama)
    pytest tests/integration -v -m "ollama"

    # Run cloud provider tests (requires API keys)
    pytest tests/integration -v -m "cloud"

Environment variables required:
    - ALIM_GROQ_API_KEY: For Groq tests
    - Local Ollama server at localhost:11434 for Ollama tests
"""

import os

import pytest
import pytest_asyncio
from alim.llm.http_pool import HTTPClientPool
from alim.llm.providers.base import LLMMessage
from alim.llm.providers.groq import GroqProvider
from alim.llm.providers.ollama import OllamaProvider

# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def azerbaijani_messages() -> list[LLMMessage]:
    """Azerbaijani test messages for agricultural context."""
    return [
        LLMMessage.system(
            "Sən ALİM kənd təsərrüfatı köməkçisisən. "
            "Azərbaycan fermerlərə kömək edirsən. "
            "Qısa və faydalı cavablar ver."
        ),
        LLMMessage.user("Salam! 2+2 nə edir?"),
    ]


@pytest.fixture
def simple_math_messages() -> list[LLMMessage]:
    """Simple math test to verify basic functionality."""
    return [
        LLMMessage.system("You are a helpful assistant. Answer briefly."),
        LLMMessage.user("What is 2+2? Just say the number."),
    ]


@pytest_asyncio.fixture
async def cleanup_pools():
    """Cleanup HTTP pools after tests."""
    yield
    await HTTPClientPool.close_all()


# ============================================================
# Ollama Integration Tests
# ============================================================


@pytest.mark.integration
@pytest.mark.ollama
class TestOllamaIntegration:
    """Integration tests for Ollama provider.

    Requires local Ollama server running at localhost:11434
    with qwen3:4b model available.

    Start Ollama:
        docker-compose -f docker-compose.local.yml up -d ollama
    """

    @pytest.mark.asyncio
    async def test_ollama_health_check(self, cleanup_pools):
        """Test Ollama server connectivity."""
        provider = OllamaProvider(
            base_url=os.getenv("ALIM_OLLAMA_BASE_URL", "http://localhost:11434"),
            model="qwen3:4b",
        )

        is_healthy = await provider.health_check()

        if not is_healthy:
            pytest.skip("Ollama server not available or qwen3:4b not loaded")

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_ollama_list_models(self, cleanup_pools):
        """Test listing available Ollama models."""
        provider = OllamaProvider(
            base_url=os.getenv("ALIM_OLLAMA_BASE_URL", "http://localhost:11434"),
        )

        try:
            models = await provider.list_models()
        except Exception:
            pytest.skip("Ollama server not available")

        assert isinstance(models, list)
        # Should have at least one model if Ollama is properly set up
        if models:
            assert all(isinstance(m, str) for m in models)

    @pytest.mark.asyncio
    async def test_ollama_generate(self, simple_math_messages, cleanup_pools):
        """Test generating a response from Ollama."""
        provider = OllamaProvider(
            base_url=os.getenv("ALIM_OLLAMA_BASE_URL", "http://localhost:11434"),
            model="qwen3:4b",
        )

        # Skip if not healthy
        if not await provider.health_check():
            pytest.skip("Ollama not available")

        response = await provider.generate(
            simple_math_messages,
            temperature=0.1,  # Low temperature for deterministic output
            max_tokens=50,
        )

        assert response.content is not None
        assert len(response.content) > 0
        assert "4" in response.content
        assert response.model == "qwen3:4b"

    @pytest.mark.asyncio
    async def test_ollama_stream(self, simple_math_messages, cleanup_pools):
        """Test streaming response from Ollama."""
        provider = OllamaProvider(
            base_url=os.getenv("ALIM_OLLAMA_BASE_URL", "http://localhost:11434"),
            model="qwen3:4b",
        )

        if not await provider.health_check():
            pytest.skip("Ollama not available")

        chunks = []
        async for chunk in provider.stream(
            simple_math_messages,
            temperature=0.1,
            max_tokens=50,
        ):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert len(full_response) > 0
        assert "4" in full_response

    @pytest.mark.asyncio
    async def test_ollama_azerbaijani(self, azerbaijani_messages, cleanup_pools):
        """Test Azerbaijani language handling."""
        provider = OllamaProvider(
            base_url=os.getenv("ALIM_OLLAMA_BASE_URL", "http://localhost:11434"),
            model="qwen3:4b",
        )

        if not await provider.health_check():
            pytest.skip("Ollama not available")

        response = await provider.generate(
            azerbaijani_messages,
            temperature=0.1,
            max_tokens=50,
        )

        # Should respond with "4" in some form
        assert "4" in response.content


# ============================================================
# Groq Integration Tests
# ============================================================


@pytest.mark.integration
@pytest.mark.cloud
class TestGroqIntegration:
    """Integration tests for Groq provider.

    Requires ALIM_GROQ_API_KEY environment variable.
    Get a free key at: https://console.groq.com/
    """

    @pytest.fixture
    def groq_provider(self):
        """Create Groq provider if API key is available."""
        api_key = os.getenv("ALIM_GROQ_API_KEY")
        if not api_key:
            pytest.skip("ALIM_GROQ_API_KEY not set")

        return GroqProvider(
            api_key=api_key,
            model="llama-3.1-8b-instant",  # Fast model for testing
        )

    @pytest.mark.asyncio
    async def test_groq_health_check(self, groq_provider, cleanup_pools):
        """Test Groq API connectivity."""
        is_healthy = await groq_provider.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_groq_generate(self, groq_provider, simple_math_messages, cleanup_pools):
        """Test generating a response from Groq."""
        response = await groq_provider.generate(
            simple_math_messages,
            temperature=0.1,
            max_tokens=50,
        )

        assert response.content is not None
        assert "4" in response.content
        assert response.tokens_used > 0

    @pytest.mark.asyncio
    async def test_groq_stream(self, groq_provider, simple_math_messages, cleanup_pools):
        """Test streaming response from Groq."""
        chunks = []
        async for chunk in groq_provider.stream(
            simple_math_messages,
            temperature=0.1,
            max_tokens=50,
        ):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert "4" in full_response

    @pytest.mark.asyncio
    async def test_groq_azerbaijani(self, groq_provider, azerbaijani_messages, cleanup_pools):
        """Test Azerbaijani language handling with Groq."""
        response = await groq_provider.generate(
            azerbaijani_messages,
            temperature=0.1,
            max_tokens=50,
        )

        # Should respond with the answer
        assert "4" in response.content

    @pytest.mark.asyncio
    async def test_groq_maverick_model(self, cleanup_pools):
        """Test Llama 4 Maverick model (2026 gold standard)."""
        api_key = os.getenv("ALIM_GROQ_API_KEY")
        if not api_key:
            pytest.skip("ALIM_GROQ_API_KEY not set")

        provider = GroqProvider(
            api_key=api_key,
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
        )

        if not await provider.health_check():
            pytest.skip("Maverick model not available on Groq")

        response = await provider.generate(
            [LLMMessage.user("Say 'hello' in Azerbaijani")],
            temperature=0.1,
            max_tokens=30,
        )

        assert response.content is not None


# ============================================================
# Provider Fallback Integration Tests
# ============================================================


@pytest.mark.integration
class TestProviderFallback:
    """Test provider fallback logic."""

    @pytest.mark.asyncio
    async def test_get_fastest_available_provider(self, cleanup_pools):
        """Test automatic provider selection."""
        from alim.llm.factory import LLMProviderError, get_fastest_available_provider

        try:
            provider = await get_fastest_available_provider()
            assert provider is not None
            assert provider.provider_name == "groq"
        except LLMProviderError:
            pytest.skip("No cloud providers configured")

    @pytest.mark.asyncio
    async def test_check_all_providers_health(self, cleanup_pools):
        """Test health check for all configured providers."""
        from alim.llm.factory import check_all_providers_health

        results = await check_all_providers_health()

        assert "groq" in results

        # Each result should have health status
        for provider, status in results.items():
            assert "healthy" in status or "error" in status
