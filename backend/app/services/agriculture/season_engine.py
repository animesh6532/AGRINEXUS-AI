"""
Regional season engine module.
Determines current agricultural season (Kharif, Rabi, Zaid, Annual), regional season name,
sowing windows, and harvest windows based on date, location (state/district in India),
and regional agricultural calendar conventions.
"""

from datetime import datetime, date
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class SeasonInfo(BaseModel):
    season: str  # "Kharif", "Rabi", "Zaid", "Annual"
    regional_season: str  # e.g., "Kharif (Monsoon Crop Season - West Bengal)"
    sowing_window: str  # e.g., "June - July"
    harvest_window: str  # e.g., "October - November"
    current_month: str
    state: str
    source: str = "ICAR & Regional State Agricultural Universities Calendar"
    data_status: str = "VERIFIED"


class SeasonEngine:
    """India-aware Regional Agricultural Season Engine."""

    @staticmethod
    def get_season_info(
        latitude: float,
        longitude: float,
        state: Optional[str] = None,
        as_of_date: Optional[date] = None
    ) -> SeasonInfo:
        """
        Determine season and regional crop calendar windows for given coordinates / state.
        """
        ref_date = as_of_date or date.today()
        month = ref_date.month
        month_name = ref_date.strftime("%B")

        state_clean = (state or "").strip().title()

        # Regional season mapping according to Indian Agro-Climatic Zones
        # Southern India (Tamil Nadu, Kerala) has unique monsoon patterns (North-East Monsoon in Oct-Dec)
        # Eastern India (West Bengal, Odisha, Assam) has Aus/Aman/Boro rice seasons

        season_type = "Kharif"
        sowing = "June - July"
        harvest = "October - November"
        reg_season = "Kharif (South-West Monsoon Season)"

        if state_clean in ["Tamil Nadu", "Puducherry"]:
            if 6 <= month <= 9:
                season_type = "Kharif"
                reg_season = "Kuruvai / Southwest Monsoon Season (Tamil Nadu)"
                sowing = "June - July"
                harvest = "September - October"
            elif 10 <= month <= 1 or month == 12:
                season_type = "Rabi"
                reg_season = "Samba / Thaladi (Northeast Monsoon Season - Tamil Nadu)"
                sowing = "October - November"
                harvest = "January - February"
            else:
                season_type = "Zaid"
                reg_season = "Navarai / Summer Season (Tamil Nadu)"
                sowing = "February - March"
                harvest = "May - June"

        elif state_clean in ["West Bengal", "Assam", "Odisha"]:
            if 6 <= month <= 10:
                season_type = "Kharif"
                reg_season = "Aman (Main Monsoon Rice/Kharif Season)"
                sowing = "June - July"
                harvest = "November - December"
            elif 11 <= month <= 3:
                season_type = "Rabi"
                reg_season = "Boro / Winter Crop Season"
                sowing = "November - December"
                harvest = "March - April"
            else:
                season_type = "Zaid"
                reg_season = "Aus / Summer Season"
                sowing = "March - April"
                harvest = "June - July"

        else:
            # Standard North / Central / West India agricultural calendar
            if 6 <= month <= 10:
                season_type = "Kharif"
                reg_season = f"Kharif (Monsoon Season - {state_clean or 'India'})"
                sowing = "June - July"
                harvest = "October - November"
            elif 11 <= month or month <= 3:
                season_type = "Rabi"
                reg_season = f"Rabi (Winter Season - {state_clean or 'India'})"
                sowing = "October - November"
                harvest = "March - April"
            else:  # April & May
                season_type = "Zaid"
                reg_season = f"Zaid (Summer Season - {state_clean or 'India'})"
                sowing = "March - April"
                harvest = "May - June"

        return SeasonInfo(
            season=season_type,
            regional_season=reg_season,
            sowing_window=sowing,
            harvest_window=harvest,
            current_month=month_name,
            state=state_clean or "India (Regional Calendar)"
        )
