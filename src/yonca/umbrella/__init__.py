"""
Yonca AI - Digital Umbrella Prototype
=====================================

Streamlit-based "Personalized Farm Assistant" demonstration.
Mobile-first UI designed for Azerbaijani farmers.

Modules:
- scenario_manager: Synthetic dataset management with 5 farm profiles
- mock_backend: FastAPI-structured mock API for sidecar architecture
- agronomy_rules: Deterministic logic guard for LLM recommendations
- styles: Custom CSS for mobile-first WhatsApp-like UI
"""

__version__ = "0.1.0"

from yonca.umbrella.scenario_manager import ScenarioManager, ScenarioProfile
from yonca.umbrella.mock_backend import (
    MockBackend, 
    RecommendationPayload,
    FarmProfileRequest,
    RecommendationItem,
)
from yonca.umbrella.agronomy_rules import AgronomyLogicGuard

__all__ = [
    "ScenarioManager",
    "ScenarioProfile", 
    "MockBackend",
    "RecommendationPayload",
    "FarmProfileRequest",
    "RecommendationItem",
    "AgronomyLogicGuard",
]
