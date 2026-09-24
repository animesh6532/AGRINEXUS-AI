"""
Unit and integration tests for Smart Crop Advisor feature.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.agriculture.crop_profiles import CROP_PROFILES, get_crop_profile
from app.services.agriculture.crop_suitability import CropSuitabilityEngine
from app.services.agriculture.weather_context import WeatherContext
from app.services.agriculture.soil_context import SoilContextService
from app.services.agriculture.season_engine import SeasonEngine


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_legacy_crop_recommendation_regression(client):
    """Verify POST /api/v1/crop/recommend legacy endpoint remains backward compatible."""
    payload = {
        "N": 90.0, "P": 42.0, "K": 43.0,
        "temperature": 20.87, "humidity": 82.0,
        "ph": 6.5, "rainfall": 202.9
    }
    res = client.post("/api/v1/crop/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "prediction" in data
    assert data["prediction"] == "rice"


def test_smart_crop_recommend_auto(client):
    """Test POST /api/v1/crop/recommend-smart in Smart Auto mode (coordinates only)."""
    payload = {
        "mode": "auto",
        "location": {
            "latitude": 22.72,
            "longitude": 88.48,
            "displayName": "Barasat, West Bengal",
            "state": "West Bengal",
            "country": "India"
        }
    }
    res = client.post("/api/v1/crop/recommend-smart", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["engine_version"] == "1.0.0"
    assert "data_completeness" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0

    # Top recommendation verification
    top_crop = data["recommendations"][0]
    assert "crop" in top_crop
    assert "suitability_score" in top_crop
    assert "suitability_level" in top_crop
    assert "reasons" in top_crop
    assert "data_sources" in top_crop


def test_smart_crop_recommend_hybrid_with_soil(client):
    """Test POST /api/v1/crop/recommend-smart in Hybrid mode with user NPK & pH."""
    payload = {
        "mode": "hybrid",
        "location": {
            "latitude": 22.72,
            "longitude": 88.48,
            "displayName": "Barasat, West Bengal",
            "state": "West Bengal"
        },
        "soil": {
            "nitrogen": 90.0,
            "phosphorus": 42.0,
            "potassium": 43.0,
            "ph": 6.5
        },
        "farm": {
            "water_availability": "Irrigated",
            "area_acres": 2.5
        }
    }
    res = client.post("/api/v1/crop/recommend-smart", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["mode"] == "hybrid"
    assert data["ml_status"]["available"] is True  # ML model ran because all 7 features are available

    # At least one ML-supported crop should have an active ML prediction probability
    ml_supported_recs = [r for r in data["recommendations"] if r["ml_prediction"]["supported"] and r["ml_prediction"]["probability"] is not None]
    assert len(ml_supported_recs) > 0



def test_smart_crop_partial_data_missing_pk(client):
    """Test partial data mode: N provided, P and K missing. Verify P & K are NOT fabricated as 0."""
    payload = {
        "mode": "hybrid",
        "location": {
            "latitude": 22.72,
            "longitude": 88.48,
            "state": "West Bengal"
        },
        "soil": {
            "nitrogen": 90.0,
            "phosphorus": None,  # Missing
            "potassium": None   # Missing
        }
    }
    res = client.post("/api/v1/crop/recommend-smart", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Soil object honesty check
    soil_data = data["soil"]
    assert soil_data["phosphorus"]["value"] is None
    assert soil_data["potassium"]["value"] is None
    assert soil_data["phosphorus"]["provenance"] == "UNKNOWN"

    # ML prediction unavailable when inputs are incomplete
    assert data["ml_status"]["available"] is False

    # But environmental suitability remains available!
    assert len(data["recommendations"]) > 0


def test_suitability_engine_unit_logic():
    """Unit test suitability engine scoring and factor breakdown."""
    rice_profile = get_crop_profile("rice")
    assert rice_profile is not None

    weather_ctx = WeatherContext(
        latitude=22.72,
        longitude=88.48,
        current_temperature=28.0,
        current_humidity=80.0,
        current_rainfall=150.0,
        data_available=True
    )
    soil_ctx = SoilContextService.get_soil_context(22.72, 88.48, user_ph=6.5)
    season_info = SeasonEngine.get_season_info(22.72, 88.48, state="West Bengal")

    result = CropSuitabilityEngine.evaluate_crop(
        profile=rice_profile,
        weather=weather_ctx,
        soil=soil_ctx,
        season=season_info,
        ml_probability=0.92,
        water_availability="Irrigated"
    )

    assert result.suitability_score >= 80
    assert result.suitability_level in ["Highly Suitable", "Suitable"]
    assert any("season" in r.lower() for r in result.reasons)
    assert result.ml_prediction["supported"] is True


def test_catalogue_expansion_crop_non_ml():
    """Verify non-ML catalogue crops (e.g. Sugarcane, Mustard) are evaluated without fabricated ML prob."""
    mustard_profile = get_crop_profile("mustard")
    assert mustard_profile is not None
    assert mustard_profile.ml_supported is False

    weather_ctx = WeatherContext(
        latitude=26.9,
        longitude=75.7,
        current_temperature=18.0,
        current_humidity=60.0,
        current_rainfall=40.0,
        data_available=True
    )
    soil_ctx = SoilContextService.get_soil_context(26.9, 75.7, user_ph=7.0)
    season_info = SeasonEngine.get_season_info(26.9, 75.7, state="Rajasthan")

    result = CropSuitabilityEngine.evaluate_crop(
        profile=mustard_profile,
        weather=weather_ctx,
        soil=soil_ctx,
        season=season_info
    )

    assert result.ml_prediction["supported"] is False
    assert result.ml_prediction["probability"] is None
    assert result.suitability_score > 0
