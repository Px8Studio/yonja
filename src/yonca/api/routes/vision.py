"""FastAPI endpoints for image upload and vision analysis."""

import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from yonca.agent.graph import get_agent
from yonca.llm.multimodal import create_multimodal_message
from yonca.observability.langfuse import create_langfuse_handler

router = APIRouter(prefix="/api/vision", tags=["vision"])


@router.post("/analyze")
async def analyze_image(
    files: list[UploadFile] = File(...),
    message: str = "",
    user_id: str | None = None,
    thread_id: str | None = None,
):
    """Analyze uploaded images and return action plan.

    Args:
        files: Uploaded image files
        message: User message/context
        user_id: User identifier
        thread_id: Conversation thread

    Returns:
        Vision analysis response
    """
    saved_paths = []

    try:
        # Save uploaded files to temp directory
        for file in files:
            if not file.content_type.startswith("image/"):
                raise HTTPException(400, "Only images allowed")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                content = await file.read()
                tmp.write(content)
                saved_paths.append(tmp.name)

        # Create multimodal message
        combined_text = (
            f"{message}\n\n(Image attachment: {len(saved_paths)} şəkil əlavə olundu)"
            if message
            else f"{len(saved_paths)} şəkil əlavə olundu"
        )
        human_msg = create_multimodal_message(combined_text, saved_paths)

        # Get agent and run
        agent = await get_agent()

        _langfuse_handler = create_langfuse_handler(
            session_id=thread_id,
            user_id=user_id,
            tags=["vision", "image_upload"],
            metadata={"image_count": len(saved_paths)},
        )

        # Prepare input state
        _input_state = {
            "messages": [human_msg],
            "current_input": combined_text,
            "thread_id": thread_id or "vision_" + os.urandom(8).hex(),
            "user_id": user_id,
        }

        result = await agent.chat(
            message=combined_text,
            thread_id=thread_id,
            user_id=user_id,
        )

        return JSONResponse(
            {
                "status": "ok",
                "response": result.content,
                "thread_id": result.thread_id,
            }
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        # Clean up temp files
        for path in saved_paths:
            try:
                os.remove(path)
            except Exception:
                pass
