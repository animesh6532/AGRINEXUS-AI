"""
Pydantic schemas for the Crop Calendar API.

Describes static/reference agricultural calendar information and the
derived schedule information computed from a supplied sowing date.

Design notes:
- Static/reference calendar data (sowing windows, crop duration, growth
  stages, activities) is clearly distinguished from dynamic context
  (sowing date, as-of date, derived stage dates) through the two response
  families: StaticCropCalendarResponse and CropCalendarScheduleResponse.
- Responses built from the bundled reference dataset are explicitly
  labelled with ``is_reference_data=True`` so static reference data is
  never presented as an authoritative or real-time prediction.

Conventions follow the existing weather/market schemas (Pydantic v2,
Field with examples, Base/Response style).
"""

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SowingWindow(BaseModel):
    """Inclusive sowing/planting window as 'MM-DD' month-day boundaries."""

    start: str = Field(
        ..., pattern=r"^\d{2}-\d{2}$", example="06-01",
        description="Window start (MM-DD)",
    )
    end: str = Field(
        ..., pattern=r"^\d{2}-\d{2}$", example="07-15",
        description="Window end (MM-DD); may be earlier than start for "
                    "windows wrapping the calendar year",
    )


class GrowthStageDefinition(BaseModel):
    """A static growth-stage definition from the calendar data."""

    stage: str = Field(..., example="tillering")
    duration_days: int = Field(..., ge=1, example=30)
    activities: List[str] = Field(
        default_factory=list,
        example=["Weed control", "Nitrogen top dressing (reference practice)"],
    )


class HarvestWindow(BaseModel):
    """Approximate harvest window derived from the maturity date."""

    start_date: date = Field(..., example="2026-10-17")
    end_date: date = Field(..., example="2026-11-06")


class ScheduledGrowthStage(GrowthStageDefinition):
    """
    A growth stage with dates computed from a supplied sowing date.

    The dates are deterministic date arithmetic on the static stage
    durations - they are NOT a real-time prediction.
    """

    start_date: date = Field(..., example="2026-07-20")
    end_date: date = Field(..., example="2026-08-18")
    is_current: bool = Field(
        default=False, example=False,
        description="Whether this stage covers the as-of date",
    )


class UpcomingActivity(BaseModel):
    """A stage whose activities fall within the upcoming-activity window."""

    stage: str = Field(..., example="tillering")
    start_date: date = Field(..., example="2026-07-20")
    end_date: date = Field(..., example="2026-08-18")
    activities: List[str] = Field(
        default_factory=list, example=["Weed control"]
    )


class StaticCropCalendarResponse(BaseModel):
    """
    Static/reference agricultural calendar for one crop and season.

    Contains only reference calendar data (no dates computed from a
    sowing date).
    """

    crop: str = Field(..., example="rice")
    aliases: List[str] = Field(
        default_factory=list, example=["paddy", "dhan"]
    )
    location: Optional[str] = Field(
        None, example="West Bengal",
        description="Echoed request location (informational only; the "
                    "active data source is region-general)",
    )
    region_scope: str = Field(
        ..., example="india_generic",
        description="Geographic scope of the active data source",
    )
    season: str = Field(..., example="kharif")
    season_source: str = Field(
        ...,
        pattern="^(provided|default|inferred_from_sowing_window|"
                "inferred_from_sowing_month)$",
        example="default",
        description="How the season was determined",
    )
    seasons_available: List[str] = Field(
        default_factory=list, example=["kharif", "rabi"]
    )
    sowing_window: Optional[SowingWindow] = None
    crop_duration_days: int = Field(..., ge=1, example=135)
    growth_stages: List[GrowthStageDefinition] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    data_source: str = Field(..., example="reference_dataset")
    is_reference_data: bool = Field(
        ...,
        example=True,
        description="True when the response is built from the bundled, "
                    "non-authoritative reference dataset",
    )
    reference_note: Optional[str] = Field(
        None,
        description="Provenance note present when is_reference_data is true",
    )
    fallback_used: bool = Field(
        default=False,
        description="True when the external provider was configured but "
                    "could not be reached/used, so the bundled reference "
                    "dataset was served instead. Never silently presented "
                    "as external provider data.",
    )
    fallback_reason: Optional[str] = Field(
        None,
        description="Why the reference fallback was used (no credentials "
                    "or error values are included)",
    )
    data_timestamp: str = Field(
        ..., example="2026-09-19T10:30:00+00:00",
        description="UTC timestamp at which the response was generated "
                    "(serving timestamp, not a data-observation time)",
    )


