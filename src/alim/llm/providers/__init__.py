# src/ALİM/llm/providers/__init__.py
"""LLM providers package.

Available providers:
- OllamaProvider: Local LLM inference via Ollama (slow on CPU)
- GroqProvider: Ultra-fast cloud inference via Groq LPU

Speed comparison on Intel i7 (no GPU):
- Groq:   ~2 seconds (200-300 tokens/sec)
- Ollama: ~3-5 minutes (CPU inference)
"""

from .base import LLMMessage, LLMProvider, LLMResponse, MessageRole
from .groq import GroqProvider
from .ollama import OllamaProvider

__all__ = [
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "MessageRole",
    "OllamaProvider",
    "GroqProvider",
]
