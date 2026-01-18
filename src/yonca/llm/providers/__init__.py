# src/yonca/llm/providers/__init__.py
"""LLM providers package.

Available providers:
- OllamaProvider: Local LLM inference via Ollama
- GeminiProvider: Cloud LLM via Google Gemini (TODO)
"""

from .base import LLMMessage, LLMProvider, LLMResponse, MessageRole
from .ollama import OllamaProvider

__all__ = [
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "MessageRole",
    "OllamaProvider",
]
