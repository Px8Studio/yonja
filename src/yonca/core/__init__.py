"""
Yonca AI - Core Package

⚠️ DEPRECATION NOTICE ⚠️
========================
This entire module is DEPRECATED and scheduled for removal.

Migration Guide:
----------------
| Old (Deprecated)                    | New (Recommended)                           |
|-------------------------------------|---------------------------------------------|
| `core.engine.RecommendationEngine`  | `sidecar.SidecarRecommendationService`     |
| `core.engine.generate_daily_schedule`| `sidecar.generate_daily_schedule`          |
| `core.rules.ALL_RULES`              | `sidecar.rules_registry.AGRONOMY_RULES`    |
| `core.rules.get_rules_by_farm_type` | `sidecar.rules_registry.RulesRegistry`     |

All unique logic has been migrated to the sidecar architecture.
The RecommendationEngine is maintained ONLY for backwards compatibility.

See docs/CLEANUP_GUIDE.md for complete migration instructions.
"""
import warnings

warnings.warn(
    "yonca.core is deprecated. Use yonca.sidecar instead. "
    "See docs/CLEANUP_GUIDE.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

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
