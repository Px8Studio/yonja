# src/yonca/llm/factory.py
"""LLM Provider Factory with multi-provider support.

Creates and manages LLM provider instances based on configuration.
Supports automatic provider selection, fallback logic, and speed-optimized selection.

Providers (in speed order):
1. Groq - Ultra-fast LPU hardware, free tier available
2. Gemini - Google's fast cloud API, free tier available  
3. Ollama - Local inference (slow on CPU, fast with GPU)
"""

from functools import lru_cache

from yonca.config import LLMProvider as LLMProviderEnum
from yonca.config import settings

from .providers.base import LLMProvider
from .providers.ollama import OllamaProvider


class LLMProviderError(Exception):
    """Raised when LLM provider creation fails."""

    pass


def create_ollama_provider(
    base_url: str | None = None,
    model: str | None = None,
    timeout: float = 300.0,  # 5 min for slow CPU inference
) -> OllamaProvider:
    """Create an Ollama provider instance.
    
    Args:
        base_url: Ollama server URL (uses config if None)
        model: Model name (uses config if None)
        timeout: Request timeout in seconds (default 5 min for CPU)
        
    Returns:
        Configured OllamaProvider instance.
    """
    return OllamaProvider(
        base_url=base_url or settings.ollama_base_url,
        model=model or settings.ollama_model,
        timeout=timeout,
    )


def create_groq_provider(
    api_key: str | None = None,
    model: str | None = None,
    timeout: float = 30.0,
) -> LLMProvider:
    """Create a Groq provider instance (ultra-fast cloud).
    
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


def create_gemini_provider(
    api_key: str | None = None,
    model: str | None = None,
    timeout: float = 60.0,
) -> LLMProvider:
    """Create a Gemini provider instance.
    
    Args:
        api_key: Gemini API key (uses config if None)
        model: Model name (uses config if None)
        timeout: Request timeout in seconds
        
    Returns:
        Configured GeminiProvider instance.
        
    Raises:
        LLMProviderError: If API key is not configured.
    """
    from .providers.gemini import GeminiProvider
    
    key = api_key or settings.gemini_api_key
    if not key:
        raise LLMProviderError(
            "Gemini API key is required. Set YONCA_GEMINI_API_KEY or get one at https://ai.google.dev/"
        )

    return GeminiProvider(
        api_key=key,
        model=model or settings.gemini_model,
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
    elif provider == LLMProviderEnum.GEMINI:
        return create_gemini_provider(**kwargs)
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
    
    Checks providers in speed order: Groq -> Gemini -> Ollama
    Returns the first one that passes a health check.
    
    This is useful for demos where speed matters more than consistency.
    
    Returns:
        The fastest available provider.
        
    Raises:
        LLMProviderError: If no providers are available.
    """
    errors = []
    
    # Try Groq first (fastest - 200-300 tokens/sec)
    if settings.groq_api_key:
        try:
            provider = create_groq_provider()
            if await provider.health_check():
                print(f"⚡ Using Groq ({provider.model_name}) - ultra-fast cloud")
                return provider
        except Exception as e:
            errors.append(f"Groq: {e}")

    # Then Gemini (fast cloud)
    if settings.gemini_api_key:
        try:
            provider = create_gemini_provider()
            if await provider.health_check():
                print(f"☁️ Using Gemini ({provider.model_name}) - fast cloud")
                return provider
        except Exception as e:
            errors.append(f"Gemini: {e}")

    # Finally Ollama (local - slow on CPU)
    try:
        provider = create_ollama_provider()
        if await provider.health_check():
            print(f"🖥️ Using Ollama ({provider.model_name}) - local inference")
            return provider
    except Exception as e:
        errors.append(f"Ollama: {e}")

    raise LLMProviderError(
        f"No LLM providers available. Errors: {'; '.join(errors)}"
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
    
    # Check Ollama
    try:
        provider = create_ollama_provider()
        results["ollama"] = {
            "model": provider.model_name,
            "healthy": await provider.health_check(),
            "speed": "slow (CPU) / fast (GPU)",
        }
    except Exception as e:
        results["ollama"] = {"healthy": False, "error": str(e)}
    
    # Check Groq
    if settings.groq_api_key:
        try:
            provider = create_groq_provider()
            results["groq"] = {
                "model": provider.model_name,
                "healthy": await provider.health_check(),
                "speed": "ultra-fast (LPU)",
            }
        except Exception as e:
            results["groq"] = {"healthy": False, "error": str(e)}
    else:
        results["groq"] = {"healthy": False, "error": "No API key configured"}
    
    # Check Gemini
    if settings.gemini_api_key:
        try:
            provider = create_gemini_provider()
            results["gemini"] = {
                "model": provider.model_name,
                "healthy": await provider.health_check(),
                "speed": "fast (cloud)",
            }
        except Exception as e:
            results["gemini"] = {"healthy": False, "error": str(e)}
    else:
        results["gemini"] = {"healthy": False, "error": "No API key configured"}
    
    return results
