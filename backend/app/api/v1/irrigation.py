"""
Irrigation Intelligence & Water Management API Router.
Provides digital irrigation advisory, FAO water balance (ET0, Kc, ETc),
7-day plans, water budgets, What-If simulation, logging, and ML prediction.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...core.dependencies import get_db
from ...core.logging import logger
from ...schemas.irrigation import (
    IrrigationPredictRequest,
    IrrigationPredictResponse,
    IrrigationLogCreate,
    IrrigationLogResponse,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
    IrrigationIntelligenceResponse,
)
from ...services.irrigation_intelligence import IrrigationIntelligenceService
from ...services.model_registry import ModelRegistry

router = APIRouter(prefix="/irrigation", tags=["Irrigation Intelligence & Water Management"])


def get_current_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> str:
    """Extract authenticated user ID from request header or default."""
    return x_user_id.strip() if x_user_id and x_user_id.strip() else "default_farmer"


@router.get(
    "/intelligence",
    response_model=IrrigationIntelligenceResponse,
    summary="Get full Irrigation Intelligence & Water Management advisory for a field",
)
async def get_irrigation_intelligence(
    field_id: Optional[int] = Query(None, description="Optional target field ID"),
    lat: Optional[float] = Query(None, description="Optional latitude override"),
    lon: Optional[float] = Query(None, description="Optional longitude override"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Retrieve comprehensive digital irrigation advisory:
    FAO water balance (ET0, Kc, ETc), soil moisture trajectory, 7-day water plan,
    water budget, irrigation window, volume requirements, What-If scenarios, and ML forecast.
    """
    service = IrrigationIntelligenceService(db)
    try:
        intel = await service.get_intelligence(user_id=user_id, field_id=field_id, lat=lat, lon=lon)
        return intel
    except Exception as e:
        logger.error(f"Error generating irrigation intelligence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate irrigation intelligence: {str(e)}",
        )


@router.post(
    "/log",
    response_model=IrrigationLogResponse,
    summary="Log a completed irrigation event for a field",
)
def log_irrigation_event(
    payload: IrrigationLogCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Record an applied irrigation event (water depth mm, method, duration, notes)."""
    service = IrrigationIntelligenceService(db)
    try:
        log_entry = service.log_irrigation(
            user_id=user_id,
            field_id=payload.field_id,
            water_amount_mm=payload.water_amount_mm,
            method=payload.method,
            duration_minutes=payload.duration_minutes,
            notes=payload.notes,
            logged_at=payload.logged_at,
        )
        return log_entry.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error logging irrigation event: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/logs",
    response_model=List[IrrigationLogResponse],
    summary="Get historical irrigation logs for a field",
)
def get_irrigation_logs(
    field_id: int = Query(..., description="Target field ID"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieve historical irrigation log records for a field."""
    service = IrrigationIntelligenceService(db)
    logs = service.get_irrigation_logs(user_id=user_id, field_id=field_id)
    return [log.to_dict() for log in logs]


@router.post(
    "/simulate",
    response_model=WhatIfSimulationResponse,
    summary="Simulate What-If water management scenarios",
)
def simulate_what_if(
    payload: WhatIfSimulationRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Simulate projected soil water content and deficit for custom irrigation/rainfall scenarios."""
    service = IrrigationIntelligenceService(db)
    res = service.simulate_what_if(
        user_id=user_id,
        field_id=payload.field_id,
        custom_irrigation_mm=payload.custom_irrigation_mm or 0.0,
        delay_hours=payload.delay_hours or 0,
        simulated_rain_mm=payload.simulated_rain_mm or 0.0,
    )
    return res


@router.post(
    "/predict",
    response_model=IrrigationPredictResponse,
    summary="Predict 3-hour ahead soil water content and irrigation needs (ML Model Inference)",
    description="Preserved ML model inference endpoint for 3-hour ahead SWC prediction and persistence benchmark.",
)
async def predict_irrigation(payload: IrrigationPredictRequest):
    """Predict 3-hour soil water content using the frozen ML model."""
    registry = ModelRegistry()
    try:
        res = registry.predict_irrigation(payload.model_dump())
        return IrrigationPredictResponse(**res)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Inference error: {str(e)}")
