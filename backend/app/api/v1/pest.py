"""
Pest Recognition & Risk Assessment API Router.
Separates visual insect classification (/predict) from environmental risk modeling (/risk).
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, status
from ...schemas.pest import VisualPestPredictResponse, PestRiskRequest, PestRiskResponse
from ...services.model_registry import ModelRegistry
from ...core.config import settings

router = APIRouter(prefix="/pest", tags=["pest"])


@router.post(
    "/predict",
    response_model=VisualPestPredictResponse,
    summary="Classify insect pest species from uploaded photo",
    description="Uses PyTorch MobileNetV3 Small (102 classes from IP102 benchmark). Performs single-insect visual classification, NOT bounding-box object detection."
)
async def predict_pest_visual(file: UploadFile = File(...)):
    """Predict insect pest category from image upload."""
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file MIME type '{file.content_type}'. Allowed types: {settings.ALLOWED_IMAGE_TYPES}"
        )

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    registry = ModelRegistry()
    try:
        res = registry.predict_pest_visual(contents)
        return VisualPestPredictResponse(**res)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Visual pest prediction error: {str(e)}")


@router.post(
    "/risk",
    response_model=PestRiskResponse,
    summary="Assess environmental pest outbreak risk level",
    description="Uses scikit-learn Pipeline (RandomForest) to classify environmental pest severity risk (Low, Medium, High) based on climate and soil factors."
)
async def predict_pest_risk(payload: PestRiskRequest):
    """Predict environmental pest risk level."""
    registry = ModelRegistry()
    try:
        res = registry.predict_pest_risk(payload.model_dump())
        return PestRiskResponse(**res)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Environmental pest risk inference error: {str(e)}")
