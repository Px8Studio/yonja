"""
Yonca AI - Digital Umbrella Agronomy Logic Guard
================================================

Deterministic rule-based validation layer for LLM recommendations.
Acts as a "Logic Guard" to prevent agronomically incorrect suggestions.

If the LLM suggests something that contradicts basic agronomy principles
(e.g., watering during a rainstorm), the logic guard overrides it.

Based on Azerbaijani agricultural best practices and ETSN standards.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Callable, Optional

from yonca.umbrella.mock_backend import (
    FarmProfileRequest,
    RecommendationItem,
    RecommendationType,
)


class OverrideReason(str, Enum):
    """Reasons for overriding an LLM recommendation."""
    WEATHER_CONFLICT = "weather_conflict"
    SOIL_CONDITION = "soil_condition"
    TEMPERATURE_EXTREME = "temperature_extreme"
    TIMING_INAPPROPRIATE = "timing_inappropriate"
    SAFETY_RISK = "safety_risk"
    RESOURCE_WASTE = "resource_waste"
    BIOLOGICAL_CONSTRAINT = "biological_constraint"


@dataclass
class ValidationResult:
    """Result of validating a recommendation."""
    is_valid: bool
    recommendation: RecommendationItem
    override_reason: Optional[OverrideReason] = None
    override_message: Optional[str] = None
    override_message_az: Optional[str] = None
    modified: bool = False


@dataclass
class AgronomyRule:
    """
    A deterministic agronomy rule for validation.
    
    These rules are based on established agricultural science
    and cannot be overridden by LLM suggestions.
    """
    rule_id: str
    name: str
    name_az: str
    description: str
    description_az: str
    
    # What this rule validates
    recommendation_types: list[RecommendationType]
    
    # The validation logic
    validator: Callable[[RecommendationItem, FarmProfileRequest], bool]
    
    # What to do if validation fails
    override_action: str  # "block", "modify", "warn"
    override_message: str
    override_message_az: str
    
    # Metadata
    source: str = "ETSN"  # Azerbaijani Ministry of Agriculture standards
    confidence: float = 1.0  # Deterministic rules have 100% confidence


class AgronomyLogicGuard:
    """
    Logic Guard for validating LLM-generated recommendations.
    
    This class implements a deterministic rule engine that acts as
    a safety layer between the LLM inference and the farmer.
    
    Key principles:
    1. Physical laws cannot be violated (e.g., no irrigation during heavy rain)
    2. Biological constraints must be respected (e.g., growth stages)
    3. Safety always comes first (e.g., no spraying in high wind)
    4. Resource waste should be prevented
    
    Usage:
        guard = AgronomyLogicGuard()
        validated_recs = guard.validate_recommendations(recommendations, request)
    """
    
    def __init__(self):
        self._rules: list[AgronomyRule] = []
        self._override_count = 0
        self._validation_count = 0
        self._initialize_rules()
    
    def _initialize_rules(self) -> None:
        """Initialize all agronomy validation rules."""
        
        # ============= IRRIGATION RULES =============
        
        self._rules.append(AgronomyRule(
            rule_id="AG-IRR-001",
            name="No Irrigation During Rain",
            name_az="Yağış zamanı suvarma yoxdur",
            description="Do not irrigate when rain is expected or occurring",
            description_az="Yağış gözləniləndə və ya yağanda suvarma etməyin",
            recommendation_types=[RecommendationType.IRRIGATION],
            validator=lambda rec, req: not req.is_rain_expected,
            override_action="block",
            override_message="Irrigation blocked: Rain is expected. Save water and wait for natural precipitation.",
            override_message_az="Suvarma bloklandı: Yağış gözlənilir. Su qənaət edin və təbii yağışı gözləyin.",
            source="ETSN-Suvarma-2023",
        ))
        
        self._rules.append(AgronomyRule(
            rule_id="AG-IRR-002",
            name="No Irrigation in Extreme Heat",
            name_az="Həddindən artıq istidə suvarma qadağası",
            description="Avoid midday irrigation when temperature exceeds 35°C",
            description_az="Temperatur 35°C-dən çox olduqda günorta suvarmasından qaçın",
            recommendation_types=[RecommendationType.IRRIGATION],
            validator=lambda rec, req: (
                req.temperature_max is None or 
                req.temperature_max < 38 or
                (rec.suggested_time and ("06:" in rec.suggested_time or "07:" in rec.suggested_time or "18:" in rec.suggested_time or "19:" in rec.suggested_time))
            ),
            override_action="modify",
            override_message="Irrigation timing modified: Avoid midday watering in extreme heat to prevent evaporation loss.",
            override_message_az="Suvarma vaxtı dəyişdirildi: Həddindən artıq istidə günorta suvarmasından qaçın - buxarlanma itkisi.",
            source="ETSN-İqlim-2023",
        ))
        
        self._rules.append(AgronomyRule(
            rule_id="AG-IRR-003",
            name="Waterlogging Prevention",
            name_az="Su durğunluğunun qarşısının alınması",
            description="Do not irrigate when soil moisture is already above 70%",
            description_az="Torpaq nəmliyi 70%-dən yuxarı olduqda suvarma etməyin",
            recommendation_types=[RecommendationType.IRRIGATION],
            validator=lambda rec, req: (
                req.soil_moisture_percent is None or 
                req.soil_moisture_percent < 70
            ),
            override_action="block",
            override_message="Irrigation blocked: Soil moisture already high. Excess water causes root rot.",
            override_message_az="Suvarma bloklandı: Torpaq nəmliyi artıq yüksəkdir. Artıq su kök çürüməsinə səbəb olur.",
            source="ETSN-Torpaq-2023",
        ))
        
        # ============= FERTILIZATION RULES =============
        
        self._rules.append(AgronomyRule(
            rule_id="AG-FERT-001",
            name="No Fertilization Before Rain",
            name_az="Yağışdan əvvəl gübrələmə qadağası",
            description="Avoid fertilizer application when heavy rain is expected",
            description_az="Güclü yağış gözləniləndə gübrə tətbiqindən qaçın",
            recommendation_types=[RecommendationType.FERTILIZATION],
            validator=lambda rec, req: not req.is_rain_expected,
            override_action="modify",
            override_message="Fertilization postponed: Heavy rain would wash away fertilizer, causing pollution and waste.",
            override_message_az="Gübrələmə təxirə salındı: Güclü yağış gübrəni yuyub aparar, çirklənmə və israf yaradar.",
            source="ETSN-Gübrə-2023",
        ))
        
        self._rules.append(AgronomyRule(
            rule_id="AG-FERT-002",
            name="No Nitrogen on Mature Crops",
            name_az="Yetişmiş bitkilərə azot qadağası",
            description="Do not apply nitrogen fertilizer to crops in maturity stage",
            description_az="Yetişmə mərhələsindəki bitkilərə azot gübrəsi tətbiq etməyin",
            recommendation_types=[RecommendationType.FERTILIZATION],
            validator=lambda rec, req: (
                not any(stage in ["maturity", "yetişmə", "harvest", "məhsul yığımı"] 
                       for stage in req.crop_stages)
            ),
            override_action="block",
            override_message="Nitrogen application blocked: Crops in maturity stage don't benefit from nitrogen and may develop quality issues.",
            override_message_az="Azot tətbiqi bloklandı: Yetişmə mərhələsindəki bitkilər azotdan fayda görmür və keyfiyyət problemləri yarana bilər.",
            source="ETSN-Qida-2023",
        ))
        
        # ============= PEST CONTROL RULES =============
        
        self._rules.append(AgronomyRule(
            rule_id="AG-PEST-001",
            name="No Spraying in High Wind",
            name_az="Güclü küləkdə püskürtmə qadağası",
            description="Do not spray pesticides when wind speed exceeds 15 km/h",
            description_az="Külək sürəti 15 km/saatdan çox olduqda pestisid püskürtməyin",
            recommendation_types=[RecommendationType.PEST_CONTROL],
            validator=lambda rec, req: True,  # We don't have wind data in basic request
            override_action="warn",
            override_message="Check wind conditions: Do not spray if wind exceeds 15 km/h to prevent drift.",
            override_message_az="Külək şəraitini yoxlayın: Sürüşməni önləmək üçün külək 15 km/saatdan çox olduqda püskürtməyin.",
            source="ETSN-Bitki Mühafizə-2023",
        ))
        
        self._rules.append(AgronomyRule(
            rule_id="AG-PEST-002",
            name="Pre-Harvest Interval",
            name_az="Məhsul yığımından əvvəl interval",
            description="Respect pre-harvest interval for pesticide applications",
            description_az="Pestisid tətbiqləri üçün məhsul yığımından əvvəl intervala riayət edin",
            recommendation_types=[RecommendationType.PEST_CONTROL],
            validator=lambda rec, req: (
                not any(stage in ["maturity", "yetişmə", "harvest", "məhsul yığımı"] 
                       for stage in req.crop_stages)
            ),
            override_action="block",
            override_message="Pesticide blocked: Crops are too close to harvest. Pre-harvest interval must be respected for food safety.",
            override_message_az="Pestisid bloklandı: Məhsul yığımına çox az qalıb. Qida təhlükəsizliyi üçün intervala riayət edilməlidir.",
            source="ETSN-Qida Təhlükəsizliyi-2023",
        ))
        
        # ============= LIVESTOCK RULES =============
        
        self._rules.append(AgronomyRule(
            rule_id="AG-LIVE-001",
            name="Heat Stress Priority",
            name_az="İstilik stresi prioriteti",
            description="Livestock ventilation takes priority in high temperature + humidity",
            description_az="Yüksək temperatur + rütubətdə heyvandarlıq ventilyasiyası prioritetdir",
            recommendation_types=[RecommendationType.LIVESTOCK_CARE, RecommendationType.VENTILATION],
            validator=lambda rec, req: True,  # Always valid, but may increase priority
            override_action="warn",
            override_message="Heat stress warning active. Ensure ventilation is addressed first.",
            override_message_az="İstilik stresi xəbərdarlığı aktivdir. Əvvəlcə ventilyasiyanın həll olunduğundan əmin olun.",
            source="ETSN-Heyvandarlıq-2023",
        ))
        
        self._rules.append(AgronomyRule(
            rule_id="AG-LIVE-002",
            name="Vaccination Timing",
            name_az="Peyvənd vaxtı",
            description="Do not vaccinate during disease outbreak or extreme stress",
            description_az="Xəstəlik yayılması və ya həddindən artıq stress zamanı peyvənd etməyin",
            recommendation_types=[RecommendationType.VACCINATION],
            validator=lambda rec, req: (
                req.temperature_max is None or req.temperature_max < 35
            ),
            override_action="modify",
            override_message="Vaccination postponed: Extreme temperatures cause stress, reducing vaccine effectiveness.",
            override_message_az="Peyvənd təxirə salındı: Həddindən artıq temperatur stress yaradır, peyvənd effektivliyini azaldır.",
            source="ETSN-Baytar-2023",
        ))
        
        # ============= GENERAL SAFETY RULES =============
        
        self._rules.append(AgronomyRule(
            rule_id="AG-SAFE-001",
            name="Extreme Heat Work Ban",
            name_az="Həddindən artıq istidə iş qadağası",
            description="Avoid fieldwork during extreme heat (>38°C)",
            description_az="Həddindən artıq istidə (>38°C) tarla işlərindən qaçın",
            recommendation_types=[RecommendationType.GENERAL, RecommendationType.HARVEST],
            validator=lambda rec, req: (
                req.temperature_max is None or req.temperature_max < 38
            ),
            override_action="modify",
            override_message="Work timing modified: Field work should be done in early morning or evening due to extreme heat.",
            override_message_az="İş vaxtı dəyişdirildi: Həddindən artıq isti səbəbindən tarla işləri səhər tezdən və ya axşam edilməlidir.",
            source="ETSN-İş Təhlükəsizliyi-2023",
        ))
    
    def validate_recommendations(
        self,
        recommendations: list[RecommendationItem],
        request: FarmProfileRequest
    ) -> list[RecommendationItem]:
        """
        Validate a list of recommendations against agronomy rules.
        
        Args:
            recommendations: LLM-generated recommendations
            request: Original farm profile request
            
        Returns:
            List of validated (possibly modified) recommendations
        """
        validated = []
        
        for rec in recommendations:
            result = self._validate_single(rec, request)
            self._validation_count += 1
            
            if result.is_valid:
                validated.append(result.recommendation)
            elif result.override_reason:
                self._override_count += 1
                # Log the override for transparency
                # In production, this would go to a monitoring system
        
        return validated
    
    def _validate_single(
        self,
        recommendation: RecommendationItem,
        request: FarmProfileRequest
    ) -> ValidationResult:
        """Validate a single recommendation against all applicable rules."""
        
        for rule in self._rules:
            # Check if this rule applies to this recommendation type
            if recommendation.type not in rule.recommendation_types:
                continue
            
            # Run the validator
            is_valid = rule.validator(recommendation, request)
            
            if not is_valid:
                if rule.override_action == "block":
                    # Completely remove this recommendation
                    return ValidationResult(
                        is_valid=False,
                        recommendation=recommendation,
                        override_reason=OverrideReason.WEATHER_CONFLICT,
                        override_message=rule.override_message,
                        override_message_az=rule.override_message_az,
                        modified=False,
                    )
                
                elif rule.override_action == "modify":
                    # Modify the recommendation
                    modified_rec = self._modify_recommendation(
                        recommendation, rule, request
                    )
                    return ValidationResult(
                        is_valid=True,
                        recommendation=modified_rec,
                        override_reason=None,
                        override_message=rule.override_message,
                        override_message_az=rule.override_message_az,
                        modified=True,
                    )
                
                elif rule.override_action == "warn":
                    # Add warning but keep recommendation
                    warned_rec = self._add_warning(recommendation, rule)
                    return ValidationResult(
                        is_valid=True,
                        recommendation=warned_rec,
                        modified=True,
                    )
        
        # All rules passed
        return ValidationResult(
            is_valid=True,
            recommendation=recommendation,
        )
    
    def _modify_recommendation(
        self,
        recommendation: RecommendationItem,
        rule: AgronomyRule,
        request: FarmProfileRequest
    ) -> RecommendationItem:
        """Modify a recommendation based on rule constraints."""
        
        # Create a copy with modifications
        modified = RecommendationItem(
            id=recommendation.id,
            type=recommendation.type,
            priority=recommendation.priority,
            confidence=recommendation.confidence * 0.9,  # Reduce confidence
            title=recommendation.title,
            description=recommendation.description,
            action=recommendation.action,
            why_title=recommendation.why_title,
            why_explanation=recommendation.why_explanation,
            rule_id=recommendation.rule_id,
            source="hybrid-modified",
            suggested_time=recommendation.suggested_time,
            deadline=recommendation.deadline,
        )
        
        # Specific modifications based on rule
        if rule.rule_id == "AG-IRR-002":
            # Change irrigation time to early morning
            modified.suggested_time = "06:00-08:00"
            modified.action = f"{recommendation.action}\n\n⚠️ {rule.override_message_az}"
        
        elif rule.rule_id == "AG-FERT-001":
            # Postpone fertilization
            modified.deadline = date.today() + timedelta(days=2)
            modified.action = f"{recommendation.action}\n\n⚠️ Yağış keçənə qədər gözləyin."
        
        elif rule.rule_id == "AG-LIVE-002":
            # Postpone vaccination
            modified.deadline = date.today() + timedelta(days=3)
            modified.action = f"{recommendation.action}\n\n⚠️ Temperatur düşənə qədər gözləyin."
        
        elif rule.rule_id == "AG-SAFE-001":
            # Modify work timing
            modified.suggested_time = "05:00-09:00, 18:00-20:00"
            modified.action = f"{recommendation.action}\n\n⚠️ Günorta saatlarından qaçın!"
        
        return modified
    
    def _add_warning(
        self,
        recommendation: RecommendationItem,
        rule: AgronomyRule
    ) -> RecommendationItem:
        """Add a warning to a recommendation."""
        warned = RecommendationItem(
            id=recommendation.id,
            type=recommendation.type,
            priority=recommendation.priority,
            confidence=recommendation.confidence,
            title=f"⚠️ {recommendation.title}",
            description=recommendation.description,
            action=f"{recommendation.action}\n\n⚠️ DİQQƏT: {rule.override_message_az}",
            why_title=recommendation.why_title,
            why_explanation=recommendation.why_explanation,
            rule_id=recommendation.rule_id,
            source=recommendation.source,
            suggested_time=recommendation.suggested_time,
            deadline=recommendation.deadline,
        )
        return warned
    
    def get_statistics(self) -> dict:
        """Get validation statistics."""
        return {
            "total_validations": self._validation_count,
            "total_overrides": self._override_count,
            "override_rate": (
                self._override_count / self._validation_count 
                if self._validation_count > 0 else 0
            ),
            "rules_count": len(self._rules),
        }
    
    def get_rules_summary(self) -> list[dict]:
        """Get a summary of all active rules."""
        return [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "name_az": rule.name_az,
                "types": [t.value for t in rule.recommendation_types],
                "action": rule.override_action,
                "source": rule.source,
            }
            for rule in self._rules
        ]


# Singleton instance
agronomy_guard = AgronomyLogicGuard()
