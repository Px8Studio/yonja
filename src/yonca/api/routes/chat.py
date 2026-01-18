# src/yonca/api/routes/chat.py
"""Chat endpoints for Yonca AI."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from yonca.config import Settings, get_settings
from yonca.llm import LLMMessage, check_llm_health, get_llm_provider


router = APIRouter()


# ============================================================
# Request/Response Models
# ============================================================


class ChatMessage(BaseModel):
    """Chat message request model."""

    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    language: str = "az"
    model: str | None = None  # Override model if specified
    stream: bool = False  # Enable streaming response


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    session_id: str
    model: str
    tokens_used: int = 0
    intent: str | None = None


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT_AZ = """Sən Yonca AI - Azərbaycan fermerlərinin süni intellekt köməkçisisən.

Sənin vəzifələrin:
- Fermerlərə əkinçilik, heyvandarlıq və kənd təsərrüfatı məsləhətləri vermək
- Suvarma, gübrələmə, zərərvericilərlə mübarizə barədə tövsiyələr vermək
- Azərbaycan iqlimi və torpaq şəraiti haqqında məlumat vermək
- Sualları sadə və anlaşılan dildə cavablandırmaq

Qaydalar:
- Həmişə Azərbaycan dilində cavab ver
- Qısa və konkret ol
- Praktik məsləhətlər ver
- Əgər bilmirsənsə, düzgün mütəxəssisə yönləndir"""


# ============================================================
# Endpoints
# ============================================================


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatMessage,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    Chat endpoint for Yonca AI.
    
    Accepts a message and returns an AI-generated response.
    Supports both streaming and non-streaming modes.
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    # Get the LLM provider
    llm = get_llm_provider()

    # Build messages
    messages = [
        LLMMessage.system(SYSTEM_PROMPT_AZ),
        LLMMessage.user(request.message),
    ]

    try:
        # Generate response
        response = await llm.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )

        return ChatResponse(
            response=response.content,
            session_id=session_id,
            model=response.model,
            tokens_used=response.tokens_used,
            intent=None,  # TODO: Add intent detection
        )

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM service unavailable: {str(e)}",
        ) from e


@router.post("/chat/stream")
async def chat_stream(
    request: ChatMessage,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    Streaming chat endpoint for Yonca AI.
    
    Returns a streaming response with incremental text chunks.
    """
    llm = get_llm_provider()

    messages = [
        LLMMessage.system(SYSTEM_PROMPT_AZ),
        LLMMessage.user(request.message),
    ]

    async def generate():
        try:
            async for chunk in llm.stream(
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            ):
                yield chunk
        except Exception as e:
            yield f"\n\n[Xəta: {str(e)}]"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )


@router.get("/status")
async def chat_status():
    """
    Chat service status endpoint.
    
    Returns the current status of the chat service and LLM health.
    """
    llm_health = await check_llm_health()

    return {
        "service": "chat",
        "status": "operational" if llm_health["healthy"] else "degraded",
        "llm": llm_health,
        "features": {
            "streaming": True,
            "context_memory": False,  # TODO: Enable with LangGraph
            "intent_detection": False,  # TODO: Enable with rules engine
        },
    }
