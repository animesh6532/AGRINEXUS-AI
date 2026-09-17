"""
Configuration module for the Market Forecast backend.
Handles loading environment variables and application settings.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "AgriNexus-AI Market Forecast"
    VERSION: str = "1.0.0"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # API Keys (Government of India)
    DATA_GOV_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for data.gov.in or agmarknet.gov.in"
    )

    # API Base URLs
    AGMARKNET_API_BASE_URL: str = "https://api.data.gov.in"
    DATA_GOV_IN_BASE_URL: str = "https://api.data.gov.in"

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./backend/data/market/market_data.db"

    # Caching Configuration
    CACHE_TTL_SECONDS: int = 300  # 5 minutes cache for market data

    # Forecasting Configuration
    DEFAULT_FORECAST_HORIZON_DAYS: int = 7
    MIN_HISTORICAL_DAYS_REQUIRED: int = 30

    @field_validator("DATA_GOV_API_KEY")
    @classmethod
    def api_key_must_be_set(cls, v):
        """Ensure API key is provided in production."""
        if not v and os.getenv("ENVIRONMENT", "development") == "production":
            raise ValueError("DATA_GOV_API_KEY must be set in production")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Global settings instance
settings = Settings()