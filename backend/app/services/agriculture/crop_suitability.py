"""
Crop Suitability Engine module.
Evaluates agro-ecological suitability for candidate crop profiles against field location,
weather context, soil context, seasonal window, water availability, and frozen ML predictions.
Distinguishes Question A ("Can this crop generally grow here?") from Question B ("Is this an appropriate crop to sow now?").
Strictly adheres to FAO AEZ principles, safety, honesty, and transparency guidelines.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .crop_profiles import CropRequirementProfile
from .weather_context import WeatherContext
from .soil_context import SoilContext
from .season_engine import SeasonInfo
from .limitation_engine import LimitationEngine, LimitationAnalysisResult
from .sowing_feasibility import SowingFeasibilityEngine, SowingFeasibilityResult


class CropSuitabilityResult(BaseModel):
    crop: str
    display_name: str
    scientific_name: str
    ml_supported: bool
    category: str
    suitability_score: int = Field(..., ge=0, le=100, description="AgriNexus Suitability Index (0-100 integer)")
    suitability_level: str  # "Highly Suitable", "Suitable", "Conditionally Suitable", "Low Suitability", "Insufficient Data"
    land_suitability: str  # "Highly Suitable", "Suitable", "Moderately Suitable", "Marginal", "Not Suitable"
    sowing_feasibility: str  # "IDEAL_WINDOW", "GOOD_WINDOW", "EARLY", "LATE", "OUTSIDE_WINDOW", "INSUFFICIENT_DATA"
    is_sowing_recommended_now: bool
    ml_prediction: Optional[Dict[str, Any]] = None  # {supported: bool, probability: float}
    factor_scores: Dict[str, float]
    limiting_factors: List[str]
    positive_factors: List[str]
    reasons: List[str]
    warnings: List[str]
    missing_data: List[str]
    data_sources: List[Dict[str, str]]
    profile_details: Dict[str, Any]


class CropSuitabilityEngine:
    """Configurable Agricultural Suitability Assessment Engine."""

    # Default weight distribution (sums to 1.0)
    DEFAULT_WEIGHTS = {
        "land_suitability": 0.45,
        "sowing_feasibility": 0.25,
        "region": 0.10,
        "ml": 0.20
    }

    @classmethod
    def evaluate_crop(
        cls,
        profile: CropRequirementProfile,
        weather: WeatherContext,
        soil: SoilContext,
        season: SeasonInfo,
        ml_probability: Optional[float] = None,
        water_availability: str = "unknown"
    ) -> CropSuitabilityResult:
        """
        Evaluate agro-ecological suitability of a candidate crop profile.
        Returns CropSuitabilityResult with score (0-100), level, factor breakdown, reasons, and warnings.
        """
        reasons: List[str] = []
        warnings: List[str] = []
        missing_data: List[str] = []
        data_sources: List[Dict[str, str]] = []

        # ------------------------------------------------------------------
        # 1. Missing Critical Data Tracking
        # ------------------------------------------------------------------
        if not weather.data_available:
            missing_data.append("weather")
            warnings.append("⚠ Weather telemetry unavailable from external provider.")

        if soil.ph is None or soil.ph.value is None:
            missing_data.append("soil_ph")
            warnings.append("⚠ Soil pH is unavailable; defaulting to neutral assumption.")

        if soil.phosphorus is None or soil.phosphorus.value is None:
            missing_data.append("phosphorus")
            warnings.append("⚠ Soil Phosphorus (P) missing — verify with lab soil test before planting.")

        if soil.potassium is None or soil.potassium.value is None:
            missing_data.append("potassium")
            warnings.append("⚠ Soil Potassium (K) missing — verify with lab soil test before planting.")

        if soil.nitrogen and soil.nitrogen.is_estimated:
            warnings.append("⚠ Soil Nitrogen is estimated from 250m geospatial data (Total N).")

        if soil.ph and soil.ph.is_estimated:
            warnings.append("⚠ Soil pH is estimated from 250m geospatial data.")

        # Data sources provenance
        data_sources.append({"domain": "Weather", "source": weather.source})
        data_sources.append({"domain": "Soil", "source": soil.data_source})
        data_sources.append({"domain": "Season & Calendar", "source": season.source})
        data_sources.append({"domain": "Crop Requirements", "source": profile.source})

        # ------------------------------------------------------------------
        # 2. Limitation Analysis (Question A: General Land Suitability)
        # ------------------------------------------------------------------
        limitations: LimitationAnalysisResult = LimitationEngine.evaluate_limitations(
            profile=profile,
            weather=weather,
            soil=soil,
            season=season,
            water_availability=water_availability
        )

        reasons.extend(limitations.positive_factors)
        warnings.extend([e.warning for e in limitations.factor_evaluations.values() if e.warning])

        # ------------------------------------------------------------------
        # 3. Sowing Feasibility Analysis (Question B: Sowing Time Feasibility)
        # ------------------------------------------------------------------
        sowing: SowingFeasibilityResult = SowingFeasibilityEngine.evaluate_sowing_feasibility(
            profile=profile,
            weather=weather,
            season=season,
            water_availability=water_availability
        )

        reasons.extend(sowing.reasons)
        warnings.extend(sowing.warnings)

        # ------------------------------------------------------------------
        # 4. Regional Alignment
        # ------------------------------------------------------------------
        region_score = 80.0
        reg_states = [r.lower() for r in profile.regional_suitability]
        if "all" in reg_states or season.state.lower() in reg_states:
            region_score = 100.0
            reasons.append(f"✓ High regional cultivation priority in {season.state}")
        else:
            region_score = 70.0

        # ------------------------------------------------------------------
        # 5. ML Model Evidence
        # ------------------------------------------------------------------
        ml_score: Optional[float] = None
        if ml_probability is not None and profile.ml_supported:
            ml_score = round(ml_probability * 100.0, 1)
            if ml_probability >= 0.70:
                reasons.append(f"✓ AgriNexus-AI ML model ranks {profile.display_name} with high probability ({ml_score:.0f}%)")
            elif ml_probability >= 0.30:
                reasons.append(f"✓ AgriNexus-AI ML model identifies {profile.display_name} as a candidate ({ml_score:.0f}%)")
        elif not profile.ml_supported:
            data_sources.append({"domain": "ML Model", "source": "Not Trained in ML Artifact (Catalogue Crop)"})

        # ------------------------------------------------------------------
        # 6. Overall AgriNexus Suitability Index Calculation
        # ------------------------------------------------------------------
        # Dynamic Weight Re-allocation
        weights = dict(cls.DEFAULT_WEIGHTS)
        if ml_score is None:
            del weights["ml"]
            tot_w = sum(weights.values())
            weights = {k: v / tot_w for k, v in weights.items()}

        land_eval_scores = [e.score for e in limitations.factor_evaluations.values()]
        land_score_avg = sum(land_eval_scores) / max(1, len(land_eval_scores))

        if limitations.is_hard_constrained:
            final_score_raw = 10.0  # Hard constraint caps suitability score near 0
        else:
            final_score_raw = (
                land_score_avg * weights.get("land_suitability", 0.45) +
                sowing.sowing_score * weights.get("sowing_feasibility", 0.25) +
                region_score * weights.get("region", 0.10) +
                (ml_score or 0.0) * weights.get("ml", 0.20)
            )

        final_suitability_score = int(round(min(100.0, max(0.0, final_score_raw))))

        # Determine Final Suitability Level Label
        if len(missing_data) >= 3:
            suitability_level = "Insufficient Data"
        elif limitations.is_hard_constrained:
            suitability_level = "Not Suitable"
        elif final_suitability_score >= 85:
            suitability_level = "Highly Suitable"
        elif final_suitability_score >= 70:
            suitability_level = "Suitable"
        elif final_suitability_score >= 50:
            suitability_level = "Conditionally Suitable"
        else:
            suitability_level = "Low Suitability"

        water_score = round(limitations.factor_evaluations["water"].score, 1)
        texture_score = round(limitations.factor_evaluations["soil_texture"].score, 1)

        factor_scores = {
            "land_suitability": round(land_score_avg, 1),
            "sowing_feasibility": round(sowing.sowing_score, 1),
            "season": round(limitations.factor_evaluations["season"].score, 1),
            "temperature": round(limitations.factor_evaluations["temperature"].score, 1),
            "rainfall": water_score,
            "water": water_score,
            "ph": round(limitations.factor_evaluations["ph"].score, 1),
            "texture": texture_score,
            "soil_texture": texture_score,
            "region": round(region_score, 1),
        }
        if ml_score is not None:
            factor_scores["ml"] = round(ml_score, 1)

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
            land_suitability=limitations.land_suitability_class,
            sowing_feasibility=sowing.sowing_status,
            is_sowing_recommended_now=sowing.is_sowing_recommended_now,
            ml_prediction=ml_pred_payload,
            factor_scores=factor_scores,
            limiting_factors=limitations.limiting_factors,
            positive_factors=limitations.positive_factors,
            reasons=list(dict.fromkeys(reasons)),  # Deduplicate
            warnings=list(dict.fromkeys(warnings)),
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
