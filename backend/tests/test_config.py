"""
Test configuration loading.
"""

import os
import tempfile
from app.core.config import Settings


def test_settings_loads():
    """Test that settings can be loaded."""
    # Create a temporary .env file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("DATA_GOV_API_KEY=test_key\n")
        f.write("DEBUG=True\n")
        temp_env_path = f.name

    try:
        # Test loading settings
        settings = Settings(_env_file=temp_env_path)
        assert settings.DATA_GOV_API_KEY == "test_key"
        assert settings.DEBUG == True
        assert settings.PROJECT_NAME == "AgriNexus-AI"
    finally:
        # Clean up temp file
        os.unlink(temp_env_path)


def test_settings_defaults():
    """Test that default settings work."""
    settings = Settings()
    assert settings.PROJECT_NAME == "AgriNexus-AI"
    assert settings.VERSION == "1.0.0"
    assert settings.API_V1_STR == "/api"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000


def test_crop_calendar_provider_defaults(monkeypatch):
    """Crop calendar provider settings load with documented defaults."""
    monkeypatch.delenv("SPORA_API_KEY", raising=False)
    monkeypatch.delenv("SPORA_API_BASE_URL", raising=False)
    monkeypatch.delenv(
        "CROP_CALENDAR_FALLBACK_TO_REFERENCE_DATA", raising=False
    )

    # No environment file and no environment variables: pure defaults.
    settings = Settings(_env_file=None)
    # The base URL has an official default; the key is the activation
    # switch and must never be hard-coded.
    assert settings.SPORA_API_BASE_URL == "https://api.spora.engineer"
    assert settings.SPORA_API_KEY is None
    assert settings.CROP_CALENDAR_FALLBACK_TO_REFERENCE_DATA is True


def test_crop_calendar_provider_from_env_file(monkeypatch):
    """Provider credentials are read from the environment file."""
    monkeypatch.delenv("SPORA_API_BASE_URL", raising=False)
    monkeypatch.delenv("SPORA_API_KEY", raising=False)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".env", delete=False
    ) as f:
        f.write("SPORA_API_BASE_URL=https://example.test/harvest\n")
        f.write("SPORA_API_KEY=dummy-key-not-a-secret\n")
        temp_env_path = f.name

    try:
        settings = Settings(_env_file=temp_env_path)
        assert settings.SPORA_API_BASE_URL == "https://example.test/harvest"
        assert settings.SPORA_API_KEY == "dummy-key-not-a-secret"
    finally:
        os.unlink(temp_env_path)