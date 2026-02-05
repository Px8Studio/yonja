# src/ALİM/api/routes/chat.py
"""Chat endpoints for ALİM with multi-turn conversation support."""

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from alim.api.middleware.rate_limit import chat_limiter, check_rate_limit
from alim.config import Settings, get_settings
from alim.data.redis_client import RedisClient, SessionStorage
from alim.llm import LLMMessage, check_llm_health, get_llm_provider

router = APIRouter()


# ============================================================
# Request/Response Models
# ============================================================


class ChatMessage(BaseModel):
    """Chat message request model."""

    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    user_id: str | None = None  # Optional user identifier for multi-user support
    farm_id: str | None = None  # Farm context for personalized advice
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
    message_count: int = 0  # Number of messages in session history


# ============================================================
# System Prompt Management
# ============================================================


def load_system_prompt(prompt_name: str = "master_v1.0.0_az_strict") -> str:
    """
    Load system prompt from file.

    Args:
        prompt_name: Name of the prompt file (without .txt extension)

    Returns:
        System prompt content as string
    """
    # Get project root (3 levels up from this file)
    project_root = Path(__file__).parent.parent.parent.parent
    prompt_path = project_root / "prompts" / "system" / f"{prompt_name}.txt"

    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        # Fallback to basic prompt if file not found
        return SYSTEM_PROMPT_AZ_FALLBACK


# Fallback prompt (used if file loading fails)
SYSTEM_PROMPT_AZ_FALLBACK = """Sən ALİM - Azərbaycan fermerlərinin süni intellekt köməkçisisən.

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

# Load enhanced system prompt with linguistic anchors
SYSTEM_PROMPT_AZ = load_system_prompt("master_v1.0.0_az_strict")


# ============================================================
# Endpoints
# ============================================================


async def _build_messages_with_history(
    session_id: str,
    user_message: str,
    user_id: str | None = None,
) -> tuple[list[LLMMessage], dict]:
    """Build messages list including conversation history.

    Args:
        session_id: Session identifier.
        user_message: Current user message.
        user_id: Optional user identifier.

    Returns:
        Tuple of (messages list, session data).
    """
    # Get or create session with conversation history
    session = await SessionStorage.get_or_create(
        session_id=session_id,
        user_id=user_id,
    )

    # Start with system prompt
    messages = [LLMMessage.system(SYSTEM_PROMPT_AZ)]

    # Add conversation history (excluding system messages)
    for msg in session.get("messages", []):
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            messages.append(LLMMessage.user(content))
        elif role == "assistant":
            messages.append(LLMMessage.assistant(content))

    # Add current user message
    messages.append(LLMMessage.user(user_message))

    return messages, session


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatMessage,
    http_request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    Chat endpoint for ALİM with multi-turn conversation support.

    Accepts a message and returns an AI-generated response.
    Maintains conversation history in Redis for multi-turn interactions.
    Supports 100+ concurrent users with session isolation.
    """
    # Apply chat-specific rate limiting
    try:
        await check_rate_limit(http_request, chat_limiter)
    except Exception:
        # Rate limiter may fail if Redis is down - fail open for availability
        pass

    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    # Get the LLM provider
    llm = get_llm_provider()

    try:
        # Build messages with conversation history
        messages, session = await _build_messages_with_history(
            session_id=session_id,
            user_message=request.message,
            user_id=request.user_id,
        )

        # Generate response
        response = await llm.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )

        # Store messages in session history
        try:
            await SessionStorage.add_message(session_id, "user", request.message)
            await SessionStorage.add_message(session_id, "assistant", response.content)

            # Get updated message count
            updated_session = await SessionStorage.get(session_id)
            message_count = len(updated_session.get("messages", [])) if updated_session else 0
        except Exception:
            # Session storage failure shouldn't break the response
            message_count = 0

        return ChatResponse(
            response=response.content,
            session_id=session_id,
            model=response.model,
            tokens_used=response.tokens_used,
            intent=None,  # TODO: Add intent detection
            message_count=message_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM service unavailable: {str(e)}",
        ) from e


