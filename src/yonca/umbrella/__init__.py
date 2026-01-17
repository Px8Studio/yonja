"""
Yonca AI - Digital Umbrella Prototype
=====================================

Modern Streamlit-based "Personalized Farm Assistant" for Azerbaijani farmers.
Mobile-first UI with Yonca brand colors.

Architecture:
    - app.py: Main Streamlit application entry point
    - core.py: Data models, farm adapters, and business logic
    - styles.py: Custom CSS styling system

Usage:
    streamlit run src/yonca/umbrella/app.py

Note: Import from core.py to avoid triggering Streamlit execution.
"""

__version__ = "0.3.0"

# Re-export UI components from core module (no Streamlit side effects)
from yonca.umbrella.core import (
    # Scenario management
    ScenarioProfile,
    SCENARIO_LABELS,
    SCENARIO_MAP,
    # UI data models
    UIFarmProfile,
    UIWeatherData,
    UISoilData,
    UICropData,
    UILivestockData,
    # Functions
    load_farm_for_scenario,
    generate_recommendations,
    generate_chat_response,
)

from yonca.umbrella.styles import (
    COLORS,
    apply_custom_styles,
)

__all__ = [
    # Scenarios
    "ScenarioProfile",
    "SCENARIO_LABELS",
    "SCENARIO_MAP",
    # Data models
    "UIFarmProfile",
    "UIWeatherData",
    "UISoilData",
    "UICropData",
    "UILivestockData",
    # Functions
    "load_farm_for_scenario",
    "generate_recommendations",
    "generate_chat_response",
    # Styles
    "COLORS",
    "apply_custom_styles",
]
