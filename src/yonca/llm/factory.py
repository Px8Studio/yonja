# src/yonca/llm/factory.py
"""LLM Provider Factory with multi-provider support.

Creates and manages LLM provider instances based on configuration.

Providers:
1. Groq - Open-source models (Llama, Qwen, Mistral) with enterprise-grade infrastructure
   - Demonstrates production-ready performance with proper hardware
   - Can be self-hosted with appropriate infrastructure (LPU, GPU clusters)
   - Ultra-fast inference (200-300 tokens/sec)
   
2. Gemini - Proprietary cloud models from Google
   - Closed-source, cloud-only
   - Fast cloud API with good multilingual support
"""

from functools import lru_cache

from yonca.config import LLMProvider as LLMProviderEnum
from yonca.config import settings

from .providers.base import LLMProvider


class LLMProviderError(Exception):
    """Raised when LLM provider creation fails."""

    pass


def create_groq_provider(
    api_key: str | None = None,
    model: str | None = None,
    timeout: float = 30.0,
) -> LLMProvider:
    """Create a Groq provider for open-source models.
    
    Groq runs open-source models (Llama, Qwen, Mistral) on enterprise-grade
    infrastructure. This demonstrates how these models perform with proper hardware.
    
    Can be self-hosted with:
    - Groq LPU (Language Processing Unit) hardware
    - NVIDIA GPU clusters (A100, H100)
    - Optimized inference servers (vLLM, TGI)
    
    Args:
        api_key: Groq API key (uses config if None)
        model: Model name (uses config if None)
        timeout: Request timeout in seconds
        
    Returns:
        Configured GroqProvider instance.
        
    Raises:
        LLMProviderError: If API key is not configured.
    """
    from .providers.groq import GroqProvider
    
    key = api_key or settings.groq_api_key
    if not key:
        raise LLMProviderError(
            "Groq API key is required. Set YONCA_GROQ_API_KEY or get a free key at https://console.groq.com/"
        )

    return GroqProvider(
        api_key=key,
        model=model or settings.groq_model,
        timeout=timeout,
    )


def create_ollama_provider(
    base_url: str | None = None,
    model: str | None = None,
    timeout: float = 120.0,
) -> LLMProvider:
    """Create an Ollama provider for local LLM inference.
    
    Args:
        base_url: Ollama server URL (uses config if None)
        model: Model name (uses config if None)
        timeout: Request timeout in seconds
        
    Returns:
        Configured OllamaProvider instance.
    """
    from .providers.ollama import OllamaProvider
    
    return OllamaProvider(
        base_url=base_url or settings.ollama_base_url,
        model=model or settings.ollama_model,
        timeout=timeout,
    )


def create_llm_provider(
    provider_type: LLMProviderEnum | None = None,
    **kwargs,
) -> LLMProvider:
    """Create an LLM provider based on type.
    
    Args:
        provider_type: Provider type (uses config if None)
        **kwargs: Additional arguments passed to provider constructor
        
    Returns:
        Configured LLMProvider instance.
        
    Raises:
        LLMProviderError: If provider type is unknown.
    """
    provider = provider_type or settings.llm_provider

    if provider == LLMProviderEnum.OLLAMA:
        return create_ollama_provider(**kwargs)
    elif provider == LLMProviderEnum.GROQ:
        return create_groq_provider(**kwargs)
    else:
        raise LLMProviderError(f"Unknown LLM provider: {provider}")


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Get the default LLM provider (cached singleton).
    
    Uses configuration to determine which provider to create.
    The instance is cached and reused across requests.
    
    Returns:
        Configured LLMProvider instance.
    """
    return create_llm_provider()


async def get_fastest_available_provider() -> LLMProvider:
    """Get the fastest available LLM provider with automatic fallback.
    
    Checks Groq provider availability and returns it if healthy.
    
    Returns:
        The fastest available provider.
        
    Raises:
        LLMProviderError: If no providers are available.
    """
    errors = []
    
    # Try Groq (fastest - 200-300 tokens/sec with open-source models)
    if settings.groq_api_key:
        try:
            provider = create_groq_provider()
            if await provider.health_check():
                print(f"⚡ Using Groq ({provider.model_name}) - open-source, enterprise-grade")
                return provider
        except Exception as e:
            errors.append(f"Groq: {e}")

    raise LLMProviderError(
        f"No LLM providers available. Configure YONCA_GROQ_API_KEY. Errors: {'; '.join(errors)}"
    )


async def check_llm_health() -> dict:
    """Check health of the configured LLM provider.
    
    Returns:
        Dict with health status and provider info.
    """
    provider = get_llm_provider()
    is_healthy = await provider.health_check()

    return {
        "provider": provider.provider_name,
        "model": provider.model_name,
        "healthy": is_healthy,
    }


async def check_all_providers_health() -> dict:
    """Check health of all configured providers.
    
    Returns:
        Dict with health status for each provider.
    """
    results = {}
    
    # Check Groq (open-source models)
    if settings.groq_api_key:
        try:
            provider = create_groq_provider()
            results["groq"] = {
                "model": provider.model_name,
                "healthy": await provider.health_check(),
                "type": "open-source",
                "speed": "ultra-fast (200-300 tok/s)",
                "self_hostable": True,
            }
        except Exception as e:
            results["groq"] = {"healthy": False, "error": str(e)}
    else:
        results["groq"] = {"healthy": False, "error": "No API key configured"}
    
    return results
