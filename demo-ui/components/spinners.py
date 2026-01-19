# demo-ui/components/spinners.py
"""ALEM-branded loading indicators and spinners.

Provides reusable, visually consistent loading states that match
the agricultural theme and ALEM branding.
"""

from typing import Literal

# ============================================
# SPINNER CONFIGURATIONS
# ============================================
# All spinners use the 🌿 clover emoji as the core ALEM brand element

SpinnerType = Literal[
    "thinking",      # Agent is processing/reasoning
    "loading",       # Data is being loaded
    "searching",     # Searching through data/documents
    "transcribing",  # Audio to text conversion
    "analyzing",     # Analyzing farm data
    "generating",    # Generating recommendations
]


# ============================================
# SPINNER TEXT (Azerbaijani)
# ============================================

SPINNER_MESSAGES: dict[SpinnerType, str] = {
    "thinking": "🌿 Düşünürəm...",
    "loading": "🌿 Yüklənir...",
    "searching": "🌿 Axtarıram...",
    "transcribing": "🌿 Səsinizi eşidirəm...",
    "analyzing": "🌿 Təhlil edirəm...",
    "generating": "🌿 Tövsiyələr hazırlayıram...",
}


# ============================================
# HTML SPINNERS (Advanced)
# ============================================
# These use custom CSS animations for richer visual feedback

def get_spinner_html(spinner_type: SpinnerType, message: str | None = None) -> str:
    """Get HTML for animated spinner with ALEM branding.
    
    Args:
        spinner_type: Type of operation being performed
        message: Custom message (defaults to SPINNER_MESSAGES)
        
    Returns:
        HTML string with animated spinner
        
    Example:
        >>> spinner_html = get_spinner_html("thinking")
        >>> await cl.Message(content=spinner_html).send()
    """
    display_message = message or SPINNER_MESSAGES[spinner_type]
    
    # Use CSS animation defined in custom.css
    return f"""
<div class="alem-spinner">
    <div class="spinner-icon">🌿</div>
    <div class="spinner-text">{display_message}</div>
</div>
"""


def get_inline_spinner(spinner_type: SpinnerType) -> str:
    """Get simple inline spinner (emoji + text).
    
    Use this for quick loading states that don't need animation.
    
    Args:
        spinner_type: Type of operation
        
    Returns:
        Simple text string with emoji
        
    Example:
        >>> await response_msg.stream_token(get_inline_spinner("thinking"))
    """
    return SPINNER_MESSAGES[spinner_type]


# ============================================
# PROGRESS INDICATORS
# ============================================

def get_progress_bar(percentage: int, label: str = "İrəliləyiş") -> str:
    """Get HTML progress bar with ALEM styling.
    
    Args:
        percentage: Progress (0-100)
        label: Label text
        
    Returns:
        HTML progress bar
        
    Example:
        >>> progress_html = get_progress_bar(45, "Model yüklənir")
        >>> await cl.Message(content=progress_html).send()
    """
    percentage = max(0, min(100, percentage))  # Clamp to 0-100
    
    return f"""
<div class="alem-progress">
    <div class="progress-label">{label}</div>
    <div class="progress-bar-container">
        <div class="progress-bar-fill" style="width: {percentage}%"></div>
    </div>
    <div class="progress-percentage">{percentage}%</div>
</div>
"""


# ============================================
# MULTI-STEP INDICATORS
# ============================================

def get_step_indicator(
    current_step: int,
    total_steps: int,
    step_name: str,
) -> str:
    """Get step indicator for multi-stage operations.
    
    Args:
        current_step: Current step (1-indexed)
        total_steps: Total number of steps
        step_name: Name of current step
        
    Returns:
        HTML step indicator
        
    Example:
        >>> step_html = get_step_indicator(2, 4, "Torpaq təhlili")
        >>> await cl.Message(content=step_html).send()
    """
    percentage = int((current_step / total_steps) * 100)
    
    return f"""
<div class="alem-step-indicator">
    <div class="step-header">
        <span class="step-number">Addım {current_step}/{total_steps}</span>
        <span class="step-percentage">{percentage}%</span>
    </div>
    <div class="step-name">🌿 {step_name}</div>
    <div class="step-progress">
        <div class="step-progress-fill" style="width: {percentage}%"></div>
    </div>
</div>
"""


# ============================================
# LOADING STATES (Common Patterns)
# ============================================

class LoadingStates:
    """Pre-configured loading states for common operations."""
    
    @staticmethod
    def thinking() -> str:
        """Agent is thinking/reasoning."""
        return get_inline_spinner("thinking")
    
    @staticmethod
    def loading_data() -> str:
        """Loading farm data."""
        return get_inline_spinner("loading")
    
    @staticmethod
    def searching_knowledge() -> str:
        """Searching knowledge base."""
        return get_inline_spinner("searching")
    
    @staticmethod
    def transcribing_audio() -> str:
        """Converting speech to text."""
        return get_inline_spinner("transcribing")
    
    @staticmethod
    def analyzing_farm() -> str:
        """Analyzing farm conditions."""
        return get_inline_spinner("analyzing")
    
    @staticmethod
    def generating_advice() -> str:
        """Generating recommendations."""
        return get_inline_spinner("generating")


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

async def show_spinner(message_obj, spinner_type: SpinnerType) -> None:
    """Update message with spinner.
    
    Args:
        message_obj: Chainlit Message object
        spinner_type: Type of spinner to show
        
    Example:
        >>> msg = cl.Message(content="")
        >>> await msg.send()
        >>> await show_spinner(msg, "thinking")
    """
    message_obj.content = get_inline_spinner(spinner_type)
    await message_obj.update()


async def clear_spinner(message_obj, final_content: str) -> None:
    """Replace spinner with final content.
    
    Args:
        message_obj: Chainlit Message object
        final_content: Final message content
        
    Example:
        >>> await clear_spinner(msg, "Analysis complete!")
    """
    message_obj.content = final_content
    await message_obj.update()


# ============================================
# EXPORTS
# ============================================

__all__ = [
    "SpinnerType",
    "SPINNER_MESSAGES",
    "get_spinner_html",
    "get_inline_spinner",
    "get_progress_bar",
    "get_step_indicator",
    "LoadingStates",
    "show_spinner",
    "clear_spinner",
]
