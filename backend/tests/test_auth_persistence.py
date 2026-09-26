"""
Integration tests for authentication, user session persistence across logout/login,
and cross-user authorization isolation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import models
from app.core.dependencies import get_db

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
    yield
    models.Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)


client = TestClient(app)


def test_auth_registration_login_flow():
    # 1. Register User A
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "farmer_a@agrinexus.ai",
            "password": "Password123!",
            "full_name": "Farmer A",
            "phone": "+919876543210",
        },
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == "farmer_a@agrinexus.ai"

    token_a = reg_data["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Login User A
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer_a@agrinexus.ai", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"]["email"] == "farmer_a@agrinexus.ai"

    # 3. Create Farm + Field + Crop under User A
    farm_res = client.post(
        "/api/v1/farmer/farms",
        json={
            "farm_name": "Green Valley Farm",
            "latitude": 22.57,
            "longitude": 88.36,
            "area_value": 3.5,
            "area_unit": "acre",
        },
        headers=headers_a,
    )
    assert farm_res.status_code == 200
    farm = farm_res.json()

    field_res = client.post(
        "/api/v1/farmer/fields",
        json={
            "farm_id": farm["id"],
            "field_name": "North Field 01",
            "area_value": 2.0,
            "area_unit": "acre",
            "centroid_lat": 22.571,
            "centroid_lng": 88.361,
            "boundary_geojson": '{"type":"Polygon","coordinates":[[[88.361,22.571],[88.362,22.571],[88.362,22.572],[88.361,22.572],[88.361,22.571]]]}',
        },
        headers=headers_a,
    )
    assert field_res.status_code == 200
    field = field_res.json()

    crop_res = client.post(
        "/api/v1/farmer/crops",
        json={
            "field_id": field["id"],
            "crop_name": "Rice",
            "growth_stage": "Vegetative",
            "status": "ACTIVE",
        },
        headers=headers_a,
    )
    assert crop_res.status_code == 200

    # 4. SIMULATE LOGOUT & RE-LOGIN USER A
    # Re-authenticate to simulate logging back in from a fresh browser session
    relogin_res = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer_a@agrinexus.ai", "password": "Password123!"},
    )
    assert relogin_res.status_code == 200
    re_token = relogin_res.json()["access_token"]
    re_headers = {"Authorization": f"Bearer {re_token}"}

    # Fetch User A's dashboard after re-login
    dash_res = client.get("/api/v1/farmer/dashboard", headers=re_headers)
    assert dash_res.status_code == 200
    dash = dash_res.json()

    # ASSERT: All persistent entities remain intact in database!
    assert dash["farmer"]["email"] == "farmer_a@agrinexus.ai"
    assert dash["total_farm_area"] == 3.5
    assert dash["fields_count"] == 1
    assert dash["active_crops_count"] == 1
    assert dash["active_crop_cards"][0]["crop_name"] == "Rice"
    assert dash["active_crop_cards"][0]["field_name"] == "North Field 01"


def test_cross_user_isolation():
    # User A
    client.post("/api/v1/auth/register", json={"email": "usera@farm.in", "password": "passA123", "full_name": "User A"})
    token_a = client.post("/api/v1/auth/login", json={"email": "usera@farm.in", "password": "passA123"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    client.post("/api/v1/auth/register", json={"email": "userb@farm.in", "password": "passB123", "full_name": "User B"})
    token_b = client.post("/api/v1/auth/login", json={"email": "userb@farm.in", "password": "passB123"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates Farm A
    farm_a = client.post("/api/v1/farmer/farms", json={"farm_name": "Farm A", "latitude": 20.0, "longitude": 80.0, "area_value": 1.0}, headers=headers_a).json()

    # User B fetches dashboard
    dash_b = client.get("/api/v1/farmer/dashboard", headers=headers_b).json()

    # User B MUST NOT see User A's farm or fields
    assert dash_b["farmer"]["email"] == "userb@farm.in"
    assert dash_b["fields_count"] == 0
    assert len(dash_b["farmer"]["farms"]) == 0

    # User B attempts to delete User A's farm -> 404
    del_res = client.delete(f"/api/v1/farmer/farms/{farm_a['id']}", headers=headers_b)
    assert del_res.status_code == 404
