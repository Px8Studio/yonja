# src/ALİM/rules/engine.py
"""Agronomy rules engine.

Evaluates farming conditions against a library of rules
to provide validated, context-aware recommendations.
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# ============================================================
# Rule Data Types
# ============================================================


class RulePriority(str, Enum):
    """Priority level for rules."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleCategory(str, Enum):
    """Category of the rule."""

    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PEST_CONTROL = "pest_control"
    HARVEST = "harvest"
    PLANTING = "planting"
    WEATHER = "weather"
    SAFETY = "safety"


class Operator(str, Enum):
    """Comparison operators for conditions."""

    EQ = "eq"  # equals
    NE = "ne"  # not equals
    GT = "gt"  # greater than
    GTE = "gte"  # greater than or equal
    LT = "lt"  # less than
    LTE = "lte"  # less than or equal
    IN = "in"  # in list
    NOT_IN = "not_in"  # not in list
    CONTAINS = "contains"  # string contains
    BETWEEN = "between"  # between two values


@dataclass
class Condition:
    """A single condition in a rule."""

    field: str  # Field path (e.g., "weather.temperature_c")
    operator: Operator
    value: Any  # Expected value or [min, max] for between

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate this condition against context.

        Args:
            context: Flattened context dict

        Returns:
            True if condition is met
        """
        actual = self._get_field_value(context)

        if actual is None:
            return False

        try:
            if self.operator == Operator.EQ:
                return actual == self.value
            elif self.operator == Operator.NE:
                return actual != self.value
            elif self.operator == Operator.GT:
                return actual > self.value
            elif self.operator == Operator.GTE:
                return actual >= self.value
            elif self.operator == Operator.LT:
                return actual < self.value
            elif self.operator == Operator.LTE:
                return actual <= self.value
            elif self.operator == Operator.IN:
                return actual in self.value
            elif self.operator == Operator.NOT_IN:
                return actual not in self.value
            elif self.operator == Operator.CONTAINS:
                return self.value in str(actual)
            elif self.operator == Operator.BETWEEN:
                return self.value[0] <= actual <= self.value[1]
        except (TypeError, ValueError):
            return False

        return False

    def _get_field_value(self, context: dict[str, Any]) -> Any:
        """Get nested field value from context."""
        parts = self.field.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value


@dataclass
class Rule:
    """An agronomy rule."""

    id: str
    name: str
    category: RuleCategory
    description: str
    conditions: list[Condition]
    recommendation_az: str
    recommendation_en: str | None = None
    priority: RulePriority = RulePriority.MEDIUM
    confidence: float = 0.9
    metadata: dict[str, Any] | None = None

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate all conditions (AND logic).

        Args:
            context: Context dictionary with all data

        Returns:
            True if all conditions pass
        """
        return all(cond.evaluate(context) for cond in self.conditions)

    def to_match_dict(self) -> dict[str, Any]:
        """Convert to match dictionary for state."""
        return {
            "rule_id": self.id,
            "rule_name": self.name,
            "category": self.category.value,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "recommendation_az": self.recommendation_az,
            "recommendation_en": self.recommendation_en,
        }


# ============================================================
# Rule Loader
# ============================================================


