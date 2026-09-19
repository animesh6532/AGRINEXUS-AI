"""
Tests for Model Registry loading and frozen artifact smoke inference.
"""

import pytest
from app.services.model_registry import ModelRegistry


def test_model_registry_startup_and_loading():
    """Verify that ModelRegistry loads all 7 frozen ML artifacts and reports READY."""
    registry = ModelRegistry()
    registry.load_all_models()

    health = registry.get_health_status()
    assert health["status"] in ["healthy", "degraded"]
    models_summary = health["models"]

    # Check that all keys exist
    expected_keys = ["crop", "disease", "fertilizer", "irrigation", "pest_visual", "pest_env", "soil", "yield"]
    for key in expected_keys:
        assert key in models_summary, f"Missing model key {key} in health summary"
        assert models_summary[key] == "READY", f"Model {key} failed to load: {health['details'][key].get('last_error')}"


def test_crop_smoke_inference():
    """Test Crop Recommendation inference."""
    registry = ModelRegistry()
    res = registry.predict_crop({
        "N": 90.0, "P": 42.0, "K": 43.0,
        "temperature": 20.87, "humidity": 82.0,
        "ph": 6.5, "rainfall": 202.9
    })
    assert isinstance(res["prediction"], str)
    assert res["confidence"] > 0.0
    assert len(res["top_k_predictions"]) > 0
    assert "is_plausible" in res


def test_irrigation_smoke_inference():
    """Test Irrigation prediction returning both ML prediction and Persistence baseline."""
    registry = ModelRegistry()
    res = registry.predict_irrigation({
        "SWC": 0.22, "SWC_lag1h": 0.225, "SWC_lag2h": 0.23, "SWC_lag3h": 0.235,
        "SWC_roll6h_mean": 0.23, "Rainfall_mm": 0.0, "Rain_roll6h_sum": 0.0
    })
    assert "ml_predicted_swc_3h" in res
    assert "persistence_swc_3h" in res
    assert res["persistence_swc_3h"] == 0.22
    assert "agronomic_status" in res


def test_soil_smoke_inference():
    """Test Soil Organic Carbon regression with empirical 95% prediction interval."""
    registry = ModelRegistry()
    res = registry.predict_soil({
        "pH(CaCl2)": 6.2, "pH(H2O)": 6.8, "Clay": 25.0, "Silt": 40.0, "Sand": 35.0,
        "CaCO3": 12.0, "P": 18.5, "N": 2.1, "K": 180.0, "EC": 15.0,
        "NUTS_0": "DE", "LC1": "B11"
    })
    assert "predicted_soc" in res
    assert "prediction_interval" in res
    assert res["prediction_interval"]["lower"] <= res["predicted_soc"] <= res["prediction_interval"]["upper"]


def test_yield_smoke_inference():
    """Test Crop Yield regression with empirical prediction interval."""
    registry = ModelRegistry()
    res = registry.predict_yield({
        "Crop": "Rice", "Season": "Kharif", "State": "Punjab",
        "Area": 100.0, "Annual_Rainfall": 1200.0, "Fertilizer": 15000.0,
        "Pesticide": 500.0, "Fertilizer_Per_Area": 150.0, "Pesticide_Per_Area": 5.0
    })
    assert "predicted_yield" in res
    assert "prediction_interval" in res
