# src/ALİM/rules/__init__.py
"""Rules module - YAML-based agronomy rules engine.

Provides a configurable rules engine for validating farming
recommendations against established agronomic best practices.

Example:
    ```python
    from alim.rules import get_rules_engine, build_rule_context

    engine = get_rules_engine()

    context = build_rule_context(
        weather={"temperature_c": 35, "humidity_percent": 30},
        farm={"region": "aran"},
        intent="irrigation",
    )

    matches = engine.evaluate(context)
    for match in matches:
        print(f"{match['rule_name']}: {match['recommendation_az']}")
    ```
"""

from alim.rules.engine import (
    Condition,
    Operator,
    Rule,
    RuleCategory,
    RuleLoader,
    RulePriority,
    RulesEngine,
    build_rule_context,
    get_rules_engine,
)

__all__ = [
    # Engine
    "RulesEngine",
    "get_rules_engine",
    # Models
    "Rule",
    "Condition",
    "Operator",
    "RuleCategory",
    "RulePriority",
    # Loader
    "RuleLoader",
    # Helpers
    "build_rule_context",
]
