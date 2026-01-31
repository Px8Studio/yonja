# demo-ui/services/__init__.py
"""Services for the Chainlit demo UI.

Service modules:
- lifecycle: Chat start/resume handlers
- welcome: Dashboard welcome message
- audio: Audio input + Whisper transcription
- actions: Action button callbacks
- expertise: Persona expertise detection
- model_resolver: LLM model resolution
- session_manager: Session state persistence
- thread_utils: Thread metadata utilities
- mcp_connector: MCP server integration
- mcp_resilience: MCP retry/fallback logic
"""

from services.actions import (
    handle_cancel_action,
    handle_confirm_action,
    handle_consent_deny,
    handle_consent_grant,
    handle_feedback_negative,
    handle_feedback_positive,
    handle_switch_to_agent_mode,
    prompt_agent_mode,
    show_data_consent_prompt,
)
from services.alim_client import AlimClient
from services.audio import (
    handle_audio_chunk,
    handle_audio_end,
    handle_audio_start,
    transcribe_audio_whisper,
)
from services.lifecycle import (
    handle_chat_resume,
    handle_chat_start,
    handle_shared_thread_view,
)
from services.mock_data import MockDataService, get_demo_farms
from services.welcome import send_dashboard_welcome

__all__ = [
    # Legacy exports
    "MockDataService",
    "AlimClient",
    "get_demo_farms",
    # Lifecycle
    "handle_chat_start",
    "handle_chat_resume",
    "handle_shared_thread_view",
    # Welcome
    "send_dashboard_welcome",
    # Audio
    "handle_audio_start",
    "handle_audio_chunk",
    "handle_audio_end",
    "transcribe_audio_whisper",
    # Actions
    "handle_confirm_action",
    "handle_cancel_action",
    "handle_feedback_positive",
    "handle_feedback_negative",
    "handle_consent_grant",
    "handle_consent_deny",
    "handle_switch_to_agent_mode",
    "show_data_consent_prompt",
    "prompt_agent_mode",
]
