"""
Yonca AI - Sidecar Recommendation Service
==========================================

Unified service that orchestrates:
1. PII Gateway (data sanitization)
2. RAG Engine (intelligent recommendations)
3. Lite-Inference (edge/offline support)

This is the main entry point for the Sidecar Intelligence Architecture.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from yonca.sidecar.pii_gateway import PIIGateway, SanitizedRequest, SanitizedResponse
from yonca.sidecar.rag_engine import AgronomyRAGEngine, RulebookValidator
from yonca.sidecar.lite_inference import (
    LiteInferenceEngine, 
    InferenceMode,
    EdgeDeploymentConfig,
    create_lite_engine_for_edge,
)


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationRequest(BaseModel):
    """
    API request for farm recommendations.
    
    This is the external-facing request model.
    Real farm/farmer IDs are accepted here and will be
    sanitized by the PII Gateway before processing.
    """
    # Identifiers (will be sanitized)
    farm_id: str = Field(..., description="Farm identifier")
    farmer_id: Optional[str] = Field(None, description="Farmer identifier (optional)")
    farmer_name: Optional[str] = Field(None, description="Farmer name for personalization")
    
    # Location (will be anonymized to region code)
    region: str = Field(..., description="Farm region in Azerbaijan")
    
    # Farm characteristics (safe categorical data)
    farm_type: str = Field(..., description="Type of farm: wheat, vegetable, orchard, livestock, mixed")
    crops: list[str] = Field(default_factory=list, description="List of crops grown")
    livestock_types: list[str] = Field(default_factory=list, description="Types of livestock")
    area_hectares: float = Field(..., gt=0, description="Farm area in hectares")
    
    # Environmental data (safe numerical data)
    soil_type: Optional[str] = Field(None, description="Soil type classification")
    soil_moisture_percent: Optional[int] = Field(None, ge=0, le=100, description="Current soil moisture")
    soil_ph: Optional[float] = Field(None, ge=0, le=14, description="Soil pH level")
    nitrogen_level: Optional[float] = Field(None, ge=0, description="Nitrogen level kg/ha")
    phosphorus_level: Optional[float] = Field(None, ge=0, description="Phosphorus level kg/ha")
    potassium_level: Optional[float] = Field(None, ge=0, description="Potassium level kg/ha")
    
    # Weather context
    temperature_min: Optional[float] = Field(None, description="Minimum temperature °C")
    temperature_max: Optional[float] = Field(None, description="Maximum temperature °C")
    precipitation_expected: bool = Field(False, description="Is rain/snow expected?")
    humidity_percent: Optional[int] = Field(None, ge=0, le=100, description="Current humidity")
    
    # User query
    query: str = Field("", description="User's question in Azerbaijani or English")
    language: str = Field("az", description="Preferred response language: az, en, ru")
    
    # Options
    max_recommendations: int = Field(5, ge=1, le=20, description="Maximum number of recommendations")
    include_rulebook_refs: bool = Field(True, description="Include rulebook references in response")
    inference_mode: Optional[str] = Field(None, description="Force inference mode: standard, lite, offline")


class RecommendationItem(BaseModel):
    """A single recommendation item."""
    id: str = Field(default_factory=lambda: f"rec-{uuid4().hex[:8]}")
    type: str = Field(..., description="Recommendation type: irrigation, fertilization, etc.")
    priority: RecommendationPriority = Field(default=RecommendationPriority.MEDIUM)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    
    # Content
    title: str = Field(..., description="Recommendation title")
    title_az: str = Field(..., description="Title in Azerbaijani")
    description: str = Field(..., description="Detailed recommendation")
    description_az: str = Field(..., description="Description in Azerbaijani")
    
    # Metadata
    source: str = Field(..., description="Source: llm, rulebook, hybrid")
    rule_id: Optional[str] = Field(None, description="Related rulebook rule ID")
    
    # Action guidance
    suggested_time: Optional[str] = Field(None, description="Best time to perform action")
    estimated_duration_minutes: Optional[int] = Field(None, description="Estimated time needed")


class RecommendationResponse(BaseModel):
    """
    API response with farm recommendations.
    
    Includes recommendations, confidence scores, and metadata.
    """
    # Request tracking
    request_id: str = Field(..., description="Unique request identifier")
    farm_id: str = Field(..., description="Farm identifier (from request)")
    
    # Recommendations
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    
    # Quality metrics
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Rulebook validation score (>0.9 target)")
    
    # Validation
    validation_notes: list[str] = Field(default_factory=list, description="Validation details")
    
    # Metadata
    inference_mode: str = Field(..., description="Inference mode used")
    model_version: str = Field(..., description="Model version used")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    
    # Timestamps
    generated_at: datetime = Field(default_factory=datetime.now)
    valid_until: Optional[datetime] = Field(None, description="Recommendation validity period")


class SidecarRecommendationService:
    """
    Main service class for the Sidecar Intelligence Architecture.
    
    Orchestrates the complete flow:
    1. Request → PII Gateway → SanitizedRequest
    2. SanitizedRequest → RAG Engine → SanitizedResponse
    3. SanitizedResponse → PII Gateway → Personalized Response
    
    Usage:
        service = SidecarRecommendationService()
        response = service.get_recommendations(request)
    """
    
    def __init__(
        self,
        pii_gateway: Optional[PIIGateway] = None,
        rag_engine: Optional[AgronomyRAGEngine] = None,
        inference_engine: Optional[LiteInferenceEngine] = None,
        edge_config: Optional[EdgeDeploymentConfig] = None,
    ):
        """
        Initialize the Sidecar Recommendation Service.
        
        Args:
            pii_gateway: PII Gateway instance (created if None)
            rag_engine: RAG Engine instance (created if None)
            inference_engine: Lite-Inference Engine (created if None)
            edge_config: Edge deployment configuration
        """
        self.pii_gateway = pii_gateway or PIIGateway(enable_audit_log=True)
        
        # Initialize inference engine
        if inference_engine:
            self.inference_engine = inference_engine
        elif edge_config:
            self.inference_engine = create_lite_engine_for_edge(edge_config)
        else:
            self.inference_engine = LiteInferenceEngine(
                preferred_mode=InferenceMode.AUTO
            )
        
        # Initialize RAG engine with the inference LLM
        if rag_engine:
            self.rag_engine = rag_engine
        else:
            self.rag_engine = AgronomyRAGEngine(
                llm=self.inference_engine.llm,
                validator=RulebookValidator(),
            )
    
    def _build_soil_data(self, request: RecommendationRequest) -> Optional[dict]:
        """Extract soil data from request."""
        if not any([
            request.soil_type,
            request.soil_moisture_percent,
            request.soil_ph,
            request.nitrogen_level,
        ]):
            return None
        
        return {
            "soil_type": request.soil_type,
            "moisture_percent": request.soil_moisture_percent,
            "ph_level": request.soil_ph,
            "nitrogen_level": request.nitrogen_level or 0,
            "phosphorus_level": request.phosphorus_level or 0,
            "potassium_level": request.potassium_level or 0,
        }
    
    def _build_weather_context(self, request: RecommendationRequest) -> Optional[dict]:
        """Extract weather context from request."""
        season = self._detect_season()
        climate_zone = self._region_to_climate(request.region)
        
        return {
            "climate_zone": climate_zone,
            "season": season,
            "temp_min": request.temperature_min or 10,
            "temp_max": request.temperature_max or 25,
            "rain_expected": request.precipitation_expected,
            "humidity_percent": request.humidity_percent,
        }
    
    def _detect_season(self) -> str:
        """Detect current season from date."""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        return "autumn"
    
    def _region_to_climate(self, region: str) -> str:
        """Map region to climate zone."""
        climate_map = {
            "Aran": "semi-arid",
            "Şəki-Zaqatala": "humid",
            "Lənkəran": "subtropical",
            "Abşeron": "semi-arid",
            "Gəncə-Qazax": "temperate",
            "Mil-Muğan": "semi-arid",
            "Şirvan": "semi-arid",
            "Quba-Xaçmaz": "temperate",
        }
        return climate_map.get(region, "temperate")
    
    def _priority_from_confidence(self, confidence: float) -> RecommendationPriority:
        """Determine priority from confidence score."""
        if confidence >= 0.9:
            return RecommendationPriority.CRITICAL
        elif confidence >= 0.8:
            return RecommendationPriority.HIGH
        elif confidence >= 0.6:
            return RecommendationPriority.MEDIUM
        return RecommendationPriority.LOW
    
    def get_recommendations(
        self,
        request: RecommendationRequest
    ) -> RecommendationResponse:
        """
        Get AI-powered farm recommendations.
        
        Complete pipeline:
        1. Sanitize request through PII Gateway
        2. Process through RAG Engine
        3. Personalize response through PII Gateway
        
        Args:
            request: The recommendation request
            
        Returns:
            Personalized recommendation response
        """
        start_time = datetime.now()
        
        # Override inference mode if specified
        if request.inference_mode:
            mode_map = {
                "standard": InferenceMode.STANDARD,
                "lite": InferenceMode.LITE,
                "offline": InferenceMode.OFFLINE,
            }
            if request.inference_mode.lower() in mode_map:
                self.inference_engine.initialize_llm(mode_map[request.inference_mode.lower()])
        
        # Step 1: Sanitize request through PII Gateway
        sanitized_request = self.pii_gateway.sanitize(
            farm_id=request.farm_id,
            farmer_id=request.farmer_id or f"farmer-{request.farm_id}",
            region=request.region,
            farm_type=request.farm_type,
            crops=request.crops,
            livestock_types=request.livestock_types,
            area_hectares=request.area_hectares,
            user_query=request.query,
            soil_data=self._build_soil_data(request),
            weather_context=self._build_weather_context(request),
            language=request.language,
        )
        
        # Step 2: Process through RAG Engine
        sanitized_response = self.rag_engine.generate_recommendation(sanitized_request)
        
        # Step 3: Personalize response through PII Gateway
        personalized = self.pii_gateway.personalize(
            response=sanitized_response,
            original_farm_id=request.farm_id,
            original_farmer_name=request.farmer_name,
        )
        
        # Build recommendation items
        recommendation_items = []
        for rec in personalized.get("recommendations", [])[:request.max_recommendations]:
            item = RecommendationItem(
                id=rec.get("id", f"rec-{uuid4().hex[:8]}"),
                type=rec.get("type", "general"),
                priority=self._priority_from_confidence(rec.get("confidence", 0.5)),
                confidence=rec.get("confidence", 0.5),
                title=rec.get("title", "Recommendation"),
                title_az=rec.get("title_az", "Tövsiyə"),
                description=rec.get("description", ""),
                description_az=rec.get("description_az", ""),
                source=rec.get("source", "hybrid"),
                rule_id=rec.get("rule_id") if request.include_rulebook_refs else None,
            )
            recommendation_items.append(item)
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return RecommendationResponse(
            request_id=sanitized_response.request_id,
            farm_id=request.farm_id,
            recommendations=recommendation_items,
            overall_confidence=personalized.get("confidence", 0.5),
            accuracy_score=personalized.get("accuracy_score", 0.5),
            validation_notes=personalized.get("validation_notes", []),
            inference_mode=sanitized_response.inference_mode,
            model_version=sanitized_response.model_version,
            processing_time_ms=processing_time,
            generated_at=datetime.now(),
            valid_until=datetime.now().replace(hour=23, minute=59, second=59),
        )
    
    def get_service_status(self) -> dict:
        """Get current service status and capabilities."""
        capability = self.inference_engine.get_capability()
        audit = self.pii_gateway.get_audit_summary()
        
        return {
            "status": "operational",
            "inference": {
                "current_mode": capability.mode.value,
                "has_llm": capability.has_llm,
                "has_network": capability.has_network,
                "estimated_latency_ms": capability.estimated_latency_ms,
            },
            "security": {
                "pii_gateway": "active",
                "total_requests_processed": audit["total_requests"],
                "pii_fields_stripped": audit["total_pii_fields_stripped"],
            },
            "accuracy": {
                "rulebook_rules": len(self.rag_engine.validator.rulebook),
                "target_accuracy": ">90%",
            },
        }


# ============= FastAPI Integration =============

def create_sidecar_router():
    """
    Create FastAPI router for Sidecar Intelligence API.
    
    Endpoints:
    - POST /sidecar/recommendations - Get AI recommendations
    - GET /sidecar/status - Service status
    - GET /sidecar/capabilities - Inference capabilities
    """
    from fastapi import APIRouter, HTTPException
    
    router = APIRouter(prefix="/sidecar", tags=["Sidecar Intelligence"])
    
    # Initialize service (singleton)
    service = SidecarRecommendationService()
    
    @router.post("/recommendations", response_model=RecommendationResponse)
    async def get_recommendations(request: RecommendationRequest):
        """
        Get AI-powered farm recommendations.
        
        This endpoint processes the request through:
        1. PII Gateway (data sanitization)
        2. RAG Engine (intelligent recommendations)
        3. Rulebook Validation (accuracy assurance)
        
        Supports multiple inference modes:
        - standard: Full LLM inference via Ollama
        - lite: Quantized GGUF for edge devices
        - offline: Pure rule-based fallback
        """
        try:
            return service.get_recommendations(request)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/status")
    async def get_status():
        """Get service status and health information."""
        return service.get_service_status()
    
    @router.get("/capabilities")
    async def get_capabilities():
        """Get current inference capabilities."""
        return service.inference_engine.get_capability().model_dump()
    
    @router.get("/models")
    async def get_model_info():
        """Get information about available models."""
        return service.inference_engine.get_model_info()
    
    return router


# ============= GraphQL Integration =============

def create_sidecar_graphql_types():
    """
    Create Strawberry GraphQL types for Sidecar Intelligence.
    
    Returns types for:
    - RecommendationQuery
    - RecommendationMutation
    """
    import strawberry
    from typing import List
    
    @strawberry.type
    class GQLRecommendationItem:
        id: str
        type: str
        priority: str
        confidence: float
        title: str
        title_az: str
        description: str
        description_az: str
        source: str
        rule_id: str | None
    
    @strawberry.type
    class GQLRecommendationResponse:
        request_id: str
        farm_id: str
        recommendations: List[GQLRecommendationItem]
        overall_confidence: float
        accuracy_score: float
        inference_mode: str
        model_version: str
        processing_time_ms: int
    
    @strawberry.input
    class GQLRecommendationInput:
        farm_id: str
        region: str
        farm_type: str
        crops: List[str] = strawberry.field(default_factory=list)
        area_hectares: float = 10.0
        query: str = ""
        language: str = "az"
        soil_moisture_percent: int | None = None
        temperature_max: float | None = None
        precipitation_expected: bool = False
    
    return GQLRecommendationItem, GQLRecommendationResponse, GQLRecommendationInput
