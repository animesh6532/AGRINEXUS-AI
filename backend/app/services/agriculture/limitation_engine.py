"""
Limitation Engine module.
Implements FAO AEZ / Liebig's Law of the Minimum limitation analysis for land evaluation.
Evaluates Hard Constraints (strict disqualification / extreme penalty) and Soft Limitations (graded suitability reduction).
"""

from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from .crop_profiles import CropRequirementProfile
from .weather_context import WeatherContext
from .soil_context import SoilContext
from .season_engine import SeasonInfo


class FactorStatus:
    OPTIMAL = "OPTIMAL"
    SUITABLE = "SUITABLE"
    MODERATE_LIMITATION = "MODERATE_LIMITATION"
    SEVERE_LIMITATION = "SEVERE_LIMITATION"
    UNSUITABLE = "UNSUITABLE"
    UNKNOWN = "UNKNOWN"


class FactorEvaluationResult(BaseModel):
    factor_name: str  # "temperature", "ph", "season", "rainfall", "soil_texture", "soil_depth", "water"
    status: str  # OPTIMAL | SUITABLE | MODERATE_LIMITATION | SEVERE_LIMITATION | UNSUITABLE | UNKNOWN
    score: float = Field(..., ge=0.0, le=100.0)
    observed_value: Optional[Any] = None
    required_range: Optional[Any] = None
    reason: str
    warning: Optional[str] = None
    source: str


class LimitationAnalysisResult(BaseModel):
    is_hard_constrained: bool = False
    hard_constraint_reasons: List[str] = Field(default_factory=list)
    limiting_factors: List[str] = Field(default_factory=list)
    positive_factors: List[str] = Field(default_factory=list)
    factor_evaluations: Dict[str, FactorEvaluationResult] = Field(default_factory=dict)
    land_suitability_class: str  # "Highly Suitable", "Suitable", "Moderately Suitable", "Marginal", "Not Suitable", "Insufficient Data"


