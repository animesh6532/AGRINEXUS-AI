"""
Fertilizer Recommendation API Router.
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File
from ...schemas.fertilizer import (
    FertilizerRecommendRequest,
    FertilizerRecommendResponse,
    FertilizerImageRequest,
    FertilizerImageResponse,
    NearbyShopsRequest,
    NearbyShopsResponse,
    OCRSoilReportResponse,
    SoilVisualScanResponse,
)
from ...services.model_registry import ModelRegistry
from ...services.fertilizer_image_resolver import FertilizerImageResolver
from ...services.nearby_shops_service import NearbyShopsService
from ...services.ocr_service import OCRSoilTestService
from ...services.cv_service import CVService

router = APIRouter(prefix="/fertilizer", tags=["fertilizer"])


@router.post(
    "/recommend",
    response_model=FertilizerRecommendResponse,
    summary="Recommend fertilizer formulation",
    description="Uses LightGBM model trained on Western Maharashtra soil/crop data to recommend a fertilizer formulation."
)
async def recommend_fertilizer(payload: FertilizerRecommendRequest):
    """Predict fertilizer formulation recommendation."""
    registry = ModelRegistry()
    try:
        res = registry.predict_fertilizer(payload.model_dump(by_alias=True))
        return FertilizerRecommendResponse(**res)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Inference error: {str(e)}")


@router.post(
    "/resolve-image",
    response_model=FertilizerImageResponse,
    summary="Resolve fertilizer product image",
    description="Resolves verified product images using catalogue, Pexels API, SerpApi, or clean fallback placeholders."
)
async def resolve_fertilizer_image(payload: FertilizerImageRequest):
    """Resolve product image for predicted fertilizer formulation."""
    try:
        res = FertilizerImageResolver.resolve_fertilizer_image(payload.fertilizer_name)
        return FertilizerImageResponse(**res)
    except Exception as e:
        return FertilizerImageResponse(attribution=f"Product image unavailable ({str(e)})")


@router.post(
    "/nearby-shops",
    response_model=NearbyShopsResponse,
    summary="Search nearby fertilizer & agro-input shops",
    description="Uses Google Places API (New) or spatial dealer search to locate nearby fertilizer suppliers around user GPS coordinates."
)
async def find_nearby_shops(payload: NearbyShopsRequest):
    """Find nearby fertilizer suppliers around GPS location."""
    try:
        shops = NearbyShopsService.find_nearby_shops(
            latitude=payload.latitude,
            longitude=payload.longitude,
            radius_km=payload.radius_km or 25.0,
            sort_by=payload.sort_by or "nearest"
        )
        return NearbyShopsResponse(
            success=True,
            total_found=len(shops),
            radius_km=payload.radius_km or 25.0,
            shops=shops
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Nearby shops search error: {str(e)}")


@router.post(
    "/ocr-soil-report",
    response_model=OCRSoilReportResponse,
    summary="Scan and extract soil test report",
    description="Uses document OCR to extract N, P, K, pH, and Organic Carbon from Soil Health Cards for user verification."
)
async def ocr_soil_report(file: UploadFile = File(...)):
    """Extract soil test parameters from uploaded report image."""
    try:
        image_bytes = await file.read()
        res = OCRSoilTestService.extract_soil_report(image_bytes)
        return OCRSoilReportResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OCR extraction failed: {str(e)}")


@router.post(
    "/soil-visual-scan",
    response_model=SoilVisualScanResponse,
    summary="Visual observation analysis of soil photo",
    description="Analyzes visual surface characteristics (color tone, texture appearance). Explicitly labeled as visual observation, not laboratory result."
)
async def soil_visual_scan(file: UploadFile = File(...)):
    """Analyze visual soil characteristics from uploaded image."""
    try:
        image_bytes = await file.read()
        res = CVService.inspect_soil_visual(image_bytes)
        return SoilVisualScanResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Soil visual scan failed: {str(e)}")

