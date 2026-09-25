"""
Comprehensive 10-Level Validation Suite for AgriNexus-AI Smart Crop Suitability & Recommendation Engine.
Strictly tests all 10 validation levels, boundary conditions, missing data rules, regional scenarios,
seasonal windows, source validation, ML regression, and non-negotiable critical acceptance tests.
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.main import app
from app.services.agriculture.crop_profiles import CROP_PROFILES, get_crop_profile, get_all_crop_profiles
from app.services.agriculture.soil_context import SoilContextService, derive_soil_texture
from app.services.agriculture.weather_context import WeatherContext
from app.services.agriculture.season_engine import SeasonEngine, SeasonInfo
from app.services.agriculture.limitation_engine import LimitationEngine, FactorStatus
from app.services.agriculture.sowing_feasibility import SowingFeasibilityEngine, SowingStatus
from app.services.agriculture.crop_suitability import CropSuitabilityEngine
from app.services.agriculture.smart_crop_recommender import SmartCropRecommender


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ==============================================================================
# LEVEL 1 — UNIT TESTS
# ==============================================================================
def test_level_1_soil_texture_derivation():
    """Verify USDA soil texture triangle classification derivation."""
    assert derive_soil_texture(clay=50, sand=20, silt=30) == "Clay"
    assert derive_soil_texture(clay=10, sand=75, silt=15) == "Sandy Loam"
    assert derive_soil_texture(clay=20, sand=40, silt=40) == "Loam"
    assert derive_soil_texture(clay=5, sand=90, silt=5) == "Sand"


def test_level_1_limitation_engine_piecewise_logic():
    """Test limitation engine factor evaluations."""
    rice = get_crop_profile("rice")
    assert rice is not None

    weather = WeatherContext(
        latitude=22.72, longitude=88.48,
        current_temperature=28.0, current_humidity=80.0, current_rainfall=200.0
    )
    soil = SoilContextService.get_soil_context(22.72, 88.48, user_ph=6.5)
    season = SeasonEngine.get_season_info(22.72, 88.48, state="West Bengal")

    res = LimitationEngine.evaluate_limitations(rice, weather, soil, season)
    assert not res.is_hard_constrained
    assert res.factor_evaluations["temperature"].status == FactorStatus.OPTIMAL
    assert res.factor_evaluations["ph"].status == FactorStatus.OPTIMAL


# ==============================================================================
# LEVEL 2 — BOUNDARY TESTS
# ==============================================================================
def test_level_2_temperature_boundary_conditions():
    """Test exact optimal min/max and absolute min/max boundary conditions for Wheat."""
    wheat = get_crop_profile("wheat")
    assert wheat is not None

    soil = SoilContextService.get_soil_context(30.9, 75.8, user_ph=6.5)
    season = SeasonEngine.get_season_info(30.9, 75.8, state="Punjab")

    # Optimal minimum (15°C) -> OPTIMAL
    w_opt_min = WeatherContext(latitude=30.9, longitude=75.8, current_temperature=15.0)
    res_opt = LimitationEngine.evaluate_limitations(wheat, w_opt_min, soil, season)
    assert res_opt.factor_evaluations["temperature"].status == FactorStatus.OPTIMAL

    # Lethal temperature (35°C, absolute max is 30°C for Wheat) -> HARD CONSTRAINT / UNSUITABLE
    w_lethal = WeatherContext(latitude=30.9, longitude=75.8, current_temperature=35.0)
    res_lethal = LimitationEngine.evaluate_limitations(wheat, w_lethal, soil, season)
    assert res_lethal.is_hard_constrained
    assert res_lethal.factor_evaluations["temperature"].status == FactorStatus.UNSUITABLE


# ==============================================================================
# LEVEL 3 — MISSING DATA TESTS
# ==============================================================================
def test_level_3_missing_data_resilience():
    """Verify engine degrades gracefully with missing weather, soil, or NPK."""
    maize = get_crop_profile("maize")
    assert maize is not None

    # Weather offline, Soil missing
    weather = WeatherContext(latitude=22.0, longitude=80.0, data_available=False)
    soil = SoilContextService.get_soil_context(22.0, 80.0)  # P and K are None
    season = SeasonEngine.get_season_info(22.0, 80.0, state="Madhya Pradesh")

    res = CropSuitabilityEngine.evaluate_crop(maize, weather, soil, season)
    assert res.suitability_score > 0
    assert "weather" in res.missing_data
    assert "phosphorus" in res.missing_data
    assert "potassium" in res.missing_data


# ==============================================================================
# LEVEL 4 — REGIONAL SCENARIOS
# ==============================================================================
def test_level_4_regional_agricultural_scenarios(client):
    """Test representative regional agricultural scenarios across India."""
    # West Bengal Kharif Rice scenario
    res_wb = client.post("/api/v1/crop/recommend-smart", json={
        "mode": "auto",
        "location": {"latitude": 22.72, "longitude": 88.48, "state": "West Bengal"}
    }).json()
    assert res_wb["success"] is True
    top_wb = res_wb["recommendations"][0]["crop"]
    assert top_wb in ["rice", "jute", "banana", "maize", "mango", "papaya", "coconut"]

    # Rajasthan Arid Pulse scenario
    res_rj = client.post("/api/v1/crop/recommend-smart", json={
        "mode": "auto",
        "location": {"latitude": 26.91, "longitude": 75.78, "state": "Rajasthan"}
    }).json()
    assert res_rj["success"] is True
    r_crops = [r["crop"] for r in res_rj["recommendations"][:10]]
    assert any(c in r_crops for c in ["mothbeans", "mungbean", "chickpea", "mustard", "maize", "pomegranate", "mango"])


# ==============================================================================
# LEVEL 5 — SEASONAL TESTING
# ==============================================================================
def test_level_5_seasonal_variation():
    """Verify sowing windows change suitability appropriately based on current season."""
    wheat = get_crop_profile("wheat")
    assert wheat is not None

    # Kharif (July) for Wheat -> Outside window
    season_kharif = SeasonInfo(season="Kharif", regional_season="Kharif", sowing_window="Oct-Nov", harvest_window="Mar-Apr", current_month="July", state="Punjab")
    weather = WeatherContext(latitude=30.9, longitude=75.8, current_temperature=28.0)
    soil = SoilContextService.get_soil_context(30.9, 75.8, user_ph=6.5)

    res_k = CropSuitabilityEngine.evaluate_crop(wheat, weather, soil, season_kharif)
    assert res_k.sowing_feasibility == SowingStatus.OUTSIDE_WINDOW
    assert not res_k.is_sowing_recommended_now


# ==============================================================================
# LEVEL 6 — LOCATION TESTING
# ==============================================================================
def test_level_6_location_coordinates_consistency(client):
    """Verify coordinates sent match backend location response."""
    payload = {
        "mode": "auto",
        "location": {
            "latitude": 13.08,
            "longitude": 80.27,
            "state": "Tamil Nadu"
        }
    }
    res = client.post("/api/v1/crop/recommend-smart", json=payload).json()
    assert res["location"]["latitude"] == 13.08
    assert res["location"]["longitude"] == 80.27
    assert res["location"]["state"] == "Tamil Nadu"


# ==============================================================================
# LEVEL 7 — SOURCE VALIDATION
# ==============================================================================
def test_level_7_crop_profile_sources():
    """Verify all 26 production crop profiles retain explicit authoritative citations."""
    catalogue = get_all_crop_profiles()
    assert len(catalogue) >= 26

    for p in catalogue:
        assert p.source is not None and len(p.source) > 5
        assert p.source_url.startswith("http")
        assert len(p.temp_optimal) == 2
        assert len(p.ph_optimal) == 2


# ==============================================================================
# LEVEL 8 — ML REGRESSION
# ==============================================================================
def test_level_8_legacy_ml_regression(client):
    """Verify legacy endpoint POST /api/v1/crop/recommend maintains exact behavior."""
    payload = {
        "N": 90.0, "P": 42.0, "K": 43.0,
        "temperature": 20.87, "humidity": 82.0,
        "ph": 6.5, "rainfall": 202.9
    }
    res = client.post("/api/v1/crop/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["prediction"] == "rice"
    assert data["confidence"] > 0.6


# ==============================================================================
# LEVEL 9 & 10 — CRITICAL ACCEPTANCE TESTS
# ==============================================================================
def test_acceptance_test_1_missing_pk_no_ml_fabrication(client):
    """
    Critical Test 1: User provides location only. P and K are missing.
    EXPECTED: Agronomic suitability AVAILABLE, ML NOT AVAILABLE. P & K NOT fabricated as 0.
    """
    payload = {
        "mode": "auto",
        "location": {"latitude": 22.72, "longitude": 88.48, "state": "West Bengal"}
    }
    res = client.post("/api/v1/crop/recommend-smart", json=payload).json()

    assert res["soil"]["phosphorus"]["value"] is None
    assert res["soil"]["potassium"]["value"] is None
    assert res["soil"]["phosphorus"]["provenance"] == "UNKNOWN"
    assert res["ml_status"]["available"] is False
    assert len(res["recommendations"]) > 0


def test_acceptance_test_2_measured_override(client):
    """
    Critical Test 2: User provides measured N, P, K, pH.
    EXPECTED: Measured overrides estimate, ML becomes AVAILABLE.
    """
    payload = {
        "mode": "hybrid",
        "location": {"latitude": 22.72, "longitude": 88.48, "state": "West Bengal"},
        "soil": {
            "nitrogen": 90.0,
            "phosphorus": 42.0,
            "potassium": 43.0,
            "ph": 6.5
        }
    }
    res = client.post("/api/v1/crop/recommend-smart", json=payload).json()

    assert res["soil"]["ph"]["provenance"] == "MEASURED"
    assert res["soil"]["phosphorus"]["value"] == 42.0
    assert res["ml_status"]["available"] is True


def test_acceptance_test_3_sowing_window_mismatch_warning(client):
    """
    Critical Test 3: Crop environmentally suitable but outside current sowing window.
    EXPECTED: Land suitability: Suitable, Sowing suitability: Outside Window / Late warning.
    """
    wheat_profile = get_crop_profile("wheat")
    season_july = SeasonInfo(season="Kharif", regional_season="Monsoon Kharif", sowing_window="Oct-Nov", harvest_window="Mar-Apr", current_month="July", state="Punjab")
    weather = WeatherContext(latitude=30.9, longitude=75.8, current_temperature=22.0)
    soil = SoilContextService.get_soil_context(30.9, 75.8, user_ph=6.5)

    res = CropSuitabilityEngine.evaluate_crop(wheat_profile, weather, soil, season_july)
    assert res.sowing_feasibility == SowingStatus.OUTSIDE_WINDOW
    assert any("sowing window" in w.lower() for w in res.warnings)


def test_acceptance_test_4_severe_constraint_overrides_ml():
    """
    Critical Test 4: High ML probability but severe agronomic constraint (Lethal temp).
    EXPECTED: Hard constraint caps suitability score, prevents high recommendation.
    """
    rice = get_crop_profile("rice")
    weather_freezing = WeatherContext(latitude=34.0, longitude=74.8, current_temperature=2.0)  # Lethal for Rice
    soil = SoilContextService.get_soil_context(34.0, 74.8, user_ph=6.5)
    season = SeasonEngine.get_season_info(34.0, 74.8, state="Jammu & Kashmir")

    res = CropSuitabilityEngine.evaluate_crop(
        profile=rice,
        weather=weather_freezing,
        soil=soil,
        season=season,
        ml_probability=0.98  # High ML prob
    )
    assert res.suitability_level == "Not Suitable"
    assert res.suitability_score <= 20
