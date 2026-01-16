"""
Yonca AI - Unified Intent Detection
===================================

Single source of truth for Azerbaijani/English agricultural intent detection.
Consolidates patterns from dialect.py and rag_engine.py.

This module provides:
- Intent patterns for Azerbaijani (standard + regional) and English
- Dialect-aware normalization before matching
- Confidence scoring
"""

import re
from dataclasses import dataclass
from typing import Optional

# Import dialect handler for normalization (optional dependency)
try:
    from yonca.sidecar.dialect import DialectHandler
    _HAS_DIALECT_HANDLER = True
except ImportError:
    _HAS_DIALECT_HANDLER = False
    DialectHandler = None  # type: ignore


@dataclass
class IntentMatch:
    """Result of intent matching."""
    intent: str
    confidence: float
    normalized_query: str
    matched_patterns: list[str]
    detected_dialect: Optional[str] = None


# =============================================================================
# UNIFIED INTENT PATTERNS
# =============================================================================
# Comprehensive patterns covering:
# - Standard Azerbaijani terms
# - Regional dialect variations
# - English equivalents
# - Common variations and suffixes

INTENT_PATTERNS: dict[str, list[str]] = {
    "irrigation": [
        # Azerbaijani standard
        "suvar", "su ver", "nəmlik", "quru", "yaş", "rütubət",
        "su lazım", "sulama", "su çəkmə", "islatma",
        # Regional variations
        "su vermə", "su tökmə", "su buraxma",
        # English
        "water", "irrigat", "moisture", "dry", "wet", "watering",
    ],
    "fertilization": [
        # Azerbaijani
        "gübrə", "azot", "fosfor", "kalium", "qidalandır",
        "kübrə", "güvrə", "peyin", "dərman",
        # English
        "fertiliz", "nitrogen", "nutrient", "npk", "phosph", "potass",
        "manure", "compost",
    ],
    "pest_control": [
        # Azerbaijani
        "zərərverici", "həşərat", "böcək", "mənənə", "gənə",
        "ziyanlı", "bit", "həşarat",
        # English
        "pest", "insect", "bug", "aphid", "mite", "infestation",
        "spray", "pesticide",
    ],
    "disease": [
        # Azerbaijani
        "xəstəlik", "göbələk", "virus", "pas", "ləkə", "çürümə",
        "kif", "mantar", "kifləmə",
        # English
        "disease", "fung", "blight", "rot", "mold", "infection",
        "wilting", "yellowing",
    ],
    "harvest": [
        # Azerbaijani
        "biçmək", "yığmaq", "məhsul", "toplama", "biçin", "yığım",
        "hösul", "yığışdırmaq", "götürmək",
        # English
        "harvest", "collect", "reap", "pick", "gathering", "yield",
    ],
    "weather": [
        # Azerbaijani
        "hava", "yağış", "temperatur", "isti", "soyuq", "şaxta",
        "yağmur", "yağıntı", "leysan", "çiskin", "don", "ayaz",
        # English
        "weather", "rain", "temperature", "hot", "cold", "frost",
        "forecast", "storm", "drought",
    ],
    "livestock": [
        # Azerbaijani
        "heyvan", "mal-qara", "qoyun", "inək", "toyuq", "yem",
        "sığır", "quzu", "sürü", "xırdabaş", "böyükbaş",
        # English
        "livestock", "cattle", "sheep", "animal", "feed", "poultry",
        "cow", "goat", "chicken",
    ],
    "soil": [
        # Azerbaijani
        "torpaq", "pH", "analiz", "mineral", "struktur",
        "yer", "torpağ", "torpax",
        # English
        "soil", "earth", "ground", "analysis", "acidity", "alkaline",
    ],
    "planting": [
        # Azerbaijani
        "əkmək", "səpmək", "toxum", "dən", "basdırmaq",
        "əkib-becərmək", "səpilən", "tum",
        # English
        "plant", "seed", "sow", "germinate", "transplant",
    ],
}


