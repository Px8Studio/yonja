# demo-ui/services/audio.py
"""Audio input handlers for voice-enabled farming assistant.

Farmers in the field can speak questions instead of typing.
Uses browser's MediaRecorder to capture audio, then transcribes via Whisper.
"""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

import httpx

from services.logger import get_logger

if TYPE_CHECKING:
    pass

# Initialize logger
logger = get_logger(__name__)


async def transcribe_audio_whisper(audio_data: bytes, mime_type: str) -> str:
    """Transcribe audio using Whisper model.

    Options:
    1. Local Whisper via Ollama (if model available)
    2. OpenAI Whisper API (requires API key)
    3. Azure Speech Services (requires Azure subscription)

    For now, we use a simple approach with httpx to Ollama or fallback.

    Args:
        audio_data: Raw audio bytes
        mime_type: MIME type (e.g., "audio/webm", "audio/wav")

    Returns:
        Transcribed text string
    """
    # Save audio to temp file (Whisper needs file input)
    ext = ".webm" if "webm" in mime_type else ".wav"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(audio_data)
        temp_path = f.name

    try:
        # Try OpenAI-compatible Whisper endpoint (works with local or cloud)
        whisper_url = os.getenv("WHISPER_API_URL", "http://localhost:11434/v1/audio/transcriptions")
        whisper_key = os.getenv("WHISPER_API_KEY", "")

        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(temp_path, "rb") as audio_file:
                files = {"file": (f"audio{ext}", audio_file, mime_type)}
                data = {"model": "whisper", "language": "az"}  # Azerbaijani
                headers = {}
                if whisper_key:
                    headers["Authorization"] = f"Bearer {whisper_key}"

                response = await client.post(whisper_url, files=files, data=data, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "")
                else:
                    logger.warning(
                        "whisper_api_error",
                        status=response.status_code,
                        detail=response.text[:200],
                    )

        # Fallback: Return placeholder if no Whisper available
        logger.warning("whisper_not_available", detail="No Whisper service configured")
        return ""

    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


async def handle_audio_start() -> bool:
    """Handle audio recording start.

    Returns:
        True to allow recording, False to reject.
    """
    logger.info("audio_recording_started")
    return True


async def handle_audio_chunk(chunk_data: bytes) -> None:
    """Process incoming audio chunks.

    For real-time transcription, we could accumulate chunks here.
    Currently we wait for the full recording (on_audio_end).

    Args:
        chunk_data: Raw audio chunk bytes
    """
    # Buffer chunks if needed for streaming transcription
    # For now, we do nothing - wait for complete audio in on_audio_end
    _ = chunk_data  # Mark as intentionally unused


async def handle_audio_end(
    audio_data: bytes,
    mime_type: str,
    on_message_fn: callable,
) -> tuple[str | None, str | None]:
    """Handle audio recording end. Transcribe and return.

    Args:
        audio_data: Complete audio recording bytes
        mime_type: MIME type of audio
        on_message_fn: Function to call with transcribed message

    Returns:
        Tuple of (transcription, error_message)
    """
    if not audio_data:
        logger.warning("audio_end_no_data")
        return None, "❌ Audio data is empty."

    logger.info(
        "audio_transcription_started",
        size_bytes=len(audio_data),
        mime_type=mime_type,
    )

    try:
        transcription = await transcribe_audio_whisper(audio_data, mime_type)

        if transcription and transcription.strip():
            logger.info("audio_transcribed", text=transcription[:100])
            return transcription, None
        else:
            logger.warning("audio_transcription_empty")
            return None, "❌ Səs aydın deyildi. Zəhmət olmasa yenidən cəhd edin."

    except Exception as e:
        logger.error("audio_transcription_error", error=str(e))
        return None, f"❌ Xəta: {str(e)}"
