"""
Yonca AI - Sidecar API Routes
=============================

REST API routes for the Sidecar Intelligence Architecture.
Integrates with the existing Yonca API without touching the database.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from yonca.sidecar.recommendation_service import (
    SidecarRecommendationService,
    RecommendationRequest,
    RecommendationResponse,
)
from yonca.sidecar.pii_gateway import PIIGateway
from yonca.sidecar.lite_inference import InferenceMode


# Initialize router
router = APIRouter(prefix="/sidecar", tags=["Sidecar Intelligence"])


# Service singleton (lazy initialization)
_service: Optional[SidecarRecommendationService] = None


def get_service() -> SidecarRecommendationService:
    """Get or create the Sidecar service singleton."""
    global _service
    if _service is None:
        _service = SidecarRecommendationService()
    return _service


# ============= Recommendation Endpoints =============

@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    service: SidecarRecommendationService = Depends(get_service)
):
    """
    🌿 Get AI-powered farm recommendations via Sidecar Intelligence.
    
    **Data Flow:**
    ```
    Request → PII Gateway → RAG Engine → Rulebook Validation → Response
    ```
    
    **Security:**
    - All PII is stripped before processing
    - No real farmer data touches the LLM
    - 100% synthetic data pipeline
    
    **Accuracy:**
    - LLM outputs validated against Azerbaijani Agronomy Rulebook
    - Target accuracy: >90%
    
    **Inference Modes:**
    - `standard`: Full Qwen2.5-7B via Ollama
    - `lite`: Quantized GGUF for edge devices
    - `offline`: Pure rule-based (no LLM)
    
    **Example Request:**
    ```json
    {
        "farm_id": "farm-123",
        "region": "Aran",
        "farm_type": "wheat",
        "crops": ["buğda"],
        "area_hectares": 50,
        "soil_moisture_percent": 25,
        "temperature_max": 35,
        "query": "Nə vaxt suvarmaq lazımdır?"
    }
    ```
    """
    try:
        return service.get_recommendations(request)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Recommendation generation failed: {str(e)}"
        )


@router.get("/status")
async def get_status(
    service: SidecarRecommendationService = Depends(get_service)
):
    """
    📊 Get Sidecar Intelligence service status.
    
    Returns:
    - Current inference mode and capabilities
    - PII Gateway audit summary
    - Rulebook coverage statistics
    """
    return service.get_service_status()


@router.get("/capabilities")
async def get_capabilities(
    service: SidecarRecommendationService = Depends(get_service)
):
    """
    ⚙️ Get current inference capabilities.
    
    Returns:
    - Active inference mode
    - LLM availability
    - Network status
    - Estimated latency
    """
    return service.inference_engine.get_capability().model_dump()


@router.get("/models")
async def get_model_info(
    service: SidecarRecommendationService = Depends(get_service)
):
    """
    🤖 Get information about available models.
    
    Returns:
    - Current model configuration
    - GGUF quantization options
    - Memory requirements
    """
    return service.inference_engine.get_model_info()


@router.post("/mode/{mode}")
async def set_inference_mode(
    mode: str,
    service: SidecarRecommendationService = Depends(get_service)
):
    """
    🔄 Switch inference mode.
    
    **Modes:**
    - `standard`: Full LLM via Ollama (requires network + Ollama running)
    - `lite`: Quantized GGUF (requires GGUF model file)
    - `offline`: Rule-based only (always available)
    - `auto`: Automatically select based on conditions
    
    **Example:**
    ```
    POST /sidecar/mode/lite
    ```
    """
    mode_map = {
        "standard": InferenceMode.STANDARD,
        "lite": InferenceMode.LITE,
        "offline": InferenceMode.OFFLINE,
        "auto": InferenceMode.AUTO,
    }
    
    if mode.lower() not in mode_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode. Choose from: {list(mode_map.keys())}"
        )
    
    service.inference_engine.initialize_llm(mode_map[mode.lower()])
    
    return {
        "message": f"Inference mode switched to: {mode}",
        "capability": service.inference_engine.get_capability().model_dump()
    }


# ============= Rulebook Endpoints =============

@router.get("/rulebook")
async def get_rulebook(
    category: Optional[str] = Query(None, description="Filter by category"),
    service: SidecarRecommendationService = Depends(get_service)
):
    """
    📖 Get the Azerbaijani Agronomy Rulebook.
    
    Returns deterministic agricultural rules used for:
    - LLM output validation
    - Offline/rule-based recommendations
    - Accuracy assurance (>90% target)
    
    **Categories:**
    - irrigation
    - fertilization
    - pest_control
    - disease_management
    - harvest
    - livestock
    - soil_management
    """
    rules = []
    for rule in service.rag_engine.validator.rulebook:
        if category and rule.category.value != category:
            continue
        rules.append({
            "rule_id": rule.rule_id,
            "name": rule.name,
            "name_az": rule.name_az,
            "category": rule.category.value,
            "description": rule.condition_description,
            "description_az": rule.condition_description_az,
            "recommendation": rule.recommendation,
            "recommendation_az": rule.recommendation_az,
            "confidence_weight": rule.confidence_weight,
        })
    
    return {
        "total_rules": len(rules),
        "category_filter": category,
        "rules": rules
    }


@router.get("/rulebook/categories")
async def get_rulebook_categories(
    service: SidecarRecommendationService = Depends(get_service)
):
    """📂 Get available rulebook categories with counts."""
    categories = {}
    for rule in service.rag_engine.validator.rulebook:
        cat = rule.category.value
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "categories": [
            {"name": cat, "count": count}
            for cat, count in sorted(categories.items())
        ]
    }


# ============= Security/Audit Endpoints =============

@router.get("/audit")
async def get_audit_summary(
    service: SidecarRecommendationService = Depends(get_service)
):
    """
    🔒 Get PII Gateway audit summary.
    
    Returns:
    - Total requests processed
    - PII fields stripped (never original values)
    - Detection statistics by type
    
    **Note:** Original PII is NEVER logged or stored.
    Only SHA-256 hashes are retained for audit compliance.
    """
    return service.pii_gateway.get_audit_summary()


# ============= Health Check =============

@router.get("/health")
async def health_check():
    """💚 Health check endpoint."""
    return {
        "status": "healthy",
        "service": "yonca-sidecar-intelligence",
        "version": "1.0.0",
    }
