# tests/unit/test_rules_engine.py
"""Unit tests for the agronomy rules engine."""

from datetime import date

import pytest
from yonca.rules.engine import (
    Condition,
    Operator,
    Rule,
    RuleCategory,
    RuleLoader,
    RulePriority,
    build_rule_context,
    get_rules_engine,
)


class TestCondition:
    """Tests for Condition class."""

    def test_eq_operator(self):
        """Test equals operator."""
        cond = Condition(field="weather.temperature_c", operator=Operator.EQ, value=25)

        assert cond.evaluate({"weather": {"temperature_c": 25}}) is True
        assert cond.evaluate({"weather": {"temperature_c": 30}}) is False

    def test_ne_operator(self):
        """Test not equals operator."""
        cond = Condition(field="intent", operator=Operator.NE, value="greeting")

        assert cond.evaluate({"intent": "irrigation"}) is True
        assert cond.evaluate({"intent": "greeting"}) is False

    def test_gt_operator(self):
        """Test greater than operator."""
        cond = Condition(field="weather.temperature_c", operator=Operator.GT, value=30)

        assert cond.evaluate({"weather": {"temperature_c": 35}}) is True
        assert cond.evaluate({"weather": {"temperature_c": 30}}) is False
        assert cond.evaluate({"weather": {"temperature_c": 25}}) is False

    def test_gte_operator(self):
        """Test greater than or equal operator."""
        cond = Condition(field="weather.temperature_c", operator=Operator.GTE, value=30)

        assert cond.evaluate({"weather": {"temperature_c": 35}}) is True
        assert cond.evaluate({"weather": {"temperature_c": 30}}) is True
        assert cond.evaluate({"weather": {"temperature_c": 25}}) is False

    def test_lt_operator(self):
        """Test less than operator."""
        cond = Condition(field="weather.humidity_percent", operator=Operator.LT, value=40)

        assert cond.evaluate({"weather": {"humidity_percent": 30}}) is True
        assert cond.evaluate({"weather": {"humidity_percent": 40}}) is False

    def test_lte_operator(self):
        """Test less than or equal operator."""
        cond = Condition(field="weather.humidity_percent", operator=Operator.LTE, value=40)

        assert cond.evaluate({"weather": {"humidity_percent": 30}}) is True
        assert cond.evaluate({"weather": {"humidity_percent": 40}}) is True
        assert cond.evaluate({"weather": {"humidity_percent": 50}}) is False

    def test_in_operator(self):
        """Test in operator."""
        cond = Condition(field="farm.region", operator=Operator.IN, value=["aran", "lankaran"])

        assert cond.evaluate({"farm": {"region": "aran"}}) is True
        assert cond.evaluate({"farm": {"region": "shaki_zagatala"}}) is False

    def test_not_in_operator(self):
        """Test not in operator."""
        cond = Condition(field="farm.region", operator=Operator.NOT_IN, value=["aran"])

        assert cond.evaluate({"farm": {"region": "lankaran"}}) is True
        assert cond.evaluate({"farm": {"region": "aran"}}) is False

    def test_between_operator(self):
        """Test between operator."""
        cond = Condition(field="weather.temperature_c", operator=Operator.BETWEEN, value=[15, 25])

        assert cond.evaluate({"weather": {"temperature_c": 20}}) is True
        assert cond.evaluate({"weather": {"temperature_c": 15}}) is True
        assert cond.evaluate({"weather": {"temperature_c": 25}}) is True
        assert cond.evaluate({"weather": {"temperature_c": 30}}) is False

    def test_contains_operator(self):
        """Test contains operator."""
        cond = Condition(field="user.input", operator=Operator.CONTAINS, value="suvarma")

        assert cond.evaluate({"user": {"input": "suvarma haqqında sual"}}) is True
        assert cond.evaluate({"user": {"input": "Gübrə haqqında"}}) is False

    def test_missing_field(self):
        """Test condition with missing field returns False."""
        cond = Condition(field="weather.temperature_c", operator=Operator.GT, value=30)

        assert cond.evaluate({}) is False
        assert cond.evaluate({"weather": {}}) is False

    def test_nested_field(self):
        """Test deeply nested field access."""
        cond = Condition(field="farm.parcel.soil.type", operator=Operator.EQ, value="chernozem")

        context = {"farm": {"parcel": {"soil": {"type": "chernozem"}}}}
        assert cond.evaluate(context) is True


