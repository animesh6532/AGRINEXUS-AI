"""
Test the crop calendar intelligence layer (pure calendar logic).

These tests exercise deterministic date arithmetic on static calendar
data. No network calls and no external services are involved.
"""

from datetime import date

import pytest

from app.intelligence.crop_calendar_intelligence import (
    CropCalendarIntelligence,
)

# Reference stages totalling 100 days for easy arithmetic
STAGES_100_DAYS = [
    {"stage": "stage_a", "duration_days": 10, "activities": ["a1", "a2"]},
    {"stage": "stage_b", "duration_days": 30, "activities": []},
    {"stage": "stage_c", "duration_days": 60, "activities": ["c1"]},
]


@pytest.fixture
def intel():
    """Create a crop calendar intelligence instance."""
    return CropCalendarIntelligence()


class TestSeasonInference:
    """Test season inference from sowing dates."""

    def test_kharif_months(self, intel):
        assert intel.infer_season_from_sowing_date(
            date(2026, 6, 15)
        ) == "kharif"
        assert intel.infer_season_from_sowing_date(
            date(2026, 10, 1)
        ) == "kharif"

    def test_rabi_months(self, intel):
        assert intel.infer_season_from_sowing_date(
            date(2026, 11, 20)
        ) == "rabi"
        assert intel.infer_season_from_sowing_date(
            date(2026, 1, 10)
        ) == "rabi"
        assert intel.infer_season_from_sowing_date(
            date(2026, 3, 31)
        ) == "rabi"

    def test_zaid_months(self, intel):
        assert intel.infer_season_from_sowing_date(
            date(2026, 4, 5)
        ) == "zaid"
        assert intel.infer_season_from_sowing_date(
            date(2026, 5, 20)
        ) == "zaid"

    def test_normalize_season(self, intel):
        assert intel.normalize_season(" KHARIF ") == "kharif"
        assert intel.normalize_season("Rabi") == "rabi"

    def test_normalize_season_invalid(self, intel):
        with pytest.raises(ValueError, match="Unsupported season"):
            intel.normalize_season("monsoon")
        with pytest.raises(ValueError):
            intel.normalize_season("")
        with pytest.raises(ValueError):
            intel.normalize_season(None)

    def test_match_sowing_window(self, intel):
        windows = {
            "kharif": {"start": "06-01", "end": "07-15"},
            "rabi": {"start": "11-15", "end": "01-15"},
        }
        assert intel.match_sowing_window(
            date(2026, 6, 15), windows
        ) == "kharif"
        assert intel.match_sowing_window(
            date(2026, 12, 1), windows
        ) == "rabi"
        assert intel.match_sowing_window(
            date(2026, 4, 1), windows
        ) is None

    def test_match_sowing_window_skips_empty(self, intel):
        windows = {"kharif": None}
        assert intel.match_sowing_window(date(2026, 6, 15), windows) is None

    def test_is_date_within_window(self, intel):
        window = {"start": "06-01", "end": "07-15"}
        assert intel.is_date_within_window(date(2026, 6, 15), window) is True
        assert intel.is_date_within_window(date(2026, 8, 1), window) is False
        assert intel.is_date_within_window(date(2026, 6, 15), None) is None


class TestStageSchedule:
    """Test stage-date calculation from a sowing date."""

    def test_schedule_starts_on_sowing_date(self, intel):
        schedule = intel.build_stage_schedule(
            date(2026, 6, 15), STAGES_100_DAYS
        )
        assert schedule[0]["start_date"] == date(2026, 6, 15)

    def test_schedule_stages_are_consecutive(self, intel):
        schedule = intel.build_stage_schedule(
            date(2026, 6, 15), STAGES_100_DAYS
        )
        assert len(schedule) == 3
        # stage_a: 10 days -> 06-15..06-24
        assert schedule[0]["end_date"] == date(2026, 6, 24)
        # stage_b starts the next day: 06-25..07-24
        assert schedule[1]["start_date"] == date(2026, 6, 25)
        assert schedule[1]["end_date"] == date(2026, 7, 24)
        # stage_c: 07-25..09-22 (60 days)
        assert schedule[2]["start_date"] == date(2026, 7, 25)
        assert schedule[2]["end_date"] == date(2026, 9, 22)

    def test_schedule_durations_preserved(self, intel):
        schedule = intel.build_stage_schedule(
            date(2026, 6, 15), STAGES_100_DAYS
        )
        total = sum(s["duration_days"] for s in schedule)
        assert total == 100
        for stage in schedule:
            assert (
                (stage["end_date"] - stage["start_date"]).days + 1
                == stage["duration_days"]
            )

    def test_schedule_activities_copied(self, intel):
        schedule = intel.build_stage_schedule(
            date(2026, 6, 15), STAGES_100_DAYS
        )
        assert schedule[0]["activities"] == ["a1", "a2"]
        assert schedule[1]["activities"] == []

    def test_schedule_empty_stages_rejected(self, intel):
        with pytest.raises(ValueError, match="No growth stages"):
            intel.build_crop_schedule(date(2026, 6, 15), [])


