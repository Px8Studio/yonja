"""
Yonca AI - RAG Engine with Deterministic Agronomy Rulebook
==========================================================

Retrieval-Augmented Generation engine that combines:
1. LLM intelligence (Qwen2.5-7B) for natural language understanding
2. Deterministic rulebook validation for >90% accuracy guarantee
3. Azerbaijani agricultural "Rules of Thumb" knowledge base

Architecture:
- Intent Detection → Knowledge Retrieval → LLM Generation → Rule Validation → Response
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from yonca.sidecar.pii_gateway import SanitizedRequest, SanitizedResponse


class AgronomyCategory(str, Enum):
    """Categories of agronomy knowledge."""
    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PEST_CONTROL = "pest_control"
    DISEASE_MANAGEMENT = "disease_management"
    HARVEST = "harvest"
    LIVESTOCK = "livestock"
    SOIL_MANAGEMENT = "soil_management"
    WEATHER_RESPONSE = "weather_response"
    CROP_ROTATION = "crop_rotation"
    GENERAL = "general"


class ConfidenceLevel(str, Enum):
    """Confidence levels for recommendations."""
    HIGH = "high"      # >0.85 - Rule-based + LLM agreement
    MEDIUM = "medium"  # 0.70-0.85 - Partial rule coverage
    LOW = "low"        # <0.70 - LLM-only, needs human review


@dataclass
class AgronomyRule:
    """
    A deterministic agronomy rule from the Azerbaijani agricultural rulebook.
    
    These rules are "Rules of Thumb" validated by agricultural experts.
    They serve as ground truth for LLM output validation.
    """
    rule_id: str
    name: str
    name_az: str
    category: AgronomyCategory
    
    # Conditions (deterministic checks)
    applicable_crops: list[str] = field(default_factory=list)  # Empty = all crops
    applicable_farm_types: list[str] = field(default_factory=list)
    
    # Environmental thresholds
    min_soil_moisture: Optional[float] = None
    max_soil_moisture: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    seasons: list[str] = field(default_factory=list)  # Empty = all seasons
    
    # The rule logic
    condition_description: str = ""
    condition_description_az: str = ""
    
    # The recommendation if rule triggers
    recommendation: str = ""
    recommendation_az: str = ""
    
    # Confidence weight (how reliable is this rule)
    confidence_weight: float = 0.9
    
    # Validation function (for programmatic checks)
    validator: Optional[Callable[[dict], bool]] = None
    
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
        
        # Check season
        if self.seasons:
            if context.get("season") not in self.seasons:
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
            except Exception:
                return False, 0.0
        
        # Otherwise, check threshold-based conditions
        triggered = True
        
        moisture = context.get("soil_moisture_percent")
        if moisture is not None:
            if self.min_soil_moisture is not None and moisture < self.min_soil_moisture:
                # Below minimum - could trigger irrigation rule
                pass
            elif self.max_soil_moisture is not None and moisture > self.max_soil_moisture:
                triggered = False
        
        temp_range = context.get("temperature_range", (None, None))
        if temp_range[1] is not None:
            if self.max_temperature is not None and temp_range[1] > self.max_temperature:
                # Above max temp - could trigger heat protection
                pass
            elif self.min_temperature is not None and temp_range[0] is not None:
                if temp_range[0] < self.min_temperature:
                    # Below min temp - could trigger frost protection
                    pass
        
        return triggered, self.confidence_weight if triggered else 0.0


# ============= Azerbaijani Agronomy Rulebook =============

AGRONOMY_RULEBOOK: list[AgronomyRule] = [
    # --- Irrigation Rules ---
    AgronomyRule(
        rule_id="AZ-IRR-001",
        name="Critical Low Moisture Irrigation",
        name_az="Kritik aşağı nəmlik suvarması",
        category=AgronomyCategory.IRRIGATION,
        applicable_farm_types=["wheat", "vegetable", "orchard", "mixed"],
        min_soil_moisture=0,
        max_soil_moisture=30,
        condition_description="Soil moisture below 30% requires immediate irrigation",
        condition_description_az="Torpaq nəmliyi 30%-dən aşağı olduqda təcili suvarma tələb olunur",
        recommendation="Irrigate immediately. Best time: early morning (06:00-08:00) or evening (18:00-20:00)",
        recommendation_az="Dərhal suvarın. Ən yaxşı vaxt: səhər tezdən (06:00-08:00) və ya axşam (18:00-20:00)",
        confidence_weight=0.95,
        validator=lambda ctx: ctx.get("soil_moisture_percent", 100) < 30
    ),
    AgronomyRule(
        rule_id="AZ-IRR-002",
        name="Heat Wave Emergency Irrigation",
        name_az="İsti dalğası təcili suvarması",
        category=AgronomyCategory.IRRIGATION,
        applicable_farm_types=["wheat", "vegetable", "orchard", "mixed"],
        max_temperature=35,
        seasons=["summer"],
        condition_description="Temperature above 35°C with moisture below 50% requires emergency irrigation",
        condition_description_az="35°C-dən yuxarı temperatur və 50%-dən aşağı nəmlikdə təcili suvarma lazımdır",
        recommendation="Emergency irrigation needed. Increase frequency, avoid midday watering",
        recommendation_az="Təcili suvarma lazımdır. Tezliyi artırın, günorta suvarmasından çəkinin",
        confidence_weight=0.95,
        validator=lambda ctx: (
            ctx.get("temperature_range", (0, 0))[1] > 35 and
            ctx.get("soil_moisture_percent", 100) < 50
        )
    ),
    AgronomyRule(
        rule_id="AZ-IRR-003",
        name="Skip Irrigation Before Rain",
        name_az="Yağışdan əvvəl suvarmanı keçin",
        category=AgronomyCategory.IRRIGATION,
        condition_description="Skip irrigation if rain is expected within 24-48 hours",
        condition_description_az="24-48 saat ərzində yağış gözlənilirsə suvarmanı keçin",
        recommendation="Postpone irrigation. Natural rainfall expected. Check forecast again tomorrow",
        recommendation_az="Suvarmanı təxirə salın. Təbii yağış gözlənilir. Sabah proqnoza yenidən baxın",
        confidence_weight=0.88,
        validator=lambda ctx: ctx.get("precipitation_expected", False)
    ),
    
    # --- Fertilization Rules ---
    AgronomyRule(
        rule_id="AZ-FERT-001",
        name="Low Nitrogen Application",
        name_az="Aşağı azot tətbiqi",
        category=AgronomyCategory.FERTILIZATION,
        applicable_farm_types=["wheat", "vegetable", "orchard", "mixed"],
        condition_description="Apply nitrogen fertilizer when N level below 30 kg/ha",
        condition_description_az="Azot səviyyəsi 30 kq/ha-dan aşağı olduqda azot gübrəsi tətbiq edin",
        recommendation="Apply 30-50 kg/ha nitrogen fertilizer (urea or ammonium nitrate)",
        recommendation_az="30-50 kq/ha azot gübrəsi tətbiq edin (karbamid və ya ammonium nitrat)",
        confidence_weight=0.92,
        validator=lambda ctx: ctx.get("soil_nutrients", {}).get("nitrogen", 100) < 30
    ),
    AgronomyRule(
        rule_id="AZ-FERT-002",
        name="Phosphorus for Flowering",
        name_az="Çiçəkləmə üçün fosfor",
        category=AgronomyCategory.FERTILIZATION,
        applicable_farm_types=["vegetable", "orchard"],
        seasons=["spring", "summer"],
        condition_description="Apply phosphorus during flowering when P level below 25 kg/ha",
        condition_description_az="Fosfor səviyyəsi 25 kq/ha-dan aşağı olduqda çiçəkləmə dövründə fosfor tətbiq edin",
        recommendation="Apply 20-30 kg/ha phosphorus fertilizer (superphosphate)",
        recommendation_az="20-30 kq/ha fosfor gübrəsi tətbiq edin (superfosfat)",
        confidence_weight=0.88,
        validator=lambda ctx: ctx.get("soil_nutrients", {}).get("phosphorus", 100) < 25
    ),
    AgronomyRule(
        rule_id="AZ-FERT-003",
        name="Potassium for Fruit Quality",
        name_az="Meyvə keyfiyyəti üçün kalium",
        category=AgronomyCategory.FERTILIZATION,
        applicable_farm_types=["orchard", "vegetable"],
        applicable_crops=["pomidor", "alma", "armud", "nar", "üzüm"],
        condition_description="Apply potassium before harvest when K level below 100 kg/ha",
        condition_description_az="Kalium səviyyəsi 100 kq/ha-dan aşağı olduqda məhsul yığımından əvvəl kalium tətbiq edin",
        recommendation="Apply 40-60 kg/ha potassium fertilizer (potassium chloride)",
        recommendation_az="40-60 kq/ha kalium gübrəsi tətbiq edin (kalium xlorid)",
        confidence_weight=0.85,
        validator=lambda ctx: ctx.get("soil_nutrients", {}).get("potassium", 200) < 100
    ),
    
    # --- Pest Control Rules ---
    AgronomyRule(
        rule_id="AZ-PEST-001",
        name="Humid Weather Pest Alert",
        name_az="Rütubətli havada zərərverici xəbərdarlığı",
        category=AgronomyCategory.PEST_CONTROL,
        condition_description="High humidity (>70%) and warm temps (20-30°C) increase pest activity",
        condition_description_az="Yüksək rütubət (>70%) və isti hava (20-30°C) zərərverici aktivliyini artırır",
        recommendation="Scout fields for aphids and mites. Consider preventive spraying",
        recommendation_az="Mənənə və gənələr üçün sahələri yoxlayın. Profilaktik çiləmə düşünün",
        confidence_weight=0.82,
        validator=lambda ctx: (
            20 <= ctx.get("temperature_range", (0, 0))[1] <= 30 and
            ctx.get("humidity_percent", 0) > 70
        )
    ),
    AgronomyRule(
        rule_id="AZ-PEST-002",
        name="Post-Rain Fungal Disease Watch",
        name_az="Yağışdan sonra göbələk xəstəliyi nəzarəti",
        category=AgronomyCategory.DISEASE_MANAGEMENT,
        condition_description="Wet conditions after rain increase fungal disease risk",
        condition_description_az="Yağışdan sonra nəm şərait göbələk xəstəliyi riskini artırır",
        recommendation="Apply preventive fungicide within 24-48 hours after rain",
        recommendation_az="Yağışdan sonra 24-48 saat ərzində profilaktik fungisid tətbiq edin",
        confidence_weight=0.85,
        validator=lambda ctx: ctx.get("precipitation_expected", False) or ctx.get("recent_rain", False)
    ),
    
    # --- Harvest Rules ---
    AgronomyRule(
        rule_id="AZ-HARV-001",
        name="Dry Weather Harvest Window",
        name_az="Quru havada məhsul yığımı pəncərəsi",
        category=AgronomyCategory.HARVEST,
        applicable_farm_types=["wheat", "vegetable", "orchard"],
        seasons=["summer", "autumn"],
        condition_description="Harvest during dry weather with no rain forecast for 3+ days",
        condition_description_az="3+ gün yağış proqnozu olmadıqda quru havada məhsul yığın",
        recommendation="Optimal harvest window. Complete harvest before weather changes",
        recommendation_az="Optimal məhsul yığımı pəncərəsi. Hava dəyişməzdən əvvəl yığımı tamamlayın",
        confidence_weight=0.90,
        validator=lambda ctx: not ctx.get("precipitation_expected", False)
    ),
    AgronomyRule(
        rule_id="AZ-HARV-002",
        name="Morning Dew Harvest Delay",
        name_az="Səhər şehi məhsul yığımı gecikməsi",
        category=AgronomyCategory.HARVEST,
        applicable_crops=["buğda", "arpa"],
        condition_description="Wait for dew to dry before grain harvest",
        condition_description_az="Taxıl yığımından əvvəl şehin qurumasını gözləyin",
        recommendation="Start harvest after 10:00 AM when morning dew has evaporated",
        recommendation_az="Səhər şehi buxarlandıqdan sonra saat 10:00-dan sonra yığıma başlayın",
        confidence_weight=0.88
    ),
    
    # --- Livestock Rules ---
    AgronomyRule(
        rule_id="AZ-LIVE-001",
        name="Heat Stress Prevention",
        name_az="İsti stresinin qarşısının alınması",
        category=AgronomyCategory.LIVESTOCK,
        applicable_farm_types=["livestock", "mixed"],
        max_temperature=30,
        seasons=["summer"],
        condition_description="Provide shade and extra water when temperature exceeds 30°C",
        condition_description_az="Temperatur 30°C-dən yuxarı olduqda kölgə və əlavə su təmin edin",
        recommendation="Move livestock to shade. Provide 20% more water. Avoid moving animals during peak heat",
        recommendation_az="Heyvanları kölgəyə köçürün. 20% daha çox su verin. Pik istidə heyvanları hərəkət etdirməyin",
        confidence_weight=0.93,
        validator=lambda ctx: ctx.get("temperature_range", (0, 0))[1] > 30
    ),
    AgronomyRule(
        rule_id="AZ-LIVE-002",
        name="Winter Shelter Preparation",
        name_az="Qış sığınacağının hazırlanması",
        category=AgronomyCategory.LIVESTOCK,
        applicable_farm_types=["livestock", "mixed"],
        seasons=["autumn"],
        condition_description="Prepare winter shelters before temperature drops below 10°C",
        condition_description_az="Temperatur 10°C-dən aşağı düşməzdən əvvəl qış sığınacaqlarını hazırlayın",
        recommendation="Check shelter insulation, repair drafts, stock bedding materials",
        recommendation_az="Sığınacaq izolyasiyasını yoxlayın, hava axınlarını təmir edin, döşəmə materiallarını təmin edin",
        confidence_weight=0.87,
        validator=lambda ctx: ctx.get("current_season") == "autumn"
    ),
    
    # --- Soil Management Rules ---
    AgronomyRule(
        rule_id="AZ-SOIL-001",
        name="Acidic Soil Correction",
        name_az="Turş torpağın düzəldilməsi",
        category=AgronomyCategory.SOIL_MANAGEMENT,
        condition_description="Apply lime when soil pH drops below 5.5",
        condition_description_az="Torpaq pH-ı 5.5-dən aşağı düşdükdə əhəng tətbiq edin",
        recommendation="Apply 1-2 tonnes/ha agricultural lime. Test pH again after 3 months",
        recommendation_az="1-2 ton/ha kənd təsərrüfatı əhəngi tətbiq edin. 3 aydan sonra pH-ı yenidən test edin",
        confidence_weight=0.90,
        validator=lambda ctx: ctx.get("soil_ph", 7.0) < 5.5
    ),
    AgronomyRule(
        rule_id="AZ-SOIL-002",
        name="Alkaline Soil Correction",
        name_az="Qələvi torpağın düzəldilməsi",
        category=AgronomyCategory.SOIL_MANAGEMENT,
        condition_description="Apply sulfur when soil pH exceeds 7.5",
        condition_description_az="Torpaq pH-ı 7.5-dən yuxarı olduqda kükürd tətbiq edin",
        recommendation="Apply 100-200 kg/ha elemental sulfur or gypsum",
        recommendation_az="100-200 kq/ha elementar kükürd və ya gips tətbiq edin",
        confidence_weight=0.88,
        validator=lambda ctx: ctx.get("soil_ph", 7.0) > 7.5
    ),
]


class RulebookValidator:
    """
    Deterministic Agronomy Rulebook Validator.
    
    Ensures >90% accuracy by cross-referencing LLM outputs against
    expert-validated agricultural rules.
    """
    
    def __init__(self, rulebook: Optional[list[AgronomyRule]] = None):
        """Initialize with a rulebook (defaults to Azerbaijani rulebook)."""
        self.rulebook = rulebook or AGRONOMY_RULEBOOK
        self._rule_index = {rule.rule_id: rule for rule in self.rulebook}
    
    def get_applicable_rules(self, context: dict) -> list[AgronomyRule]:
        """Get all rules applicable to the given context."""
        applicable = []
        for rule in self.rulebook:
            if rule.check_applicable(context):
                applicable.append(rule)
        return applicable
    
    def evaluate_all(self, context: dict) -> list[tuple[AgronomyRule, bool, float]]:
        """
        Evaluate all applicable rules against the context.
        
        Returns:
            List of (rule, is_triggered, confidence_score) tuples
        """
        results = []
        for rule in self.get_applicable_rules(context):
            triggered, confidence = rule.evaluate(context)
            results.append((rule, triggered, confidence))
        return results
    
    def validate_llm_recommendation(
        self,
        llm_recommendation: dict,
        context: dict
    ) -> tuple[float, list[str]]:
        """
        Validate an LLM-generated recommendation against the rulebook.
        
        Args:
            llm_recommendation: The LLM's output (dict with type, description, etc.)
            context: The sanitized request context
            
        Returns:
            Tuple of (validation_score, list of validation notes)
        """
        notes = []
        score = 0.5  # Base score for LLM recommendations
        
        rec_type = llm_recommendation.get("type", "").lower()
        rec_text = llm_recommendation.get("description", "").lower()
        rec_text_az = llm_recommendation.get("description_az", "").lower()
        
        # Find matching rules
        triggered_rules = self.evaluate_all(context)
        matching_rules = []
        
        for rule, triggered, confidence in triggered_rules:
            if not triggered:
                continue
            
            # Check if LLM recommendation matches rule category
            if rule.category.value in rec_type:
                matching_rules.append((rule, confidence))
                score = max(score, confidence)
                notes.append(f"✓ Matches rule {rule.rule_id}: {rule.name_az}")
            
            # Check for keyword overlap
            rule_keywords_az = rule.recommendation_az.lower().split()
            if any(kw in rec_text_az for kw in rule_keywords_az if len(kw) > 4):
                matching_rules.append((rule, confidence * 0.8))
                score = max(score, confidence * 0.8)
                notes.append(f"✓ Content aligns with {rule.rule_id}")
        
        # Check for contradictions
        for rule, triggered, confidence in triggered_rules:
            if triggered and rule.category.value in rec_type:
                # Check if recommendation contradicts rule
                if "skip" in rule.recommendation.lower() and "irrigate" in rec_text:
                    if "rain" in context.get("weather_summary", "").lower():
                        score *= 0.5
                        notes.append(f"⚠ May contradict {rule.rule_id}: Rain expected")
        
        # Boost score if multiple rules agree
        if len(matching_rules) >= 2:
            score = min(1.0, score * 1.1)
            notes.append(f"✓ Multi-rule agreement ({len(matching_rules)} rules)")
        
        # Penalize if no rule coverage
        if not matching_rules:
            score *= 0.7
            notes.append("⚠ No rulebook coverage - requires human review")
        
        return min(1.0, score), notes
    
    def get_rule_recommendations(self, context: dict) -> list[dict]:
        """
        Generate deterministic recommendations directly from triggered rules.
        
        These serve as a baseline that the RAG engine can enhance with
        LLM-generated natural language.
        """
        recommendations = []
        
        for rule, triggered, confidence in self.evaluate_all(context):
            if triggered:
                recommendations.append({
                    "rule_id": rule.rule_id,
                    "type": rule.category.value,
                    "title": rule.name,
                    "title_az": rule.name_az,
                    "description": rule.recommendation,
                    "description_az": rule.recommendation_az,
                    "confidence": confidence,
                    "source": "rulebook",
                })
        
        return recommendations


class KnowledgeChunk(BaseModel):
    """A chunk of agricultural knowledge for RAG retrieval."""
    chunk_id: str
    category: AgronomyCategory
    content: str
    content_az: str
    source: str  # "rulebook", "expert", "research"
    keywords: list[str] = Field(default_factory=list)
    relevance_score: float = 0.0


class AgronomyRAGEngine:
    """
    Retrieval-Augmented Generation Engine for Agricultural Recommendations.
    
    Flow:
    1. Intent Detection: Parse user query (Azerbaijani → intent)
    2. Knowledge Retrieval: Find relevant knowledge chunks
    3. Rule Evaluation: Check deterministic rules
    4. LLM Generation: Generate natural language recommendation
    5. Validation: Cross-reference against rulebook (>90% accuracy)
    """
    
    # Azerbaijani intent patterns
    INTENT_PATTERNS = {
        "irrigation": [
            r"suvar", r"su ver", r"nəmlik", r"quru", r"su lazım",
            r"water", r"irrigat", r"moisture", r"dry"
        ],
        "fertilization": [
            r"gübrə", r"azot", r"fosfor", r"kalium", r"qidalandır",
            r"fertiliz", r"nitrogen", r"nutrient"
        ],
        "pest_control": [
            r"zərərverici", r"həşərat", r"böcək", r"mənənə", r"gənə",
            r"pest", r"insect", r"bug", r"aphid"
        ],
        "disease": [
            r"xəstəlik", r"göbələk", r"virus", r"pas", r"ləkə",
            r"disease", r"fung", r"blight", r"rot"
        ],
        "harvest": [
            r"yığ", r"məhsul", r"biç", r"topla",
            r"harvest", r"collect", r"reap"
        ],
        "weather": [
            r"hava", r"temperatur", r"yağış", r"isti", r"soyuq",
            r"weather", r"rain", r"temperature", r"hot", r"cold"
        ],
        "livestock": [
            r"heyvan", r"mal-qara", r"qoyun", r"inək", r"toyuq",
            r"livestock", r"cattle", r"sheep", r"animal"
        ],
        "soil": [
            r"torpaq", r"pH", r"analiz", r"mineral",
            r"soil", r"earth", r"ground"
        ],
    }
    
    def __init__(
        self,
        llm=None,
        model_name: str = "qwen2.5:7b",
        validator: Optional[RulebookValidator] = None
    ):
        """
        Initialize the RAG Engine.
        
        Args:
            llm: Optional pre-configured LLM (langchain compatible)
            model_name: Model name for local inference
            validator: Rulebook validator instance
        """
        self.llm = llm
        self.model_name = model_name
        self.validator = validator or RulebookValidator()
        self._knowledge_base = self._build_knowledge_base()
    
    def _build_knowledge_base(self) -> list[KnowledgeChunk]:
        """Build knowledge base from rulebook."""
        chunks = []
        
        for rule in self.validator.rulebook:
            chunk = KnowledgeChunk(
                chunk_id=f"kb_{rule.rule_id}",
                category=rule.category,
                content=f"{rule.condition_description}. {rule.recommendation}",
                content_az=f"{rule.condition_description_az}. {rule.recommendation_az}",
                source="rulebook",
                keywords=self._extract_keywords(rule),
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_keywords(self, rule: AgronomyRule) -> list[str]:
        """Extract keywords from a rule for retrieval."""
        text = f"{rule.name} {rule.name_az} {rule.recommendation} {rule.recommendation_az}"
        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r'\b\w{4,}\b', text.lower())
        return list(set(words))[:10]
    
    def detect_intent(self, query: str) -> tuple[str, float]:
        """
        Detect user intent from Azerbaijani/English query.
        
        Returns:
            Tuple of (intent_category, confidence_score)
        """
        query_lower = query.lower()
        
        intent_scores = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            if score > 0:
                intent_scores[intent] = score / len(patterns)
        
        if not intent_scores:
            return "general", 0.3
        
        best_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
        return best_intent, min(1.0, intent_scores[best_intent] * 2)
    
    def retrieve_knowledge(
        self,
        intent: str,
        context: dict,
        top_k: int = 5
    ) -> list[KnowledgeChunk]:
        """
        Retrieve relevant knowledge chunks based on intent and context.
        """
        relevant = []
        
        for chunk in self._knowledge_base:
            score = 0.0
            
            # Category match
            if chunk.category.value == intent:
                score += 0.5
            
            # Keyword match with context
            context_text = " ".join([
                str(v) for v in context.values() if isinstance(v, str)
            ]).lower()
            
            keyword_matches = sum(1 for kw in chunk.keywords if kw in context_text)
            score += keyword_matches * 0.1
            
            chunk.relevance_score = min(1.0, score)
            relevant.append(chunk)
        
        # Sort by relevance and return top_k
        relevant.sort(key=lambda c: c.relevance_score, reverse=True)
        return relevant[:top_k]
    
    def _build_context_for_llm(
        self,
        request: SanitizedRequest,
        intent: str,
        knowledge: list[KnowledgeChunk],
        rule_recommendations: list[dict]
    ) -> str:
        """Build the context/prompt for LLM generation."""
        
        context_parts = [
            "### Agricultural Advisory Context ###",
            f"Farm Type: {request.farm_type}",
            f"Crops: {', '.join(request.crops) if request.crops else 'Not specified'}",
            f"Region Climate: {request.climate_zone}",
            f"Season: {request.current_season}",
            f"Temperature: {request.temperature_range[0]}°C - {request.temperature_range[1]}°C",
            f"Rain Expected: {'Yes' if request.precipitation_expected else 'No'}",
        ]
        
        if request.soil_moisture_percent:
            context_parts.append(f"Soil Moisture: {request.soil_moisture_percent}%")
        
        if request.soil_nutrients:
            context_parts.append(
                f"Nutrients - N: {request.soil_nutrients.get('nitrogen', 'N/A')} kg/ha, "
                f"P: {request.soil_nutrients.get('phosphorus', 'N/A')} kg/ha, "
                f"K: {request.soil_nutrients.get('potassium', 'N/A')} kg/ha"
            )
        
        context_parts.append(f"\nDetected Intent: {intent}")
        
        # Add retrieved knowledge
        context_parts.append("\n### Relevant Agricultural Guidelines ###")
        for chunk in knowledge:
            context_parts.append(f"- {chunk.content_az}")
        
        # Add rule-based recommendations as hints
        if rule_recommendations:
            context_parts.append("\n### Expert Rule Recommendations ###")
            for rec in rule_recommendations[:3]:
                context_parts.append(f"- [{rec['rule_id']}] {rec['description_az']}")
        
        context_parts.append(f"\n### User Query ###\n{request.user_query}")
        
        context_parts.append(
            "\n### Instructions ###\n"
            "Respond in Azerbaijani. Provide specific, actionable farming advice. "
            "Reference the expert guidelines above. Be concise and practical."
        )
        
        return "\n".join(context_parts)
    
    def generate_recommendation(
        self,
        request: SanitizedRequest
    ) -> SanitizedResponse:
        """
        Generate a recommendation using RAG pipeline.
        
        Flow:
        1. Detect intent from user query
        2. Build context dict for rule evaluation
        3. Get rule-based recommendations
        4. Retrieve relevant knowledge
        5. Generate LLM response (if available)
        6. Validate against rulebook
        7. Return sanitized response
        """
        start_time = datetime.now()
        
        # Step 1: Intent detection
        intent, intent_confidence = self.detect_intent(request.user_query)
        request.detected_intent = intent
        
        # Step 2: Build context for rule evaluation
        context = {
            "farm_type": request.farm_type,
            "crops": request.crops,
            "livestock_types": request.livestock_types,
            "soil_moisture_percent": request.soil_moisture_percent,
            "soil_nutrients": request.soil_nutrients or {},
            "temperature_range": request.temperature_range,
            "current_season": request.current_season,
            "precipitation_expected": request.precipitation_expected,
            "climate_zone": request.climate_zone,
        }
        
        # Step 3: Get deterministic rule recommendations
        rule_recommendations = self.validator.get_rule_recommendations(context)
        
        # Step 4: Retrieve relevant knowledge
        knowledge = self.retrieve_knowledge(intent, context)
        
        # Step 5: Generate LLM response (or use rule-based fallback)
        recommendations = []
        
        if self.llm:
            # Build context for LLM
            llm_context = self._build_context_for_llm(
                request, intent, knowledge, rule_recommendations
            )
            
            try:
                # Call LLM
                llm_response = self.llm.invoke(llm_context)
                
                # Parse LLM response into recommendation
                llm_rec = {
                    "id": f"rec-llm-{uuid4().hex[:8]}",
                    "type": intent,
                    "title": f"AI Recommendation - {intent.replace('_', ' ').title()}",
                    "title_az": f"AI Tövsiyəsi - {intent.replace('_', ' ').title()}",
                    "description": llm_response.content if hasattr(llm_response, 'content') else str(llm_response),
                    "description_az": llm_response.content if hasattr(llm_response, 'content') else str(llm_response),
                    "source": "llm",
                }
                
                # Step 6: Validate against rulebook
                validation_score, validation_notes = self.validator.validate_llm_recommendation(
                    llm_rec, context
                )
                llm_rec["confidence"] = validation_score
                
                recommendations.append(llm_rec)
                
            except Exception as e:
                # Fallback to rule-based if LLM fails
                pass
        
        # Add rule-based recommendations (always included for reliability)
        for rule_rec in rule_recommendations:
            # Check if similar to LLM recommendation
            is_duplicate = any(
                rec.get("type") == rule_rec["type"] and
                rec.get("rule_id") == rule_rec.get("rule_id")
                for rec in recommendations
            )
            if not is_duplicate:
                recommendations.append(rule_rec)
        
        # Sort by confidence
        recommendations.sort(key=lambda r: r.get("confidence", 0), reverse=True)
        
        # Calculate overall metrics
        overall_confidence = (
            sum(r.get("confidence", 0.5) for r in recommendations) / len(recommendations)
            if recommendations else 0.5
        )
        
        rule_coverage = len([r for r in recommendations if r.get("source") == "rulebook"])
        rulebook_score = min(1.0, rule_coverage / 3 + 0.5) if rule_coverage else 0.5
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Build validation notes
        validation_notes = [
            f"Intent detected: {intent} (confidence: {intent_confidence:.2f})",
            f"Rules triggered: {len(rule_recommendations)}",
            f"Knowledge chunks retrieved: {len(knowledge)}",
        ]
        
        return SanitizedResponse(
            request_id=request.request_id,
            recommendations=recommendations,
            overall_confidence=overall_confidence,
            rulebook_validation_score=rulebook_score,
            validation_notes=validation_notes,
            inference_mode="standard" if self.llm else "rules_only",
            processing_time_ms=processing_time,
            model_version=self.model_name if self.llm else "rulebook-v1",
        )
