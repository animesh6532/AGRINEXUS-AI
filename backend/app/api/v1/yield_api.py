"""
Crop Yield Prediction API Router.
"""

from fastapi import APIRouter, HTTPException, status
from ...schemas.yield_schema import YieldPredictRequest, YieldPredictResponse
from ...services.model_registry import ModelRegistry

router = APIRouter(prefix="/yield", tags=["yield"])


@router.post(
    "/predict",
    response_model=YieldPredictResponse,
    summary="Predict crop yield with 95% empirical prediction interval",
    description="Uses XGBoost Regressor model fitted on Indian Agricultural Crop Yield dataset to forecast crop yield with empirical uncertainty bounds."
)
async def predict_yield(payload: YieldPredictRequest):
    """Predict crop yield."""
    registry = ModelRegistry()
    try:
        res = registry.predict_yield(payload.model_dump())
        return YieldPredictResponse(**res)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Inference error: {str(e)}")
