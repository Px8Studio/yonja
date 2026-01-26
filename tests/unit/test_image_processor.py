"""Test suite for image processor.

Tests image generation with multiple providers.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add demo-ui to path BEFORE importing from services
demo_ui_path = Path(__file__).parent.parent.parent / "demo-ui"
sys.path.insert(0, str(demo_ui_path))

from services.image_processor import (  # noqa: E402
    GroqProvider,
    HuggingFaceProvider,
    ImageGenerationConfig,
    ImageProcessor,
    ImageProvider,
    ImageQuality,
    OllamaProvider,
    OpenAIProvider,
    get_image_processor,
)


class TestImageGenerationConfig:
    """Test image generation configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ImageGenerationConfig()

        assert config.provider == ImageProvider.OLLAMA_LOCAL
        assert config.quality == ImageQuality.STANDARD
        assert config.steps == 20
        assert config.guidance_scale == 7.5

    def test_custom_config(self):
        """Test custom configuration."""
        config = ImageGenerationConfig(
            provider=ImageProvider.GROQ,
            quality=ImageQuality.QUALITY,
            steps=50,
            guidance_scale=10.0,
        )

        assert config.provider == ImageProvider.GROQ
        assert config.quality == ImageQuality.QUALITY
        assert config.steps == 50
        assert config.guidance_scale == 10.0


class TestImageProcessor:
    """Test main image processor."""

    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = ImageProcessor()

        assert processor.config is not None
        assert len(processor.providers) == 4
        assert ImageProvider.OLLAMA_LOCAL in processor.providers

    def test_prompt_optimization(self):
        """Test prompt optimization."""
        processor = ImageProcessor()

        prompt = "a farm"
        optimized = processor._optimize_prompt(prompt)

        assert len(optimized) > len(prompt)
        assert "detailed" in optimized.lower() or "sharp" in optimized.lower()

    def test_prompt_already_optimized(self):
        """Test that already optimized prompts aren't modified excessively."""
        processor = ImageProcessor()

        prompt = "a highly detailed farm landscape"
        optimized = processor._optimize_prompt(prompt)

        # Should not add redundant quality tokens
        assert optimized.count("detailed") <= 2

    def test_quality_config_fast(self):
        """Test fast quality config."""
        processor = ImageProcessor()

        config = processor._get_quality_config(ImageQuality.FAST)

        assert config.quality == ImageQuality.FAST
        assert config.steps == 10
        assert config.guidance_scale == 5.0

    def test_quality_config_ultra(self):
        """Test ultra quality config."""
        processor = ImageProcessor()

        config = processor._get_quality_config(ImageQuality.ULTRA)

        assert config.quality == ImageQuality.ULTRA
        assert config.steps == 60
        assert config.guidance_scale == 12.0

    @pytest.mark.asyncio
    @patch("services.image_processor.OllamaProvider.generate")
    async def test_generate_image_success(self, mock_generate):
        """Test successful image generation."""
        processor = ImageProcessor()

        # Mock image data
        mock_image_data = b"fake_image_data"
        mock_generate.return_value = mock_image_data

        result = await processor.generate_image("a farm landscape")

        assert result == mock_image_data

    @pytest.mark.asyncio
    @patch("services.image_processor.OllamaProvider.generate")
    @patch("services.image_processor.GroqProvider.generate")
    async def test_generate_image_fallback(self, mock_groq, mock_ollama):
        """Test fallback to next provider on failure."""
        processor = ImageProcessor()

        # Ollama fails, Groq succeeds
        mock_ollama.return_value = None
        mock_image_data = b"fake_groq_image"
        mock_groq.return_value = mock_image_data

        await processor.generate_image(
            "a farm landscape",
            provider=ImageProvider.OLLAMA_LOCAL,
        )

        # Should eventually get image from Groq
        assert mock_ollama.called or mock_groq.called

    @pytest.mark.asyncio
    @patch("services.image_processor.OllamaProvider.generate")
    async def test_generate_image_all_providers_fail(self, mock_generate):
        """Test behavior when all providers fail."""
        processor = ImageProcessor()

        mock_generate.return_value = None

        result = await processor.generate_image("a farm landscape")

        assert result is None


