"""
Yonca AI - Sidecar Intelligence Architecture
============================================

High-Security AgTech Module for Sovereign AI-driven farm recommendations.
100% synthetic data pipeline with "Ready-to-Plug" national ecosystem integration.

Architecture Components:
- PII Gateway: Zero-trust data sanitization layer
- RAG Engine: Retrieval-Augmented Generation with agronomy rulebook
- Lite-Inference: Edge-optimized GGUF quantization support
- Multilingual: Azerbaijani intent ↔ English/Azerbaijani logic processing

Strategic Enhancements:
- Agronomist-in-the-Loop: Human expert validation system
- Dialect Handler: Regional Azerbaijani term normalization
- Temporal State: Farm timeline memory for contextual advice
- Trust Scores: Confidence scoring with source citations
- Digital Twin: Simulation engine for scenario planning

Author: Digital Umbrella
License: MIT
"""

from yonca.sidecar.pii_gateway import PIIGateway, SanitizedRequest, SanitizedResponse
from yonca.sidecar.rag_engine import AgronomyRAGEngine, RulebookValidator
from yonca.sidecar.lite_inference import LiteInferenceEngine, InferenceMode
from yonca.sidecar.recommendation_service import (
    SidecarRecommendationService,
    RecommendationRequest as SidecarRecommendationRequest,
    RecommendationResponse as SidecarRecommendationResponse,
)

# Strategic Enhancement Modules
from yonca.sidecar.validation import (
    AgronomistInTheLoopValidator,
    ValidationTier,
    ValidationStatus,
)
from yonca.sidecar.dialect import DialectHandler, Dialect, MultilingualIntentMatcher
from yonca.sidecar.temporal import (
    TemporalStateManager,
    TemporalContext,
    FarmAction,
    ActionType,
)
from yonca.sidecar.trust import TrustScoreCalculator, TrustScore, Citation, ConfidenceLevel
from yonca.sidecar.digital_twin import (
    DigitalTwinSimulator,
    SimulationParameters,
    SimulationOutcome,
    SimulationMode,
    CropType,
)

__all__ = [
    # PII Gateway
    "PIIGateway",
    "SanitizedRequest",
    "SanitizedResponse",
    # RAG Engine
    "AgronomyRAGEngine",
    "RulebookValidator",
    # Lite Inference
    "LiteInferenceEngine",
    "InferenceMode",
    # Recommendation Service
    "SidecarRecommendationService",
    "SidecarRecommendationRequest",
    "SidecarRecommendationResponse",
    # Agronomist-in-the-Loop
    "AgronomistInTheLoopValidator",
    "ValidationTier",
    "ValidationStatus",
    # Dialect Handler
    "DialectHandler",
    "Dialect",
    "MultilingualIntentMatcher",
    # Temporal State
    "TemporalStateManager",
    "TemporalContext",
    "FarmAction",
    "ActionType",
    # Trust Scores
    "TrustScoreCalculator",
    "TrustScore",
    "Citation",
    "ConfidenceLevel",
    # Digital Twin
    "DigitalTwinSimulator",
    "SimulationParameters",
    "SimulationOutcome",
    "SimulationMode",
    "CropType",
]
