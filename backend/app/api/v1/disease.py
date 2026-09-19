"""
Plant Disease Detection API Router.
"""

from fastapi import APIRouter, File, UploadFile, Query, HTTPException, status
from ...schemas.disease import DiseasePredictResponse
from ...services.model_registry import ModelRegistry
from ...core.config import settings

router = APIRouter(prefix="/disease", tags=["disease"])


@router.post(
    "/predict",
    response_model=DiseasePredictResponse,
    summary="Detect plant leaf disease from uploaded image",
    description="Uses PyTorch ResNet18 visual classification model (39 classes) with OpenCV image quality validation and optional Grad-CAM explainability."
)
async def predict_disease(
    file: UploadFile = File(...),
    include_gradcam: bool = Query(False, description="Set to true to generate Grad-CAM visual heatmap overlay")
):
    """Predict plant disease from image file upload."""
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
        res = registry.predict_disease(contents, include_gradcam=include_gradcam)
        return DiseasePredictResponse(**res)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Disease prediction error: {str(e)}")

