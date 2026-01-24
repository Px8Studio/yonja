import chainlit as cl
from config import settings as demo_settings
from constants import LLM_MODEL_PROFILES

from yonca.config import AgentMode
from yonca.config import settings as yonca_settings


def resolve_active_model() -> dict:
    """Return a single source of truth for the active model metadata.

    Checks for model selection from:
    1. Chat Profile (header dropdown - now used for LLM selection)
    2. Chat Settings (sidebar settings panel)
    3. Default from config
    """
    integration_mode = demo_settings.integration_mode.lower()
    provider = demo_settings.llm_provider.lower()

    if integration_mode == "api":
        return {
            "provider": "yonca-api",
            "model": "server_default",
            "location": "cloud",
            "integration_mode": "api",
            "source": "fastapi",
        }

    # Get mode from chat profile (header dropdown) or settings
    selected_mode = None
    try:
        # Chat Profile is now the Agent Mode (e.g., "fast", "thinking", "agent")
        chat_profile = cl.user_session.get("chat_profile")
        if chat_profile and chat_profile in LLM_MODEL_PROFILES:
            selected_mode = chat_profile

        # Fallback to settings panel selection
        if not selected_mode:
            settings = cl.user_session.get("chat_settings") or {}
            selected_mode = settings.get("llm_model") if isinstance(settings, dict) else None
    except Exception:
        pass  # Session not available yet

    # Resolve mode to backend model
    try:
        if selected_mode:
            # If it's a known mode, get the mapped model
            mode = AgentMode(selected_mode)
            model = yonca_settings.get_model_for_mode(mode)
        else:
            # Default to Fast mode
            model = yonca_settings.get_model_for_mode(AgentMode.FAST)
    except Exception:
        # Fallback for safety
        model = yonca_settings.get_model_for_mode(AgentMode.FAST)

    location = "local" if provider == "ollama" else "cloud"
    base_url = (
        demo_settings.ollama_base_url if provider == "ollama" else "https://api.groq.com/openai/v1"
    )

    return {
        "provider": provider,
        "model": model,
        "mode": selected_mode or AgentMode.FAST.value,
        "location": location,
        "integration_mode": integration_mode,
        "source": "langgraph",
        "base_url": base_url,
    }
