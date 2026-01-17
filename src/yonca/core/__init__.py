"""
Yonca AI - Core Package

DEPRECATION NOTICE:
==================
This module is being phased out in favor of the Sidecar architecture.

- For rules: Use yonca.sidecar.rules_registry
- For recommendations: Use yonca.sidecar.recommendation_service

The RecommendationEngine here is maintained for backwards compatibility
with the LangGraph agent (yonca.agent) and API layer.
"""
from yonca.core.engine import RecommendationEngine, recommendation_engine
from yonca.core.rules import (
    Rule, ALL_RULES, get_rules_by_category, get_rules_by_farm_type
)

__all__ = [
    "RecommendationEngine",
    "recommendation_engine",
    "Rule",
    "ALL_RULES",
    "get_rules_by_category",
    "get_rules_by_farm_type",
]
