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
]
