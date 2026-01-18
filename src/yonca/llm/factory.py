# src/yonca/llm/factory.py
"""LLM Provider Factory.

Creates and manages LLM provider instances based on configuration.
Supports automatic provider selection and fallback logic.
"""

from functools import lru_cache

from yonca.config import LLMProvider as LLMProviderEnum
from yonca.config import settings

from .providers import LLMProvider, OllamaProvider


class LLMProviderError(Exception):
    """Raised when LLM provider creation fails."""

    pass


def create_ollama_provider(
    base_url: str | None = None,
    model: str | None = None,
) -> OllamaProvider:
    """Create an Ollama provider instance.
    
    Args:
        base_url: Ollama server URL (uses config if None)
        model: Model name (uses config if None)
        
    Returns:
        Configured OllamaProvider instance.
    """
    return OllamaProvider(
        base_url=base_url or settings.ollama_base_url,
        model=model or settings.ollama_model,
    )


def create_gemini_provider(
    api_key: str | None = None,
    model: str | None = None,
) -> LLMProvider:
    """Create a Gemini provider instance.
    
    Args:
        api_key: Gemini API key (uses config if None)
        model: Model name (uses config if None)
        
    Returns:
        Configured GeminiProvider instance.
        
    Raises:
        LLMProviderError: If API key is not configured.
        NotImplementedError: Gemini provider not yet implemented.
    """
    key = api_key or settings.gemini_api_key
    if not key:
        raise LLMProviderError(
            "Gemini API key is required. Set YONCA_GEMINI_API_KEY environment variable."
        )

    # TODO: Implement GeminiProvider
    raise NotImplementedError(
        "Gemini provider is not yet implemented. Use Ollama for local development."
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
