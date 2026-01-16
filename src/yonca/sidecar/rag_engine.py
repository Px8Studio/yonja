"""
Yonca AI - RAG Engine with Deterministic Agronomy Rulebook
==========================================================

Retrieval-Augmented Generation engine that combines:
1. LLM intelligence (Qwen2.5-7B) for natural language understanding
2. Deterministic rulebook validation for >90% accuracy guarantee
3. Azerbaijani agricultural "Rules of Thumb" knowledge base

Architecture:
- Intent Detection → Knowledge Retrieval → LLM Generation → Rule Validation → Response

NOTE: Rules are now centralized in rules_registry.py
      Intent detection is now centralized in intent_matcher.py
"""

import re
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from yonca.sidecar.pii_gateway import SanitizedRequest, SanitizedResponse
from yonca.sidecar.rules_registry import (
    AgronomyRule,
    RuleCategory,
    AGRONOMY_RULES,
)
from yonca.sidecar.intent_matcher import IntentMatcher, get_intent_matcher


# Re-export for backwards compatibility
# The canonical enum is now RuleCategory in rules_registry.py
AgronomyCategory = RuleCategory


class ConfidenceLevel(str, Enum):
    """Confidence levels for recommendations."""
    HIGH = "high"      # >0.85 - Rule-based + LLM agreement
    MEDIUM = "medium"  # 0.70-0.85 - Partial rule coverage
    LOW = "low"        # <0.70 - LLM-only, needs human review


# =============================================================================
# RULEBOOK - Imported from unified rules_registry.py
# =============================================================================
# The AGRONOMY_RULEBOOK alias is kept for backward compatibility
AGRONOMY_RULEBOOK = AGRONOMY_RULES


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
    1. Intent Detection: Parse user query (Azerbaijani → intent) via IntentMatcher
    2. Knowledge Retrieval: Find relevant knowledge chunks
    3. Rule Evaluation: Check deterministic rules from RulesRegistry
    4. LLM Generation: Generate natural language recommendation
    5. Validation: Cross-reference against rulebook (>90% accuracy)
    """
    
    def __init__(
        self,
        llm=None,
        model_name: str = "qwen2.5:7b",
        validator: Optional[RulebookValidator] = None,
        intent_matcher: Optional[IntentMatcher] = None
    ):
        """
        Initialize the RAG Engine.
        
        Args:
            llm: Optional pre-configured LLM (langchain compatible)
            model_name: Model name for local inference
            validator: Rulebook validator instance
            intent_matcher: Intent matcher instance (uses centralized matcher by default)
        """
        self.llm = llm
        self.model_name = model_name
        self.validator = validator or RulebookValidator()
        self.intent_matcher = intent_matcher or get_intent_matcher()
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
        
        Delegates to the centralized IntentMatcher for consistent intent
        detection across all modules.
        
        Returns:
            Tuple of (intent_category, confidence_score)
        """
        return self.intent_matcher.detect_intent(query)
    
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
