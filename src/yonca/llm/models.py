# src/yonca/llm/models.py
"""Local LLM model registry and configuration.

This module defines the available local LLM models that can be used with Ollama.
Both pulled models (from Ollama Hub) and imported GGUF models are supported.
"""

from enum import Enum
from typing import NamedTuple


class ModelSource(str, Enum):
    """Source of the model."""

    OLLAMA_HUB = "ollama_hub"  # Pulled via `ollama pull`
    GGUF_IMPORT = "gguf_import"  # Imported from GGUF file via Modelfile


class LocalModel(NamedTuple):
    """Definition of a local LLM model."""

    name: str  # Model name/tag in Ollama
    display_name: str  # Human-readable name for UI
    description: str  # Model description
    source: ModelSource  # Where the model comes from
    size_gb: float  # Approximate model size in GB
    languages: list[str]  # Supported languages (ISO codes)
    recommended_ram_gb: int  # Minimum recommended RAM
    gguf_path: str | None = None  # Path to GGUF file (for imported models)


# ============================================================
# Available Local Models Registry
# ============================================================

AVAILABLE_MODELS: dict[str, LocalModel] = {
    # --------------------------------------------------------
    # Qwen3 Models (Pulled from Ollama Hub)
    # Excellent multilingual support including Azerbaijani
    # --------------------------------------------------------
    "qwen3:4b": LocalModel(
        name="qwen3:4b",
        display_name="Qwen3 4B",
        description="Alibaba's Qwen3 4B parameter model. Excellent balance of speed and quality with strong multilingual capabilities including Azerbaijani.",
        source=ModelSource.OLLAMA_HUB,
        size_gb=2.6,
        languages=["en", "az", "tr", "ru", "zh", "ar"],
        recommended_ram_gb=8,
    ),
    "qwen3:1.7b": LocalModel(
        name="qwen3:1.7b",
        display_name="Qwen3 1.7B (Fast)",
        description="Lightweight Qwen3 model. Faster responses with good quality for simpler tasks.",
        source=ModelSource.OLLAMA_HUB,
        size_gb=1.2,
        languages=["en", "az", "tr", "ru", "zh", "ar"],
        recommended_ram_gb=4,
    ),
    "qwen3:8b": LocalModel(
        name="qwen3:8b",
        display_name="Qwen3 8B (Quality)",
        description="Larger Qwen3 model for higher quality responses. Better reasoning capabilities.",
        source=ModelSource.OLLAMA_HUB,
        size_gb=5.0,
        languages=["en", "az", "tr", "ru", "zh", "ar"],
        recommended_ram_gb=16,
    ),
    # --------------------------------------------------------
    # ATLLaMA - Azerbaijani-Tuned LLaMA (GGUF Import)
    # Fine-tuned for Azerbaijani language
    # --------------------------------------------------------
    "atllama": LocalModel(
        name="atllama",
        display_name="ATLLaMA 3.5 (Azerbaijani)",
        description="LLaMA model fine-tuned specifically for Azerbaijani language. Best for native Azerbaijani content generation.",
        source=ModelSource.GGUF_IMPORT,
        size_gb=2.5,
        languages=["az", "en", "tr"],
        recommended_ram_gb=8,
        gguf_path="models/atllama.v3.5.Q4_K_M.gguf",
    ),
    # --------------------------------------------------------
    # Other Multilingual Models
    # --------------------------------------------------------
    "aya:8b": LocalModel(
        name="aya:8b",
        display_name="Aya 8B (Multilingual)",
        description="Cohere's Aya model with strong multilingual support across 100+ languages.",
        source=ModelSource.OLLAMA_HUB,
        size_gb=4.8,
        languages=["en", "az", "tr", "ru", "ar", "fa"],
        recommended_ram_gb=16,
    ),
}

# Default model to use
DEFAULT_MODEL = "qwen3:4b"


def get_model_info(model_name: str) -> LocalModel | None:
    """Get model information by name."""
    return AVAILABLE_MODELS.get(model_name)


def get_available_model_names() -> list[str]:
    """Get list of available model names."""
    return list(AVAILABLE_MODELS.keys())


def get_models_for_language(language: str) -> list[LocalModel]:
    """Get models that support a specific language."""
    return [model for model in AVAILABLE_MODELS.values() if language in model.languages]


def get_gguf_models() -> list[LocalModel]:
    """Get models that require GGUF import."""
    return [model for model in AVAILABLE_MODELS.values() if model.source == ModelSource.GGUF_IMPORT]


def get_pullable_models() -> list[LocalModel]:
    """Get models that can be pulled from Ollama Hub."""
    return [model for model in AVAILABLE_MODELS.values() if model.source == ModelSource.OLLAMA_HUB]
