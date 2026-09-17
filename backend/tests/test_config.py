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
        assert settings.PROJECT_NAME == "AgriNexus-AI Market Forecast"
    finally:
        # Clean up temp file
        os.unlink(temp_env_path)


def test_settings_defaults():
    """Test that default settings work."""
    settings = Settings()
    assert settings.PROJECT_NAME == "AgriNexus-AI Market Forecast"
    assert settings.VERSION == "1.0.0"
    assert settings.API_V1_STR == "/api"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000