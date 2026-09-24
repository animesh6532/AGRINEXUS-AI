"""
Smart crop recommender orchestrator service.
Integrates Location, Weather Context, Soil Context, Season Engine, Crop Calendar,
Frozen ExtraTrees ML Model, and Crop Suitability Engine to produce ranked crop recommendations.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from .crop_profiles import CROP_PROFILES, get_all_crop_profiles, CropRequirementProfile
from .weather_context import WeatherContextService, WeatherContext
from .soil_context import SoilContextService, SoilContext
from .season_engine import SeasonEngine, SeasonInfo
from .crop_suitability import CropSuitabilityEngine, CropSuitabilityResult
from ..model_registry import ModelRegistry
from ...core.logging import logger


class SmartCropRecommender:
    """Orchestrator for Smart Crop Advisor intelligence pipeline."""

    def __init__(
        self,
        weather_service: Optional[WeatherContextService] = None,
        soil_service: Optional[SoilContextService] = None
    ):
        self.weather_service = weather_service or WeatherContextService()
        self.soil_service = soil_service or SoilContextService()

    async def generate_smart_recommendations(
        self,
        latitude: float,
        longitude: float,
        location_name: Optional[str] = None,
        district: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = "India",
        user_n: Optional[float] = None,
        user_p: Optional[float] = None,
        user_k: Optional[float] = None,
        user_ph: Optional[float] = None,
        weather_override_temp: Optional[float] = None,
        weather_override_humidity: Optional[float] = None,
        weather_override_rain: Optional[float] = None,
        water_availability: str = "unknown",
        farm_area_acres: Optional[float] = None,
        category_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run complete Smart Crop Recommendation pipeline.
        """
        logger.info(f"Starting Smart Crop Recommendation for lat={latitude}, lon={longitude}, state={state}")

        # 1. Weather Context
        weather_ctx = await self.weather_service.get_weather_context(
            latitude=latitude,
            longitude=longitude,
            override_temperature=weather_override_temp,
            override_humidity=weather_override_humidity,
            override_rainfall=weather_override_rain
        )

        # 2. Soil Context
        soil_ctx = self.soil_service.get_soil_context(
            latitude=latitude,
            longitude=longitude,
            user_nitrogen=user_n,
            user_phosphorus=user_p,
            user_potassium=user_k,
            user_ph=user_ph
        )

        # 3. Season Engine
        season_info = SeasonEngine.get_season_info(
            latitude=latitude,
            longitude=longitude,
            state=state or "West Bengal"
        )

        # 4. Check ML Model Input Availability
        ml_probs_map: Dict[str, float] = {}
        ml_available = False
        ml_anomaly_msg: Optional[str] = None

        # ML requires: N, P, K, temperature, humidity, ph, rainfall
        temp_val = weather_ctx.current_temperature or weather_ctx.forecast_temperature_mean
        hum_val = weather_ctx.current_humidity
        ph_val = soil_ctx.ph.value if (soil_ctx.ph and soil_ctx.ph.value is not None) else None
        rain_val = weather_ctx.current_rainfall or weather_ctx.forecast_rainfall_sum

        if (
            user_n is not None and
            user_p is not None and
            user_k is not None and
            temp_val is not None and
            hum_val is not None and
            ph_val is not None and
            rain_val is not None
        ):
            try:
                registry = ModelRegistry()
                if registry.models_meta["crop"].status == "READY":
                    ml_input = {
                        "N": float(user_n),
                        "P": float(user_p),
                        "K": float(user_k),
                        "temperature": float(temp_val),
                        "humidity": float(hum_val),
                        "ph": float(ph_val),
                        "rainfall": float(rain_val)
                    }
                    ml_res = registry.predict_crop(ml_input)
                    ml_available = True
                    ml_anomaly_msg = ml_res.get("anomaly_status")

                    # Map top predictions to probability dict
                    if "top_k_predictions" in ml_res:
                        for item in ml_res["top_k_predictions"]:
                            ml_probs_map[item["crop"].lower()] = item["probability"]
                    # Top prediction gets probability
                    top_crop = ml_res["prediction"].lower()
                    top_conf = ml_res.get("confidence", 0.95)
                    ml_probs_map[top_crop] = top_conf
            except Exception as ml_err:
                logger.warning(f"ML Model inference skipped for smart advisor: {ml_err}")

        # 5. Evaluate all crops in catalogue
        crop_catalogue = get_all_crop_profiles()
        recommendations: List[CropSuitabilityResult] = []

        for profile in crop_catalogue:
            if category_filter and category_filter.lower() != "all":
                if profile.category.lower() != category_filter.lower():
                    continue

            ml_prob = ml_probs_map.get(profile.crop.lower())

            result = CropSuitabilityEngine.evaluate_crop(
                profile=profile,
                weather=weather_ctx,
                soil=soil_ctx,
                season=season_info,
                ml_probability=ml_prob,
                water_availability=water_availability
            )
            recommendations.append(result)

        # Sort recommendations by suitability_score descending
        recommendations.sort(key=lambda r: r.suitability_score, reverse=True)

        # Calculate Overall Data Completeness
        # Location=20%, Weather=20%, Season=20%, Soil pH/Texture=20%, NPK=20%
        loc_score = 1.0
        weath_score = 1.0 if weather_ctx.data_available else 0.0
        seas_score = 1.0
        soil_base_score = 1.0 if soil_ctx.ph and soil_ctx.ph.value is not None else 0.5
        npk_score = sum(1 for v in [user_n, user_p, user_k] if v is not None) / 3.0

        overall_completeness = round(
            (loc_score * 0.2) + (weath_score * 0.2) + (seas_score * 0.2) + (soil_base_score * 0.2) + (npk_score * 0.2),
            2
        )

        return {
            "success": True,
            "engine_version": "1.0.0",
            "mode": "auto" if not any([user_n, user_p, user_k, weather_override_temp]) else "hybrid",
            "data_completeness": overall_completeness,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "display_name": location_name or f"{latitude:.2f}° N, {longitude:.2f}° E",
                "district": district,
                "state": state or season_info.state,
                "country": country
            },
            "season": season_info.model_dump(),
            "weather": weather_ctx.model_dump(),
            "soil": soil_ctx.model_dump(),
            "ml_status": {
                "available": ml_available,
                "anomaly_status": ml_anomaly_msg or ("Inputs incomplete — ML prediction unavailable" if not ml_available else "Plausible agronomic profile")
            },
            "farm": {
                "area_acres": farm_area_acres,
                "water_availability": water_availability
            },
            "recommendations": [rec.model_dump() for rec in recommendations]
        }
