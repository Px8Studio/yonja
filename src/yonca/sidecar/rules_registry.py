"""
Yonca AI - Unified Rules Registry
=================================

Single source of truth for all Azerbaijani agricultural rules.
Consolidates rules from rag_engine.py and core/rules.py.

This module provides:
- AgronomyRule dataclass with all metadata
- Pre-approved status for Agronomist-in-the-Loop validation
- Confidence weights for trust score calculation
- Callable validators for deterministic evaluation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class RuleCategory(str, Enum):
    """Categories of agronomy rules."""
    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PEST_CONTROL = "pest_control"
    DISEASE_MANAGEMENT = "disease_management"
    HARVEST = "harvest"
    LIVESTOCK = "livestock"
    SOIL_MANAGEMENT = "soil_management"
    WEATHER_RESPONSE = "weather_response"
    CROP_ROTATION = "crop_rotation"
    SUBSIDY = "subsidy"
    GENERAL = "general"


class SeasonPhase(str, Enum):
    """
    Agricultural season phases in Azerbaijan.
    Standardized from temporal.py - use this everywhere.
    """
    EARLY_SPRING = "early_spring"      # February-March
    LATE_SPRING = "late_spring"        # April-May
    EARLY_SUMMER = "early_summer"      # June-July
    LATE_SUMMER = "late_summer"        # August-September
    EARLY_AUTUMN = "early_autumn"      # October-November
    LATE_AUTUMN = "late_autumn"        # November-December
    WINTER = "winter"                  # December-February
    
    @classmethod
    def from_month(cls, month: int) -> "SeasonPhase":
        """Get season phase from month number (1-12)."""
        if month in (2, 3):
            return cls.EARLY_SPRING
        elif month in (4, 5):
            return cls.LATE_SPRING
        elif month in (6, 7):
            return cls.EARLY_SUMMER
        elif month in (8, 9):
            return cls.LATE_SUMMER
        elif month == 10 or month == 11:
            return cls.EARLY_AUTUMN if month == 10 else cls.LATE_AUTUMN
        else:  # 12, 1
            return cls.WINTER
    
    @classmethod
    def from_simple_season(cls, season: str) -> list["SeasonPhase"]:
        """Convert simple season name to phase(s)."""
        mapping = {
            "spring": [cls.EARLY_SPRING, cls.LATE_SPRING],
            "summer": [cls.EARLY_SUMMER, cls.LATE_SUMMER],
            "autumn": [cls.EARLY_AUTUMN, cls.LATE_AUTUMN],
            "fall": [cls.EARLY_AUTUMN, cls.LATE_AUTUMN],
            "winter": [cls.WINTER],
        }
        return mapping.get(season.lower(), [])
    
    def to_simple_season(self) -> str:
        """Convert phase to simple season name."""
        if self in (SeasonPhase.EARLY_SPRING, SeasonPhase.LATE_SPRING):
            return "spring"
        elif self in (SeasonPhase.EARLY_SUMMER, SeasonPhase.LATE_SUMMER):
            return "summer"
        elif self in (SeasonPhase.EARLY_AUTUMN, SeasonPhase.LATE_AUTUMN):
            return "autumn"
        return "winter"


@dataclass
class AgronomyRule:
    """
    A deterministic agronomy rule from the Azerbaijani agricultural rulebook.
    
    This is the canonical rule definition used across all modules:
    - rag_engine.py: For RAG validation
    - validation.py: For expert approval workflow
    - trust.py: For citation and confidence scoring
    - core/engine.py: For recommendation generation
    """
    rule_id: str                         # Canonical ID with AZ- prefix
    name: str                            # English name
    name_az: str                         # Azerbaijani name
    category: RuleCategory
    
    # Conditions
    condition_description: str = ""
    condition_description_az: str = ""
    
    # Recommendation text
    recommendation: str = ""
    recommendation_az: str = ""
    
    # Applicability filters
    applicable_crops: list[str] = field(default_factory=list)      # Empty = all
    applicable_farm_types: list[str] = field(default_factory=list)  # Empty = all
    seasons: list[str] = field(default_factory=list)               # Empty = all
    
    # Thresholds (for rule-based matching)
    min_soil_moisture: Optional[float] = None
    max_soil_moisture: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_soil_ph: Optional[float] = None
    max_soil_ph: Optional[float] = None
    
    # Confidence & Trust
    confidence_weight: float = 0.9       # How reliable is this rule (0-1)
    is_pre_approved: bool = False        # Auto-pass Agronomist-in-the-Loop?
    requires_expert_review: bool = False # Force expert review?
    
    # Programmatic validator
    validator: Optional[Callable[[dict], bool]] = None
    
    # Legacy mapping (for backwards compatibility)
    legacy_rule_id: Optional[str] = None  # Old ID from core/rules.py (e.g., "IRR-001")
    
    def check_applicable(self, context: dict) -> bool:
        """Check if this rule is applicable to the given context."""
        # Check crop applicability
        if self.applicable_crops:
            request_crops = context.get("crops", [])
            if not any(crop in self.applicable_crops for crop in request_crops):
                return False
        
        # Check farm type
        if self.applicable_farm_types:
            if context.get("farm_type") not in self.applicable_farm_types:
                return False
        
        # Check season (support both simple and phase-based)
        if self.seasons:
            ctx_season = context.get("season") or context.get("current_season")
            if ctx_season and ctx_season not in self.seasons:
                # Check if it's a phase that maps to our seasons
                if isinstance(ctx_season, SeasonPhase):
                    simple = ctx_season.to_simple_season()
                    if simple not in self.seasons:
                        return False
                else:
                    return False
        
        return True
    
    def evaluate(self, context: dict) -> tuple[bool, float]:
        """
        Evaluate if this rule's condition is met.
        
        Returns:
            Tuple of (is_triggered, confidence_score)
        """
        if not self.check_applicable(context):
            return False, 0.0
        
        # Use custom validator if provided
        if self.validator:
            try:
                triggered = self.validator(context)
                return triggered, self.confidence_weight if triggered else 0.0
            except (TypeError, ValueError, KeyError):
                return False, 0.0
        
        # Otherwise, check threshold-based conditions
        triggered = True
        
        # Soil moisture check
        moisture = context.get("soil_moisture_percent")
        if moisture is not None:
            if self.max_soil_moisture is not None and moisture > self.max_soil_moisture:
                triggered = False
            if self.min_soil_moisture is not None and moisture < self.min_soil_moisture:
                # Rule triggers when below minimum
                pass
        
        # Temperature check
        temp_max = context.get("temperature_range", (None, None))[1]
        temp_min = context.get("temperature_range", (None, None))[0]
        
        if temp_max is not None and self.max_temperature is not None:
            if temp_max <= self.max_temperature:
                triggered = False  # Not hot enough to trigger
        
        if temp_min is not None and self.min_temperature is not None:
            if temp_min >= self.min_temperature:
                triggered = False  # Not cold enough to trigger
        
        # Soil pH check
        soil_ph = context.get("soil_ph")
        if soil_ph is not None:
            if self.min_soil_ph is not None and soil_ph < self.min_soil_ph:
                pass  # Rule triggers for acidic soil
            elif self.max_soil_ph is not None and soil_ph > self.max_soil_ph:
                pass  # Rule triggers for alkaline soil
        
        return triggered, self.confidence_weight if triggered else 0.0


# =============================================================================
# UNIFIED AGRONOMY RULEBOOK
# =============================================================================

AGRONOMY_RULES: list[AgronomyRule] = [
    # =========================================================================
    # IRRIGATION RULES
    # =========================================================================
    AgronomyRule(
        rule_id="AZ-IRR-001",
        legacy_rule_id="IRR-001",
        name="Critical Low Moisture Irrigation",
        name_az="Kritik aşağı nəmlik suvarması",
        category=RuleCategory.IRRIGATION,
        applicable_farm_types=["wheat", "vegetable", "orchard", "mixed"],
        max_soil_moisture=30,
        condition_description="Soil moisture below 30% requires immediate irrigation",
        condition_description_az="Torpaq nəmliyi 30%-dən aşağı olduqda təcili suvarma tələb olunur",
        recommendation="Irrigate immediately. Best time: early morning (06:00-08:00) or evening (18:00-20:00)",
        recommendation_az="Dərhal suvarın. Ən yaxşı vaxt: səhər tezdən (06:00-08:00) və ya axşam (18:00-20:00)",
        confidence_weight=0.95,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("soil_moisture_percent", 100) < 30
    ),
    AgronomyRule(
        rule_id="AZ-IRR-002",
        legacy_rule_id="IRR-003",
        name="Heat Wave Emergency Irrigation",
        name_az="İsti dalğası təcili suvarması",
        category=RuleCategory.IRRIGATION,
        applicable_farm_types=["wheat", "vegetable", "orchard", "mixed"],
        max_temperature=35,
        seasons=["summer"],
        condition_description="Temperature above 35°C with moisture below 50% requires emergency irrigation",
        condition_description_az="35°C-dən yuxarı temperatur və 50%-dən aşağı nəmlikdə təcili suvarma lazımdır",
        recommendation="Emergency irrigation needed. Increase frequency, avoid midday watering",
        recommendation_az="Təcili suvarma lazımdır. Tezliyi artırın, günorta suvarmasından çəkinin",
        confidence_weight=0.95,
        is_pre_approved=True,
        validator=lambda ctx: (
            ctx.get("temperature_range", (0, 0))[1] > 35 and
            ctx.get("soil_moisture_percent", 100) < 50
        )
    ),
    AgronomyRule(
        rule_id="AZ-IRR-003",
        legacy_rule_id="IRR-002",
        name="Skip Irrigation Before Rain",
        name_az="Yağışdan əvvəl suvarmanı keçin",
        category=RuleCategory.IRRIGATION,
        condition_description="Skip irrigation if rain is expected within 24-48 hours",
        condition_description_az="24-48 saat ərzində yağış gözlənilirsə suvarmanı keçin",
        recommendation="Postpone irrigation. Natural rainfall expected. Check forecast again tomorrow",
        recommendation_az="Suvarmanı təxirə salın. Təbii yağış gözlənilir. Sabah proqnoza yenidən baxın",
        confidence_weight=0.88,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("precipitation_expected", False)
    ),
    AgronomyRule(
        rule_id="AZ-IRR-004",
        legacy_rule_id="IRR-004",
        name="Early Morning Irrigation",
        name_az="Səhər tezdən suvarma",
        category=RuleCategory.IRRIGATION,
        applicable_farm_types=["wheat", "vegetable", "orchard", "mixed"],
        seasons=["summer"],
        condition_description="Recommend early morning irrigation to reduce evaporation during hot days",
        condition_description_az="İsti günlərdə buxarlanmanı azaltmaq üçün səhər tezdən suvarma tövsiyə olunur",
        recommendation="Schedule irrigation for early morning (6-8 AM) to minimize evaporation",
        recommendation_az="Buxarlanmanı minimuma endirmək üçün suvarmanı səhər saatlarına (6-8) planlaşdırın",
        confidence_weight=0.85,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("temperature_range", (0, 0))[1] > 30
    ),
    
    # =========================================================================
    # FERTILIZATION RULES
    # =========================================================================
    AgronomyRule(
        rule_id="AZ-FERT-001",
        legacy_rule_id="FERT-001",
        name="Low Nitrogen Application",
        name_az="Aşağı azot tətbiqi",
        category=RuleCategory.FERTILIZATION,
        applicable_farm_types=["wheat", "vegetable", "orchard", "mixed"],
        condition_description="Apply nitrogen fertilizer when N level below 30 kg/ha",
        condition_description_az="Azot səviyyəsi 30 kq/ha-dan aşağı olduqda azot gübrəsi tətbiq edin",
        recommendation="Apply 30-50 kg/ha nitrogen fertilizer (urea or ammonium nitrate)",
        recommendation_az="30-50 kq/ha azot gübrəsi tətbiq edin (karbamid və ya ammonium nitrat)",
        confidence_weight=0.92,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("soil_nutrients", {}).get("nitrogen", 100) < 30
    ),
    AgronomyRule(
        rule_id="AZ-FERT-002",
        legacy_rule_id="FERT-002",
        name="Phosphorus for Flowering",
        name_az="Çiçəkləmə üçün fosfor",
        category=RuleCategory.FERTILIZATION,
        applicable_farm_types=["vegetable", "orchard"],
        seasons=["spring", "summer"],
        condition_description="Apply phosphorus during flowering when P level below 25 kg/ha",
        condition_description_az="Fosfor səviyyəsi 25 kq/ha-dan aşağı olduqda çiçəkləmə dövründə fosfor tətbiq edin",
        recommendation="Apply 20-30 kg/ha phosphorus fertilizer (superphosphate)",
        recommendation_az="20-30 kq/ha fosfor gübrəsi tətbiq edin (superfosfat)",
        confidence_weight=0.88,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("soil_nutrients", {}).get("phosphorus", 100) < 25
    ),
    AgronomyRule(
        rule_id="AZ-FERT-003",
        legacy_rule_id="FERT-003",
        name="Potassium for Fruit Quality",
        name_az="Meyvə keyfiyyəti üçün kalium",
        category=RuleCategory.FERTILIZATION,
        applicable_farm_types=["orchard", "vegetable"],
        applicable_crops=["pomidor", "alma", "armud", "nar", "üzüm"],
        condition_description="Apply potassium before harvest when K level below 100 kg/ha",
        condition_description_az="Kalium səviyyəsi 100 kq/ha-dan aşağı olduqda məhsul yığımından əvvəl kalium tətbiq edin",
        recommendation="Apply 40-60 kg/ha potassium fertilizer (potassium chloride)",
        recommendation_az="40-60 kq/ha kalium gübrəsi tətbiq edin (kalium xlorid)",
        confidence_weight=0.85,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("soil_nutrients", {}).get("potassium", 200) < 100
    ),
    
    # =========================================================================
    # PEST & DISEASE RULES
    # =========================================================================
    AgronomyRule(
        rule_id="AZ-PEST-001",
        legacy_rule_id="PEST-001",
        name="Humid Weather Pest Alert",
        name_az="Rütubətli havada zərərverici xəbərdarlığı",
        category=RuleCategory.PEST_CONTROL,
        condition_description="High humidity (>70%) and warm temps (20-30°C) increase pest activity",
        condition_description_az="Yüksək rütubət (>70%) və isti hava (20-30°C) zərərverici aktivliyini artırır",
        recommendation="Scout fields for aphids and mites. Consider preventive spraying",
        recommendation_az="Mənənə və gənələr üçün sahələri yoxlayın. Profilaktik çiləmə düşünün",
        confidence_weight=0.82,
        is_pre_approved=True,
        validator=lambda ctx: (
            20 <= ctx.get("temperature_range", (0, 0))[1] <= 30 and
            ctx.get("humidity_percent", 0) > 70
        )
    ),
    AgronomyRule(
        rule_id="AZ-PEST-002",
        legacy_rule_id="PEST-003",
        name="Post-Rain Fungal Disease Watch",
        name_az="Yağışdan sonra göbələk xəstəliyi nəzarəti",
        category=RuleCategory.DISEASE_MANAGEMENT,
        condition_description="Wet conditions after rain increase fungal disease risk",
        condition_description_az="Yağışdan sonra nəm şərait göbələk xəstəliyi riskini artırır",
        recommendation="Apply preventive fungicide within 24-48 hours after rain",
        recommendation_az="Yağışdan sonra 24-48 saat ərzində profilaktik fungisid tətbiq edin",
        confidence_weight=0.85,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("precipitation_expected", False) or ctx.get("recent_rain", False)
    ),
    AgronomyRule(
        rule_id="AZ-PEST-003",
        legacy_rule_id="PEST-002",
        name="Aphid Alert - Warm Dry Conditions",
        name_az="Mənənə xəbərdarlığı - isti quru şərait",
        category=RuleCategory.PEST_CONTROL,
        applicable_farm_types=["vegetable", "orchard"],
        condition_description="Watch for aphids in warm (>25°C), dry (<50% humidity) conditions",
        condition_description_az="İsti (>25°C), quru (<50% rütubət) şəraitdə mənənələrə diqqət edin",
        recommendation="Check crops for aphid infestation. Apply neem oil or insecticidal soap",
        recommendation_az="Bitkiləri mənənə üçün yoxlayın. Neem yağı və ya həşərat sabunu tətbiq edin",
        confidence_weight=0.80,
        is_pre_approved=True,
        validator=lambda ctx: (
            ctx.get("temperature_range", (0, 0))[1] > 25 and
            ctx.get("humidity_percent", 100) < 50
        )
    ),
    
    # =========================================================================
    # HARVEST RULES
    # =========================================================================
    AgronomyRule(
        rule_id="AZ-HARV-001",
        legacy_rule_id="HARV-001",
        name="Dry Weather Harvest Window",
        name_az="Quru havada məhsul yığımı pəncərəsi",
        category=RuleCategory.HARVEST,
        applicable_farm_types=["wheat", "vegetable", "orchard"],
        seasons=["summer", "autumn"],
        condition_description="Harvest during dry weather with no rain forecast for 3+ days",
        condition_description_az="3+ gün yağış proqnozu olmadıqda quru havada məhsul yığın",
        recommendation="Optimal harvest window. Complete harvest before weather changes",
        recommendation_az="Optimal məhsul yığımı pəncərəsi. Hava dəyişməzdən əvvəl yığımı tamamlayın",
        confidence_weight=0.90,
        is_pre_approved=True,
        validator=lambda ctx: not ctx.get("precipitation_expected", False)
    ),
    AgronomyRule(
        rule_id="AZ-HARV-002",
        legacy_rule_id="HARV-002",
        name="Morning Dew Harvest Delay",
        name_az="Səhər şehi məhsul yığımı gecikməsi",
        category=RuleCategory.HARVEST,
        applicable_crops=["buğda", "arpa"],
        condition_description="Wait for dew to dry before grain harvest",
        condition_description_az="Taxıl yığımından əvvəl şehin qurumasını gözləyin",
        recommendation="Start harvest after 10:00 AM when morning dew has evaporated",
        recommendation_az="Səhər şehi buxarlandıqdan sonra saat 10:00-dan sonra yığıma başlayın",
        confidence_weight=0.88,
        is_pre_approved=True,
    ),
    
    # =========================================================================
    # LIVESTOCK RULES
    # =========================================================================
    AgronomyRule(
        rule_id="AZ-LIVE-001",
        legacy_rule_id="LIVE-001",
        name="Heat Stress Prevention",
        name_az="İsti stresinin qarşısının alınması",
        category=RuleCategory.LIVESTOCK,
        applicable_farm_types=["livestock", "mixed"],
        max_temperature=30,  # Triggers when above 30°C
        seasons=["summer"],
        condition_description="Provide shade and extra water when temperature exceeds 30°C",
        condition_description_az="Temperatur 30°C-dən yuxarı olduqda kölgə və əlavə su təmin edin",
        recommendation="Move livestock to shade. Provide 20% more water. Avoid moving animals during peak heat",
        recommendation_az="Heyvanları kölgəyə köçürün. 20% daha çox su verin. Pik istidə heyvanları hərəkət etdirməyin",
        confidence_weight=0.93,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("temperature_range", (0, 0))[1] > 30
    ),
    AgronomyRule(
        rule_id="AZ-LIVE-002",
        legacy_rule_id="LIVE-003",
        name="Cold Weather Shelter",
        name_az="Soyuq havada sığınacaq",
        category=RuleCategory.LIVESTOCK,
        applicable_farm_types=["livestock", "mixed"],
        min_temperature=5,  # Triggers when below 5°C
        seasons=["winter"],
        condition_description="Ensure proper shelter when temperature drops below 5°C",
        condition_description_az="Temperatur 5°C-dən aşağı düşdükdə düzgün sığınacaq təmin edin",
        recommendation="Check shelter insulation, repair drafts, provide extra bedding",
        recommendation_az="Sığınacaq izolyasiyasını yoxlayın, hava axınlarını təmir edin, əlavə döşəmə təmin edin",
        confidence_weight=0.90,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("temperature_range", (0, 0))[0] < 5
    ),
    AgronomyRule(
        rule_id="AZ-LIVE-003",
        legacy_rule_id="LIVE-002",
        name="Vaccination Reminder",
        name_az="Peyvənd xatırlatması",
        category=RuleCategory.LIVESTOCK,
        applicable_farm_types=["livestock", "mixed"],
        condition_description="Remind vaccination when overdue by 180+ days",
        condition_description_az="180+ gün keçdikdə peyvəndi xatırladın",
        recommendation="Schedule vaccination for livestock - overdue",
        recommendation_az="Heyvandarlıq üçün peyvənd planlaşdırın - vaxtı keçib",
        confidence_weight=0.85,
        is_pre_approved=False,  # Requires expert review for medical advice
        requires_expert_review=True,
    ),
    
    # =========================================================================
    # SOIL MANAGEMENT RULES
    # =========================================================================
    AgronomyRule(
        rule_id="AZ-SOIL-001",
        legacy_rule_id="FERT-004",
        name="Acidic Soil Correction",
        name_az="Turş torpağın düzəldilməsi",
        category=RuleCategory.SOIL_MANAGEMENT,
        max_soil_ph=5.5,
        condition_description="Apply lime when soil pH drops below 5.5",
        condition_description_az="Torpaq pH-ı 5.5-dən aşağı düşdükdə əhəng tətbiq edin",
        recommendation="Apply 1-2 tonnes/ha agricultural lime. Test pH again after 3 months",
        recommendation_az="1-2 ton/ha kənd təsərrüfatı əhəngi tətbiq edin. 3 aydan sonra pH-ı yenidən test edin",
        confidence_weight=0.90,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("soil_ph", 7.0) < 5.5
    ),
    AgronomyRule(
        rule_id="AZ-SOIL-002",
        name="Alkaline Soil Correction",
        name_az="Qələvi torpağın düzəldilməsi",
        category=RuleCategory.SOIL_MANAGEMENT,
        min_soil_ph=7.5,
        condition_description="Apply sulfur when soil pH exceeds 7.5",
        condition_description_az="Torpaq pH-ı 7.5-dən yuxarı olduqda kükürd tətbiq edin",
        recommendation="Apply 100-200 kg/ha elemental sulfur or gypsum",
        recommendation_az="100-200 kq/ha elementar kükürd və ya gips tətbiq edin",
        confidence_weight=0.88,
        is_pre_approved=True,
        validator=lambda ctx: ctx.get("soil_ph", 7.0) > 7.5
    ),
]


# =============================================================================
# REGISTRY UTILITIES
# =============================================================================

class RulesRegistry:
    """
    Central registry for all agronomy rules.
    
    Provides lookup, filtering, and validation utilities.
    """
    
    def __init__(self, rules: Optional[list[AgronomyRule]] = None):
        self._rules = rules or AGRONOMY_RULES
        self._id_index = {r.rule_id: r for r in self._rules}
        self._legacy_index = {
            r.legacy_rule_id: r for r in self._rules if r.legacy_rule_id
        }
    
    @property
    def all_rules(self) -> list[AgronomyRule]:
        """Get all rules."""
        return self._rules
    
    @property
    def pre_approved_rules(self) -> list[AgronomyRule]:
        """Get rules that are pre-approved for auto-validation."""
        return [r for r in self._rules if r.is_pre_approved]
    
    @property
    def pre_approved_rule_ids(self) -> set[str]:
        """Get IDs of pre-approved rules."""
        return {r.rule_id for r in self._rules if r.is_pre_approved}
    
    def get_by_id(self, rule_id: str) -> Optional[AgronomyRule]:
        """Get rule by ID (supports both AZ- and legacy IDs)."""
        if rule_id in self._id_index:
            return self._id_index[rule_id]
        if rule_id in self._legacy_index:
            return self._legacy_index[rule_id]
        return None
    
    def get_by_category(self, category: RuleCategory) -> list[AgronomyRule]:
        """Get all rules for a category."""
        return [r for r in self._rules if r.category == category]
    
    def get_by_farm_type(self, farm_type: str) -> list[AgronomyRule]:
        """Get rules applicable to a farm type."""
        return [
            r for r in self._rules
            if not r.applicable_farm_types or farm_type in r.applicable_farm_types
        ]
    
    def get_applicable(self, context: dict) -> list[AgronomyRule]:
        """Get all rules applicable to the given context."""
        return [r for r in self._rules if r.check_applicable(context)]
    
    def evaluate_all(self, context: dict) -> list[tuple[AgronomyRule, bool, float]]:
        """
        Evaluate all applicable rules.
        
        Returns:
            List of (rule, is_triggered, confidence) tuples
        """
        results = []
        for rule in self.get_applicable(context):
            triggered, confidence = rule.evaluate(context)
            results.append((rule, triggered, confidence))
        return results


# Default singleton registry
_default_registry: Optional[RulesRegistry] = None


def get_rules_registry() -> RulesRegistry:
    """Get the default rules registry singleton."""
    global _default_registry
    if _default_registry is None:
        _default_registry = RulesRegistry()
    return _default_registry


def get_rule_by_id(rule_id: str) -> Optional[AgronomyRule]:
    """Convenience function to get rule by ID."""
    return get_rules_registry().get_by_id(rule_id)


def get_pre_approved_rule_ids() -> set[str]:
    """Convenience function to get pre-approved rule IDs."""
    return get_rules_registry().pre_approved_rule_ids
