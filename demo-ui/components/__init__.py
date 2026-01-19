# demo-ui/components/__init__.py
"""UI components for the Chainlit demo."""

from components.farm_selector import create_farm_settings, handle_farm_change
from components.insights_dashboard import (
    format_response_metadata,
    add_response_metadata_element,
    create_activity_heatmap,
    format_dashboard_summary,
    format_daily_breakdown,
    render_dashboard_sidebar,
    update_dashboard_with_day,
    format_welcome_stats,
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
]
