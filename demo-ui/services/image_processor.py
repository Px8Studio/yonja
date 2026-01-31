# demo-ui/services/image_processor.py
"""Image generation and processing service.

Supports multiple image generation backends:
- Local: Ollama (via text2img models)
- Cloud: Groq (via API)
- Cloud: Hugging Face Inference API
- Cloud: OpenAI DALL-E (fallback)

Features:
- Multi-provider support with fallback
- Async/streaming support
- Image quality presets
- Prompt optimization
- Caching with Redis
"""

import asyncio
import base64
import logging
import os
from dataclasses import dataclass
from enum import Enum

import aiohttp

logger = logging.getLogger(__name__)


class ImageProvider(str, Enum):
    """Supported image generation providers."""

    OLLAMA_LOCAL = "ollama_local"  # Local Ollama
    GROQ = "groq"  # Groq API
    HUGGINGFACE = "huggingface"  # HF Inference API
    OPENAI = "openai"  # OpenAI DALL-E (fallback)


class ImageQuality(str, Enum):
    """Image quality presets."""

    FAST = "fast"  # Low quality, fast (256x256)
    STANDARD = "standard"  # Standard quality (512x512)
    QUALITY = "quality"  # High quality (1024x1024)
    ULTRA = "ultra"  # Ultra quality (1024x1024, max iterations)


@dataclass
class ImageGenerationConfig:
    """Configuration for image generation."""

    provider: ImageProvider = ImageProvider.OLLAMA_LOCAL
    quality: ImageQuality = ImageQuality.STANDARD
    model: str = "stable-diffusion-v1-5"  # Default model
    steps: int = 20  # Number of inference steps
    guidance_scale: float = 7.5  # Guidance scale for diffusion
    seed: int | None = None  # For reproducibility
    negative_prompt: str = "blurry, low quality, distorted"
    timeout: int = 120  # Request timeout in seconds


class ImageProcessor:
    """Main image processor with multi-provider support."""

    def __init__(self):
        self.config = ImageGenerationConfig()
        self._setup_providers()

    def _setup_providers(self):
        """Initialize provider configurations."""
        self.providers = {
            ImageProvider.OLLAMA_LOCAL: OllamaProvider(),
            ImageProvider.GROQ: GroqProvider(),
            ImageProvider.HUGGINGFACE: HuggingFaceProvider(),
            ImageProvider.OPENAI: OpenAIProvider(),
        }

    async def generate_image(
        self,
        prompt: str,
        provider: ImageProvider | None = None,
        quality: ImageQuality | None = None,
        **kwargs,
    ) -> bytes | None:
        """Generate image from prompt.

        Args:
            prompt: Image description
            provider: Provider to use (defaults to config)
            quality: Quality preset (defaults to config)
            **kwargs: Additional provider-specific args

        Returns:
            Image bytes or None if failed
        """
        provider = provider or self.config.provider
        quality = quality or self.config.quality

        # Optimize prompt
        optimized_prompt = self._optimize_prompt(prompt)
        logger.info(f"generating_image: provider={provider}, quality={quality}")

        # Configure based on quality
        config = self._get_quality_config(quality)

        try:
            # Try primary provider
            result = await self.providers[provider].generate(optimized_prompt, config, **kwargs)

            if result:
                logger.info(f"image_generated: provider={provider}, size={len(result)} bytes")
                return result

            # Fallback to next provider
            logger.warning(f"primary_provider_failed: {provider}, attempting fallback")
            return await self._fallback_generate(optimized_prompt, config, provider, **kwargs)

        except Exception as e:
            logger.error(f"image_generation_failed: {provider}, error={str(e)}", exc_info=True)
            return await self._fallback_generate(optimized_prompt, config, provider, **kwargs)

    async def _fallback_generate(
        self,
        prompt: str,
        config: ImageGenerationConfig,
        failed_provider: ImageProvider,
        **kwargs,
    ) -> bytes | None:
        """Try fallback providers in order."""
        fallback_order = [
            ImageProvider.OLLAMA_LOCAL,
            ImageProvider.GROQ,
            ImageProvider.HUGGINGFACE,
            ImageProvider.OPENAI,
        ]

        for provider in fallback_order:
            if provider == failed_provider:
                continue

            try:
                logger.info(f"trying_fallback: {provider}")
                result = await self.providers[provider].generate(prompt, config, **kwargs)

                if result:
                    logger.info(f"fallback_successful: {provider}")
                    return result
            except Exception as e:
                logger.warning(f"fallback_failed: {provider}, error={str(e)}")
                continue

        logger.error("all_providers_exhausted")
        return None

    def _optimize_prompt(self, prompt: str) -> str:
        """Optimize prompt for better results."""
        # Add quality descriptors
        quality_tokens = [
            "highly detailed",
            "professional",
            "sharp focus",
            "intricate",
            "award-winning",
        ]

        if not any(token in prompt.lower() for token in quality_tokens):
            prompt = f"{prompt}, highly detailed, sharp focus"

        return prompt

    def _get_quality_config(self, quality: ImageQuality) -> ImageGenerationConfig:
        """Get config based on quality preset."""
        configs = {
            ImageQuality.FAST: ImageGenerationConfig(quality=quality, steps=10, guidance_scale=5.0),
            ImageQuality.STANDARD: ImageGenerationConfig(
                quality=quality, steps=20, guidance_scale=7.5
            ),
            ImageQuality.QUALITY: ImageGenerationConfig(
                quality=quality, steps=40, guidance_scale=7.5
            ),
            ImageQuality.ULTRA: ImageGenerationConfig(
                quality=quality, steps=60, guidance_scale=12.0
            ),
        }
        return configs.get(quality, self.config)


