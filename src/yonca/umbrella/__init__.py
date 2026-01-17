"""
Yonca AI - Digital Umbrella Prototype
=====================================

Streamlit-based "Personalized Farm Assistant" demonstration.
Mobile-first UI designed for Azerbaijani farmers.

Architecture:
    This module consumes the Sidecar Intelligence Engine for recommendations.
    Farm scenarios are loaded from the canonical yonca.data.scenarios module.
    
Modules:
- app: Main Streamlit application (run with `streamlit run`)
- core: Core data definitions (ScenarioProfile, UIFarmProfile, etc.)
- styles: Custom CSS for mobile-first WhatsApp-like UI

Note: The core module contains importable definitions without Streamlit side effects.
      Import from core.py to avoid triggering Streamlit execution.
"""

__version__ = "0.2.0"

# Re-export UI components from core module (no Streamlit side effects)
from yonca.umbrella.core import (
    ScenarioProfile,
    SCENARIO_LABELS,
    SCENARIO_MAP,
    UIFarmProfile,
    UIWeatherData,
    UISoilData,
    UICropInfo,
    UILivestockInfo,
    adapt_farm_profile,
)

__all__ = [
    "ScenarioProfile",
    "SCENARIO_LABELS",
    "SCENARIO_MAP",
    "UIFarmProfile",
    "UIWeatherData",
    "UISoilData",
    "UICropInfo",
    "UILivestockInfo",
    "adapt_farm_profile",
]