class CropCalendarScheduleResponse(StaticCropCalendarResponse):
    """
    Crop calendar with a derived schedule for a supplied sowing date.

    Extends the static calendar with dynamic context: stage dates
    computed from the sowing date, the current/next growth stage at the
    as-of date, the harvest window and upcoming activities. All derived
    values are deterministic date arithmetic on the static data - they
    are NOT real-time predictions.
    """

    sowing_date: date = Field(..., example="2026-06-15")
    as_of_date: date = Field(..., example="2026-09-19")
    scheduled_growth_stages: List[ScheduledGrowthStage] = Field(
        default_factory=list
    )
    current_stage: Optional[str] = Field(
        None, example="tillering",
        description="Growth stage covering the as-of date (null when the "
                    "as-of date is outside the crop duration)",
    )
    current_stage_progress_percent: Optional[float] = Field(
        None, ge=0, le=100, example=40.0,
        description="Progress through the current stage (percent)",
    )
    next_stage: Optional[str] = Field(None, example="panicle_initiation")
    harvest_window: Optional[HarvestWindow] = None
    days_to_harvest_estimate: Optional[int] = Field(
        None, example=48,
        description="Days from the as-of date to the end of the harvest "
                    "window (null once the window has passed)",
    )
    upcoming_activities: List[UpcomingActivity] = Field(default_factory=list)
    sowing_window_compliant: Optional[bool] = Field(
        None, example=True,
        description="Whether the sowing date falls inside the reference "
                    "sowing window (null when no window is available)",
    )
    warnings: List[str] = Field(default_factory=list)


class CropCatalogEntry(BaseModel):
    """A crop available in the calendar catalogue."""

    crop: str = Field(..., example="rice")
    aliases: List[str] = Field(default_factory=list, example=["paddy"])
    seasons: List[str] = Field(default_factory=list, example=["kharif", "rabi"])
    crop_duration_days: Dict[str, int] = Field(
        default_factory=dict, example={"kharif": 135, "rabi": 130}
    )


class CropCatalogResponse(BaseModel):
    """Catalogue of crops available from the active calendar data source."""

    crops: List[CropCatalogEntry] = Field(default_factory=list)
    total: int = Field(..., ge=0, example=4)
    region_scope: str = Field(..., example="india_generic")
    data_source: str = Field(..., example="reference_dataset")
    is_reference_data: bool = Field(..., example=True)
    external_provider_configured: bool = Field(
        ..., example=False,
        description="Whether an external crop-calendar provider is "
                    "configured (never exposes the provider key)",
    )
    note: Optional[str] = Field(
        None,
        description="Provenance/coverage note for the catalogue",
    )
    data_timestamp: str = Field(..., example="2026-09-19T10:30:00+00:00")


class CropCalendarHealthResponse(BaseModel):
    """
    Health check response for the crop calendar module.

    Reports configuration status only. It never returns provider URLs
    beyond configuration status booleans or any secret values.
    """

    status: str = Field(..., example="healthy")
    service: str = Field(..., example="agrinexus-crop-calendar")
    version: str = Field(..., example="1.0.0")
    timestamp: str = Field(..., example="2026-09-19T10:30:00+00:00")
    data_source_active: str = Field(
        ..., example="reference_dataset",
        description="Currently active calendar data source",
    )
    external_provider_configured: bool = Field(
        ..., example=False,
        description="Whether the external crop-calendar provider is "
                    "configured (SPORA_API_BASE_URL + SPORA_API_KEY set)",
    )
    external_api_key_configured: bool = Field(
        ..., example=False,
        description="Whether the SPORA_API_KEY is set (status only; the "
                    "key value is never exposed)",
    )
    reference_dataset_available: bool = Field(..., example=True)
    supported_crops_count: int = Field(..., ge=0, example=4)
    external_connectivity: Optional[bool] = Field(
        None,
        description="External provider connectivity probe result; null "
                    "when no external provider is configured",
    )

