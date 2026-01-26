# src/ALİM/llm/__init__.py
"""LLM module for ALİM.

Provides abstracted access to multiple LLM backends (Ollama, Groq).

Usage:
    ```python
    from alim.llm import get_llm_provider, LLMMessage

    # Get the configured provider
    llm = get_llm_provider()

    # Generate a response
    response = await llm.generate([
        LLMMessage.system("You are a helpful farming assistant."),
        LLMMessage.user("Buğda əkinini nə vaxt suvarmalıyam?")
    ])
    print(response.content)
    ```
"""

from .factory import (
    LLMProviderError,
    check_llm_health,
    create_llm_provider,
    create_ollama_provider,
    get_llm_from_config,
    get_llm_provider,
    get_llm_provider_with_model,
)
from .models import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    LocalModel,
    ModelSource,
    get_available_model_names,
    get_model_info,
)
from .providers import LLMMessage, LLMProvider, LLMResponse, MessageRole, OllamaProvider

__all__ = [
    # Factory
    "create_llm_provider",
    "create_ollama_provider",
    "get_llm_provider",
    "get_llm_provider_with_model",
    "get_llm_from_config",
    "check_llm_health",
    "LLMProviderError",
    # Providers
    "LLMProvider",
    "OllamaProvider",
    "LLMMessage",
    "LLMResponse",
    "MessageRole",
    # Models
    "AVAILABLE_MODELS",
    "DEFAULT_MODEL",
    "LocalModel",
    "ModelSource",
    "get_model_info",
    "get_available_model_names",
]
