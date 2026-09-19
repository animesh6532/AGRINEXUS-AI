"""
Fertilizer Recommendation API Router.
"""

from fastapi import APIRouter, HTTPException, status
from ...schemas.fertilizer import FertilizerRecommendRequest, FertilizerRecommendResponse
from ...services.model_registry import ModelRegistry

router = APIRouter(prefix="/fertilizer", tags=["fertilizer"])


@router.post(
    "/recommend",
    response_model=FertilizerRecommendResponse,
    summary="Recommend commercial fertilizer formulation",
    description="Uses scikit-learn Pipeline to recommend product formulations based on soil NPK, pH, climate, and crop context (Western Maharashtra dataset scope)."
)
async def recommend_fertilizer(payload: FertilizerRecommendRequest):
    """Predict commercial fertilizer formulation recommendation."""
    registry = ModelRegistry()
    try:
        res = registry.predict_fertilizer(payload.model_dump(by_alias=True))
        return FertilizerRecommendResponse(**res)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Inference error: {str(e)}")
