"""
Unit tests for Irrigation Intelligence & Water Management System endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import models
from app.core.dependencies import get_db
from app.services.model_registry import ModelRegistry

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


@pytest.fixture(autouse=True)
def setup_db():
    models.Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    ModelRegistry().load_all_models()
    yield
    models.Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)


client = TestClient(app)


def test_irrigation_intelligence_auto_profile():
    headers = {"X-User-ID": "irrigation_test_user_1"}

    # Fetch intelligence (should auto-create default farm/field if none exist)
    res = client.get("/api/v1/irrigation/intelligence", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "field_context" in data
    assert "water_status" in data
    assert "decision" in data
    assert "et0" in data
    assert "water_balance_trajectory" in data
    assert "seven_day_plan" in data
    assert "water_budget" in data
    assert "ml_forecast" in data
    assert "what_if_scenarios" in data

    assert data["field_context"]["crop_name"] in ("Rice", "Paddy", "Maize", "Potato", "Tomato", "Wheat")
    assert data["et0"]["et0_today_mm"] > 0.0


def test_irrigation_logging_flow():
    headers = {"X-User-ID": "irrigation_log_user"}

    # Setup Farm & Field
    farm = client.post(
        "/api/v1/farmer/farms",
        json={"farm_name": "Log Farm", "area_value": 3.0, "latitude": 22.5, "longitude": 88.5},
        headers=headers,
    ).json()

    field = client.post(
        "/api/v1/farmer/fields",
        json={"farm_id": farm["id"], "field_name": "South Field", "area_value": 2.0},
        headers=headers,
    ).json()

    # Log Irrigation
    log_res = client.post(
        "/api/v1/irrigation/log",
        json={
            "field_id": field["id"],
            "water_amount_mm": 18.0,
            "method": "Drip",
            "duration_minutes": 45,
            "notes": "Evening drip irrigation cycle",
        },
        headers=headers,
    )
    assert log_res.status_code == 200
    log_data = log_res.json()

    assert log_data["water_amount_mm"] == 18.0
    assert log_data["water_amount_liters"] == pytest.approx(18.0 * field["total_area_m2"], rel=1e-3)

    # Retrieve Logs
    get_logs_res = client.get(f"/api/v1/irrigation/logs?field_id={field['id']}", headers=headers)
    assert get_logs_res.status_code == 200
    logs = get_logs_res.json()
    assert len(logs) == 1
    assert logs[0]["notes"] == "Evening drip irrigation cycle"


def test_what_if_simulation():
    headers = {"X-User-ID": "sim_user"}

    farm = client.post(
        "/api/v1/farmer/farms",
        json={"farm_name": "Sim Farm", "area_value": 2.0, "latitude": 22.5, "longitude": 88.5},
        headers=headers,
    ).json()

    field = client.post(
        "/api/v1/farmer/fields",
        json={"farm_id": farm["id"], "field_name": "Sim Field", "area_value": 2.0},
        headers=headers,
    ).json()

    sim_res = client.post(
        "/api/v1/irrigation/simulate",
        json={
            "field_id": field["id"],
            "custom_irrigation_mm": 20.0,
            "delay_hours": 12,
            "simulated_rain_mm": 10.0,
        },
        headers=headers,
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()

    assert sim_data["field_id"] == field["id"]
    assert len(sim_data["scenarios"]) >= 3


def test_preserved_ml_predict_endpoint():
    payload = {
        "SWC": 0.22,
        "SWC_lag1h": 0.225,
        "SWC_lag2h": 0.23,
        "SWC_lag3h": 0.235,
        "SWC_roll6h_mean": 0.23,
        "Rainfall_mm": 0.0,
        "Rain_roll6h_sum": 0.0,
    }
    res = client.post("/api/v1/irrigation/predict", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "ml_predicted_swc_3h" in data
    assert "persistence_swc_3h" in data
    assert "agronomic_status" in data
