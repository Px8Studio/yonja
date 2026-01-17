"""
Yonca AI - Digital Umbrella Prototype
=====================================

Streamlit-based "Personalized Farm Assistant" demonstration.
Mobile-first UI designed for Azerbaijani farmers.

Architecture:
    This module consumes the Sidecar Intelligence Engine for recommendations.
    Farm scenarios are loaded from the canonical yonca.data.scenarios module.
    
Modules:
- app: Main Streamlit application with UI adapters
- styles: Custom CSS for mobile-first WhatsApp-like UI
"""

__version__ = "0.2.0"

# Re-export UI components for convenience
from yonca.umbrella.app import (
    ScenarioProfile,
    SCENARIO_LABELS,
    SCENARIO_MAP,
    UIFarmProfile,
    adapt_farm_profile,
    generate_ui_recommendations,
)

__all__ = [
    "ScenarioProfile",
    "SCENARIO_LABELS",
    "SCENARIO_MAP",
    "UIFarmProfile",
    "adapt_farm_profile",
    "generate_ui_recommendations",
]
