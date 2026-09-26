"""
Crop Recommendation API Router.
"""

from fastapi import APIRouter, HTTPException, status
from ...schemas.crop import (
    CropRecommendationRequest,
    CropRecommendationResponse,
    SmartCropRequest,
    SmartCropResponse
)
from ...services.model_registry import ModelRegistry
from ...services.agriculture.smart_crop_recommender import SmartCropRecommender

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


@router.post(
    "/recommend-smart",
    response_model=SmartCropResponse,
    summary="Smart Crop Advisor multi-source recommendation engine",
    description="Combines location, weather telemetry, soil context, regional season engine, crop calendar, and frozen ExtraTrees ML model to rank crop suitability."
)
async def recommend_crop_smart(payload: SmartCropRequest):
    """Generate smart agricultural crop recommendations."""
    recommender = SmartCropRecommender()
    try:
        res = await recommender.generate_smart_recommendations(
            latitude=payload.location.latitude,
            longitude=payload.location.longitude,
            mode=payload.mode,
            location_name=payload.location.displayName,
            district=payload.location.district,
            state=payload.location.state,
            country=payload.location.country,
            user_n=payload.soil.nitrogen if payload.soil else None,
            user_p=payload.soil.phosphorus if payload.soil else None,
            user_k=payload.soil.potassium if payload.soil else None,
            user_ph=payload.soil.ph if payload.soil else None,
            weather_override_temp=payload.weather_override.temperature if payload.weather_override else None,
            weather_override_humidity=payload.weather_override.humidity if payload.weather_override else None,
            weather_override_rain=payload.weather_override.rainfall if payload.weather_override else None,
            water_availability=payload.farm.water_availability if payload.farm and payload.farm.water_availability else "unknown",
            farm_area_acres=payload.farm.area_acres if payload.farm else None,
            category_filter=payload.preferences.category if payload.preferences else "all"
        )
        return SmartCropResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Smart recommendation error: {str(e)}")

