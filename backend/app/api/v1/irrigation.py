"""
Irrigation Prediction API Router.
"""

from fastapi import APIRouter, HTTPException, status
from ...schemas.irrigation import IrrigationPredictRequest, IrrigationPredictResponse
from ...services.model_registry import ModelRegistry

router = APIRouter(prefix="/irrigation", tags=["irrigation"])


@router.post(
    "/predict",
    response_model=IrrigationPredictResponse,
    summary="Predict 3-hour ahead soil water content and irrigation needs",
    description="Uses LinearRegression model and benchmark Persistence Baseline (SWC_t+3h = SWC_t) to predict future soil moisture and assess agronomic thresholds."
)
async def predict_irrigation(payload: IrrigationPredictRequest):
    """Predict 3-hour soil water content and assess irrigation status."""
    registry = ModelRegistry()
    try:
        res = registry.predict_irrigation(payload.model_dump())
        return IrrigationPredictResponse(**res)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Inference error: {str(e)}")
