# src/yonca/llm/providers/__init__.py
"""LLM providers package.

Available providers:
- OllamaProvider: Local LLM inference via Ollama (slow on CPU)
- GroqProvider: Ultra-fast cloud inference via Groq LPU
- GeminiProvider: Cloud LLM via Google Gemini

Speed comparison on Intel i7 (no GPU):
- Groq:   ~2 seconds (200-300 tokens/sec)
- Gemini: ~5 seconds (cloud latency)
- Ollama: ~3-5 minutes (CPU inference)
"""

from .base import LLMMessage, LLMProvider, LLMResponse, MessageRole
from .gemini import GeminiProvider
from .groq import GroqProvider
from .ollama import OllamaProvider

__all__ = [
    "LLMMessage",
    "LLMProvider", 
    "LLMResponse",
    "MessageRole",
    "OllamaProvider",
    "GroqProvider",
    "GeminiProvider",
]
