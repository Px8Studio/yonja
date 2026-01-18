# src/yonca/api/routes/models.py
"""API routes for LLM model management.

Provides endpoints to list available models, check model status,
and switch between models (for UI selection).
"""

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from yonca.config import Settings, get_settings
from yonca.llm.models import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    LocalModel,
    ModelSource,
    get_model_info,
)

router = APIRouter(prefix="/models", tags=["models"])


# ============================================================
# Response Models
# ============================================================


class ModelInfo(BaseModel):
    """Model information for API response."""

    name: str
    display_name: str
    description: str
    source: str
    size_gb: float
    languages: list[str]
    recommended_ram_gb: int
    is_available: bool = False
    is_active: bool = False


class ModelListResponse(BaseModel):
    """Response for listing all models."""

    models: list[ModelInfo]
    active_model: str
    default_model: str


class ModelStatusResponse(BaseModel):
    """Response for model status check."""

    name: str
    is_available: bool
    is_active: bool
    error: str | None = None


class SwitchModelRequest(BaseModel):
    """Request to switch active model."""

    model_name: str


class SwitchModelResponse(BaseModel):
    """Response for model switch."""

    success: bool
    active_model: str
    message: str


# ============================================================
# Helper Functions
# ============================================================


async def check_model_available(
    model_name: str,
    ollama_base_url: str,
) -> bool:
    """Check if a model is available in Ollama."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                available_models = [m["name"] for m in data.get("models", [])]
                # Check both exact match and without tag
                return (
                    model_name in available_models
                    or any(m.startswith(model_name.split(":")[0]) for m in available_models)
                )
    except httpx.HTTPError:
        pass
    return False


def model_to_response(
    model: LocalModel,
    is_available: bool,
    active_model: str,
) -> ModelInfo:
    """Convert LocalModel to API response."""
    return ModelInfo(
        name=model.name,
        display_name=model.display_name,
        description=model.description,
        source=model.source.value,
        size_gb=model.size_gb,
        languages=model.languages,
        recommended_ram_gb=model.recommended_ram_gb,
        is_available=is_available,
        is_active=model.name == active_model,
    )


# ============================================================
# API Endpoints
# ============================================================


@router.get("", response_model=ModelListResponse)
async def list_models(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ModelListResponse:
    """List all available local LLM models.
    
    Returns information about all registered models including:
    - Whether they are available (pulled/imported in Ollama)
    - Whether they are currently active
    """
    models_info: list[ModelInfo] = []
    active_model = settings.ollama_model
    
    for model in AVAILABLE_MODELS.values():
        is_available = await check_model_available(
            model.name,
            settings.ollama_base_url,
        )
        models_info.append(
            model_to_response(model, is_available, active_model)
        )
    
    return ModelListResponse(
        models=models_info,
        active_model=active_model,
        default_model=DEFAULT_MODEL,
    )


@router.get("/{model_name}", response_model=ModelStatusResponse)
async def get_model_status(
    model_name: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ModelStatusResponse:
    """Get status of a specific model."""
    model = get_model_info(model_name)
    
    if not model:
        # Check if it's a valid Ollama model even if not in registry
        is_available = await check_model_available(
            model_name,
            settings.ollama_base_url,
        )
        return ModelStatusResponse(
            name=model_name,
            is_available=is_available,
            is_active=model_name == settings.ollama_model,
            error=None if is_available else "Model not found in registry or Ollama",
        )
    
    is_available = await check_model_available(
        model.name,
        settings.ollama_base_url,
    )
    
    return ModelStatusResponse(
        name=model.name,
        is_available=is_available,
        is_active=model.name == settings.ollama_model,
    )


@router.get("/active", response_model=ModelStatusResponse)
async def get_active_model(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ModelStatusResponse:
    """Get the currently active model."""
    active_model = settings.ollama_model
    is_available = await check_model_available(
        active_model,
        settings.ollama_base_url,
    )
    
    return ModelStatusResponse(
        name=active_model,
        is_available=is_available,
        is_active=True,
    )


@router.post("/pull/{model_name}")
async def pull_model(
    model_name: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Trigger model pull from Ollama Hub.
    
    Note: This only works for models with source=OLLAMA_HUB.
    GGUF models must be imported using the import_model.py script.
    """
    model = get_model_info(model_name)
    
    if model and model.source == ModelSource.GGUF_IMPORT:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model_name}' is a GGUF import. Use 'python scripts/import_model.py --name {model_name}' instead.",
        )
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout for pulling
            response = await client.post(
                f"{settings.ollama_base_url}/api/pull",
                json={"name": model_name},
            )
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Model '{model_name}' pulled successfully",
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to pull model: {response.text}",
                )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Model pull timed out. Try pulling directly with: ollama pull " + model_name,
        ) from exc
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pull model: {str(e)}",
        ) from e
