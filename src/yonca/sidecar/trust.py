"""
Yonca AI - Trust Score & Citation System
========================================

Transparency layer for AI recommendations.
Every recommendation includes:
- Confidence score with breakdown
- Source citations (rulebook, guidelines, expert validation)
- Explainability traces

"Sourced from: Yonca Wheat Guideline v2"
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SourceType(str, Enum):
    """Types of sources for recommendations."""
    RULEBOOK = "rulebook"           # Internal agronomy rulebook
    GUIDELINE = "guideline"         # Published guidelines
    EXPERT_VALIDATED = "expert"     # Human expert verification
    RESEARCH_PAPER = "research"     # Academic research
    HISTORICAL_DATA = "historical"  # Historical farm data
    WEATHER_SERVICE = "weather"     # Weather service data
    GOVERNMENT = "government"       # Government agricultural standards
    AI_INFERENCE = "ai_inference"   # AI model inference (lower trust)


class ConfidenceLevel(str, Enum):
    """Confidence levels for recommendations."""
    VERY_HIGH = "very_high"   # 90-100%: Rule-based, expert validated
    HIGH = "high"             # 75-89%: Strong evidence
    MODERATE = "moderate"     # 60-74%: Good evidence with caveats
    LOW = "low"               # 40-59%: Limited evidence
    EXPERIMENTAL = "experimental"  # <40%: Speculative, needs validation


@dataclass
class Citation:
    """A single source citation."""
    source_id: str
    source_type: SourceType
    title: str
    title_en: Optional[str] = None
    version: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    url: Optional[str] = None
    date_published: Optional[datetime] = None
    reliability_score: float = 0.8  # 0-1 scale
    
    def to_citation_string(self, language: str = "az") -> str:
        """Format as a readable citation."""
        parts = []
        
        if language == "az":
            title = self.title
        else:
            title = self.title_en or self.title
        
        parts.append(title)
        
        if self.version:
            parts.append(f"v{self.version}")
        
        if self.section:
            if language == "az":
                parts.append(f"Bölmə: {self.section}")
            else:
                parts.append(f"Section: {self.section}")
        
        return ", ".join(parts)
    
    def get_badge(self) -> str:
        """Get a visual badge for the source type."""
        badges = {
            SourceType.RULEBOOK: "📘",
            SourceType.GUIDELINE: "📗",
            SourceType.EXPERT_VALIDATED: "👨‍🔬",
            SourceType.RESEARCH_PAPER: "📄",
            SourceType.HISTORICAL_DATA: "📊",
            SourceType.WEATHER_SERVICE: "🌤️",
            SourceType.GOVERNMENT: "🏛️",
            SourceType.AI_INFERENCE: "🤖",
        }
        return badges.get(self.source_type, "📌")


@dataclass
class ConfidenceBreakdown:
    """Detailed breakdown of confidence score."""
    rule_match_score: float = 0.0       # How well it matches rulebook
    source_quality_score: float = 0.0   # Quality of sources
    expert_validation_score: float = 0.0 # Expert verification level
    temporal_relevance_score: float = 0.0 # Seasonal/timing relevance
    regional_relevance_score: float = 0.0 # Region-specific accuracy
    
    def calculate_overall(self) -> float:
        """Calculate weighted overall confidence."""
        weights = {
            "rule_match": 0.30,
            "source_quality": 0.25,
            "expert_validation": 0.20,
            "temporal_relevance": 0.15,
            "regional_relevance": 0.10,
        }
        
        overall = (
            self.rule_match_score * weights["rule_match"] +
            self.source_quality_score * weights["source_quality"] +
            self.expert_validation_score * weights["expert_validation"] +
            self.temporal_relevance_score * weights["temporal_relevance"] +
            self.regional_relevance_score * weights["regional_relevance"]
        )
        
        return min(1.0, max(0.0, overall))
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """Get confidence level from overall score."""
        overall = self.calculate_overall()
        
        if overall >= 0.90:
            return ConfidenceLevel.VERY_HIGH
        elif overall >= 0.75:
            return ConfidenceLevel.HIGH
        elif overall >= 0.60:
            return ConfidenceLevel.MODERATE
        elif overall >= 0.40:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.EXPERIMENTAL


@dataclass
class TrustScore:
    """
    Complete trust score for a recommendation.
    
    Provides full transparency about confidence and sources.
    """
    recommendation_id: str
    overall_confidence: float
    confidence_level: ConfidenceLevel
    breakdown: ConfidenceBreakdown
    citations: list[Citation] = field(default_factory=list)
    primary_source: Optional[Citation] = None
    warnings: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    explanation_trace: list[str] = field(default_factory=list)
    
    def get_confidence_badge(self) -> str:
        """Get visual confidence badge."""
        badges = {
            ConfidenceLevel.VERY_HIGH: "✅ Çox Yüksək Etibarlılıq",
            ConfidenceLevel.HIGH: "🟢 Yüksək Etibarlılıq",
            ConfidenceLevel.MODERATE: "🟡 Orta Etibarlılıq",
            ConfidenceLevel.LOW: "🟠 Aşağı Etibarlılıq",
            ConfidenceLevel.EXPERIMENTAL: "🔴 Eksperimental",
        }
        return badges.get(self.confidence_level, "⚪ Naməlum")
    
    def format_citation_block(self, language: str = "az") -> str:
        """Format all citations as a readable block."""
        if not self.citations:
            if language == "az":
                return "📚 Mənbələr: AI təhlili"
            return "📚 Sources: AI analysis"
        
        lines = []
        if language == "az":
            lines.append("📚 Mənbələr:")
        else:
            lines.append("📚 Sources:")
        
        for i, citation in enumerate(self.citations[:3], 1):  # Top 3 sources
            badge = citation.get_badge()
            citation_str = citation.to_citation_string(language)
            lines.append(f"  {i}. {badge} {citation_str}")
        
        if len(self.citations) > 3:
            remaining = len(self.citations) - 3
            if language == "az":
                lines.append(f"  ... və daha {remaining} mənbə")
            else:
                lines.append(f"  ... and {remaining} more sources")
        
        return "\n".join(lines)
    
    def to_transparency_report(self, language: str = "az") -> str:
        """Generate full transparency report."""
        sections = []
        
        # Confidence section
        badge = self.get_confidence_badge()
        pct = int(self.overall_confidence * 100)
        
        if language == "az":
            sections.append(f"🎯 Etibarlılıq: {pct}% - {badge}")
        else:
            sections.append(f"🎯 Confidence: {pct}% - {badge}")
        
        # Breakdown
        if language == "az":
            sections.append("\n📊 Təhlil:")
            sections.append(f"  • Qayda uyğunluğu: {int(self.breakdown.rule_match_score * 100)}%")
            sections.append(f"  • Mənbə keyfiyyəti: {int(self.breakdown.source_quality_score * 100)}%")
            sections.append(f"  • Ekspert təsdiqi: {int(self.breakdown.expert_validation_score * 100)}%")
            sections.append(f"  • Mövsüm uyğunluğu: {int(self.breakdown.temporal_relevance_score * 100)}%")
            sections.append(f"  • Bölgə uyğunluğu: {int(self.breakdown.regional_relevance_score * 100)}%")
        else:
            sections.append("\n📊 Analysis Breakdown:")
            sections.append(f"  • Rule match: {int(self.breakdown.rule_match_score * 100)}%")
            sections.append(f"  • Source quality: {int(self.breakdown.source_quality_score * 100)}%")
            sections.append(f"  • Expert validation: {int(self.breakdown.expert_validation_score * 100)}%")
            sections.append(f"  • Seasonal relevance: {int(self.breakdown.temporal_relevance_score * 100)}%")
            sections.append(f"  • Regional relevance: {int(self.breakdown.regional_relevance_score * 100)}%")
        
        # Citations
        sections.append("\n" + self.format_citation_block(language))
        
        # Warnings
        if self.warnings:
            sections.append("")
            if language == "az":
                sections.append("⚠️ Xəbərdarlıqlar:")
            else:
                sections.append("⚠️ Warnings:")
            for w in self.warnings:
                sections.append(f"  • {w}")
        
        # Caveats
        if self.caveats:
            sections.append("")
            if language == "az":
                sections.append("💡 Qeydlər:")
            else:
                sections.append("💡 Notes:")
            for c in self.caveats:
                sections.append(f"  • {c}")
        
        return "\n".join(sections)


# Pre-defined citation library
YONCA_CITATION_LIBRARY: dict[str, Citation] = {
    "AZ-IRR-001": Citation(
        source_id="AZ-IRR-001",
        source_type=SourceType.RULEBOOK,
        title="Yonca Suvarma Təlimatı",
        title_en="Yonca Irrigation Guidelines",
        version="2.1",
        section="Torpaq Nəmliyi İdarəetməsi",
        reliability_score=0.95,
    ),
    "AZ-FERT-001": Citation(
        source_id="AZ-FERT-001",
        source_type=SourceType.RULEBOOK,
        title="Yonca Gübrələmə Standartları",
        title_en="Yonca Fertilization Standards",
        version="2.0",
        section="Azot Tətbiqi",
        reliability_score=0.95,
    ),
    "AZ-PEST-001": Citation(
        source_id="AZ-PEST-001",
        source_type=SourceType.RULEBOOK,
        title="Yonca Zərərverici Nəzarəti",
        title_en="Yonca Pest Control Guide",
        version="1.5",
        section="Mənənə Mübarizəsi",
        reliability_score=0.90,
    ),
    "GOV-AG-2024": Citation(
        source_id="GOV-AG-2024",
        source_type=SourceType.GOVERNMENT,
        title="Azərbaycan Kənd Təsərrüfatı Standartları",
        title_en="Azerbaijan Agricultural Standards",
        version="2024",
        date_published=datetime(2024, 1, 1),
        reliability_score=0.92,
    ),
    "WHEAT-GUIDE-V2": Citation(
        source_id="WHEAT-GUIDE-V2",
        source_type=SourceType.GUIDELINE,
        title="Yonca Buğda Bələdçisi",
        title_en="Yonca Wheat Guideline",
        version="2.0",
        reliability_score=0.90,
    ),
    "COTTON-GUIDE-V1": Citation(
        source_id="COTTON-GUIDE-V1",
        source_type=SourceType.GUIDELINE,
        title="Yonca Pambıq Bələdçisi",
        title_en="Yonca Cotton Guideline",
        version="1.2",
        reliability_score=0.88,
    ),
    "GRAPE-GUIDE-V1": Citation(
        source_id="GRAPE-GUIDE-V1",
        source_type=SourceType.GUIDELINE,
        title="Yonca Üzümçülük Bələdçisi",
        title_en="Yonca Viticulture Guideline",
        version="1.0",
        reliability_score=0.85,
    ),
    "AZ-METEO": Citation(
        source_id="AZ-METEO",
        source_type=SourceType.WEATHER_SERVICE,
        title="Milli Hidrometeorologiya Xidməti",
        title_en="National Hydrometeorology Service",
        url="https://meteo.az",
        reliability_score=0.88,
    ),
    "ANAS-SOIL-2023": Citation(
        source_id="ANAS-SOIL-2023",
        source_type=SourceType.RESEARCH_PAPER,
        title="AMEA Torpaqşünaslıq Tədqiqatları",
        title_en="ANAS Soil Science Research",
        version="2023",
        reliability_score=0.85,
    ),
}


class TrustScoreCalculator:
    """
    Calculates trust scores for recommendations.
    
    Provides transparency and traceability for all AI outputs.
    """
    
    def __init__(self, citation_library: Optional[dict[str, Citation]] = None):
        """
        Initialize the trust score calculator.
        
        Args:
            citation_library: Custom citation library (defaults to YONCA_CITATION_LIBRARY)
        """
        self.citation_library = citation_library or YONCA_CITATION_LIBRARY
    
    def calculate_trust_score(
        self,
        recommendation_id: str,
        rule_ids: list[str],
        intent: str,
        region: str,
        season: str,
        expert_validated: bool = False,
        ai_confidence: float = 0.7
    ) -> TrustScore:
        """
        Calculate trust score for a recommendation.
        
        Args:
            recommendation_id: Unique recommendation identifier
            rule_ids: List of matched rule IDs
            intent: Detected user intent
            region: Farm region
            season: Current season
            expert_validated: Whether expert has validated
            ai_confidence: Raw AI confidence score
            
        Returns:
            Complete TrustScore
        """
        # Gather citations
        citations = self._gather_citations(rule_ids, intent)
        
        # Calculate breakdown
        breakdown = self._calculate_breakdown(
            rule_ids=rule_ids,
            citations=citations,
            expert_validated=expert_validated,
            region=region,
            season=season,
            ai_confidence=ai_confidence
        )
        
        # Determine warnings and caveats
        warnings, caveats = self._generate_warnings_caveats(
            breakdown, region, season, intent
        )
        
        # Build explanation trace
        trace = self._build_explanation_trace(
            rule_ids, intent, region, season
        )
        
        # Create trust score
        overall = breakdown.calculate_overall()
        confidence_level = breakdown.get_confidence_level()
        
        return TrustScore(
            recommendation_id=recommendation_id,
            overall_confidence=overall,
            confidence_level=confidence_level,
            breakdown=breakdown,
            citations=citations,
            primary_source=citations[0] if citations else None,
            warnings=warnings,
            caveats=caveats,
            explanation_trace=trace,
        )
    
    def _gather_citations(
        self,
        rule_ids: list[str],
        intent: str
    ) -> list[Citation]:
        """Gather relevant citations for the recommendation."""
        citations = []
        
        # Add citations from matched rules
        for rule_id in rule_ids:
            # Map rule categories to citation IDs
            if "IRR" in rule_id:
                citation_id = "AZ-IRR-001"
            elif "FERT" in rule_id:
                citation_id = "AZ-FERT-001"
            elif "PEST" in rule_id:
                citation_id = "AZ-PEST-001"
            else:
                citation_id = "GOV-AG-2024"
            
            if citation_id in self.citation_library:
                citation = self.citation_library[citation_id]
                if citation not in citations:
                    citations.append(citation)
        
        # Add intent-specific citations
        intent_citations = {
            "irrigation": ["AZ-IRR-001", "AZ-METEO"],
            "fertilization": ["AZ-FERT-001", "ANAS-SOIL-2023"],
            "pest_control": ["AZ-PEST-001"],
            "harvest": ["WHEAT-GUIDE-V2", "COTTON-GUIDE-V1"],
        }
        
        for citation_id in intent_citations.get(intent, []):
            if citation_id in self.citation_library:
                citation = self.citation_library[citation_id]
                if citation not in citations:
                    citations.append(citation)
        
        # Sort by reliability
        citations.sort(key=lambda c: c.reliability_score, reverse=True)
        
        return citations
    
    def _calculate_breakdown(
        self,
        rule_ids: list[str],
        citations: list[Citation],
        expert_validated: bool,
        region: str,
        season: str,
        ai_confidence: float
    ) -> ConfidenceBreakdown:
        """Calculate detailed confidence breakdown."""
        # Rule match score
        if len(rule_ids) >= 2:
            rule_match = 0.95
        elif len(rule_ids) == 1:
            rule_match = 0.80
        else:
            rule_match = ai_confidence * 0.6
        
        # Source quality score
        if citations:
            source_quality = sum(c.reliability_score for c in citations) / len(citations)
        else:
            source_quality = 0.5  # AI-only inference
        
        # Expert validation score
        if expert_validated:
            expert_score = 1.0
        elif rule_ids:
            expert_score = 0.7  # Rules are pre-validated
        else:
            expert_score = 0.4
        
        # Temporal relevance (placeholder - would use actual season logic)
        temporal_score = 0.85 if season else 0.6
        
        # Regional relevance (placeholder - would check region-specific data)
        regional_score = 0.80 if region else 0.6
        
        return ConfidenceBreakdown(
            rule_match_score=rule_match,
            source_quality_score=source_quality,
            expert_validation_score=expert_score,
            temporal_relevance_score=temporal_score,
            regional_relevance_score=regional_score,
        )
    
    def _generate_warnings_caveats(
        self,
        breakdown: ConfidenceBreakdown,
        region: str,
        season: str,
        intent: str
    ) -> tuple[list[str], list[str]]:
        """Generate warnings and caveats based on analysis."""
        warnings = []
        caveats = []
        
        # Low confidence warnings
        overall = breakdown.calculate_overall()
        if overall < 0.6:
            warnings.append(
                "Bu tövsiyə aşağı etibarlılığa malikdir. "
                "Mütəxəssislə məsləhətləşmə tövsiyə olunur."
            )
        
        # Temporal warnings
        if breakdown.temporal_relevance_score < 0.7:
            caveats.append(
                "Mövsüm uyğunluğu tam deyil - yerli şəraitə uyğunlaşdırın."
            )
        
        # Regional warnings
        if breakdown.regional_relevance_score < 0.7:
            caveats.append(
                "Bu tövsiyə bölgənizə tam uyğunlaşdırılmayıb."
            )
        
        # Intent-specific caveats
        if intent == "pesticide":
            caveats.append(
                "Pestisid istifadəsi zamanı təhlükəsizlik təlimatlarına əməl edin."
            )
        
        return warnings, caveats
    
    def _build_explanation_trace(
        self,
        rule_ids: list[str],
        intent: str,
        region: str,
        season: str
    ) -> list[str]:
        """Build explanation trace for transparency."""
        trace = []
        
        trace.append(f"1. Sorğu niyyəti təyin edildi: {intent}")
        
        if rule_ids:
            trace.append(f"2. Qaydalar tapıldı: {', '.join(rule_ids)}")
        else:
            trace.append("2. Uyğun qayda tapılmadı - AI təhlili istifadə edildi")
        
        trace.append(f"3. Bölgə konteksti: {region or 'müəyyən edilmədi'}")
        trace.append(f"4. Mövsüm konteksti: {season or 'müəyyən edilmədi'}")
        
        return trace
    
    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """Get a citation by ID."""
        return self.citation_library.get(citation_id)
    
    def add_custom_citation(self, citation: Citation):
        """Add a custom citation to the library."""
        self.citation_library[citation.source_id] = citation
