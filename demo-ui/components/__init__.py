# demo-ui/components/__init__.py
"""UI components for the Chainlit demo."""

from components.farm_selector import create_farm_settings, handle_farm_change
from components.insights_dashboard import (
    add_response_metadata_element,
    create_activity_heatmap,
    format_daily_breakdown,
    format_dashboard_summary,
    format_response_metadata,
    format_welcome_stats,
    render_dashboard_sidebar,
    update_dashboard_with_day,
)
from components.spinners import (
    SPINNER_MESSAGES,
    LoadingStates,
    SpinnerType,
    clear_spinner,
    get_inline_spinner,
    get_progress_bar,
    get_spinner_html,
    get_step_indicator,
    show_spinner,
)

__all__ = [
    "create_farm_settings",
    "handle_farm_change",
    # Insights Dashboard
    "format_response_metadata",
    "add_response_metadata_element",
    "create_activity_heatmap",
    "format_dashboard_summary",
    "format_daily_breakdown",
    "render_dashboard_sidebar",
    "update_dashboard_with_day",
    "format_welcome_stats",
    # Spinners
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
