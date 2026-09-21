"""
Soil Organic Carbon Analysis API Router.
"""

from fastapi import APIRouter, HTTPException, status
from ...schemas.soil import SoilAnalyzeRequest, SoilAnalyzeResponse
from ...services.model_registry import ModelRegistry

router = APIRouter(prefix="/soil", tags=["soil"])


@router.post(
    "/analyze",
    response_model=SoilAnalyzeResponse,
    summary="Predict Soil Organic Carbon (g/kg) with empirical prediction interval",
    description="Uses HistGradientBoostingRegressor model fitted on LUCAS European Topsoil dataset to predict Soil Organic Carbon (OC) in g/kg with 95% empirical prediction interval."
)
async def analyze_soil(payload: SoilAnalyzeRequest):
    """Predict Soil Organic Carbon (SOC)."""
    registry = ModelRegistry()
    try:
        res = registry.predict_soil(payload.model_dump(by_alias=True))
        return SoilAnalyzeResponse(**res)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Inference error: {str(e)}")
