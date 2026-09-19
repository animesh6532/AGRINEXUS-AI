"""
Crop Recommendation API Router.
"""

from fastapi import APIRouter, HTTPException, status
from ...schemas.crop import CropRecommendationRequest, CropRecommendationResponse
from ...services.model_registry import ModelRegistry

router = APIRouter(prefix="/crop", tags=["crop"])


@router.post(
    "/recommend",
    response_model=CropRecommendationResponse,
    summary="Recommend optimal crop based on soil and climate factors",
    description="Uses ExtraTreesClassifier model and IsolationForest anomaly detection to recommend optimal crop for given N, P, K, temperature, humidity, pH, and rainfall."
)
async def recommend_crop(payload: CropRecommendationRequest):
    """Predict optimal crop recommendation."""
    registry = ModelRegistry()
    try:
        res = registry.predict_crop(payload.model_dump())
        return CropRecommendationResponse(**res)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Inference error: {str(e)}")