@router.post("/chat/stream")
async def chat_stream(
    request: ChatMessage,
    http_request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    Streaming chat endpoint for ALİM with multi-turn support.

    Returns a streaming response with incremental text chunks.
    Maintains conversation history in Redis.
    """
    # Apply chat-specific rate limiting
    try:
        await check_rate_limit(http_request, chat_limiter)
    except Exception:
        pass  # Fail open

    session_id = request.session_id or str(uuid.uuid4())
    llm = get_llm_provider()

    # Build messages with history
    try:
        messages, _ = await _build_messages_with_history(
            session_id=session_id,
            user_message=request.message,
            user_id=request.user_id,
        )
    except Exception:
        # Fallback to no history if Redis fails
        messages = [
            LLMMessage.system(SYSTEM_PROMPT_AZ),
            LLMMessage.user(request.message),
        ]

    async def generate():
        full_response = []
        try:
            async for chunk in llm.stream(
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            ):
                full_response.append(chunk)
                yield chunk

            # Store conversation in session after streaming completes
            try:
                await SessionStorage.add_message(session_id, "user", request.message)
                await SessionStorage.add_message(session_id, "assistant", "".join(full_response))
            except Exception:
                pass  # Don't fail stream for session storage issues

        except Exception as e:
            yield f"\n\n[Xəta: {str(e)}]"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={"X-Session-Id": session_id},
    )


@router.get("/status")
async def chat_status():
    """
    Chat service status endpoint.

    Returns the current status of the chat service and LLM health.
    """
    llm_health = await check_llm_health()

    # Check Redis health
    try:
        redis_healthy = await RedisClient.health_check()
    except Exception:
        redis_healthy = False

    return {
        "service": "chat",
        "status": "operational" if llm_health["healthy"] and redis_healthy else "degraded",
        "llm": llm_health,
        "redis": {"healthy": redis_healthy},
        "features": {
            "streaming": True,
            "context_memory": redis_healthy,  # Enabled when Redis is available
            "multi_turn": redis_healthy,
            "intent_detection": False,  # TODO: Enable with rules engine
        },
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get session history for a given session ID.

    Args:
        session_id: The session UUID.

    Returns:
        Session data including conversation history.
    """
    session = await SessionStorage.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "message_count": len(session.get("messages", [])),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at"),
        "messages": session.get("messages", []),
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its conversation history.

    Args:
        session_id: The session UUID.

    Returns:
        Deletion confirmation.
    """
    deleted = await SessionStorage.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "deleted", "session_id": session_id}


@router.get("/chat")
async def get_chat_info(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """Get chat endpoint information and usage instructions.

    This endpoint provides API discovery and documentation for external clients.
    Authenticated applications can use this to understand available methods,
    request/response formats, and current service configuration.

    Returns:
        API contract information including:
        - Available HTTP methods
        - Request/response schema examples
        - Current model configuration
        - Rate limit information
        - Documentation links
    """
    base_url = str(request.base_url).rstrip("/")

    return {
        "service": "ALİM-chat",
        "version": settings.app_version,
        "endpoint": "/api/v1/chat",
        "methods": {
            "GET": "Get API information (this endpoint)",
            "POST": "Send a chat message to the AI assistant",
        },
        "description": "ALİM - Azerbaijani farming assistant chat API",
        "request_schema": {
            "message": {
                "type": "string",
                "required": True,
                "min_length": 1,
                "max_length": 4000,
                "description": "User message in Azerbaijani",
            },
            "session_id": {
                "type": "string",
                "required": False,
                "description": "Session ID for conversation continuity. Auto-generated if not provided.",
            },
            "user_id": {
                "type": "string",
                "required": False,
                "description": "User identifier for multi-user tracking.",
            },
            "farm_id": {
                "type": "string",
                "required": False,
                "description": "Farm context for personalized advice.",
            },
            "language": {
                "type": "string",
                "required": False,
                "default": "az",
                "description": "Response language code.",
            },
            "stream": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Enable streaming response (use /chat/stream endpoint instead).",
            },
        },
        "response_schema": {
            "response": "string - AI assistant response",
            "session_id": "string - Session identifier",
            "model": "string - Model used for generation",
            "tokens_used": "integer - Token count",
            "message_count": "integer - Messages in session history",
        },
        "example": {
            "request": {
                "method": "POST",
                "url": f"{base_url}/api/v1/chat",
                "headers": {
                    "Content-Type": "application/json",
                },
                "body": {
                    "message": "Salam! Buğda əkini haqqında məlumat verə bilərsinizmi?",
                    "session_id": "optional-uuid",
                    "user_id": "farmer_123",
                    "stream": False,
                },
            },
            "response": {
                "response": "Salam! Buğda əkini üçün...",
                "session_id": "uuid-string",
                "model": settings.active_llm_model,
                "tokens_used": 150,
                "message_count": 2,
            },
        },
        "related_endpoints": {
            "chat_stream": {
                "path": "/api/v1/chat/stream",
                "method": "POST",
                "description": "Streaming chat with Server-Sent Events",
            },
            "session_get": {
                "path": "/api/v1/session/{session_id}",
                "method": "GET",
                "description": "Retrieve conversation history",
            },
            "session_delete": {
                "path": "/api/v1/session/{session_id}",
                "method": "DELETE",
                "description": "Delete session and history",
            },
            "status": {
                "path": "/api/v1/status",
                "method": "GET",
                "description": "Chat service health status",
            },
        },
        "model": {
            "provider": settings.llm_provider.value,
            "name": settings.active_llm_model,
            "capabilities": [
                "Azerbaijani language (native)",
                "Farm planning assistance",
                "Crop recommendations",
                "Weather analysis",
                "Pest management advice",
                "Multi-turn conversation",
            ],
        },
        "rate_limits": {
            "requests_per_minute": settings.rate_limit_requests_per_minute,
            "burst_limit": settings.rate_limit_burst,
            "note": "Per-client rate limiting based on IP address",
        },
        "documentation": {
            "swagger": f"{base_url}/docs",
            "redoc": f"{base_url}/redoc",
            "openapi": f"{base_url}/openapi.json",
        },
    }
