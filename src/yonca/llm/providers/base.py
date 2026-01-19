# src/yonca/llm/providers/base.py
"""Abstract base class for LLM providers.

Defines the interface that all LLM providers (Ollama, Groq, etc.) must implement.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncIterator

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message in the conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMMessage(BaseModel):
    """A single message in an LLM conversation."""

    role: MessageRole
    content: str

    @classmethod
    def system(cls, content: str) -> "LLMMessage":
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "LLMMessage":
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> "LLMMessage":
        """Create an assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content)


class LLMResponse(BaseModel):
    """Response from an LLM provider."""

    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"
    metadata: dict = Field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    All LLM providers (Ollama, Groq, etc.) must implement this interface.
    This ensures consistent behavior across different backends.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'ollama', 'groq')."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name being used."""
        ...

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.
            
        Returns:
            LLMResponse with the generated content.
        """
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Stream a response from the LLM.
        
        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.
            
        Yields:
            String chunks of the generated response.
        """
        # Make this a proper async generator
        yield ""  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM provider is healthy and reachable.
        
        Returns:
            True if healthy, False otherwise.
        """
        ...

    async def __aenter__(self) -> "LLMProvider":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - cleanup resources."""
        pass
