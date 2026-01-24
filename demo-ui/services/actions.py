# demo-ui/services/actions.py
"""Action callback handlers for Chainlit UI actions.

Handles button clicks for:
- Confirm/cancel actions
- Feedback (👍/👎)
- Data consent prompts
- Agent mode switching
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import chainlit as cl
from constants import AgentMode

from services.logger import get_logger
from services.thread_utils import update_thread_presentation

if TYPE_CHECKING:
    pass

# Initialize logger
logger = get_logger(__name__)


# ============================================
# CONFIRM/CANCEL ACTIONS
# ============================================


async def handle_confirm_action(action_value: str) -> str:
    """Handle confirm action button clicks.

    Args:
        action_value: Value from the action payload

    Returns:
        Message to display
    """
    return f"✅ Action confirmed: {action_value}"


async def handle_cancel_action() -> str:
    """Handle cancel action button clicks.

    Returns:
        Message to display
    """
    return "❌ Action cancelled"


# ============================================
# FEEDBACK ACTIONS
# ============================================


async def handle_feedback_positive() -> str:
    """Handle positive feedback.

    Returns:
        Message to display
    """
    return "👍 Təşəkkürlər! Rəyiniz qeydə alındı."


async def handle_feedback_negative() -> str:
    """Handle negative feedback.

    Returns:
        Message to display
    """
    return "👎 Rəyiniz qeydə alındı. Təkmilləşdirəcəyik."


# ============================================
# DATA CONSENT FLOW
# ============================================


async def show_data_consent_prompt() -> None:
    """Display consent prompt asking user permission for external data access.

    This implements GDPR/privacy-friendly data access patterns.
    When user grants consent, weather APIs and other external services
    can be called to enhance responses.
    """
    consent_msg = """🔒 **Xarici Məlumat İcazəsi**

Daha dəqiq məlumat üçün xarici xidmətlərdən (hava proqnozu, subsidiya bazası) istifadə edə bilərəm.

Xarici serverlərlə əlaqə qurmağıma icazə verirsinizmi?

> _İcazə verməsəniz, yalnız yerli məlumatlardan istifadə edəcəyəm._"""

    actions = [
        cl.Action(
            name="consent_grant",
            payload={"consent": True},
            label="✓ İcazə verirəm",
        ),
        cl.Action(
            name="consent_deny",
            payload={"consent": False},
            label="✗ İcazə vermirəm",
        ),
    ]

    await cl.Message(
        content=consent_msg,
        author="ALİM",
        actions=actions,
    ).send()


async def handle_consent_grant() -> str:
    """Handle consent grant.

    Returns:
        Message to display
    """
    cl.user_session.set("data_consent_given", True)
    logger.info("data_consent_granted", user_id=cl.user_session.get("user_id"))
    return "✓ **Təşəkkürlər!** Xarici xidmətlərdən istifadə edə bilərəm. Hava proqnozu və digər məlumatlar əldə olunacaq."


async def handle_consent_deny() -> str:
    """Handle consent denial.

    Returns:
        Message to display
    """
    cl.user_session.set("data_consent_given", False)
    logger.info("data_consent_denied", user_id=cl.user_session.get("user_id"))
    return "✓ **Anlaşıldı.** Yalnız yerli məlumatlardan istifadə edəcəyəm. İstədiyiniz zaman parametrlərdən dəyişə bilərsiniz."


# ============================================
# AGENT MODE SWITCH
# ============================================


async def handle_switch_to_agent_mode() -> str:
    """Enable Agent mode (tools/connectors) after user confirmation.

    Returns:
        Message to display
    """
    cl.user_session.set("chat_profile", AgentMode.AGENT.value)

    # Persist profile change to thread metadata
    thread_id = cl.user_session.get("thread_id")
    if thread_id:
        await update_thread_presentation(
            metadata_updates={"chat_profile": AgentMode.AGENT.value},
        )
        logger.info(
            "chat_profile_switched",
            thread_id=thread_id,
            new_profile=AgentMode.AGENT.value,
            trigger="user_action",
        )

    return "✅ Agent mode enabled. Tools/connectors are now available. Re-run your request."


async def prompt_agent_mode(reason: str, auto_switch: bool = False) -> None:
    """Ask user to enable Agent mode before using tools/connectors.

    Args:
        reason: Why Agent mode is needed
        auto_switch: If True, automatically switches without asking
    """
    if auto_switch:
        # Auto-switch to Agent mode and persist
        cl.user_session.set("chat_profile", AgentMode.AGENT.value)
        thread_id = cl.user_session.get("thread_id")
        if thread_id:
            await update_thread_presentation(
                metadata_updates={"chat_profile": AgentMode.AGENT.value},
            )
            logger.info(
                "chat_profile_auto_switched",
                thread_id=thread_id,
                new_profile=AgentMode.AGENT.value,
                reason=reason,
            )

        await cl.Message(
            content=f"🤖 Automatically switched to Agent mode to {reason}.",
            author="System",
        ).send()
        return

    # Prompt user to switch
    actions = [
        cl.Action(
            name="switch_to_agent_mode",
            label="Enable Agent Mode",
            value="agent",
            description="Turn on tools & connectors",
        )
    ]

    await cl.Message(
        content=f"🔒 Agent mode required to {reason}. Enable Agent mode?",
        author="System",
        actions=actions,
    ).send()
