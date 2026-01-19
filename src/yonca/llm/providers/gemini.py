# src/yonca/llm/providers/gemini.py
"""Google Gemini LLM provider for cloud inference.

Uses Google's Generative AI API for high-quality, multilingual responses.
Free tier available at: https://ai.google.dev/
"""

import json
from typing import AsyncIterator, Any

from .base import LLMMessage, LLMProvider, LLMResponse, LLMProviderError
from yonca.llm.http_pool import HTTPClientPool

genai: Any = None


class GeminiProvider(LLMProvider):
    """Google Gemini provider for cloud LLM inference.
    
    Gemini offers excellent multilingual support including Azerbaijani.
    
    Example:
        ```python
        async with GeminiProvider(api_key="AIza...") as llm:
            response = await llm.generate([
                LLMMessage.user("Salam! Buğda əkmək üçün ən yaxşı vaxt nədir?")
            ])
            print(response.content)
        ```
    """

    # Available Gemini models
    MODELS = {
        "gemini-2.0-flash-exp": "Latest flash model, very fast",
        "gemini-1.5-flash": "Fast and efficient",
        "gemini-1.5-pro": "Highest quality, complex reasoning",
        "gemini-1.5-flash-8b": "Lightweight flash variant",
    }

    DEFAULT_MODEL = "gemini-2.0-flash-exp"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout: float = 60.0,
    ):
        """Initialize Gemini provider.
        
        Args:
            api_key: Google AI API key (get at https://ai.google.dev/)
            model: Model name (default: gemini-2.0-flash-exp)
            timeout: Request timeout in seconds
        """
        global genai
        if genai is None:
            try:
                import google.generativeai as _genai  # type: ignore
            except ImportError as exc:
                raise LLMProviderError(
                    "Gemini provider requires optional dependency 'google-generativeai' "
                    "(kept out of default deps to avoid protobuf<6 conflicts). "
                    "Install it manually in an isolated env if you need Gemini."
                ) from exc
            genai = _genai
        genai.configure(api_key=api_key)
        self.model_name = model
        self._client = genai.GenerativeModel(model=model)

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self.model

    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client from the shared connection pool.
        
        Uses HTTPClientPool for proper connection management across
        multiple concurrent users.
        """
        return await HTTPClientPool.get_pool(
            provider="gemini",
            headers={
                "Content-Type": "application/json",
            },
        )

    async def __aenter__(self) -> "GeminiProvider":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Connection pool cleanup is handled by HTTPClientPool.close_all()."""
        pass

    async def close(self) -> None:
        """Connection pool cleanup is handled by HTTPClientPool.close_all()."""
        pass

    def _format_messages(self, messages: list[LLMMessage]) -> tuple[str | None, list[dict]]:
        """Convert LLMMessage list to Gemini format.
        
        Returns:
            Tuple of (system_instruction, contents)
        """
        system_instruction = None
        contents = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Gemini handles system as separate instruction
                system_instruction = msg.content
            elif msg.role == MessageRole.USER:
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.content}]
                })
            elif msg.role == MessageRole.ASSISTANT:
                contents.append({
                    "role": "model",
                    "parts": [{"text": msg.content}]
                })
        
        return system_instruction, contents

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate a response from Gemini.
        
        Args:
            messages: Conversation messages.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.
            
        Returns:
            LLMResponse with the generated content.
        """
        client = await self._get_client()
        
        system_instruction, contents = self._format_messages(messages)
        
        url = f"{self.base_url}/models/{self.model}:generateContent"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        response = await client.post(
            url,
            json=payload,
            params={"key": self.api_key},
        )
        response.raise_for_status()

        data = response.json()
        
        # Extract content from Gemini response
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("No response candidates from Gemini")
        
        content = candidates[0]["content"]["parts"][0]["text"]
        finish_reason = candidates[0].get("finishReason", "STOP")
        
        # Extract token usage
        usage = data.get("usageMetadata", {})
        tokens_used = usage.get("totalTokenCount", 0)

        return LLMResponse(
            content=content,
            model=self.model,
            tokens_used=tokens_used,
            finish_reason=finish_reason.lower(),
            metadata={
                "prompt_tokens": usage.get("promptTokenCount"),
                "completion_tokens": usage.get("candidatesTokenCount"),
            },
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Stream responses from Gemini.
        
        Args:
            messages: Conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            
        Yields:
            Content chunks as they arrive.
        """
        client = await self._get_client()
        
        system_instruction, contents = self._format_messages(messages)
        
        url = f"{self.base_url}/models/{self.model}:streamGenerateContent"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        async with client.stream(
            "POST",
            url,
            json=payload,
            params={"key": self.api_key, "alt": "sse"},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                if "text" in part:
                                    yield part["text"]
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            client = await self._get_client()
            url = f"{self.base_url}/models/{self.model}"
            response = await client.get(url, params={"key": self.api_key})
            return response.status_code == 200
        except Exception:
            return False