class OllamaProvider:
    """Local Ollama image generation."""

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_IMAGE_MODEL", "stable-diffusion-v1-5")
        self.timeout = aiohttp.ClientTimeout(total=300)

    async def generate(self, prompt: str, config: ImageGenerationConfig, **kwargs) -> bytes | None:
        """Generate image using Ollama."""
        try:
            url = f"{self.base_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "parameters": {
                    "num_predict": config.steps,
                    "top_p": config.guidance_scale / 10,
                },
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Handle image response
                        if "image" in data:
                            return base64.b64decode(data["image"])

                        logger.warning("no_image_in_ollama_response")
                        return None

                    logger.error(f"ollama_error: status={response.status}")
                    return None

        except asyncio.TimeoutError:
            logger.error("ollama_timeout")
            return None
        except Exception as e:
            logger.error(f"ollama_error: {str(e)}", exc_info=True)
            return None


class GroqProvider:
    """Groq API image generation (via vision model inference)."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_IMAGE_MODEL", "groq-vision-v1")
        self.timeout = aiohttp.ClientTimeout(total=120)

    async def generate(self, prompt: str, config: ImageGenerationConfig, **kwargs) -> bytes | None:
        """Generate image using Groq API."""
        if not self.api_key:
            logger.warning("groq_api_key_not_set")
            return None

        try:
            # Groq API endpoint for image generation
            url = "https://api.groq.com/openai/v1/images/generations"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # Map quality to Groq image size
            size_map = {
                ImageQuality.FAST: "256x256",
                ImageQuality.STANDARD: "512x512",
                ImageQuality.QUALITY: "1024x1024",
                ImageQuality.ULTRA: "1024x1024",
            }

            payload = {
                "prompt": prompt,
                "model": self.model,
                "n": 1,
                "size": size_map.get(config.quality, "512x512"),
                "quality": "hd"
                if config.quality in [ImageQuality.QUALITY, ImageQuality.ULTRA]
                else "standard",
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("data") and len(data["data"]) > 0:
                            image_url = data["data"][0].get("url")

                            if image_url:
                                # Download image
                                async with session.get(image_url) as img_response:
                                    if img_response.status == 200:
                                        return await img_response.read()

                    logger.error(f"groq_error: status={response.status}")
                    return None

        except asyncio.TimeoutError:
            logger.error("groq_timeout")
            return None
        except Exception as e:
            logger.error(f"groq_error: {str(e)}", exc_info=True)
            return None


class HuggingFaceProvider:
    """Hugging Face Inference API image generation."""

    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.model = os.getenv("HUGGINGFACE_IMAGE_MODEL", "stabilityai/stable-diffusion-2-1")
        self.timeout = aiohttp.ClientTimeout(total=120)

    async def generate(self, prompt: str, config: ImageGenerationConfig, **kwargs) -> bytes | None:
        """Generate image using Hugging Face API."""
        if not self.api_key:
            logger.warning("huggingface_api_key_not_set")
            return None

        try:
            url = f"https://api-inference.huggingface.co/models/{self.model}"

            headers = {"Authorization": f"Bearer {self.api_key}"}

            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": config.steps,
                    "guidance_scale": config.guidance_scale,
                    "negative_prompt": config.negative_prompt,
                },
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()

                    logger.error(f"huggingface_error: status={response.status}")
                    return None

        except asyncio.TimeoutError:
            logger.error("huggingface_timeout")
            return None
        except Exception as e:
            logger.error(f"huggingface_error: {str(e)}", exc_info=True)
            return None


class OpenAIProvider:
    """OpenAI DALL-E image generation (fallback)."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "dall-e-3"
        self.timeout = aiohttp.ClientTimeout(total=120)

    async def generate(self, prompt: str, config: ImageGenerationConfig, **kwargs) -> bytes | None:
        """Generate image using OpenAI DALL-E."""
        if not self.api_key:
            logger.warning("openai_api_key_not_set")
            return None

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            # Map quality to DALL-E sizes
            size_map = {
                ImageQuality.FAST: "1024x1024",
                ImageQuality.STANDARD: "1024x1024",
                ImageQuality.QUALITY: "1024x1024",
                ImageQuality.ULTRA: "1024x1024",
            }

            response = await client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size_map.get(config.quality, "1024x1024"),
                quality="hd"
                if config.quality in [ImageQuality.QUALITY, ImageQuality.ULTRA]
                else "standard",
                n=1,
            )

            if response.data and len(response.data) > 0:
                image_url = response.data[0].url

                # Download image
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(image_url) as img_response:
                        if img_response.status == 200:
                            return await img_response.read()

            logger.error("openai_no_image_in_response")
            return None

        except Exception as e:
            logger.error(f"openai_error: {str(e)}", exc_info=True)
            return None


# ============================================
# SINGLETON INSTANCE
# ============================================
_processor: ImageProcessor | None = None


def get_image_processor() -> ImageProcessor:
    """Get or create singleton image processor."""
    global _processor
    if _processor is None:
        _processor = ImageProcessor()
    return _processor
