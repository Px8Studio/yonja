# Yonca AI Package
"""Yonca - Agricultural Intelligence Platform for Azerbaijan."""

from yonca.models import (
    # Enums
    FarmType,
    SoilType,
    CropStage,
    LivestockType,
    WeatherCondition,
    TaskStatus,
    TaskPriority,
    AlertSeverity,
    # Core models
    Location,
    FarmProfile,
    CropInfo,
    LivestockInfo,
    SoilData,
    WeatherData,
    # Task & Schedule models
    Task,
    Alert,
    DailySchedule,
    # Recommendation models
    Recommendation,
    RecommendationRequest,
    RecommendationResponse,
    # Chat models
    ChatMessage,
    ChatResponse,
)

__version__ = "0.2.0"

__all__ = [
    # Enums
    "FarmType",
    "SoilType",
    "CropStage",
    "LivestockType",
    "WeatherCondition",
    "TaskStatus",
    "TaskPriority",
    "AlertSeverity",
    # Core models
    "Location",
    "FarmProfile",
    "CropInfo",
    "LivestockInfo",
    "SoilData",
    "WeatherData",
    # Task & Schedule models
    "Task",
    "Alert",
    "DailySchedule",
    # Recommendation models
    "Recommendation",
    "RecommendationRequest",
    "RecommendationResponse",
    # Chat models
    "ChatMessage",
    "ChatResponse",
    "__version__",
]
