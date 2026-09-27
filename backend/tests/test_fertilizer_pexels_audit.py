"""
Fertilizer Recommendation & Pexels Image Resolution Audit Test Suite.
Verifies LightGBM frozen model inference, Pexels API image resolution, attribution,
scoring, caching, and fallback handling.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.model_registry import ModelRegistry
from app.services.fertilizer_image_resolver import FertilizerImageResolver, generate_fertilizer_queries, score_pexels_candidate

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def init_models():
    """Ensure ModelRegistry models are loaded for tests."""
    registry = ModelRegistry()
    registry.load_all_models()


def test_fertilizer_model_ready():
    """Verify frozen LightGBM fertilizer recommendation model is loaded and READY."""
    registry = ModelRegistry()
    assert registry.models_meta["fertilizer"].status == "READY"


def test_fertilizer_recommendation_prediction():
    """Test valid model prediction for Paddy/Rice in Pune district."""
    payload = {
        "Nitrogen": 37.0,
        "Phosphorus": 20.0,
        "Potassium": 20.0,
        "pH": 6.5,
        "Rainfall": 120.0,
        "Temperature": 26.0,
        "District_Name": "Pune",
        "Soil_color": "Black",
        "Crop": "Rice",
        "Link": "https://example.com"
    }
    response = client.post("/api/v1/fertilizer/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "predicted_formulation" in data
    assert data["predicted_formulation"] is not None
    assert "Western Maharashtra" in data["scope_warning"]


def test_fertilizer_recommendation_numeric_validation():
    """Verify negative N/P/K or invalid pH input raises 422 Unprocessable Entity."""
    payload = {
        "Nitrogen": -10.0,  # Invalid negative
        "Phosphorus": 20.0,
        "Potassium": 20.0,
        "pH": 6.5,
        "Rainfall": 120.0,
        "Temperature": 26.0,
        "District_Name": "Pune",
        "Soil_color": "Black",
        "Crop": "Rice"
    }
    response = client.post("/api/v1/fertilizer/recommend", json=payload)
    assert response.status_code == 422


def test_generate_fertilizer_queries():
    """Verify query generation never outputs standalone generic 'fertilizer'."""
    queries_urea = generate_fertilizer_queries("Urea")
    assert "urea fertilizer" in queries_urea
    assert "fertilizer" not in queries_urea

    queries_npk = generate_fertilizer_queries("19:19:19 NPK")
    assert "19-19-19 NPK fertilizer" in queries_npk


def test_score_pexels_candidate():
    """Test fertilizer candidate scoring with positive and negative keyword signals."""
    positive_photo = {
        "alt": "Bag of urea fertilizer granules for agricultural soil",
        "url": "https://pexels.com/photo/urea-fertilizer-12345",
        "width": 1280,
        "height": 720
    }
    score_pos = score_pexels_candidate(positive_photo, "Urea")
    assert score_pos >= 60

    negative_photo = {
        "alt": "Farmer driving tractor spraying pesticide on diseased plant leaf",
        "url": "https://pexels.com/photo/tractor-pesticide-67890",
        "width": 1280,
        "height": 720
    }
    score_neg = score_pexels_candidate(negative_photo, "Urea")
    assert score_neg < score_pos


def test_resolve_fertilizer_image_endpoint():
    """Test POST /api/v1/fertilizer/resolve-image endpoint structure."""
    payload = {"fertilizer_name": "Urea"}
    response = client.post("/api/v1/fertilizer/resolve-image", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "verified_product" in data
    assert data["verified_product"] is False


def test_resolve_fertilizer_image_caching():
    """Verify normalized queries hit memory cache on subsequent calls."""
    res1 = FertilizerImageResolver.resolve_fertilizer_image("Urea")
    res2 = FertilizerImageResolver.resolve_fertilizer_image("urea")
    assert res1 == res2
