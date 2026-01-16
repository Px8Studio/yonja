"""
Yonca AI Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Yonca AI"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]
    
    # Database (SQLite for offline support)
    database_url: str = "sqlite+aiosqlite:///./yonca.db"
    
    # Recommendation Engine
    default_language: Literal["az", "en", "ru"] = "az"
    recommendation_confidence_threshold: float = 0.7
    max_daily_recommendations: int = 10
    
    # Weather Simulation
    weather_update_interval_hours: int = 6
    
    # Chatbot
    chatbot_confidence_threshold: float = 0.6
    chatbot_fallback_message: str = "Bağışlayın, sualınızı başa düşmədim. Zəhmət olmasa yenidən cəhd edin."
    
    class Config:
        env_prefix = "YONCA_"
        env_file = ".env"


settings = Settings()
