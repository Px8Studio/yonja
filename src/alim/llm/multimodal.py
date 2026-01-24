# src/ALİM/llm/multimodal.py
"""Multimodal message handling for images in LangGraph.

Converts image file paths to proper LangChain message content.
"""

import base64
from pathlib import Path


def image_path_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_media_type(image_path: str) -> str:
    """Get MIME type from file extension."""
    ext = Path(image_path).suffix.lower()
    types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return types.get(ext, "image/jpeg")


def create_multimodal_message(text: str, image_paths: list[str] | None = None):
    """Create a LangChain HumanMessage with text + images.

    Args:
        text: The text portion
        image_paths: List of local image file paths

    Returns:
        HumanMessage with content as list of dicts (text + images)
    """
    from langchain_core.messages import HumanMessage

    if not image_paths:
        return HumanMessage(content=text)

    # Build multimodal content
    content = [{"type": "text", "text": text}]

    for img_path in image_paths:
        try:
            b64 = image_path_to_base64(img_path)
            media_type = get_image_media_type(img_path)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{b64}"},
                }
            )
        except Exception:
            pass  # Skip broken image paths

    return HumanMessage(content=content)
