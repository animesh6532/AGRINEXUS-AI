"""
Crop suitability engine module.
Evaluates agro-ecological suitability for a candidate crop profile against field location,
weather context, soil context, seasonal window, water availability, and frozen ML predictions.
Adheres strictly to safety, honesty, and transparency guidelines.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .crop_profiles import CropRequirementProfile
from .weather_context import WeatherContext
from .soil_context import SoilContext
from .season_engine import SeasonInfo


class CropSuitabilityResult(BaseModel):
    crop: str
    display_name: str
    scientific_name: str
    ml_supported: bool
    category: str
    suitability_score: int = Field(..., ge=0, le=100, description="Suitability Score (0-100 integer)")
    suitability_level: str  # "Highly Suitable", "Suitable", "Conditionally Suitable", "Low Suitability", "Insufficient Data"
    ml_prediction: Optional[Dict[str, Any]] = None  # {supported: bool, probability: float}
    factor_scores: Dict[str, float]  # season, temperature, rainfall, ph, texture, regional, ml
    reasons: List[str]
    warnings: List[str]
    missing_data: List[str]
    data_sources: List[Dict[str, str]]
    profile_details: Dict[str, Any]


class CropSuitabilityEngine:
    """Configurable Agricultural Suitability Assessment Engine."""

    # Default engine configuration weights (sums to 1.0)
    DEFAULT_WEIGHTS = {
        "ml": 0.30,
        "season": 0.15,
        "temperature": 0.15,
        "rainfall": 0.15,
        "ph": 0.10,
        "texture": 0.05,
        "region": 0.10
    }

    @classmethod
    def evaluate_crop(
        cls,
        profile: CropRequirementProfile,
        weather: WeatherContext,
        soil: SoilContext,
        season: SeasonInfo,
        ml_probability: Optional[float] = None,
        water_availability: str = "unknown",
        weights_config: Optional[Dict[str, float]] = None
    ) -> CropSuitabilityResult:
        """
        Evaluate agro-ecological suitability of a candidate crop profile.
        Returns CropSuitabilityResult with score (0-100), level, factor breakdown, reasons, and warnings.
        """
        weights = dict(weights_config or cls.DEFAULT_WEIGHTS)
        reasons: List[str] = []
        warnings: List[str] = []
        missing_data: List[str] = []
        data_sources: List[Dict[str, str]] = []

        # Track missing critical information
        if not weather.data_available:
            missing_data.append("weather")
            warnings.append("⚠ Weather telemetry unavailable from external provider.")

        if soil.ph is None or soil.ph.value is None:
            missing_data.append("soil_ph")
            warnings.append("⚠ Soil pH is unavailable; defaulting to neutral assumption.")

        if soil.phosphorus is None or soil.phosphorus.value is None:
            missing_data.append("phosphorus")
            warnings.append("⚠ Phosphorus (P) missing from soil data — verify with lab soil test.")

        if soil.potassium is None or soil.potassium.value is None:
            missing_data.append("potassium")
            warnings.append("⚠ Potassium (K) missing from soil data — verify with lab soil test.")

        if soil.nitrogen and soil.nitrogen.is_estimated:
            warnings.append("⚠ Soil Nitrogen is estimated from geospatial data (Total N).")

        if soil.ph and soil.ph.is_estimated:
            warnings.append("⚠ Soil pH is estimated from geospatial 250m data.")

        # Data sources provenance
        data_sources.append({"domain": "Weather", "source": weather.source})
        data_sources.append({"domain": "Soil", "source": soil.data_source})
        data_sources.append({"domain": "Season & Calendar", "source": season.source})
        data_sources.append({"domain": "Crop Requirements", "source": profile.source})

        # ------------------------------------------------------------------
        # 1. Season Evaluation
        # ------------------------------------------------------------------
        season_score = 100.0
        req_seasons = [s.lower() for s in profile.seasons]
        curr_season = season.season.lower()

        if "annual" in req_seasons or curr_season in req_seasons:
            season_score = 100.0
            reasons.append(f"✓ Current season ({season.season}) matches optimal growing window ({', '.join(profile.seasons).title()})")
        else:
            season_score = 30.0
            warnings.append(f"⚠ Seasonal mismatch: Current season is {season.season}, but {profile.display_name} prefers {', '.join(profile.seasons).title()}")

        # ------------------------------------------------------------------
        # 2. Temperature Evaluation
        # ------------------------------------------------------------------
        temp_score = 80.0  # default neutral if missing
        temp_val = weather.current_temperature or weather.forecast_temperature_mean

        if temp_val is not None:
            opt_min, opt_max = profile.temp_optimal
            acc_min, acc_max = profile.temp_acceptable

            if opt_min <= temp_val <= opt_max:
                temp_score = 100.0
                reasons.append(f"✓ Temperature ({temp_val:.1f}°C) is optimal ({opt_min}-{opt_max}°C)")
            elif acc_min <= temp_val <= acc_max:
                temp_score = 70.0
                reasons.append(f"✓ Temperature ({temp_val:.1f}°C) is within acceptable range ({acc_min}-{acc_max}°C)")
                warnings.append(f"⚠ Temperature ({temp_val:.1f}°C) is suboptimal for {profile.display_name} (Optimal: {opt_min}-{opt_max}°C)")
            else:
                temp_score = 20.0
                warnings.append(f"⚠ Temperature ({temp_val:.1f}°C) is outside acceptable bounds ({acc_min}-{acc_max}°C)")

        # ------------------------------------------------------------------
        # 3. Rainfall & Water Availability Evaluation
        # ------------------------------------------------------------------
        rain_score = 80.0
        rain_val = weather.current_rainfall or weather.forecast_rainfall_sum or weather.recent_rainfall_14d

        if rain_val is not None:
            r_opt_min, r_opt_max = profile.rainfall_optimal
            r_acc_min, r_acc_max = profile.rainfall_acceptable

            # Convert 7-14 day rain sum into seasonal equivalent estimate (approx x 10)
            est_seasonal_rain = rain_val * 10.0

            if r_opt_min <= est_seasonal_rain <= r_opt_max:
                rain_score = 100.0
                reasons.append(f"✓ Rainfall / Moisture availability ({rain_val:.1f} mm) aligns with optimal crop water requirements")
            elif r_acc_min <= est_seasonal_rain <= r_acc_max:
                rain_score = 70.0
                reasons.append(f"✓ Rainfall / Moisture ({rain_val:.1f} mm) is within acceptable limits")
            else:
                rain_score = 30.0
                warnings.append(f"⚠ Water requirement: {profile.display_name} requires {profile.water_requirement.upper()} water, but available moisture is constrained.")

        # Adjust water score based on irrigation availability
        if water_availability.lower() == "irrigated" and profile.water_requirement in ["high", "medium"]:
            rain_score = max(rain_score, 90.0)
            reasons.append("✓ Farm irrigation availability compensates for rainfall deficits")
        elif water_availability.lower() == "rainfed" and profile.water_requirement == "high":
            rain_score = min(rain_score, 50.0)
            warnings.append("⚠ Rainfed field status may cause moisture stress for high-water crop")

        # ------------------------------------------------------------------
        # 4. Soil pH Evaluation
        # ------------------------------------------------------------------
        ph_score = 80.0
        ph_val = soil.ph.value if (soil.ph and soil.ph.value is not None) else None

        if ph_val is not None:
            p_opt_min, p_opt_max = profile.ph_optimal
            p_acc_min, p_acc_max = profile.ph_acceptable

            if p_opt_min <= ph_val <= p_opt_max:
                ph_score = 100.0
                reasons.append(f"✓ Soil pH ({ph_val:.1f}) is optimal ({p_opt_min}-{p_opt_max})")
            elif p_acc_min <= ph_val <= p_acc_max:
                ph_score = 70.0
                reasons.append(f"✓ Soil pH ({ph_val:.1f}) is acceptable ({p_acc_min}-{p_acc_max})")
                warnings.append(f"⚠ Soil pH ({ph_val:.1f}) is suboptimal (Optimal: {p_opt_min}-{p_opt_max})")
            else:
                ph_score = 25.0
                warnings.append(f"⚠ Soil pH ({ph_val:.1f}) is hostile for {profile.display_name} (Acceptable: {p_acc_min}-{p_acc_max})")

        # ------------------------------------------------------------------
        # 5. Soil Texture Evaluation
        # ------------------------------------------------------------------
        texture_score = 75.0
        soil_tex = (soil.soil_texture or "").lower()
        pref_textures = [t.lower() for t in profile.soil_textures]

        if any(pt in soil_tex or soil_tex in pt for pt in pref_textures):
            texture_score = 100.0
            reasons.append(f"✓ Soil texture ({soil.soil_texture}) matches preferred soil types ({', '.join(profile.soil_textures)})")
        else:
            texture_score = 60.0

        # ------------------------------------------------------------------
        # 6. Regional Alignment Evaluation
        # ------------------------------------------------------------------
        region_score = 80.0
        reg_states = [r.lower() for r in profile.regional_suitability]

        if "all" in reg_states or season.state.lower() in reg_states:
            region_score = 100.0
            reasons.append(f"✓ High regional cultivation priority in {season.state}")
        else:
            region_score = 70.0

        # ------------------------------------------------------------------
        # 7. ML Model Probability Evaluation
        # ------------------------------------------------------------------
        ml_score: Optional[float] = None
        if ml_probability is not None and profile.ml_supported:
            ml_score = round(ml_probability * 100.0, 1)
            if ml_probability >= 0.70:
                reasons.append(f"✓ AgriNexus-AI ML model ranks {profile.display_name} with high confidence ({ml_score:.0f}%)")
            elif ml_probability >= 0.30:
                reasons.append(f"✓ AgriNexus-AI ML model identifies {profile.display_name} as a candidate ({ml_score:.0f}%)")
        elif not profile.ml_supported:
            # Catalogue crop without ML support
            data_sources.append({"domain": "ML Model", "source": "Not Trained in ML Artifact (Catalogue Crop)"})

        # ------------------------------------------------------------------
        # Dynamic Weight Normalization
        # ------------------------------------------------------------------
        active_weights = dict(weights)
        if ml_score is None:
            # Redistribute ML weight (30%) across remaining 6 factors
            del active_weights["ml"]
            total_w = sum(active_weights.values())
            active_weights = {k: v / total_w for k, v in active_weights.items()}

        factor_scores = {
            "season": round(season_score, 1),
            "temperature": round(temp_score, 1),
            "rainfall": round(rain_score, 1),
            "ph": round(ph_score, 1),
            "texture": round(texture_score, 1),
            "region": round(region_score, 1),
        }
        if ml_score is not None:
            factor_scores["ml"] = round(ml_score, 1)

        final_score_raw = (
            season_score * active_weights.get("season", 0) +
            temp_score * active_weights.get("temperature", 0) +
            rain_score * active_weights.get("rainfall", 0) +
            ph_score * active_weights.get("ph", 0) +
            texture_score * active_weights.get("texture", 0) +
            region_score * active_weights.get("region", 0) +
            (ml_score or 0) * active_weights.get("ml", 0)
        )

        final_suitability_score = int(round(min(100.0, max(0.0, final_score_raw))))

        # Determine Suitability Level
        if len(missing_data) >= 3:
            suitability_level = "Insufficient Data"
        elif final_suitability_score >= 85:
            suitability_level = "Highly Suitable"
        elif final_suitability_score >= 70:
            suitability_level = "Suitable"
        elif final_suitability_score >= 50:
            suitability_level = "Conditionally Suitable"
        else:
            suitability_level = "Low Suitability"

        ml_pred_payload = None
        if profile.ml_supported:
            ml_pred_payload = {
                "supported": True,
                "probability": round(ml_probability, 4) if ml_probability is not None else None
            }
        else:
            ml_pred_payload = {
                "supported": False,
                "probability": None
            }

        return CropSuitabilityResult(
            crop=profile.crop,
            display_name=profile.display_name,
            scientific_name=profile.scientific_name,
            ml_supported=profile.ml_supported,
            category=profile.category,
            suitability_score=final_suitability_score,
            suitability_level=suitability_level,
            ml_prediction=ml_pred_payload,
            factor_scores=factor_scores,
            reasons=reasons,
            warnings=warnings,
            missing_data=missing_data,
            data_sources=data_sources,
            profile_details={
                "seasons": profile.seasons,
                "temp_optimal": profile.temp_optimal,
                "temp_acceptable": profile.temp_acceptable,
                "rainfall_optimal": profile.rainfall_optimal,
                "ph_optimal": profile.ph_optimal,
                "ph_acceptable": profile.ph_acceptable,
                "soil_textures": profile.soil_textures,
                "water_requirement": profile.water_requirement,
                "growth_duration_days": profile.growth_duration_days,
                "source": profile.source,
                "source_url": profile.source_url,
                "notes": profile.notes
            }
        )
