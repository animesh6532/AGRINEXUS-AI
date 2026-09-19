"""
Crop calendar intelligence layer for the Crop Calendar module.

Derives deterministic, explainable calendar information from a static crop
calendar definition (growth stages, durations, sowing windows) and user-
supplied dynamic context (sowing date, as-of date).

IMPORTANT SCOPE NOTES:
- This is NOT an ML model and NOT a real-time prediction. All computations
  are deterministic date arithmetic on top of reference/external calendar
  data provided by the service layer.
- The service layer handles data retrieval; this layer handles derived
  agricultural/calendar logic; the API layer handles HTTP concerns.

Season conventions (generalised Indian agricultural seasons, documented for
explainability - not site-specific):
- kharif: sowing months June-October
- rabi:   sowing months November-March
- zaid:   sowing months April-May
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..core.logging import logger


class CropCalendarIntelligence:
    """
    Rule-based crop-calendar intelligence.

    Every output is derived from explicit, documented rules applied to the
    static calendar data supplied by the service layer. Nothing is
    fabricated: unknown/ambiguous situations produce explicit ``None``
    values and warnings instead of invented agricultural data.
    """

    # Harvest window tolerance around the computed maturity date (days).
    HARVEST_WINDOW_TOLERANCE_DAYS = 10

    # Window (days) used to surface upcoming activities relative to the
    # as-of date.
    UPCOMING_ACTIVITY_WINDOW_DAYS = 14

    # Generalised Indian season month conventions (sowing month based).
    KHARIF_SOWING_MONTHS = {6, 7, 8, 9, 10}
    RABI_SOWING_MONTHS = {11, 12, 1, 2, 3}
    ZAID_SOWING_MONTHS = {4, 5}

    SUPPORTED_SEASONS = ("kharif", "rabi", "zaid")

    def __init__(self):
        logger.debug("Initialized CropCalendarIntelligence service")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_mmdd(value: str) -> Tuple[int, int]:
        """Parse an 'MM-DD' string into a (month, day) tuple."""
        month_text, day_text = value.split("-")
        return int(month_text), int(day_text)

    @staticmethod
    def _date_to_mmdd(value: date) -> str:
        """Format a date as an 'MM-DD' string."""
        return f"{value.month:02d}-{value.day:02d}"

    @staticmethod
    def _mmdd_in_window(mmdd: str, start: str, end: str) -> bool:
        """
        Check whether an 'MM-DD' value falls within an inclusive window.

        Windows that wrap the calendar year (start > end, e.g. rabi rice
        sowing 11-15 to 01-15) are supported.
        """
        if start <= end:
            return start <= mmdd <= end
        # Wrapping window (e.g. November -> January)
        return mmdd >= start or mmdd <= end

    # ------------------------------------------------------------------
    # Season logic
    # ------------------------------------------------------------------
    def normalize_season(self, season: str) -> str:
        """
        Normalize and validate a season name.

        Raises:
            ValueError: When the season name is empty or unsupported
        """
        if season is None:
            raise ValueError("Season is required")
        normalized = str(season).strip().lower()
        if not normalized:
            raise ValueError("Season must not be empty")
        if normalized not in self.SUPPORTED_SEASONS:
            raise ValueError(
                f"Unsupported season '{season}'. Supported seasons: "
                f"{', '.join(self.SUPPORTED_SEASONS)}"
            )
        return normalized

    def infer_season_from_sowing_date(self, sowing_date: date) -> str:
        """
        Infer the generalised agricultural season from the sowing month.

        Returns one of 'kharif', 'rabi', 'zaid'.
        """
        month = sowing_date.month
        if month in self.KHARIF_SOWING_MONTHS:
            return "kharif"
        if month in self.RABI_SOWING_MONTHS:
            return "rabi"
        return "zaid"

    def match_sowing_window(
        self,
        sowing_date: date,
        sowing_windows: Dict[str, Optional[Dict[str, str]]],
    ) -> Optional[str]:
        """
        Find the season whose sowing window contains the sowing date.

        Args:
            sowing_date: The sowing date to match
            sowing_windows: Mapping of season -> {"start": "MM-DD",
                "end": "MM-DD"} (values may be None)

        Returns:
            Matching season name, or None when no window matches
        """
        mmdd = self._date_to_mmdd(sowing_date)
        for season, window in sowing_windows.items():
            if not window:
                continue
            if self._mmdd_in_window(mmdd, window["start"], window["end"]):
                return season
        return None

    def is_date_within_window(
        self,
        value: date,
        window: Optional[Dict[str, str]],
    ) -> Optional[bool]:
        """
        Whether a date's month-day falls inside an 'MM-DD' window.

        Returns None when no window is available (cannot be determined).
        """
        if not window:
            return None
        return self._mmdd_in_window(
            self._date_to_mmdd(value), window["start"], window["end"]
        )

    # ------------------------------------------------------------------
    # Stage schedule calculation
    # ------------------------------------------------------------------
    def build_stage_schedule(
        self,
        sowing_date: date,
        growth_stages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Compute start/end dates for every growth stage from a sowing date.

        Stages are laid out consecutively: each stage starts the day after
        the previous stage ends. The first stage starts on the sowing date.

        Args:
            sowing_date: The sowing/planting date
            growth_stages: Static stage definitions (stage, duration_days,
                activities) from the service layer

        Returns:
            List of scheduled stage dictionaries with start_date, end_date,
            duration_days and activities
        """
        schedule: List[Dict[str, Any]] = []
        cursor = sowing_date
        for stage in growth_stages:
            duration = int(stage["duration_days"])
            start = cursor
            end = cursor + timedelta(days=duration - 1)
            schedule.append({
                "stage": stage["stage"],
                "duration_days": duration,
                "activities": list(stage.get("activities", [])),
                "start_date": start,
                "end_date": end,
            })
            cursor = end + timedelta(days=1)
        return schedule

    # ------------------------------------------------------------------
    # Stage determination
    # ------------------------------------------------------------------
    @staticmethod
    def _stage_index_for_date(
        schedule: List[Dict[str, Any]], target: date
    ) -> Optional[int]:
        """Index of the stage covering the target date, if any."""
        for index, stage in enumerate(schedule):
            if stage["start_date"] <= target <= stage["end_date"]:
                return index
        return None

    def determine_current_stage(
        self, schedule: List[Dict[str, Any]], as_of_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Identify the growth stage covering the as-of date.

        Returns a dictionary with the stage name, its index and the
        percentage progress through the stage, or None when the as-of date
        is outside the crop duration (e.g. before sowing).
        """
        index = self._stage_index_for_date(schedule, as_of_date)
        if index is None:
            return None

        stage = schedule[index]
        stage_duration = (stage["end_date"] - stage["start_date"]).days + 1
        elapsed = (as_of_date - stage["start_date"]).days + 1
        progress_percent = round(elapsed / stage_duration * 100.0, 1)

        return {
            "stage": stage["stage"],
            "index": index,
            "progress_percent": progress_percent,
        }

    def get_next_stage(
        self, schedule: List[Dict[str, Any]], as_of_date: date
    ) -> Optional[str]:
        """
        Name of the next stage after the as-of date, if any.

        Returns None when the as-of date falls within the final stage or
        beyond the crop duration.
        """
        index = self._stage_index_for_date(schedule, as_of_date)
        if index is not None and index < len(schedule) - 1:
            return schedule[index + 1]["stage"]
        if index is None and schedule and as_of_date < schedule[0]["start_date"]:
            return schedule[0]["stage"]
        return None

    # ------------------------------------------------------------------
    # Harvest window and activities
    # ------------------------------------------------------------------
    def calculate_harvest_window(
        self,
        schedule: List[Dict[str, Any]],
        tolerance_days: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Approximate harvest window derived from the maturity date.

        The window spans the last stage end date +/- the tolerance in days.
        Returns None when the schedule is empty.
        """
        if not schedule:
            return None
        tolerance = (
            tolerance_days
            if tolerance_days is not None
            else self.HARVEST_WINDOW_TOLERANCE_DAYS
        )
        maturity_date = schedule[-1]["end_date"]
        return {
            "start_date": maturity_date - timedelta(days=tolerance),
            "end_date": maturity_date + timedelta(days=tolerance),
        }

    def get_upcoming_activities(
        self,
        schedule: List[Dict[str, Any]],
        as_of_date: date,
        within_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Stage activities scheduled within a window around the as-of date.

        A stage is included when it starts within ``within_days`` days of
        the as-of date (stages already in progress are included too).
        """
        window = (
            within_days
            if within_days is not None
            else self.UPCOMING_ACTIVITY_WINDOW_DAYS
        )
        horizon = as_of_date + timedelta(days=window)
        upcoming: List[Dict[str, Any]] = []
        for stage in schedule:
            if stage["start_date"] <= horizon and stage["end_date"] >= as_of_date:
                upcoming.append({
                    "stage": stage["stage"],
                    "start_date": stage["start_date"],
                    "end_date": stage["end_date"],
                    "activities": list(stage["activities"]),
                })
        return upcoming

    # ------------------------------------------------------------------
    # Combined schedule
    # ------------------------------------------------------------------
    def build_crop_schedule(
        self,
        sowing_date: date,
        growth_stages: List[Dict[str, Any]],
        as_of_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Build the full derived schedule for a sowing date.

        Combines stage-date calculation, current/next stage determination,
        harvest-window calculation and upcoming-activity extraction into a
        single deterministic result with explicit warnings.
        """
        as_of = as_of_date if as_of_date is not None else date.today()
        warnings: List[str] = []

        if not growth_stages:
            raise ValueError("No growth stages available to schedule")

        schedule = self.build_stage_schedule(sowing_date, growth_stages)

        if as_of < sowing_date:
            warnings.append(
                "As-of date is before the sowing date; current growth "
                "stage is not available."
            )

        current = self.determine_current_stage(schedule, as_of)
        next_stage = self.get_next_stage(schedule, as_of)
        harvest_window = self.calculate_harvest_window(schedule)

        days_to_harvest: Optional[int] = None
        if harvest_window and as_of <= harvest_window["end_date"]:
            days_to_harvest = (harvest_window["end_date"] - as_of).days

        if harvest_window and as_of > harvest_window["end_date"]:
            warnings.append(
                "As-of date is after the estimated harvest window for "
                "this sowing date."
            )

        return {
            "sowing_date": sowing_date,
            "as_of_date": as_of,
            "scheduled_growth_stages": schedule,
            "current_stage": current["stage"] if current else None,
            "current_stage_progress_percent": (
                current["progress_percent"] if current else None
            ),
            "next_stage": next_stage,
            "harvest_window": harvest_window,
            "days_to_harvest_estimate": days_to_harvest,
            "upcoming_activities": self.get_upcoming_activities(
                schedule, as_of
            ),
            "warnings": warnings,
        }
