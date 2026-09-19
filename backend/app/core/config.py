"""
Configuration module for the AgriNexus-AI backend.
Handles loading environment variables and application settings.
"""

import os
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import Optional


# Determine the project root (where backend directory is located)
# This file is at: <project-root>/backend/app/core/config.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# Load .env from backend directory (consistent location)
ENV_FILE_PATH = BACKEND_DIR / ".env"



class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "AgriNexus-AI"
    VERSION: str = "1.0.0"


    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    CORS_ORIGINS: list = ["*"]

    # Model Artifact Directories (Checks models/ first, falls back to Notebook/models/)
    MODEL_DIR: Optional[str] = None


    # OpenCV / Computer Vision Quality Gates
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp", "image/bmp"]
    CV_BLUR_THRESHOLD: float = 50.0       # Minimum Laplacian variance for sharp frame
    CV_BRIGHTNESS_LOW: float = 30.0       # Minimum mean brightness
    CV_BRIGHTNESS_HIGH: float = 225.0     # Maximum mean brightness
    LIVE_FRAME_SAMPLING_FPS: int = 10     # Cap live streaming frame evaluation rate
    SMOOTHING_BUFFER_SIZE: int = 5        # Rolling buffer length for temporal smoothing

    # API Keys (Government of India)
    DATA_GOV_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for data.gov.in or agmarknet.gov.in"
    )

    # API Base URLs
    AGMARKNET_API_BASE_URL: str = "https://api.data.gov.in"
    DATA_GOV_IN_BASE_URL: str = "https://api.data.gov.in"

    # Crop Calendar Configuration (external provider: Spora)
    # Official provider documentation (https://spora.engineer/docs):
    # - Base URL: https://api.spora.engineer
    # - Auth: "X-Api-Key" request header (key alone is sufficient; no
    #   username/password). Keys look like "spk_live_..." and are issued
    #   at https://spora.engineer/request
    # - Calendar endpoint: GET /harvest/{location} (lowercase country
    #   slug, e.g. "italy", "france", "kenya", "india")
    # When SPORA_API_KEY is unset, the Crop Calendar module serves the
    # bundled reference dataset. When set, the module fetches calendar
    # data from the Spora /harvest endpoint. The key is backend-only:
    # it is never logged, never returned in responses, and never stored
    # in code.
    SPORA_API_BASE_URL: str = Field(
        default="https://api.spora.engineer",
        description=(
            "Base URL of the Spora crop-calendar provider (official "
            "documented default; override only for testing)."
        ),
    )
    SPORA_API_KEY: Optional[str] = Field(
        default=None,
        description=(
            "API key for the Spora crop-calendar provider "
            "(backend-only; never exposed in responses or logs)."
        ),
    )
    # Safe fallback behaviour: when the external provider is configured
    # but unreachable/failing, the Crop Calendar module serves the
    # bundled reference dataset instead of failing the request, and
    # labels the response with fallback_used/fallback_reason. No
    # fabricated external data is ever returned.
    CROP_CALENDAR_FALLBACK_TO_REFERENCE_DATA: bool = Field(
        default=True,
        description=(
            "Fall back to the bundled reference dataset when the "
            "external crop-calendar provider is unavailable "
            "(default: true)."
        ),
    )

    # Database Configuration - will be overridden from .env
    DATABASE_URL: str = "sqlite:///./data/market/market_data.db"


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
        "env_file": str(ENV_FILE_PATH) if ENV_FILE_PATH.exists() else None,
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Global settings instance
settings = Settings()


def _resolve_database_url(url: str) -> str:
    """Resolve database URL to absolute path based on backend directory."""
    if not url or not url.startswith("sqlite:///"):
        return url

    # Extract the file path from sqlite:///path
    relative_path = url[10:]  # Remove "sqlite:///" prefix

    # If the path is already an absolute path, return as-is
    if Path(relative_path).is_absolute():
        return url

    relative = Path(relative_path)

    # Normalize the relative path: drop any leading "." components so that
    # "./backend/..." and "backend/..." are detected the same way, regardless
    # of how pathlib represents them on a given platform or version.
    parts = [part for part in relative.parts if part != "."]

    # Degenerate input (e.g. "sqlite:///.") - nothing to resolve.
    if not parts:
        return url

    if parts[0] == "backend":
        # Path written relative to the project root
        # (e.g. sqlite:///./backend/data/market/market_data.db)
        absolute_path = (PROJECT_ROOT / Path(*parts)).resolve()
    else:
        # Path written relative to the backend directory
        # (e.g. sqlite:///./data/market/market_data.db)
        absolute_path = (BACKEND_DIR / Path(*parts)).resolve()

    return f"sqlite:///{absolute_path}"


# Resolve the database URL to be absolute
settings.DATABASE_URL = _resolve_database_url(settings.DATABASE_URL)


# Ensure the market data directory exists
def _ensure_market_data_dir():
    """Ensure the market data directory exists."""
    # Extract database path from DATABASE_URL
    if settings.DATABASE_URL.startswith("sqlite:///"):
        db_path = settings.DATABASE_URL[10:]  # Remove "sqlite:///" prefix
        market_data_dir = Path(db_path).parent
        market_data_dir.mkdir(parents=True, exist_ok=True)


# Create directory on import
_ensure_market_data_dir()