class TestRule:
    """Tests for Rule class."""

    @pytest.fixture
    def sample_rule(self):
        """Create a sample rule for testing."""
        return Rule(
            id="TEST_001",
            name="Test Rule",
            category=RuleCategory.IRRIGATION,
            description="Test rule for unit testing",
            conditions=[
                Condition(field="weather.temperature_c", operator=Operator.GTE, value=30),
                Condition(field="weather.humidity_percent", operator=Operator.LTE, value=40),
            ],
            recommendation_az="Suvarma tövsiyə olunur",
            recommendation_en="Irrigation recommended",
            priority=RulePriority.HIGH,
            confidence=0.9,
        )

    def test_rule_creation(self, sample_rule):
        """Test rule is created correctly."""
        assert sample_rule.id == "TEST_001"
        assert sample_rule.name == "Test Rule"
        assert sample_rule.category == RuleCategory.IRRIGATION
        assert len(sample_rule.conditions) == 2

    def test_rule_evaluates_all_conditions(self, sample_rule):
        """Test rule requires all conditions to pass."""
        # Both conditions met
        assert (
            sample_rule.evaluate({"weather": {"temperature_c": 35, "humidity_percent": 30}}) is True
        )

        # Only first condition met
        assert (
            sample_rule.evaluate({"weather": {"temperature_c": 35, "humidity_percent": 60}})
            is False
        )

        # Only second condition met
        assert (
            sample_rule.evaluate({"weather": {"temperature_c": 25, "humidity_percent": 30}})
            is False
        )

        # Neither condition met
        assert (
            sample_rule.evaluate({"weather": {"temperature_c": 25, "humidity_percent": 60}})
            is False
        )

    def test_to_match_dict(self, sample_rule):
        """Test converting rule to match dictionary."""
        match = sample_rule.to_match_dict()

        assert match["rule_id"] == "TEST_001"
        assert match["rule_name"] == "Test Rule"
        assert match["category"] == "irrigation"
        assert match["priority"] == "high"
        assert match["confidence"] == 0.9
        assert "Suvarma" in match["recommendation_az"]


class TestRuleLoader:
    """Tests for RuleLoader class."""

    def test_load_rules_from_directory(self):
        """Test loading rules from the rules directory."""
        loader = RuleLoader()
        rules = loader.load_all()

        # Should load rules from YAML files
        assert len(rules) > 0

    def test_rules_have_required_fields(self):
        """Test that loaded rules have required fields."""
        loader = RuleLoader()
        rules = loader.load_all()

        for rule in rules:
            assert rule.id is not None
            assert rule.name is not None
            assert rule.category is not None
            assert rule.recommendation_az is not None
            assert len(rule.conditions) > 0


class TestRulesEngine:
    """Tests for RulesEngine class."""

    @pytest.fixture
    def engine(self):
        """Create rules engine for testing."""
        return get_rules_engine()

    def test_engine_loads_rules(self, engine):
        """Test engine loads rules on first use."""
        assert engine.rule_count > 0

    def test_evaluate_returns_matches(self, engine):
        """Test evaluate returns matching rules."""
        # Create context that should match high temperature irrigation rule
        context = {
            "weather": {
                "temperature_c": 35,
                "humidity_percent": 30,
                "precipitation_mm": 0,
                "wind_speed_kmh": 5,
            },
            "farm": {"region": "aran"},
            "intent": "irrigation",
            "date": {"month": 7, "day": 15, "year": 2026},
        }

        matches = engine.evaluate(context)

        # Should match at least the high temperature rule
        assert len(matches) > 0
        assert any(
            "temperature" in m["rule_name"].lower() or "temperatur" in m["rule_name"].lower()
            for m in matches
        )

    def test_evaluate_with_category_filter(self, engine):
        """Test filtering by category."""
        context = {
            "weather": {"temperature_c": 35, "humidity_percent": 30},
            "intent": "irrigation",
        }

        matches = engine.evaluate(context, categories=[RuleCategory.IRRIGATION])

        # All matches should be irrigation category
        for match in matches:
            assert match["category"] == "irrigation"

    def test_matches_sorted_by_priority(self, engine):
        """Test matches are sorted by priority."""
        context = {
            "weather": {
                "temperature_c": 35,
                "humidity_percent": 30,
                "precipitation_mm": 10,
                "wind_speed_kmh": 5,
            },
            "intent": "irrigation",
        }

        matches = engine.evaluate(context)

        if len(matches) >= 2:
            # Priority order: critical > high > medium > low
            priority_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            priorities = [priority_map.get(m["priority"], 4) for m in matches]

            assert priorities == sorted(priorities)


