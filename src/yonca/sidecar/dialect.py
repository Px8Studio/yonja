"""
Yonca AI - Dialect & Regional Term Handler
==========================================

Linguistic nuance layer for Azerbaijani agricultural terminology.
Handles regional dialects vs. technical Baku vocabulary.

Azerbaijan has diverse regional dialects:
- Aran (lowland) dialect
- Şəki-Zaqatala (mountain) dialect
- Lənkəran (southern) dialect
- Naxçıvan dialect
- Quba-Xaçmaz (northern) dialect

Farmers may use local terms that differ from official/technical terms.
This module normalizes regional variations to standard terms for processing,
then converts responses back to farmer's preferred dialect.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Dialect(str, Enum):
    """Azerbaijani regional dialects."""
    STANDARD = "standard"      # Bakı ədəbi dili (Standard Baku)
    ARAN = "aran"              # Aran bölgəsi
    SEKI_ZAQATALA = "seki"     # Şəki-Zaqatala
    LENKERAN = "lenkeran"      # Lənkəran
    NAXCIVAN = "naxcivan"      # Naxçıvan
    QUBA = "quba"              # Quba-Xaçmaz
    GENCE = "gence"            # Gəncə-Qazax


@dataclass
class TermMapping:
    """Mapping between standard term and regional variants."""
    standard_term: str           # Technical/standard Baku term
    standard_term_en: str        # English equivalent
    category: str                # agricultural category
    regional_variants: dict[Dialect, list[str]] = field(default_factory=dict)
    phonetic_variants: list[str] = field(default_factory=list)  # Common misspellings
    
    def get_all_variants(self) -> list[str]:
        """Get all possible variants including regional and phonetic."""
        variants = [self.standard_term]
        for dialect_terms in self.regional_variants.values():
            variants.extend(dialect_terms)
        variants.extend(self.phonetic_variants)
        return list(set(variants))


# Comprehensive Azerbaijani agricultural term dictionary
AGRICULTURAL_TERMS: list[TermMapping] = [
    # ============= Irrigation Terms =============
    TermMapping(
        standard_term="suvarma",
        standard_term_en="irrigation",
        category="irrigation",
        regional_variants={
            Dialect.ARAN: ["su vermə", "sulama"],
            Dialect.SEKI_ZAQATALA: ["su çəkmə", "suvarmağ"],
            Dialect.LENKERAN: ["sulamaq", "su tökmə"],
            Dialect.QUBA: ["su buraxma", "islatma"],
        },
        phonetic_variants=["suvama", "suvarme", "suvarmaq"],
    ),
    TermMapping(
        standard_term="damcı suvarma",
        standard_term_en="drip irrigation",
        category="irrigation",
        regional_variants={
            Dialect.ARAN: ["damla suvarma", "damlalı su"],
            Dialect.SEKI_ZAQATALA: ["damcılı sistem"],
            Dialect.GENCE: ["damcı sistemi"],
        },
    ),
    TermMapping(
        standard_term="arxlar",
        standard_term_en="irrigation channels",
        category="irrigation",
        regional_variants={
            Dialect.ARAN: ["arıxlar", "su yolları"],
            Dialect.LENKERAN: ["kanallar", "su arxları"],
            Dialect.NAXCIVAN: ["arıq", "su arığı"],
        },
    ),
    
    # ============= Soil Terms =============
    TermMapping(
        standard_term="torpaq",
        standard_term_en="soil",
        category="soil",
        regional_variants={
            Dialect.ARAN: ["yer", "torpax"],
            Dialect.SEKI_ZAQATALA: ["torpağ", "yer üzü"],
            Dialect.NAXCIVAN: ["torpax", "torpaγ"],
        },
        phonetic_variants=["torpak", "torpağ"],
    ),
    TermMapping(
        standard_term="nəmlik",
        standard_term_en="moisture",
        category="soil",
        regional_variants={
            Dialect.ARAN: ["yaşlıq", "rütubət"],
            Dialect.SEKI_ZAQATALA: ["nəmlilik", "islaq"],
            Dialect.LENKERAN: ["rütubətlilik", "yaş"],
        },
        phonetic_variants=["nemlik", "nəmlig"],
    ),
    TermMapping(
        standard_term="gübrə",
        standard_term_en="fertilizer",
        category="fertilization",
        regional_variants={
            Dialect.ARAN: ["gübrə", "peyin"],
            Dialect.SEKI_ZAQATALA: ["kübrə", "dərman"],
            Dialect.LENKERAN: ["güvrə", "qida"],
            Dialect.NAXCIVAN: ["gübrə", "peyini"],
            Dialect.QUBA: ["kübrə", "dərmən"],
        },
        phonetic_variants=["gubre", "gübre", "gübrə"],
    ),
    TermMapping(
        standard_term="azot",
        standard_term_en="nitrogen",
        category="fertilization",
        regional_variants={
            Dialect.ARAN: ["azod", "nitrogen"],
            Dialect.SEKI_ZAQATALA: ["azot gübrəsi"],
        },
    ),
    
    # ============= Pest & Disease Terms =============
    TermMapping(
        standard_term="zərərverici",
        standard_term_en="pest",
        category="pest_control",
        regional_variants={
            Dialect.ARAN: ["zərərli böcək", "həşərat"],
            Dialect.SEKI_ZAQATALA: ["ziyanlı", "böcəklər"],
            Dialect.LENKERAN: ["zərər verən", "həşarat"],
            Dialect.GENCE: ["zərərverən", "böjəklər"],
        },
        phonetic_variants=["zererverici", "zararverici"],
    ),
    TermMapping(
        standard_term="mənənə",
        standard_term_en="aphid",
        category="pest_control",
        regional_variants={
            Dialect.ARAN: ["meyvə biti", "yarpaq biti"],
            Dialect.SEKI_ZAQATALA: ["şirə", "yastıca"],
            Dialect.LENKERAN: ["bit", "bitki biti"],
        },
    ),
    TermMapping(
        standard_term="göbələk xəstəliyi",
        standard_term_en="fungal disease",
        category="disease",
        regional_variants={
            Dialect.ARAN: ["göbələk", "kif"],
            Dialect.SEKI_ZAQATALA: ["mantar xəstəliyi", "kifləmə"],
            Dialect.LENKERAN: ["çürümə", "göbələk xəstəliği"],
        },
    ),
    TermMapping(
        standard_term="pestisid",
        standard_term_en="pesticide",
        category="pest_control",
        regional_variants={
            Dialect.ARAN: ["dərman", "zəhər"],
            Dialect.SEKI_ZAQATALA: ["böcək dərmanı", "çiləmə dərmanı"],
            Dialect.LENKERAN: ["həşərat dərmanı", "spray"],
        },
        phonetic_variants=["pestisit", "pestisid"],
    ),
    
    # ============= Crop Terms =============
    TermMapping(
        standard_term="buğda",
        standard_term_en="wheat",
        category="crops",
        regional_variants={
            Dialect.ARAN: ["buğda", "taxıl"],
            Dialect.SEKI_ZAQATALA: ["buğda", "dən"],
            Dialect.NAXCIVAN: ["buγda", "buğda"],
        },
        phonetic_variants=["bugda", "buqda"],
    ),
    TermMapping(
        standard_term="məhsul",
        standard_term_en="crop/harvest",
        category="harvest",
        regional_variants={
            Dialect.ARAN: ["biçin", "yığım"],
            Dialect.SEKI_ZAQATALA: ["məhsul yığımı", "hösul"],
            Dialect.LENKERAN: ["məsul", "yığma"],
            Dialect.GENCE: ["hasıl", "yığılma"],
        },
        phonetic_variants=["mehsul", "mahsul"],
    ),
    TermMapping(
        standard_term="toxum",
        standard_term_en="seed",
        category="crops",
        regional_variants={
            Dialect.ARAN: ["dən", "tum"],
            Dialect.SEKI_ZAQATALA: ["toxum", "taxıl dəni"],
            Dialect.LENKERAN: ["dənə", "səpilən"],
            Dialect.NAXCIVAN: ["toxum", "toxm"],
        },
        phonetic_variants=["tohum", "toxm"],
    ),
    
    # ============= Weather Terms =============
    TermMapping(
        standard_term="yağış",
        standard_term_en="rain",
        category="weather",
        regional_variants={
            Dialect.ARAN: ["yağmur", "yağıntı"],
            Dialect.SEKI_ZAQATALA: ["yağış", "leysan"],
            Dialect.LENKERAN: ["yağmur", "çiskin"],
        },
        phonetic_variants=["yagis", "yağiş"],
    ),
    TermMapping(
        standard_term="quraqlıq",
        standard_term_en="drought",
        category="weather",
        regional_variants={
            Dialect.ARAN: ["susuzluq", "quru hava"],
            Dialect.SEKI_ZAQATALA: ["quraxlıq", "yağışsızlıq"],
            Dialect.LENKERAN: ["susuzluğ", "quraqlığ"],
        },
    ),
    TermMapping(
        standard_term="şaxta",
        standard_term_en="frost",
        category="weather",
        regional_variants={
            Dialect.ARAN: ["soyuq", "don"],
            Dialect.SEKI_ZAQATALA: ["şaxda", "ayaz"],
            Dialect.NAXCIVAN: ["şaxta", "buz"],
        },
    ),
    
    # ============= Livestock Terms =============
    TermMapping(
        standard_term="mal-qara",
        standard_term_en="cattle",
        category="livestock",
        regional_variants={
            Dialect.ARAN: ["inək-öküz", "qaramal"],
            Dialect.SEKI_ZAQATALA: ["sığır", "mal"],
            Dialect.NAXCIVAN: ["mal", "böyükbaş"],
        },
    ),
    TermMapping(
        standard_term="qoyun",
        standard_term_en="sheep",
        category="livestock",
        regional_variants={
            Dialect.ARAN: ["qoyun", "quzulu"],
            Dialect.SEKI_ZAQATALA: ["quzu-qoyun", "sürü"],
            Dialect.NAXCIVAN: ["qoyun-quzu", "xırdabaş"],
        },
    ),
    TermMapping(
        standard_term="yem",
        standard_term_en="feed/fodder",
        category="livestock",
        regional_variants={
            Dialect.ARAN: ["ot", "saman"],
            Dialect.SEKI_ZAQATALA: ["yemlik", "ot-yem"],
            Dialect.LENKERAN: ["yeməlik", "otlaq"],
        },
    ),
    
    # ============= Action Terms =============
    TermMapping(
        standard_term="əkmək",
        standard_term_en="to plant/sow",
        category="action",
        regional_variants={
            Dialect.ARAN: ["səpmək", "basdırmaq"],
            Dialect.SEKI_ZAQATALA: ["əkmağ", "taxmaq"],
            Dialect.LENKERAN: ["əkib-becərmək", "səpmə"],
        },
    ),
    TermMapping(
        standard_term="biçmək",
        standard_term_en="to harvest/reap",
        category="action",
        regional_variants={
            Dialect.ARAN: ["yığmaq", "kəsmək"],
            Dialect.SEKI_ZAQATALA: ["toplamaq", "biçmağ"],
            Dialect.LENKERAN: ["yığışdırmaq", "götürmək"],
        },
    ),
    TermMapping(
        standard_term="çiləmək",
        standard_term_en="to spray",
        category="action",
        regional_variants={
            Dialect.ARAN: ["püskürtmək", "vurmaq"],
            Dialect.SEKI_ZAQATALA: ["dərmanlama", "çiləmağ"],
            Dialect.LENKERAN: ["sprayla vermək", "səpmək"],
        },
    ),
]


class DialectHandler:
    """
    Handler for Azerbaijani dialect normalization and conversion.
    
    Workflow:
    1. Farmer input → normalize() → Standard Azerbaijani
    2. AI Processing in Standard Azerbaijani
    3. AI Response → localize() → Farmer's preferred dialect
    """
    
    # Region to dialect mapping
    REGION_DIALECT_MAP = {
        "Aran": Dialect.ARAN,
        "Mil-Muğan": Dialect.ARAN,
        "Şirvan": Dialect.ARAN,
        "Şəki-Zaqatala": Dialect.SEKI_ZAQATALA,
        "Lənkəran": Dialect.LENKERAN,
        "Naxçıvan": Dialect.NAXCIVAN,
        "Quba-Xaçmaz": Dialect.QUBA,
        "Gəncə-Qazax": Dialect.GENCE,
        "Abşeron": Dialect.STANDARD,
    }
    
    def __init__(self, terms: list[TermMapping] = None):
        """
        Initialize the dialect handler.
        
        Args:
            terms: List of term mappings (defaults to AGRICULTURAL_TERMS)
        """
        self.terms = terms or AGRICULTURAL_TERMS
        self._build_indices()
    
    def _build_indices(self):
        """Build lookup indices for fast normalization."""
        # Variant to standard term mapping
        self._variant_to_standard: dict[str, str] = {}
        
        # Standard to regional variants
        self._standard_to_variants: dict[str, dict[Dialect, list[str]]] = {}
        
        # Category index
        self._terms_by_category: dict[str, list[TermMapping]] = {}
        
        for term in self.terms:
            # Index standard term
            self._standard_to_variants[term.standard_term] = term.regional_variants
            
            # Index all variants pointing to standard
            for variant in term.get_all_variants():
                self._variant_to_standard[variant.lower()] = term.standard_term
            
            # Index by category
            cat = term.category
            if cat not in self._terms_by_category:
                self._terms_by_category[cat] = []
            self._terms_by_category[cat].append(term)
    
    def detect_dialect(self, text: str, region: Optional[str] = None) -> Dialect:
        """
        Detect the dialect used in input text.
        
        Args:
            text: Input text
            region: Optional region hint
            
        Returns:
            Detected or inferred Dialect
        """
        # If region is provided, use mapping
        if region and region in self.REGION_DIALECT_MAP:
            return self.REGION_DIALECT_MAP[region]
        
        # Otherwise, detect from vocabulary
        text_lower = text.lower()
        dialect_scores = {d: 0 for d in Dialect}
        
        for term in self.terms:
            for dialect, variants in term.regional_variants.items():
                for variant in variants:
                    if variant.lower() in text_lower:
                        dialect_scores[dialect] += 1
        
        # Find highest scoring dialect
        if max(dialect_scores.values()) > 0:
            return max(dialect_scores, key=dialect_scores.get)
        
        return Dialect.STANDARD
    
    def normalize(self, text: str, source_dialect: Optional[Dialect] = None) -> str:
        """
        Normalize regional dialect text to standard Azerbaijani.
        
        Args:
            text: Input text (possibly in regional dialect)
            source_dialect: Known source dialect (optional)
            
        Returns:
            Text with regional terms replaced by standard terms
        """
        normalized = text
        
        # Sort by length (longest first) to avoid partial replacements
        variants_sorted = sorted(
            self._variant_to_standard.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for variant, standard in variants_sorted:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(variant), re.IGNORECASE)
            normalized = pattern.sub(standard, normalized)
        
        return normalized
    
    def localize(
        self,
        text: str,
        target_dialect: Dialect,
        preserve_technical: bool = True
    ) -> str:
        """
        Convert standard Azerbaijani text to a regional dialect.
        
        Args:
            text: Input text in standard Azerbaijani
            target_dialect: Target regional dialect
            preserve_technical: If True, keep technical terms as-is
            
        Returns:
            Text with standard terms replaced by regional variants
        """
        if target_dialect == Dialect.STANDARD:
            return text
        
        localized = text
        
        for standard_term, variants in self._standard_to_variants.items():
            if target_dialect in variants and variants[target_dialect]:
                # Use first variant as default
                regional_term = variants[target_dialect][0]
                
                # Check if we should preserve technical terms
                if preserve_technical:
                    # Look up if this is a technical term
                    term_obj = next(
                        (t for t in self.terms if t.standard_term == standard_term),
                        None
                    )
                    if term_obj and term_obj.category in ["fertilization", "disease"]:
                        continue  # Keep technical terms
                
                # Replace standard with regional
                pattern = re.compile(re.escape(standard_term), re.IGNORECASE)
                localized = pattern.sub(regional_term, localized)
        
        return localized
    
    def get_term_info(self, term: str) -> Optional[dict]:
        """
        Get information about a term (standard or variant).
        
        Args:
            term: The term to look up
            
        Returns:
            Dict with term information or None
        """
        term_lower = term.lower()
        
        # Check if it's a known variant
        standard = self._variant_to_standard.get(term_lower)
        if not standard:
            return None
        
        # Find the full term mapping
        term_obj = next(
            (t for t in self.terms if t.standard_term == standard),
            None
        )
        
        if not term_obj:
            return None
        
        return {
            "input_term": term,
            "standard_term": term_obj.standard_term,
            "english": term_obj.standard_term_en,
            "category": term_obj.category,
            "regional_variants": {
                d.value: v for d, v in term_obj.regional_variants.items()
            },
        }
    
    def suggest_corrections(self, text: str) -> list[dict]:
        """
        Suggest corrections for potentially misspelled terms.
        
        Args:
            text: Input text
            
        Returns:
            List of suggested corrections
        """
        suggestions = []
        words = text.lower().split()
        
        for word in words:
            # Check if word is similar to any known term
            for term in self.terms:
                all_variants = term.get_all_variants()
                
                for variant in all_variants:
                    # Simple Levenshtein-like check (within 2 edits)
                    if self._is_similar(word, variant.lower(), max_distance=2):
                        if word != variant.lower():
                            suggestions.append({
                                "original": word,
                                "suggested": variant,
                                "standard": term.standard_term,
                                "english": term.standard_term_en,
                            })
                        break
        
        return suggestions
    
    def _is_similar(self, s1: str, s2: str, max_distance: int = 2) -> bool:
        """Check if two strings are within max_distance edits."""
        if abs(len(s1) - len(s2)) > max_distance:
            return False
        
        # Simple check: count character differences
        if len(s1) != len(s2):
            return False
        
        differences = sum(c1 != c2 for c1, c2 in zip(s1, s2))
        return differences <= max_distance
    
    def get_dialect_for_region(self, region: str) -> Dialect:
        """Get the typical dialect for a region."""
        return self.REGION_DIALECT_MAP.get(region, Dialect.STANDARD)
    
    def get_category_vocabulary(self, category: str) -> list[dict]:
        """Get all terms for a category with their variants."""
        terms = self._terms_by_category.get(category, [])
        
        return [
            {
                "standard": t.standard_term,
                "english": t.standard_term_en,
                "variants": {d.value: v for d, v in t.regional_variants.items()},
            }
            for t in terms
        ]


class MultilingualIntentMatcher:
    """
    Intent matching that handles Azerbaijani dialects and English.
    
    Normalizes input to standard form before intent classification.
    """
    
    def __init__(self, dialect_handler: Optional[DialectHandler] = None):
        self.dialect_handler = dialect_handler or DialectHandler()
        
        # Intent patterns in standard Azerbaijani
        self.intent_patterns = {
            "irrigation": [
                "suvar", "su ver", "nəmlik", "quru", "yaş", "rütubət",
                "water", "irrigat", "moisture", "dry", "wet"
            ],
            "fertilization": [
                "gübrə", "azot", "fosfor", "kalium", "qidalandır",
                "fertiliz", "nitrogen", "nutrient", "npk"
            ],
            "pest_control": [
                "zərərverici", "həşərat", "böcək", "mənənə", "gənə",
                "pest", "insect", "bug", "aphid", "mite"
            ],
            "disease": [
                "xəstəlik", "göbələk", "virus", "pas", "ləkə", "çürümə",
                "disease", "fung", "blight", "rot", "mold"
            ],
            "harvest": [
                "biçmək", "yığmaq", "məhsul", "toplama",
                "harvest", "collect", "reap", "pick"
            ],
            "weather": [
                "hava", "yağış", "temperatur", "isti", "soyuq", "şaxta",
                "weather", "rain", "temperature", "hot", "cold", "frost"
            ],
            "livestock": [
                "heyvan", "mal-qara", "qoyun", "inək", "toyuq", "yem",
                "livestock", "cattle", "sheep", "animal", "feed"
            ],
            "soil": [
                "torpaq", "pH", "analiz", "mineral", "struktur",
                "soil", "earth", "ground", "analysis"
            ],
        }
    
    def match_intent(
        self,
        text: str,
        region: Optional[str] = None
    ) -> tuple[str, float, str]:
        """
        Match user intent from text with dialect normalization.
        
        Args:
            text: User input text
            region: Optional region for dialect detection
            
        Returns:
            Tuple of (intent, confidence, normalized_text)
        """
        # Detect and normalize dialect
        dialect = self.dialect_handler.detect_dialect(text, region)
        normalized = self.dialect_handler.normalize(text)
        
        # Match against intent patterns
        text_lower = normalized.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in text_lower:
                    score += 1
            if score > 0:
                intent_scores[intent] = score / len(patterns)
        
        if not intent_scores:
            return "general", 0.3, normalized
        
        best_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
        confidence = min(1.0, intent_scores[best_intent] * 2)
        
        return best_intent, confidence, normalized
