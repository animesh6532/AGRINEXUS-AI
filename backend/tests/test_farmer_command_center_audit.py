"""
End-to-End Forensic Audit & Verification Test Suite for Farmer Profile & Farm Command Center.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.connection import get_db
from app.database.models import Base, User, FarmerProfile, Farm, Field, CropPlanting, NotificationPreferenceRecord
from app.core.security import hash_password, create_access_token

# Create isolated test client
client = TestClient(app)


def test_farmer_profile_e2e_flow():
    """Verify complete end-to-end user flow: Profile -> Farm -> Field -> Crop -> Preferences."""
    # 1. Register new test user
    test_email = f"audit_farmer_{uuid.uuid4().hex[:6]}@agrinexus.ai"
    reg_payload = {
        "email": test_email,
        "password": "Password123!",
        "full_name": "Audit Test Farmer",
        "phone": "+91 9876543210",
        "preferred_language": "en"
    }

    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    auth_data = reg_resp.json()
    token = auth_data["access_token"]
    user_id = auth_data["user"]["id"]
    headers = {"Authorization": f"Bearer {token}", "X-User-ID": user_id}

    # 2. Get initial profile
    prof_resp = client.get("/api/v1/farmer/profile", headers=headers)
    assert prof_resp.status_code == 200
    prof_data = prof_resp.json()
    assert prof_data["full_name"] == "Audit Test Farmer"
    assert prof_data["email"] == test_email

    # 3. Update Farmer Profile
    update_payload = {
        "full_name": "Updated Audit Farmer",
        "phone": "+91 9999988888",
        "timezone": "Asia/Kolkata",
        "location": "Barasat, North 24 Parganas, West Bengal",
        "preferred_units": "acre"
    }
    put_resp = client.put("/api/v1/farmer/profile", json=update_payload, headers=headers)
    assert put_resp.status_code == 200
    updated_prof = put_resp.json()
    assert updated_prof["full_name"] == "Updated Audit Farmer"
    assert updated_prof["timezone"] == "Asia/Kolkata"

    # 4. Create Farm
    farm_payload = {
        "farm_name": "Green Gold Command Farm",
        "location_name": "Barasat Sector 4",
        "latitude": 22.72,
        "longitude": 88.48,
        "area_value": 5.5,
        "area_unit": "acre"
    }
    farm_resp = client.post("/api/v1/farmer/farms", json=farm_payload, headers=headers)
    assert farm_resp.status_code == 200
    farm_data = farm_resp.json()
    farm_id = farm_data["id"]
    assert farm_data["farm_name"] == "Green Gold Command Farm"
    assert farm_data["total_area_m2"] > 20000.0  # Normalized area check

    # 5. Create Field with Boundary Polygon
    geojson_polygon = {
        "type": "Polygon",
        "coordinates": [[
            [88.48, 22.72],
            [88.485, 22.72],
            [88.485, 22.725],
            [88.48, 22.725],
            [88.48, 22.72]
        ]]
    }
    field_payload = {
        "farm_id": farm_id,
        "field_name": "North Field Polygon A",
        "area_value": 2.5,
        "area_unit": "acre",
        "soil_type": "Clay Loam",
        "boundary_geojson": geojson_polygon
    }
    field_resp = client.post("/api/v1/farmer/fields", json=field_payload, headers=headers)
    assert field_resp.status_code == 200
    field_data = field_resp.json()
    field_id = field_data["id"]
    assert field_data["field_name"] == "North Field Polygon A"
    assert field_data["geometry_source"] == "GEOMETRIC"
    assert field_data["total_area_m2"] > 0

    # 6. Create Active Crop Planting
    crop_payload = {
        "field_id": field_id,
        "crop_name": "Rice",
        "variety": "Swarna Masuri",
        "sowing_date": "2026-06-15",
        "growth_stage": "Vegetative",
        "status": "ACTIVE"
    }
    crop_resp = client.post("/api/v1/farmer/crops", json=crop_payload, headers=headers)
    assert crop_resp.status_code == 200
    crop_data = crop_resp.json()
    crop_id = crop_data["id"]
    assert crop_data["crop_name"] == "Rice"
    assert crop_data["growth_stage"] == "Vegetative"

    # 7. Get Command Center Aggregated Dashboard
    dash_resp = client.get("/api/v1/farmer/dashboard", headers=headers)
    assert dash_resp.status_code == 200
    dash = dash_resp.json()
    assert dash["farmer"]["full_name"] == "Updated Audit Farmer"
    assert dash["active_crops_count"] >= 1
    assert dash["fields_count"] >= 1
    assert "weather_impacts" in dash
    assert "risks_and_opportunities" in dash
    assert "action_plan" in dash

    # 8. Notification Preferences GET & PUT
    notif_get = client.get("/api/v1/farmer/notifications/preferences", headers=headers)
    assert notif_get.status_code == 200
    prefs = notif_get.json()
    assert "channels" in prefs or "in_app_enabled" in prefs

    update_notif_payload = {
        "channels": {"in_app": True, "email": True, "sms": False, "whatsapp": False},
        "categories": {"critical_risks": True, "weather": True, "crop_health": True, "market": True},
        "quiet_hours": {"enabled": True, "start": "23:00", "end": "05:00", "critical_override": True}
    }
    notif_put = client.put("/api/v1/farmer/notifications/preferences", json=update_notif_payload, headers=headers)
    assert notif_put.status_code == 200
    updated_prefs = notif_put.json()
    assert updated_prefs["quiet_hours"]["enabled"] is True

    # 9. Clean deletion test (Delete Crop, Field, Farm)
    del_crop = client.delete(f"/api/v1/farmer/crops/{crop_id}", headers=headers)
    assert del_crop.status_code == 200

    del_field = client.delete(f"/api/v1/farmer/fields/{field_id}", headers=headers)
    assert del_field.status_code == 200

    del_farm = client.delete(f"/api/v1/farmer/farms/{farm_id}", headers=headers)
    assert del_farm.status_code == 200
