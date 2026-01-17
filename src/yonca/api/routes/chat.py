# src/yonca/api/routes/chat.py
"""Chat endpoints for Yonca AI."""

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model."""

    message: str
    session_id: str | None = None
    language: str = "az"


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    session_id: str
    intent: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """
    Chat endpoint for Yonca AI.
    
    Accepts a message and returns an AI-generated response.
    This is a placeholder - full implementation will come later.
    """
    # TODO: Implement full chat logic with LangGraph agent
    return ChatResponse(
        response="Salam! Mən Yonca AI-yəm. Bu endpoint hələ inkişaf mərhələsindədir.",
        session_id=request.session_id or "demo-session",
        intent="greeting",
    )


@router.get("/status")
async def chat_status():
    """
    Chat service status endpoint.
    
    Returns the current status of the chat service.
    """
    return {
        "service": "chat",
        "status": "operational",
        "features": {
            "streaming": False,  # TODO: Enable when implemented
            "context_memory": False,  # TODO: Enable when implemented
            "intent_detection": False,  # TODO: Enable when implemented
        },
    }