class IntentMatcher:
    """
    Unified intent matcher for Azerbaijani/English agricultural queries.
    
    Features:
    - Dialect-aware normalization (optional)
    - Pattern-based matching with confidence scoring
    - Support for both Azerbaijani and English
    """
    
    def __init__(
        self,
        patterns: Optional[dict[str, list[str]]] = None,
        dialect_handler: Optional["DialectHandler"] = None,
        use_dialect_normalization: bool = True
    ):
        """
        Initialize the intent matcher.
        
        Args:
            patterns: Custom intent patterns (defaults to INTENT_PATTERNS)
            dialect_handler: DialectHandler for normalization (auto-created if None)
            use_dialect_normalization: Whether to normalize dialects before matching
        """
        self.patterns = patterns or INTENT_PATTERNS
        self._compile_patterns()
        
        # Set up dialect handling
        self.use_dialect_normalization = use_dialect_normalization and _HAS_DIALECT_HANDLER
        if self.use_dialect_normalization:
            self.dialect_handler = dialect_handler or DialectHandler()
        else:
            self.dialect_handler = None
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self._compiled_patterns: dict[str, list[re.Pattern]] = {}
        for intent, patterns in self.patterns.items():
            self._compiled_patterns[intent] = [
                re.compile(rf"\b{re.escape(p)}", re.IGNORECASE)
                for p in patterns
            ]
    
    def match(
        self,
        query: str,
        region: Optional[str] = None
    ) -> IntentMatch:
        """
        Match intent from query with full analysis.
        
        Args:
            query: User query in Azerbaijani or English
            region: Optional region hint for dialect detection
            
        Returns:
            IntentMatch with full details
        """
        # Normalize dialect if enabled
        normalized_query = query
        detected_dialect = None
        
        if self.dialect_handler and self.use_dialect_normalization:
            detected_dialect = self.dialect_handler.detect_dialect(query, region).value
            normalized_query = self.dialect_handler.normalize(query)
        
        # Match against patterns
        query_lower = normalized_query.lower()
        intent_scores: dict[str, float] = {}
        matched_patterns: dict[str, list[str]] = {}
        
        for intent, compiled in self._compiled_patterns.items():
            score = 0
            matches = []
            for i, pattern in enumerate(compiled):
                if pattern.search(query_lower):
                    score += 1
                    matches.append(self.patterns[intent][i])
            
            if score > 0:
                # Normalize score by pattern count
                intent_scores[intent] = score / len(compiled)
                matched_patterns[intent] = matches
        
        # Find best intent
        if not intent_scores:
            return IntentMatch(
                intent="general",
                confidence=0.3,
                normalized_query=normalized_query,
                matched_patterns=[],
                detected_dialect=detected_dialect,
            )
        
        best_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
        confidence = min(1.0, intent_scores[best_intent] * 2)  # Scale up
        
        return IntentMatch(
            intent=best_intent,
            confidence=confidence,
            normalized_query=normalized_query,
            matched_patterns=matched_patterns.get(best_intent, []),
            detected_dialect=detected_dialect,
        )
    
    def detect_intent(self, query: str) -> tuple[str, float]:
        """
        Simple interface for intent detection (backward compatible).
        
        Args:
            query: User query
            
        Returns:
            Tuple of (intent_category, confidence_score)
        """
        result = self.match(query)
        return result.intent, result.confidence
    
    def get_all_patterns(self, intent: str) -> list[str]:
        """Get all patterns for an intent category."""
        return self.patterns.get(intent, [])
    
    def add_patterns(self, intent: str, patterns: list[str]):
        """Add patterns to an intent category."""
        if intent not in self.patterns:
            self.patterns[intent] = []
        self.patterns[intent].extend(patterns)
        # Recompile
        self._compile_patterns()


# =============================================================================
# MODULE-LEVEL UTILITIES
# =============================================================================

# Default singleton matcher
_default_matcher: Optional[IntentMatcher] = None


def get_intent_matcher() -> IntentMatcher:
    """Get the default intent matcher singleton."""
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = IntentMatcher()
    return _default_matcher


def detect_intent(query: str) -> tuple[str, float]:
    """Convenience function for simple intent detection."""
    return get_intent_matcher().detect_intent(query)


def match_intent(query: str, region: Optional[str] = None) -> IntentMatch:
    """Convenience function for full intent matching."""
    return get_intent_matcher().match(query, region)
