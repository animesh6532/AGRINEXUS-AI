"""
Integration tests for API v1 REST endpoints and image processing.
"""

import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c



def test_health_endpoints(client):
    """Test GET /health and GET /api/v1/models/health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "models" in data

    models_response = client.get("/api/v1/models/health")
    assert models_response.status_code == 200
    m_data = models_response.json()
    assert m_data["status"] in ["healthy", "degraded"]


def test_crop_recommendation_endpoint(client):
    """Test POST /api/v1/crop/recommend."""
    payload = {
        "N": 90.0, "P": 42.0, "K": 43.0,
        "temperature": 20.87, "humidity": 82.0,
        "ph": 6.5, "rainfall": 202.9
    }
    response = client.post("/api/v1/crop/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "prediction" in data
    assert "top_k_predictions" in data


def test_crop_invalid_input_range(client):
    """Test validation failure for out-of-range pH."""
    payload = {
        "N": 90.0, "P": 42.0, "K": 43.0,
        "temperature": 20.87, "humidity": 82.0,
        "ph": 99.0,  # Invalid pH > 14
        "rainfall": 202.9
    }
    response = client.post("/api/v1/crop/recommend", json=payload)
    assert response.status_code == 422


def test_fertilizer_recommendation_endpoint(client):
    """Test POST /api/v1/fertilizer/recommend."""
    payload = {
        "Nitrogen": 20.0, "Phosphorus": 20.0, "Potassium": 20.0,
        "pH": 6.5, "Rainfall": 800.0, "Temperature": 26.0,
        "District_Name": "Pune", "Soil_color": "Black", "Crop": "Sugarcane",
        "Link": "https://example.com"
    }
    response = client.post("/api/v1/fertilizer/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "predicted_formulation" in data
    assert "Western Maharashtra" in data["scope_warning"]


def test_irrigation_prediction_endpoint(client):
    """Test POST /api/v1/irrigation/predict."""
    payload = {
        "SWC": 0.22, "SWC_lag1h": 0.225, "SWC_lag2h": 0.23, "SWC_lag3h": 0.235,
        "SWC_roll6h_mean": 0.23, "Rainfall_mm": 0.0, "Rain_roll6h_sum": 0.0
    }
    response = client.post("/api/v1/irrigation/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "ml_predicted_swc_3h" in data
    assert "persistence_swc_3h" in data
    assert data["persistence_swc_3h"] == 0.22


def test_soil_analysis_endpoint(client):
    """Test POST /api/v1/soil/analyze."""
    payload = {
        "pH(CaCl2)": 6.2, "pH(H2O)": 6.8, "Clay": 25.0, "Silt": 40.0, "Sand": 35.0,
        "CaCO3": 12.0, "P": 18.5, "N": 2.1, "K": 180.0, "EC": 15.0,
        "NUTS_0": "DE", "LC1": "B11"
    }
    response = client.post("/api/v1/soil/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_soc" in data
    assert data["unit"] == "g/kg"


def test_yield_prediction_endpoint(client):
    """Test POST /api/v1/yield/predict."""
    payload = {
        "Crop": "Rice", "Season": "Kharif", "State": "Punjab",
        "Area": 100.0, "Annual_Rainfall": 1200.0, "Fertilizer": 15000.0,
        "Pesticide": 500.0, "Fertilizer_Per_Area": 150.0, "Pesticide_Per_Area": 5.0
    }
    response = client.post("/api/v1/yield/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_yield" in data


def test_pest_environmental_risk_endpoint(client):
    """Test POST /api/v1/pest/risk."""
    payload = {
        "Temperature": 28.5, "Humidity": 75.0, "Rainfall": 120.0,
        "Crop_Type": "Rice", "Soil_Type": "Clay", "Region": "South"
    }
    response = client.post("/api/v1/pest/risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "pest_severity_risk" in data


def test_disease_image_predict_endpoint(client):
    """Test POST /api/v1/disease/predict with generated RGB image."""
    img = Image.new("RGB", (224, 224), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("test_leaf.jpg", buf, "image/jpeg")}
    response = client.post("/api/v1/disease/predict", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "predicted_disease" in data
    assert "image_quality" in data


def test_disease_image_unsupported_type(client):
    """Test POST /api/v1/disease/predict with invalid MIME type."""
    files = {"file": ("test.txt", io.BytesIO(b"hello text"), "text/plain")}
    response = client.post("/api/v1/disease/predict", files=files)
    assert response.status_code == 415
