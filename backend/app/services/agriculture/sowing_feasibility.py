"""
Sowing Feasibility Engine module.
Evaluates Question B: "Is this an appropriate crop to establish/sow now?"
Separates agro-ecological land capability from immediate temporal sowing window feasibility.
Evaluates calendar dates, regional sowing windows, recent 14-day rainfall seedbed moisture, and forecast extreme weather.
"""

from datetime import date
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .crop_profiles import CropRequirementProfile
from .weather_context import WeatherContext
from .season_engine import SeasonInfo


class SowingStatus:
    IDEAL_WINDOW = "IDEAL_WINDOW"
    GOOD_WINDOW = "GOOD_WINDOW"
    EARLY = "EARLY"
    LATE = "LATE"
    OUTSIDE_WINDOW = "OUTSIDE_WINDOW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class SowingFeasibilityResult(BaseModel):
    sowing_status: str  # IDEAL_WINDOW | GOOD_WINDOW | EARLY | LATE | OUTSIDE_WINDOW | INSUFFICIENT_DATA
    sowing_score: float = Field(..., ge=0.0, le=100.0)
    is_sowing_recommended_now: bool
    sowing_window_label: str  # e.g., "Optimal Sowing Window: June - July"
    moisture_status: str  # "Adequate Seedbed Moisture", "Dry Seedbed Risk", "Excess Waterlogging Risk"
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SowingFeasibilityEngine:
    """Evaluates short-term temporal sowing feasibility for field operations."""

    MONTH_MAP = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    @classmethod
    def evaluate_sowing_feasibility(
        cls,
        profile: CropRequirementProfile,
        weather: WeatherContext,
        season: SeasonInfo,
        as_of_date: Optional[date] = None,
        water_availability: str = "unknown"
    ) -> SowingFeasibilityResult:
        """
        Evaluate sowing feasibility based on date, season window, 14-day recent rainfall, and 7-day forecast.
        """
        ref_date = as_of_date or date.today()
        curr_month = ref_date.month
        reasons: List[str] = []
        warnings: List[str] = []

        # 1. Season Window Check
        req_seasons = [s.lower() for s in profile.seasons]
        curr_season = season.season.lower()

        sowing_status = SowingStatus.GOOD_WINDOW
        sowing_score = 85.0

        if "annual" in req_seasons:
            sowing_status = SowingStatus.IDEAL_WINDOW
            sowing_score = 95.0
            reasons.append("✓ Perennial/Annual crop can be planted throughout favorable temperature windows.")
        elif curr_season in req_seasons:
            # Inside target season
            # Check sowing window month alignment
            if curr_month in [6, 7] and "kharif" in req_seasons:
                sowing_status = SowingStatus.IDEAL_WINDOW
                sowing_score = 100.0
                reasons.append("✓ Peak Kharif sowing window (June - July). Ideal time for germination.")
            elif curr_month in [10, 11] and "rabi" in req_seasons:
                sowing_status = SowingStatus.IDEAL_WINDOW
                sowing_score = 100.0
                reasons.append("✓ Peak Rabi sowing window (October - November). Optimal soil temperature for emergence.")
            elif curr_month in [2, 3] and "zaid" in req_seasons:
                sowing_status = SowingStatus.IDEAL_WINDOW
                sowing_score = 100.0
                reasons.append("✓ Peak Zaid summer sowing window (February - March).")
            else:
                sowing_status = SowingStatus.GOOD_WINDOW
                sowing_score = 80.0
                reasons.append(f"✓ Currently within crop's growing season ({season.season}), though past peak initial sowing month.")
        else:
            sowing_status = SowingStatus.OUTSIDE_WINDOW
            sowing_score = 25.0
            warnings.append(f"⚠ Recommended sowing window has passed: {profile.display_name} prefers {', '.join(profile.seasons).title()} season (Current season: {season.season}).")

        # 2. Seedbed Moisture & Forecast Weather Assessment
        moisture_status = "Adequate Seedbed Moisture"
        recent_rain = weather.recent_rainfall_14d or weather.current_rainfall or 0.0
        forecast_rain = weather.forecast_rainfall_sum or 0.0
        irrigated = water_availability.lower() == "irrigated"

        if recent_rain < 15.0 and not irrigated:
            moisture_status = "Dry Seedbed Risk"
            sowing_score = max(20.0, sowing_score - 20.0)
            warnings.append("⚠ Dry seedbed warning: Recent 14-day rainfall is low (<15 mm). Pre-sowing irrigation required before planting.")
        elif forecast_rain > 120.0:
            moisture_status = "Excess Waterlogging Risk"
            sowing_score = max(30.0, sowing_score - 15.0)
            warnings.append("⚠ Torrential rain forecast: Heavy 7-day rainfall (>120 mm) forecast may cause seed wash-out or waterlogging.")
        else:
            reasons.append(f"✓ Seedbed moisture status: {moisture_status}.")

        is_recommended = sowing_status in [SowingStatus.IDEAL_WINDOW, SowingStatus.GOOD_WINDOW] and sowing_score >= 60.0

        return SowingFeasibilityResult(
            sowing_status=sowing_status,
            sowing_score=round(sowing_score, 1),
            is_sowing_recommended_now=is_recommended,
            sowing_window_label=f"Season Window: {', '.join(profile.seasons).title()} ({season.sowing_window})",
            moisture_status=moisture_status,
            reasons=reasons,
            warnings=warnings
        )