class TestCurrentStageDetermination:
    """Test current/next stage determination."""

    @pytest.fixture
    def schedule(self, intel):
        return intel.build_stage_schedule(
            date(2026, 6, 15), STAGES_100_DAYS
        )

    def test_current_stage_first_day(self, intel, schedule):
        result = intel.determine_current_stage(schedule, date(2026, 6, 15))
        assert result["stage"] == "stage_a"
        assert result["progress_percent"] == 10.0

    def test_current_stage_last_day_of_stage(self, intel, schedule):
        result = intel.determine_current_stage(schedule, date(2026, 6, 24))
        assert result["stage"] == "stage_a"
        assert result["progress_percent"] == 100.0

    def test_current_stage_mid_crop(self, intel, schedule):
        result = intel.determine_current_stage(schedule, date(2026, 7, 1))
        assert result["stage"] == "stage_b"

    def test_current_stage_after_crop_returns_none(self, intel, schedule):
        assert intel.determine_current_stage(
            schedule, date(2026, 10, 1)
        ) is None

    def test_current_stage_before_sowing_returns_none(
        self, intel, schedule
    ):
        assert intel.determine_current_stage(
            schedule, date(2026, 6, 1)
        ) is None

    def test_next_stage_during_crop(self, intel, schedule):
        assert intel.get_next_stage(schedule, date(2026, 7, 1)) == "stage_c"

    def test_next_stage_in_final_stage_is_none(self, intel, schedule):
        assert intel.get_next_stage(schedule, date(2026, 9, 1)) is None

    def test_next_stage_before_sowing_is_first_stage(self, intel, schedule):
        assert intel.get_next_stage(schedule, date(2026, 6, 1)) == "stage_a"


class TestHarvestWindow:
    """Test harvest-window calculation."""

    @pytest.fixture
    def schedule(self, intel):
        return intel.build_stage_schedule(
            date(2026, 6, 15), STAGES_100_DAYS
        )

    def test_harvest_window_default_tolerance(self, intel, schedule):
        window = intel.calculate_harvest_window(schedule)
        # Maturity (last stage end) is 2026-09-22
        assert window["start_date"] == date(2026, 9, 12)
        assert window["end_date"] == date(2026, 10, 2)

    def test_harvest_window_custom_tolerance(self, intel, schedule):
        window = intel.calculate_harvest_window(schedule, tolerance_days=5)
        assert window["start_date"] == date(2026, 9, 17)
        assert window["end_date"] == date(2026, 9, 27)

    def test_harvest_window_empty_schedule(self, intel):
        assert intel.calculate_harvest_window([]) is None


class TestUpcomingActivities:
    """Test upcoming-activity extraction."""

    def test_includes_active_and_near_future_stages(self, intel):
        schedule = intel.build_stage_schedule(
            date(2026, 6, 15), STAGES_100_DAYS
        )
        # as-of 2026-06-20 (inside stage_a): stage_a active, stage_b
        # starts within 14 days (06-25), stage_c does not (07-25).
        upcoming = intel.get_upcoming_activities(
            schedule, date(2026, 6, 20), within_days=14
        )
        assert [u["stage"] for u in upcoming] == ["stage_a", "stage_b"]

    def test_activities_only_after_as_of_date(self, intel):
        schedule = intel.build_stage_schedule(
            date(2026, 6, 15), STAGES_100_DAYS
        )
        upcoming = intel.get_upcoming_activities(
            schedule, date(2026, 9, 30), within_days=14
        )
        assert upcoming == []


class TestBuildCropSchedule:
    """Test the combined schedule builder."""

    def test_full_schedule(self, intel):
        result = intel.build_crop_schedule(
            sowing_date=date(2026, 6, 15),
            growth_stages=STAGES_100_DAYS,
            as_of_date=date(2026, 7, 1),
        )
        assert result["sowing_date"] == date(2026, 6, 15)
        assert result["as_of_date"] == date(2026, 7, 1)
        assert result["current_stage"] == "stage_b"
        assert result["current_stage_progress_percent"] == 23.3
        assert result["next_stage"] == "stage_c"
        assert result["harvest_window"]["start_date"] == date(2026, 9, 12)
        assert result["days_to_harvest_estimate"] == 93
        assert result["warnings"] == []

    def test_before_sowing_adds_warning_and_no_current_stage(self, intel):
        result = intel.build_crop_schedule(
            sowing_date=date(2026, 6, 15),
            growth_stages=STAGES_100_DAYS,
            as_of_date=date(2026, 6, 1),
        )
        assert result["current_stage"] is None
        assert result["next_stage"] == "stage_a"
        assert result["days_to_harvest_estimate"] is not None
        assert any("before the sowing date" in w for w in result["warnings"])

    def test_after_harvest_adds_warning_and_null_days_to_harvest(
        self, intel
    ):
        result = intel.build_crop_schedule(
            sowing_date=date(2026, 6, 15),
            growth_stages=STAGES_100_DAYS,
            as_of_date=date(2027, 1, 1),
        )
        assert result["current_stage"] is None
        assert result["days_to_harvest_estimate"] is None
        assert any(
            "after the estimated harvest window" in w
            for w in result["warnings"]
        )

    def test_defaults_as_of_to_today(self, intel):
        result = intel.build_crop_schedule(
            sowing_date=date(2026, 6, 15),
            growth_stages=STAGES_100_DAYS,
        )
        assert result["as_of_date"] == date.today()

