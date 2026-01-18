# src/yonca/llm/providers/groq.py
"""Groq LLM provider for ultra-fast cloud inference.

Groq uses custom LPU (Language Processing Unit) hardware that delivers
200-300 tokens/second - perfect for production demos.

Free tier: https://console.groq.com/
"""

import json
import re
from typing import AsyncIterator

import httpx

from .base import LLMMessage, LLMProvider, LLMResponse


# Qwen3 models have a "thinking mode" that outputs <think>...</think> tags.
# We need to strip these from the response.
THINKING_TAG_PATTERN = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


def strip_thinking_tags(content: str) -> str:
    """Strip Qwen3 thinking mode tags from response content."""
    return THINKING_TAG_PATTERN.sub("", content).strip()


class GroqProvider(LLMProvider):
    """Groq provider for ultra-fast cloud LLM inference.
    
    Groq offers free tier access to Llama 3, Mixtral, and other models
    with exceptionally fast inference (200-300 tokens/sec).
    
    Example:
        ```python
        async with GroqProvider(api_key="gsk_...") as llm:
            response = await llm.generate([
                LLMMessage.user("Salam! 2+2 neçədir?")
            ])
            print(response.content)  # Instant response!
        ```
    """

    # Available models on Groq (as of 2024)
    MODELS = {
        # Meta Llama models
        "llama-3.3-70b-versatile": "Best quality, still very fast",
        "llama-3.1-8b-instant": "Fast and capable (default)",
        "llama3-8b-8192": "Llama 3 8B, good balance",
        "llama3-70b-8192": "Llama 3 70B, highest quality",
        # Alibaba Qwen models
        "qwen/qwen3-32b": "Qwen3 32B, excellent multilingual (Azerbaijani)",
        # Mistral/Mixtral
        "mixtral-8x7b-32768": "Mixtral MoE, large context",
        # Google Gemma
        "gemma2-9b-it": "Google Gemma 2 9B",
    }

    DEFAULT_MODEL = "llama-3.1-8b-instant"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        base_url: str = "https://api.groq.com/openai/v1",
        timeout: float = 30.0,
    ):
        """Initialize Groq provider.
        
        Args:
            api_key: Groq API key (get free at https://console.groq.com/)
            model: Model name (default: llama-3.1-8b-instant)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("Groq API key is required. Get one at https://console.groq.com/")
        
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self.model

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def __aenter__(self) -> "GroqProvider":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the HTTP client on exit."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.__aexit__(None, None, None)

    def _format_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Convert LLMMessage list to OpenAI format (Groq uses OpenAI-compatible API)."""
        return [{"role": m.role.value, "content": m.content} for m in messages]

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate a response from Groq (ultra-fast!).
        
        Args:
            messages: Conversation messages.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.
            
        Returns:
            LLMResponse with the generated content.
        """
        client = await self._get_client()

        payload = {
            "model": self.model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()
        choice = data["choices"][0]
        content = choice["message"]["content"]
        
        # Strip Qwen3 thinking tags if present
        if self.model.startswith("qwen"):
            content = strip_thinking_tags(content)

        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
            metadata={
                "prompt_tokens": data.get("usage", {}).get("prompt_tokens"),
                "completion_tokens": data.get("usage", {}).get("completion_tokens"),
                "id": data.get("id"),
            },
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Stream responses from Groq.
        
        Args:
            messages: Conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            
        Yields:
            Content chunks as they arrive.
            
        Note:
            For Qwen3 models, thinking tags are accumulated and stripped
            before yielding content.
        """
        client = await self._get_client()

        payload = {
            "model": self.model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        is_qwen = self.model.startswith("qwen")
        in_thinking_block = False
        buffer = ""

        async with client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            content = delta["content"]
                            
                            # Handle Qwen3 thinking tags in streaming
                            if is_qwen:
                                buffer += content
                                
                                # Check for start of thinking block
                                if "<think>" in buffer and not in_thinking_block:
                                    in_thinking_block = True
                                    # Yield content before <think> tag
                                    before_think = buffer.split("<think>")[0]
                                    if before_think:
                                        yield before_think
                                    buffer = buffer[buffer.index("<think>"):]
                                    
                                # Check for end of thinking block
                                if "</think>" in buffer and in_thinking_block:
                                    in_thinking_block = False
                                    # Skip the thinking content
                                    buffer = buffer.split("</think>", 1)[1].lstrip()
                                    if buffer:
                                        yield buffer
                                    buffer = ""
                                    continue
                                    
                                # If in thinking block, don't yield
                                if in_thinking_block:
                                    continue
                                    
                                # Not in thinking block, yield accumulated buffer
                                if buffer:
                                    yield buffer
                                    buffer = ""
                            else:
                                yield content
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> bool:
        """Check if Groq API is accessible."""
        try:
            client = await self._get_client()
            response = await client.get("/models")
            return response.status_code == 200
        except Exception:
            return False
