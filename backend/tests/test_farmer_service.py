"""
Unit tests for Farmer Profile, Farm, Field, Crop, and Farm Intelligence endpoints/services.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import models, connection
from app.core.dependencies import get_db

# Create an in-memory SQLite database engine for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_farmer_profile_create_and_get():
    # 1. Get default profile
    res = client.get("/api/v1/farmer/profile", headers={"X-User-ID": "test_user_1"})
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == "test_user_1"
    assert data["full_name"] == "Default Farmer"

    # 2. Update profile
    update_res = client.put(
        "/api/v1/farmer/profile",
        json={"full_name": "Animesh Farmer", "preferred_language": "bn"},
        headers={"X-User-ID": "test_user_1"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["full_name"] == "Animesh Farmer"
    assert updated_data["preferred_language"] == "bn"


def test_farm_field_crop_hierarchy_and_dashboard():
    headers = {"X-User-ID": "test_user_scenario1"}

    # Step 1: Create Farm
    farm_res = client.post(
        "/api/v1/farmer/farms",
        json={
            "farm_name": "Main Green Farm",
            "location_name": "North 24 Parganas, West Bengal",
            "latitude": 22.7,
            "longitude": 88.4,
            "area_value": 5.0,
            "area_unit": "acre",
        },
        headers=headers,
    )
    assert farm_res.status_code == 200
    farm = farm_res.json()
    farm_id = farm["id"]
    assert farm["farm_name"] == "Main Green Farm"
    assert farm["total_area_m2"] == pytest.approx(5.0 * 4046.86, rel=1e-3)

    # Step 2: Create Fields
    field_a_res = client.post(
        "/api/v1/farmer/fields",
        json={
            "farm_id": farm_id,
            "field_name": "Field A",
            "area_value": 2.0,
            "area_unit": "acre",
            "soil_type": "Clay Loam",
            "soil_test_available": True,
            "ph": 6.5,
            "ph_provenance": "MEASURED",
            "nitrogen": 90.0,
            "nitrogen_provenance": "MEASURED",
        },
        headers=headers,
    )
    assert field_a_res.status_code == 200
    field_a = field_a_res.json()
    field_a_id = field_a["id"]

    field_b_res = client.post(
        "/api/v1/farmer/fields",
        json={
            "farm_id": farm_id,
            "field_name": "Field B",
            "area_value": 3.0,
            "area_unit": "acre",
            "soil_type": "Sandy Loam",
            "soil_test_available": False,
        },
        headers=headers,
    )
    assert field_b_res.status_code == 200
    field_b_id = field_b_res.json()["id"]

    # Step 3: Add Crops (Rice to Field A, Potato to Field B)
    crop_a_res = client.post(
        "/api/v1/farmer/crops",
        json={
            "field_id": field_a_id,
            "crop_name": "Rice",
            "sowing_date": "2026-08-15",
            "growth_stage": "Vegetative",
            "status": "ACTIVE",
        },
        headers=headers,
    )
    assert crop_a_res.status_code == 200

    crop_b_res = client.post(
        "/api/v1/farmer/crops",
        json={
            "field_id": field_b_id,
            "crop_name": "Potato",
            "sowing_date": "2026-09-01",
            "growth_stage": "Early Growth",
            "status": "ACTIVE",
        },
        headers=headers,
    )
    assert crop_b_res.status_code == 200

    # Step 4: Fetch Aggregated Farm Command Center Dashboard
    dash_res = client.get("/api/v1/farmer/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash = dash_res.json()

    assert dash["total_farm_area"] == 5.0
    assert dash["active_crops_count"] == 2
    assert dash["fields_count"] == 2

    # Active Crops Cards
    crop_names = [card["crop_name"] for card in dash["active_crop_cards"]]
    assert "Rice" in crop_names
    assert "Potato" in crop_names

    # Soil Intelligence - Test Scenario 4 (pH=6.5 measured, N=90 measured, P=unknown, K=unknown)
    soil_impact_rice = next(s for s in dash["soil_impacts"] if s["crop_name"] == "Rice")
    assert "6.5" in soil_impact_rice["ph_status"]
    assert "MEASURED" in soil_impact_rice["ph_status"]
    assert "90.0" in soil_impact_rice["n_status"]
    assert soil_impact_rice["p_status"] == "Unknown"

    # Soil Intelligence - Test Scenario 5 (No soil test for Field B / Potato)
    soil_impact_potato = next(s for s in dash["soil_impacts"] if s["crop_name"] == "Potato")
    assert "Soil test recommended" in soil_impact_potato["impact_text"]

    # Market Watch - Separate for Rice vs Potato
    mkt_crops = [m["crop_name"] for m in dash["market_watch"]]
    assert "Rice" in mkt_crops
    assert "Potato" in mkt_crops


def test_edit_crop_updates_intelligence():
    headers = {"X-User-ID": "test_user_scenario2"}

    # Setup Farm + Field + Rice
    farm = client.post("/api/v1/farmer/farms", json={"farm_name": "Farm X", "latitude": 22.0, "longitude": 88.0, "area_value": 2.0}, headers=headers).json()
    field = client.post("/api/v1/farmer/fields", json={"farm_id": farm["id"], "field_name": "Field X", "area_value": 2.0}, headers=headers).json()
    crop = client.post("/api/v1/farmer/crops", json={"field_id": field["id"], "crop_name": "Rice", "status": "ACTIVE"}, headers=headers).json()

    # Verify Rice is present
    dash1 = client.get("/api/v1/farmer/dashboard", headers=headers).json()
    assert any(card["crop_name"] == "Rice" for card in dash1["active_crop_cards"])

    # Edit Rice -> Tomato
    edit_res = client.put(f"/api/v1/farmer/crops/{crop['id']}", json={"crop_name": "Tomato"}, headers=headers)
    assert edit_res.status_code == 200

    # Verify Rice is gone and Tomato is present
    dash2 = client.get("/api/v1/farmer/dashboard", headers=headers).json()
    crop_names2 = [card["crop_name"] for card in dash2["active_crop_cards"]]
    assert "Rice" not in crop_names2
    assert "Tomato" in crop_names2
