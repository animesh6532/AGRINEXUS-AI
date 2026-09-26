"""
API endpoints for Farmer Profile, Farms, Fields, Crops, and Farm Command Center Intelligence.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_db
from ...core.logging import logger
from ...schemas.farmer import (
    CropPlantingCreate,
    CropPlantingResponse,
    CropPlantingUpdate,
    FarmCreate,
    FarmDashboardResponse,
    FarmerProfileCreate,
    FarmerProfileResponse,
    FarmerProfileUpdate,
    FarmResponse,
    FarmUpdate,
    FieldCreate,
    FieldResponse,
    FieldUpdate,
)
from ...database.models import User
from ...services.farmer_service import FarmerRepository, FarmIntelligenceService
from .auth import get_current_user

router = APIRouter(prefix="/farmer", tags=["Farmer Profile & Command Center"])


def get_current_user_id(user: User = Depends(get_current_user)) -> str:
    """Extract authenticated user ID from authenticated database User entity."""
    return user.id


@router.get("/profile", response_model=FarmerProfileResponse)
def get_farmer_profile(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieve authenticated farmer profile with farms, fields, and crops."""
    repo = FarmerRepository(db)
    profile = repo.get_or_create_profile(user_id)
    return profile.to_dict()


@router.put("/profile", response_model=FarmerProfileResponse)
def update_farmer_profile(
    payload: FarmerProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update farmer profile details."""
    repo = FarmerRepository(db)
    updated = repo.update_profile(user_id, payload.model_dump(exclude_unset=True))
    return updated.to_dict()


@router.get("/dashboard")
async def get_farmer_dashboard(
    lat: Optional[float] = Query(None, description="Optional override latitude"),
    lon: Optional[float] = Query(None, description="Optional override longitude"),
    display_name: Optional[str] = Query(None, description="Optional location name"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get full aggregated personalized farm intelligence for the Farmer Command Center.
    """
    service = FarmIntelligenceService(db)
    location_override = None
    if lat is not None and lon is not None:
        location_override = {"latitude": lat, "longitude": lon, "displayName": display_name}

    dashboard = await service.get_dashboard(user_id, location_override=location_override)
    return dashboard


@router.post("/farms")
def create_farm(
    payload: FarmCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new farm for the authenticated farmer."""
    repo = FarmerRepository(db)
    farm = repo.create_farm(user_id, payload.model_dump())
    return farm.to_dict()


@router.put("/farms/{farm_id}")
def update_farm(
    farm_id: int,
    payload: FarmUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update an existing farm."""
    repo = FarmerRepository(db)
    updated = repo.update_farm(farm_id, user_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Farm not found or unauthorized")
    return updated.to_dict()


@router.delete("/farms/{farm_id}")
def delete_farm(
    farm_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a farm."""
    repo = FarmerRepository(db)
    success = repo.delete_farm(farm_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Farm not found or unauthorized")
    return {"success": True, "message": "Farm deleted successfully"}


@router.post("/fields")
def create_field(
    payload: FieldCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new field within a farm."""
    repo = FarmerRepository(db)
    field = repo.create_field(user_id, payload.model_dump())
    if not field:
        raise HTTPException(status_code=404, detail="Farm not found or unauthorized")
    return field.to_dict()


@router.put("/fields/{field_id}")
def update_field(
    field_id: int,
    payload: FieldUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update field information and soil lab measurements."""
    repo = FarmerRepository(db)
    updated = repo.update_field(field_id, user_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Field not found or unauthorized")
    return updated.to_dict()


@router.delete("/fields/{field_id}")
def delete_field(
    field_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a field."""
    repo = FarmerRepository(db)
    success = repo.delete_field(field_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Field not found or unauthorized")
    return {"success": True, "message": "Field deleted successfully"}


@router.post("/crops")
def create_crop_planting(
    payload: CropPlantingCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add a new crop planting to a field."""
    repo = FarmerRepository(db)
    crop = repo.create_crop_planting(user_id, payload.model_dump())
    if not crop:
        raise HTTPException(status_code=404, detail="Field not found or unauthorized")
    return crop.to_dict()


@router.put("/crops/{crop_id}")
def update_crop_planting(
    crop_id: int,
    payload: CropPlantingUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update crop planting details, sowing date, or growth stage."""
    repo = FarmerRepository(db)
    updated = repo.update_crop_planting(crop_id, user_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Crop planting not found or unauthorized")
    return updated.to_dict()


@router.delete("/crops/{crop_id}")
def delete_crop_planting(
    crop_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a crop planting."""
    repo = FarmerRepository(db)
    success = repo.delete_crop_planting(crop_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Crop planting not found or unauthorized")
    return {"success": True, "message": "Crop planting deleted successfully"}


@router.post("/observations")
def create_plant_observation(
    payload: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new plant/field observation or scouting record."""
    repo = FarmerRepository(db)
    obs = repo.create_plant_observation(user_id, payload)
    if not obs:
        raise HTTPException(status_code=404, detail="Field not found or unauthorized")
    return obs.to_dict()


@router.post("/actions/{action_id}/complete")
def complete_action_item(
    action_id: str,
    payload: Optional[Dict[str, Any]] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark a personalized action plan item as DONE, SNOOZED, or DISMISSED."""
    repo = FarmerRepository(db)
    status_val = (payload or {}).get("status", "DONE")
    success = repo.complete_action_item(action_id, user_id, status=status_val)
    return {"success": True, "action_id": action_id, "status": status_val}


@router.get("/notifications/preferences")
def get_notification_preferences(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get farmer notification channel and category preferences."""
    from ...services.notification_service import NotificationDispatcher
    repo = FarmerRepository(db)
    profile = repo.get_or_create_profile(user_id)
    dispatcher = NotificationDispatcher(db)
    prefs = dispatcher.get_or_create_preferences(profile.id)
    return prefs.to_dict()


@router.put("/notifications/preferences")
def update_notification_preferences(
    payload: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update farmer notification channel and category preferences."""
    from ...services.notification_service import NotificationDispatcher
    repo = FarmerRepository(db)
    profile = repo.get_or_create_profile(user_id)
    dispatcher = NotificationDispatcher(db)
    updated = dispatcher.update_preferences(profile.id, payload)
    return updated.to_dict()