class LimitationEngine:
    """FAO Limitation-Based Evaluation Engine."""

    @staticmethod
    def evaluate_limitations(
        profile: CropRequirementProfile,
        weather: WeatherContext,
        soil: SoilContext,
        season: SeasonInfo,
        water_availability: str = "unknown"
    ) -> LimitationAnalysisResult:
        """
        Evaluate agronomic suitability limitations across land, soil, climate, and season.
        """
        hard_constrained = False
        hard_constraint_reasons: List[str] = []
        limiting_factors: List[str] = []
        positive_factors: List[str] = []
        evaluations: Dict[str, FactorEvaluationResult] = {}

        # ------------------------------------------------------------------
        # 1. Season Evaluation
        # ------------------------------------------------------------------
        req_seasons = [s.lower() for s in profile.seasons]
        curr_season = season.season.lower()

        if "annual" in req_seasons or curr_season in req_seasons:
            season_eval = FactorEvaluationResult(
                factor_name="season",
                status=FactorStatus.OPTIMAL,
                score=100.0,
                observed_value=season.season,
                required_range=", ".join(profile.seasons).title(),
                reason=f"Current season ({season.season}) matches optimal crop season window ({', '.join(profile.seasons).title()})",
                source=season.source
            )
            positive_factors.append(f"Current regional season ({season.season}) aligns with crop cycle.")
        else:
            season_eval = FactorEvaluationResult(
                factor_name="season",
                status=FactorStatus.SEVERE_LIMITATION,
                score=30.0,
                observed_value=season.season,
                required_range=", ".join(profile.seasons).title(),
                reason=f"Seasonal mismatch: Current season is {season.season}, but {profile.display_name} prefers {', '.join(profile.seasons).title()}",
                warning=f"⚠ Seasonal timing mismatch: {profile.display_name} is best cultivated in {', '.join(profile.seasons).title()} season.",
                source=season.source
            )
            limiting_factors.append(f"Seasonal mismatch (Current: {season.season}, Prefers: {', '.join(profile.seasons).title()})")

        evaluations["season"] = season_eval

        # ------------------------------------------------------------------
        # 2. Temperature Evaluation (Optimal vs Absolute)
        # ------------------------------------------------------------------
        temp_val = weather.current_temperature or weather.forecast_temperature_mean

        if temp_val is not None:
            opt_min, opt_max = profile.temp_optimal
            acc_min, acc_max = profile.temp_acceptable

            if opt_min <= temp_val <= opt_max:
                temp_eval = FactorEvaluationResult(
                    factor_name="temperature",
                    status=FactorStatus.OPTIMAL,
                    score=100.0,
                    observed_value=f"{temp_val:.1f}°C",
                    required_range=f"{opt_min}-{opt_max}°C",
                    reason=f"Temperature ({temp_val:.1f}°C) is within optimal range ({opt_min}-{opt_max}°C)",
                    source=weather.source
                )
                positive_factors.append(f"Temperature ({temp_val:.1f}°C) is optimal for crop growth.")
            elif acc_min <= temp_val <= acc_max:
                temp_eval = FactorEvaluationResult(
                    factor_name="temperature",
                    status=FactorStatus.MODERATE_LIMITATION,
                    score=70.0,
                    observed_value=f"{temp_val:.1f}°C",
                    required_range=f"Optimal: {opt_min}-{opt_max}°C, Acceptable: {acc_min}-{acc_max}°C",
                    reason=f"Temperature ({temp_val:.1f}°C) is acceptable but suboptimal (Optimal: {opt_min}-{opt_max}°C)",
                    warning=f"⚠ Temperature ({temp_val:.1f}°C) is outside preferred optimal bounds.",
                    source=weather.source
                )
                limiting_factors.append(f"Suboptimal temperature ({temp_val:.1f}°C vs optimal {opt_min}-{opt_max}°C)")
            else:
                # Lethal temperature / Outside absolute bounds -> Hard Constraint
                hard_constrained = True
                msg = f"Temperature ({temp_val:.1f}°C) violates absolute survival limits ({acc_min}-{acc_max}°C) for {profile.display_name}."
                hard_constraint_reasons.append(msg)

                temp_eval = FactorEvaluationResult(
                    factor_name="temperature",
                    status=FactorStatus.UNSUITABLE,
                    score=0.0,
                    observed_value=f"{temp_val:.1f}°C",
                    required_range=f"{acc_min}-{acc_max}°C",
                    reason=msg,
                    warning=f"⚠ Lethal temperature condition: {temp_val:.1f}°C is outside survival range ({acc_min}-{acc_max}°C).",
                    source=weather.source
                )
                limiting_factors.append(f"Extreme temperature incompatibility ({temp_val:.1f}°C)")
        else:
            temp_eval = FactorEvaluationResult(
                factor_name="temperature",
                status=FactorStatus.UNKNOWN,
                score=70.0,
                reason="Temperature telemetry unavailable",
                source="Unavailable"
            )

        evaluations["temperature"] = temp_eval

        # ------------------------------------------------------------------
        # 3. Soil pH Evaluation
        # ------------------------------------------------------------------
        ph_val = soil.ph.value if (soil.ph and soil.ph.value is not None) else None

        if ph_val is not None:
            p_opt_min, p_opt_max = profile.ph_optimal
            p_acc_min, p_acc_max = profile.ph_acceptable

            if p_opt_min <= ph_val <= p_opt_max:
                ph_eval = FactorEvaluationResult(
                    factor_name="ph",
                    status=FactorStatus.OPTIMAL,
                    score=100.0,
                    observed_value=f"{ph_val:.1f}",
                    required_range=f"{p_opt_min}-{p_opt_max}",
                    reason=f"Soil pH ({ph_val:.1f}) is within optimal range ({p_opt_min}-{p_opt_max})",
                    source=soil.ph.source_description
                )
                positive_factors.append(f"Soil pH ({ph_val:.1f}) is optimal for nutrient uptake.")
            elif p_acc_min <= ph_val <= p_acc_max:
                ph_eval = FactorEvaluationResult(
                    factor_name="ph",
                    status=FactorStatus.MODERATE_LIMITATION,
                    score=70.0,
                    observed_value=f"{ph_val:.1f}",
                    required_range=f"Optimal: {p_opt_min}-{p_opt_max}, Acceptable: {p_acc_min}-{p_acc_max}",
                    reason=f"Soil pH ({ph_val:.1f}) is acceptable but suboptimal",
                    warning=f"⚠ Soil pH ({ph_val:.1f}) is slightly acidic/alkaline for optimal growth.",
                    source=soil.ph.source_description
                )
                limiting_factors.append(f"Suboptimal soil pH ({ph_val:.1f})")
            else:
                # Severe pH toxicity -> Hard Constraint
                hard_constrained = True
                msg = f"Soil pH ({ph_val:.1f}) is outside acceptable physiological tolerance ({p_acc_min}-{p_acc_max})."
                hard_constraint_reasons.append(msg)

                ph_eval = FactorEvaluationResult(
                    factor_name="ph",
                    status=FactorStatus.UNSUITABLE,
                    score=10.0,
                    observed_value=f"{ph_val:.1f}",
                    required_range=f"{p_acc_min}-{p_acc_max}",
                    reason=msg,
                    warning=f"⚠ Severe pH stress: Soil pH ({ph_val:.1f}) restricts nutrient availability.",
                    source=soil.ph.source_description
                )
                limiting_factors.append(f"Hostile soil pH ({ph_val:.1f})")
        else:
            ph_eval = FactorEvaluationResult(
                factor_name="ph",
                status=FactorStatus.UNKNOWN,
                score=70.0,
                reason="Soil pH unavailable",
                source="Unknown"
            )

        evaluations["ph"] = ph_eval

        # ------------------------------------------------------------------
        # 4. Soil Texture Evaluation
        # ------------------------------------------------------------------
        soil_tex = (soil.soil_texture or "").lower()
        pref_textures = [t.lower() for t in profile.soil_textures]

        if any(pt in soil_tex or soil_tex in pt for pt in pref_textures):
            texture_eval = FactorEvaluationResult(
                factor_name="soil_texture",
                status=FactorStatus.OPTIMAL,
                score=100.0,
                observed_value=soil.soil_texture,
                required_range=", ".join(profile.soil_textures),
                reason=f"Soil texture ({soil.soil_texture}) matches preferred soil types ({', '.join(profile.soil_textures)})",
                source=soil.data_source
            )
            positive_factors.append(f"Soil texture ({soil.soil_texture}) provides ideal physical structure.")
        else:
            texture_eval = FactorEvaluationResult(
                factor_name="soil_texture",
                status=FactorStatus.MODERATE_LIMITATION,
                score=60.0,
                observed_value=soil.soil_texture,
                required_range=", ".join(profile.soil_textures),
                reason=f"Soil texture ({soil.soil_texture}) differs from preferred texture types ({', '.join(profile.soil_textures)})",
                source=soil.data_source
            )
            limiting_factors.append(f"Suboptimal soil texture ({soil.soil_texture})")

        evaluations["soil_texture"] = texture_eval

        # ------------------------------------------------------------------
        # 5. Water / Rainfall & Irrigation Evaluation
        # ------------------------------------------------------------------
        rain_val = weather.current_rainfall or weather.forecast_rainfall_sum or weather.recent_rainfall_14d
        req_water = profile.water_requirement.lower()
        irrigated = water_availability.lower() == "irrigated"

        if req_water == "high" and not irrigated and (rain_val is None or rain_val < 50.0):
            water_eval = FactorEvaluationResult(
                factor_name="water",
                status=FactorStatus.SEVERE_LIMITATION,
                score=40.0,
                observed_value=f"Rainfed / {rain_val or 0:.1f} mm rain",
                required_range="High Water Requirement (Requires Irrigation or Heavy Rainfall)",
                reason=f"{profile.display_name} requires high water input, but rainfed field moisture is limited.",
                warning="⚠ Moisture deficit risk: High-water crop grown under rainfed conditions without irrigation.",
                source="Agronomic Water Balance Assessment"
            )
            limiting_factors.append(f"High water demand unsupported by rainfed status")
        elif irrigated and req_water in ["high", "medium"]:
            water_eval = FactorEvaluationResult(
                factor_name="water",
                status=FactorStatus.OPTIMAL,
                score=100.0,
                observed_value="Irrigated Field",
                required_range=f"{profile.water_requirement.title()} Water Requirement",
                reason="Farm irrigation facility satisfies crop moisture demand.",
                source="User Farm Irrigation Context"
            )
            positive_factors.append("Irrigation access compensates for precipitation deficits.")
        else:
            water_eval = FactorEvaluationResult(
                factor_name="water",
                status=FactorStatus.SUITABLE,
                score=85.0,
                observed_value=f"{water_availability.title()} / {rain_val or 0:.1f} mm rain",
                required_range=f"{profile.water_requirement.title()} Water Requirement",
                reason=f"Moisture availability is adequate for {profile.water_requirement} water demand.",
                source=weather.source
            )

        evaluations["water"] = water_eval

        # Determine Overall Land Suitability Class
        if hard_constrained:
            land_class = "Not Suitable"
        else:
            avg_score = sum(e.score for e in evaluations.values()) / len(evaluations)
            if avg_score >= 85:
                land_class = "Highly Suitable"
            elif avg_score >= 70:
                land_class = "Suitable"
            elif avg_score >= 50:
                land_class = "Moderately Suitable"
            elif avg_score >= 35:
                land_class = "Marginal"
            else:
                land_class = "Not Suitable"

        return LimitationAnalysisResult(
            is_hard_constrained=hard_constrained,
            hard_constraint_reasons=hard_constraint_reasons,
            limiting_factors=limiting_factors,
            positive_factors=positive_factors,
            factor_evaluations=evaluations,
            land_suitability_class=land_class
        )