class RuleLoader:
    """Loads rules from YAML files."""

    def __init__(self, rules_dir: Path | str | None = None):
        """Initialize the loader.

        Args:
            rules_dir: Directory containing rule YAML files
        """
        if rules_dir is None:
            rules_dir = Path(__file__).parent / "rules"

        self.rules_dir = Path(rules_dir)

    def load_all(self) -> list[Rule]:
        """Load all rules from the rules directory."""
        rules = []

        if not self.rules_dir.exists():
            return rules

        for yaml_file in self.rules_dir.glob("*.yaml"):
            rules.extend(self.load_file(yaml_file))

        for yml_file in self.rules_dir.glob("*.yml"):
            rules.extend(self.load_file(yml_file))

        return rules

    def load_file(self, filepath: Path) -> list[Rule]:
        """Load rules from a single YAML file."""
        try:
            with open(filepath, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "rules" not in data:
                return []

            return [self._parse_rule(r) for r in data["rules"]]

        except Exception as e:
            print(f"Error loading rules from {filepath}: {e}")
            return []

    def _parse_rule(self, data: dict) -> Rule:
        """Parse a rule from YAML data."""
        conditions = []
        for cond_data in data.get("conditions", []):
            conditions.append(
                Condition(
                    field=cond_data["field"],
                    operator=Operator(cond_data["operator"]),
                    value=cond_data.get("value") or cond_data.get("values"),
                )
            )

        recommendation = data.get("recommendation", {})

        return Rule(
            id=data["id"],
            name=data["name"],
            category=RuleCategory(data["category"]),
            description=data.get("description", ""),
            conditions=conditions,
            recommendation_az=recommendation.get("az", ""),
            recommendation_en=recommendation.get("en"),
            priority=RulePriority(data.get("priority", "medium")),
            confidence=data.get("confidence", 0.9),
            metadata=data.get("metadata"),
        )


# ============================================================
# Rules Engine
# ============================================================


class RulesEngine:
    """Agronomy rules engine.

    Evaluates context against a library of rules to provide
    validated, context-aware recommendations.

    Example:
        ```python
        engine = RulesEngine()

        context = {
            "weather": {"temperature_c": 35, "humidity_percent": 30},
            "farm": {"region": "aran"},
            "intent": "irrigation",
        }

        matches = engine.evaluate(context)
        for match in matches:
            print(f"{match['rule_name']}: {match['recommendation_az']}")
        ```
    """

    def __init__(self, rules_dir: Path | str | None = None):
        """Initialize the engine.

        Args:
            rules_dir: Directory containing rule YAML files
        """
        self.loader = RuleLoader(rules_dir)
        self._rules: list[Rule] = []
        self._loaded = False

    def load_rules(self) -> int:
        """Load rules from files.

        Returns:
            Number of rules loaded
        """
        self._rules = self.loader.load_all()
        self._loaded = True
        return len(self._rules)

    def add_rule(self, rule: Rule) -> None:
        """Add a rule programmatically.

        Args:
            rule: Rule to add
        """
        self._rules.append(rule)

    def evaluate(
        self,
        context: dict[str, Any],
        categories: list[RuleCategory] | None = None,
    ) -> list[dict[str, Any]]:
        """Evaluate context against all rules.

        Args:
            context: Context dictionary with farm, weather, intent, etc.
            categories: Optional filter for rule categories

        Returns:
            List of matched rule dictionaries
        """
        if not self._loaded:
            self.load_rules()

        matches = []

        for rule in self._rules:
            # Filter by category if specified
            if categories and rule.category not in categories:
                continue

            # Evaluate rule
            if rule.evaluate(context):
                matches.append(rule.to_match_dict())

        # Sort by priority (critical > high > medium > low)
        priority_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
        }
        matches.sort(key=lambda m: priority_order.get(m["priority"], 4))

        return matches

    def get_rules_for_intent(self, intent: str) -> list[Rule]:
        """Get rules relevant to a specific intent.

        Args:
            intent: Intent string (e.g., "irrigation")

        Returns:
            List of relevant rules
        """
        if not self._loaded:
            self.load_rules()

        try:
            category = RuleCategory(intent)
            return [r for r in self._rules if r.category == category]
        except ValueError:
            return []

    @property
    def rule_count(self) -> int:
        """Get the number of loaded rules."""
        return len(self._rules)


# ============================================================
# Context Builder
# ============================================================


def build_rule_context(
    weather: dict | None = None,
    farm: dict | None = None,
    user: dict | None = None,
    intent: str | None = None,
    current_date: date | None = None,
) -> dict[str, Any]:
    """Build a context dictionary for rule evaluation.

    Args:
        weather: Weather data (temperature, humidity, etc.)
        farm: Farm data (region, crops, etc.)
        user: User data (experience level, etc.)
        intent: User's intent
        current_date: Current date (for seasonal rules)

    Returns:
        Flattened context dictionary
    """
    context = {
        "weather": weather or {},
        "farm": farm or {},
        "user": user or {},
        "intent": intent,
        "date": {
            "month": (current_date or date.today()).month,
            "day": (current_date or date.today()).day,
            "year": (current_date or date.today()).year,
        },
    }

    return context


# ============================================================
# Singleton Instance
# ============================================================

_engine: RulesEngine | None = None


def get_rules_engine() -> RulesEngine:
    """Get the singleton rules engine."""
    global _engine
    if _engine is None:
        _engine = RulesEngine()
        _engine.load_rules()
    return _engine