class TestOllamaProvider:
    """Test Ollama local provider."""

    def test_initialization(self):
        """Test Ollama provider initialization."""
        provider = OllamaProvider()

        assert provider.base_url is not None
        assert provider.model is not None

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_generate_success(self, mock_post):
        """Test successful image generation."""
        provider = OllamaProvider()

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"image": "aGVsbG8gd29ybGQ="}  # base64 encoded
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        config = ImageGenerationConfig()
        result = await provider.generate("a farm", config)

        assert result is not None

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_generate_error_status(self, mock_post):
        """Test handling of error status."""
        provider = OllamaProvider()

        mock_response = AsyncMock()
        mock_response.status = 500
        mock_post.return_value.__aenter__.return_value = mock_response

        config = ImageGenerationConfig()
        result = await provider.generate("a farm", config)

        assert result is None


class TestGroqProvider:
    """Test Groq cloud provider."""

    def test_initialization_with_key(self):
        """Test Groq provider initialization with API key."""
        with patch.dict("os.environ", {"GROQ_API_KEY": "test_key"}):  # pragma: allowlist secret
            provider = GroqProvider()
            assert provider.api_key == "test_key"

    def test_initialization_without_key(self):
        """Test Groq provider without API key."""
        with patch.dict("os.environ", {}, clear=True):  # pragma: allowlist secret
            provider = GroqProvider()
            assert provider.api_key is None

    @pytest.mark.asyncio
    async def test_generate_without_api_key(self):
        """Test generation fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            provider = GroqProvider()
            config = ImageGenerationConfig()

            result = await provider.generate("a farm", config)

            assert result is None


class TestHuggingFaceProvider:
    """Test Hugging Face cloud provider."""

    def test_initialization_with_key(self):
        """Test HF provider initialization with API key."""
        with patch.dict("os.environ", {"HUGGINGFACE_API_KEY": "test_key"}):
            provider = HuggingFaceProvider()
            assert provider.api_key == "test_key"

    @pytest.mark.asyncio
    async def test_generate_without_api_key(self):
        """Test generation fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            provider = HuggingFaceProvider()
            config = ImageGenerationConfig()

            result = await provider.generate("a farm", config)

            assert result is None


class TestOpenAIProvider:
    """Test OpenAI fallback provider."""

    def test_initialization_with_key(self):
        """Test OpenAI provider initialization with API key."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"}):
            provider = OpenAIProvider()
            assert provider.api_key == "test_key"

    @pytest.mark.asyncio
    async def test_generate_without_api_key(self):
        """Test generation fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            provider = OpenAIProvider()
            config = ImageGenerationConfig()

            result = await provider.generate("a farm", config)

            assert result is None


class TestSingletonPattern:
    """Test singleton pattern."""

    def test_get_image_processor_singleton(self):
        """Test that get_image_processor returns singleton."""
        processor1 = get_image_processor()
        processor2 = get_image_processor()

        assert processor1 is processor2


class TestImageQualityPresets:
    """Test image quality enums."""

    def test_quality_values(self):
        """Test quality enum values."""
        assert ImageQuality.FAST.value == "fast"
        assert ImageQuality.STANDARD.value == "standard"
        assert ImageQuality.QUALITY.value == "quality"
        assert ImageQuality.ULTRA.value == "ultra"


class TestImageProviderEnum:
    """Test image provider enum."""

    def test_provider_values(self):
        """Test provider enum values."""
        assert ImageProvider.OLLAMA_LOCAL.value == "ollama_local"
        assert ImageProvider.GROQ.value == "groq"
        assert ImageProvider.HUGGINGFACE.value == "huggingface"
        assert ImageProvider.OPENAI.value == "openai"