class TestBuildRuleContext:
    """Tests for build_rule_context function."""

    def test_basic_context(self):
        """Test building basic context."""
        context = build_rule_context(
            weather={"temperature_c": 25},
            intent="irrigation",
        )

        assert context["weather"]["temperature_c"] == 25
        assert context["intent"] == "irrigation"
        assert "date" in context

    def test_context_with_all_fields(self):
        """Test building context with all fields."""
        context = build_rule_context(
            weather={"temperature_c": 30, "humidity_percent": 50},
            farm={"region": "aran", "total_area_ha": 10},
            user={"experience_level": "expert"},
            intent="fertilization",
            current_date=date(2026, 7, 15),
        )

        assert context["weather"]["temperature_c"] == 30
        assert context["farm"]["region"] == "aran"
        assert context["user"]["experience_level"] == "expert"
        assert context["intent"] == "fertilization"
        assert context["date"]["month"] == 7
        assert context["date"]["day"] == 15

    def test_context_defaults(self):
        """Test default values in context."""
        context = build_rule_context()

        assert context["weather"] == {}
        assert context["farm"] == {}
        assert context["user"] == {}
        assert context["intent"] is None
        assert "month" in context["date"]


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    @pytest.fixture
    def engine(self):
        """Create rules engine for testing."""
        return get_rules_engine()

    def test_hot_day_irrigation_scenario(self, engine):
        """Test hot day irrigation recommendations."""
        context = build_rule_context(
            weather={
                "temperature_c": 36,
                "humidity_percent": 25,
                "precipitation_mm": 0,
                "wind_speed_kmh": 8,
            },
            farm={"region": "aran"},
            intent="irrigation",
        )

        matches = engine.evaluate(context, categories=[RuleCategory.IRRIGATION])

        # Should get high temperature and low humidity alerts
        assert len(matches) >= 1
        recommendations = " ".join(m["recommendation_az"] for m in matches)
        # Check for temperature or irrigation related recommendations
        assert any(word in recommendations.lower() for word in ["temperatur", "suvar", "isti"])

    def test_rainy_day_pest_control_scenario(self, engine):
        """Test rainy day pest control recommendations."""
        context = build_rule_context(
            weather={
                "temperature_c": 22,
                "humidity_percent": 85,
                "precipitation_mm": 15,
                "wind_speed_kmh": 5,
            },
            intent="pest_control",
        )

        matches = engine.evaluate(context, categories=[RuleCategory.PEST_CONTROL])

        # Should warn about rain wash-off and humidity
        recommendations = " ".join(m["recommendation_az"] for m in matches)
        assert "yağış" in recommendations.lower() or "rütubət" in recommendations.lower()

    def test_frost_harvest_scenario(self, engine):
        """Test frost warning for harvest."""
        context = build_rule_context(
            weather={
                "temperature_c": 1,
                "humidity_percent": 70,
                "precipitation_mm": 0,
                "wind_speed_kmh": 5,
            },
            intent="harvest",
            current_date=date(2026, 10, 25),
        )

        matches = engine.evaluate(context, categories=[RuleCategory.HARVEST])

        # Should get frost warning
        if matches:
            recommendations = " ".join(m["recommendation_az"] for m in matches)
            # Check for frost or cold related warnings
            assert any(word in recommendations.lower() for word in ["şaxta", "soyuq", "don"])
