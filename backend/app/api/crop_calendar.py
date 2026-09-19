"""
Crop Calendar API endpoints.

Exposes static/reference agricultural calendar data and derived crop
schedules through the FastAPI backend:

- ``GET /api/crop-calendar``            -> crop catalogue
- ``GET /api/crop-calendar/health``     -> module health check
- ``GET /api/crop-calendar/{crop}``     -> static calendar for a crop
- ``GET /api/crop-calendar/{crop}/schedule``
                                        -> schedule derived from a sowing date

Static/reference calendar data (sowing windows, durations, stages,
activities) is clearly separated from dynamic context (sowing date,
as-of date, computed stage dates). Responses built from the bundled
reference dataset are explicitly labelled as reference data - they are
never presented as authoritative or real-time predictions.

Error handling contract (mirrors the weather module):
- 400: invalid request parameters caught at the service/intelligence
  layer (ValueError)
- 404: unsupported crop (CropNotFoundError)
- 422: request parameter validation failures (FastAPI/Pydantic)
- 500: unexpected internal errors (no stack trace is exposed)
- 502: upstream provider failures (CropCalendarServiceError)
"""

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from ..core.logging import logger
from ..intelligence import crop_calendar_intelligence
from ..schemas import crop_calendar as schemas
from ..services import crop_calendar_service

# Create router
router = APIRouter(
    prefix="/api/crop-calendar",
    tags=["crop-calendar"],
    responses={404: {"description": "Not found"}},
)

SERVICE_NAME = "agrinexus-crop-calendar"
SERVICE_VERSION = "1.0.0"


# Dependency injection
def get_crop_calendar_service(
) -> crop_calendar_service.CropCalendarService:
    """Dependency to get the crop calendar service."""
    return crop_calendar_service.CropCalendarService()


def get_crop_calendar_intelligence_service(
) -> crop_calendar_intelligence.CropCalendarIntelligence:
    """Dependency to get the crop calendar intelligence service."""
    return crop_calendar_intelligence.CropCalendarIntelligence()


def _utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


@router.get(
    "",
    response_model=schemas.CropCatalogResponse,
    summary="List crops available in the crop calendar",
    description=(
        "Retrieve the catalogue of crops supported by the active calendar "
        "data source, including aliases, seasons and typical crop "
        "durations. By default this is the bundled, non-authoritative "
        "reference dataset."
    ),
)
async def get_crop_catalog(
    crop_calendar_svc: (
        crop_calendar_service.CropCalendarService
    ) = Depends(get_crop_calendar_service),
):
    """Get the crop calendar catalogue."""
    logger.info("Fetching crop calendar catalogue")

    try:
        catalog = crop_calendar_svc.get_supported_crops()
        return schemas.CropCatalogResponse(
            crops=catalog["crops"],
            total=catalog["total"],
            region_scope=catalog["region_scope"],
            data_source=catalog["data_source"],
            is_reference_data=catalog["is_reference_data"],
            external_provider_configured=(
                catalog["external_provider_configured"]
            ),
            note=catalog["note"],
            data_timestamp=catalog["data_timestamp"],
        )
    except Exception as e:
        logger.error(f"Error building crop calendar catalogue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while listing crops",
        )


@router.get(
    "/health",
    response_model=schemas.CropCalendarHealthResponse,
    summary="Health check for the crop calendar module",
    description=(
        "Check whether the crop calendar module is operational, which "
        "data source is active and whether an external provider is "
        "configured and reachable. Reports configuration status only - "
        "no secret values, no provider URLs and no credentials are "
        "exposed. When SPORA_API_KEY is unset the bundled reference "
        "dataset is the active source."
    ),
)
async def crop_calendar_health_check(
    crop_calendar_svc: (
        crop_calendar_service.CropCalendarService
    ) = Depends(get_crop_calendar_service),
):
    """Report module status and data-source configuration."""
    logger.info("Checking crop calendar module health")

    external_configured = crop_calendar_svc.is_external_provider_configured

    reference_available = False
    supported_crops_count = 0
    try:
        catalog = crop_calendar_svc.get_supported_crops()
        supported_crops_count = catalog["total"]
        reference_available = supported_crops_count > 0
    except Exception as e:
        logger.warning(f"Reference dataset check failed: {e}")

    external_connectivity: Optional[bool] = None
    if external_configured:
        external_connectivity = (
            await crop_calendar_svc.external_client.check_connectivity()
        )

    health_status = (
        "healthy"
        if reference_available and (
            not external_configured
            or external_connectivity is not False
        )
        else "degraded"
    )

    return schemas.CropCalendarHealthResponse(
        status=health_status,
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        timestamp=_utc_now_iso(),
        data_source_active=crop_calendar_svc.get_active_data_source(),
        external_provider_configured=external_configured,
        external_api_key_configured=(
            crop_calendar_svc.is_external_api_key_configured
        ),
        reference_dataset_available=reference_available,
        supported_crops_count=supported_crops_count,
        external_connectivity=external_connectivity,
    )


@router.get(
    "/{crop}",
    response_model=schemas.StaticCropCalendarResponse,
    summary="Get the static crop calendar for a crop",
    description=(
        "Retrieve the static/reference agricultural calendar for a crop "
        "and season: sowing window, crop duration, growth stages with "
        "durations and reference activities, harvest-related notes and "
        "data provenance. No dates are computed; supply a sowing date to "
        "the schedule endpoint for derived stage dates."
    ),
)
async def get_crop_calendar(
    crop: str = Path(
        ..., min_length=1, max_length=50,
        description="Crop name or common alias", example="rice",
    ),
    season: Optional[str] = Query(
        None,
        description=(
            "Agricultural season (kharif, rabi, zaid). Defaults to the "
            "crop's primary season when omitted."
        ),
        example="kharif",
    ),
    location: Optional[str] = Query(
        None, max_length=100,
        description=(
            "Optional location label echoed in the response "
            "(informational; the active data source is region-general)"
        ),
        example="West Bengal",
    ),
    crop_calendar_svc: (
        crop_calendar_service.CropCalendarService
    ) = Depends(get_crop_calendar_service),
):
    """
    Get the static crop calendar for a crop.

    Data comes from the active data source (bundled reference dataset by
    default). Responses built from the reference dataset are explicitly
    labelled with ``is_reference_data=True``.
    """
    logger.info(
        f"Fetching static crop calendar for crop={crop}, season={season}, "
        f"location={'provided' if location else 'not provided'}"
    )

    try:
        calendar = await crop_calendar_svc.get_crop_calendar(
            crop=crop, season=season, location=location
        )
        # Map service keys to the response schema explicitly rather than
        # relying on FastAPI's model filtering.
        return schemas.StaticCropCalendarResponse(
            crop=calendar["crop"],
            aliases=calendar.get("aliases", []),
            location=calendar.get("location"),
            region_scope=calendar["region_scope"],
            season=calendar["season"],
            season_source=calendar["season_source"],
            seasons_available=calendar.get("seasons_available", []),
            sowing_window=calendar.get("sowing_window"),
            crop_duration_days=calendar["crop_duration_days"],
            growth_stages=calendar["growth_stages"],
            notes=calendar.get("notes", []),
            data_source=calendar["data_source"],
            is_reference_data=calendar["is_reference_data"],
            reference_note=calendar.get("reference_note"),
            fallback_used=calendar.get("fallback_used", False),
            fallback_reason=calendar.get("fallback_reason"),
            data_timestamp=calendar["data_timestamp"],
        )
    except ValueError as e:
        logger.warning(f"Invalid crop calendar request parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except crop_calendar_service.CropNotFoundError as e:
        logger.warning(f"Unsupported crop requested: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except crop_calendar_service.CropCalendarServiceError as e:
        logger.error(f"Upstream crop calendar provider failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Crop calendar data provider is currently unavailable",
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching crop calendar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching the crop calendar",
        )


@router.get(
    "/{crop}/schedule",
    response_model=schemas.CropCalendarScheduleResponse,
    summary="Get the crop schedule for a sowing date",
    description=(
        "Derive the growth-stage schedule for a supplied sowing date: "
        "stage start/end dates, the current and next growth stage at the "
        "as-of date, the approximate harvest window and upcoming "
        "activities. All derived values are deterministic date arithmetic "
        "on the static calendar data - they are NOT real-time predictions "
        "and NOT weather-adjusted."
    ),
)
async def get_crop_schedule(
    crop: str = Path(
        ..., min_length=1, max_length=50,
        description="Crop name or common alias", example="rice",
    ),
    sowing_date: date = Query(
        ...,
        description="Sowing/planting date used to compute stage dates",
        example="2026-06-15",
    ),
    as_of_date: Optional[date] = Query(
        None,
        description=(
            "Reference date for current-stage determination; defaults to "
            "today (UTC server date)"
        ),
        example="2026-09-19",
    ),
    season: Optional[str] = Query(
        None,
        description=(
            "Agricultural season (kharif, rabi, zaid). When omitted, the "
            "season is inferred from the crop's sowing windows and then "
            "from the sowing month."
        ),
        example="kharif",
    ),
    location: Optional[str] = Query(
        None, max_length=100,
        description=(
            "Optional location label echoed in the response "
            "(informational; the active data source is region-general)"
        ),
        example="West Bengal",
    ),
    crop_calendar_svc: (
        crop_calendar_service.CropCalendarService
    ) = Depends(get_crop_calendar_service),
    intel_svc: (
        crop_calendar_intelligence.CropCalendarIntelligence
    ) = Depends(get_crop_calendar_intelligence_service),
):
    """
    Get the derived crop schedule for a sowing date.

    The season is resolved in this order: explicit request parameter,
    sowing-window match for the crop, then sowing-month convention. The
    service supplies the static calendar; the intelligence layer computes
    the schedule.
    """
    logger.info(
        f"Fetching crop schedule for crop={crop}, "
        f"sowing_date={sowing_date}, season={season}, "
        f"as_of_date={as_of_date}"
    )

    try:
        # 1. Resolve the crop and its supported seasons / sowing windows.
        season_info = crop_calendar_svc.get_crop_season_info(crop)
        seasons_available = season_info.get("seasons_available")
        sowing_windows = season_info.get("sowing_windows")

        # 2. Resolve the season (provided -> window match -> month rule).
        resolved_season: Optional[str] = None
        season_source: str
        if season is not None:
            resolved_season = intel_svc.normalize_season(season)
            season_source = "provided"
            if (
                seasons_available is not None
                and resolved_season not in seasons_available
            ):
                raise ValueError(
                    f"Crop '{season_info['crop']}' does not have a "
                    f"'{resolved_season}' calendar. Available seasons: "
                    f"{', '.join(seasons_available)}"
                )
        else:
            if sowing_windows:
                resolved_season = intel_svc.match_sowing_window(
                    sowing_date, sowing_windows
                )
                if resolved_season is not None:
                    season_source = "inferred_from_sowing_window"
            if resolved_season is None:
                resolved_season = intel_svc.infer_season_from_sowing_date(
                    sowing_date
                )
                season_source = "inferred_from_sowing_month"
                if (
                    seasons_available is not None
                    and resolved_season not in seasons_available
                ):
                    raise ValueError(
                        f"Crop '{season_info['crop']}' does not have a "
                        f"'{resolved_season}' calendar for a sowing date "
                        f"of {sowing_date.isoformat()}. Available "
                        f"seasons: {', '.join(seasons_available)}"
                    )

        # 3. Fetch the static calendar for the resolved crop/season.
        calendar = await crop_calendar_svc.get_crop_calendar(
            crop=crop, season=resolved_season, location=location
        )
        calendar["season"] = resolved_season
        calendar["season_source"] = season_source

        # 4. Derive the schedule (intelligence layer).
        schedule = intel_svc.build_crop_schedule(
            sowing_date=sowing_date,
            growth_stages=calendar["growth_stages"],
            as_of_date=as_of_date,
        )

        # 5. Sowing-window compliance and explicit warning when outside.
        sowing_window_compliant = intel_svc.is_date_within_window(
            sowing_date, calendar.get("sowing_window")
        )
        if sowing_window_compliant is False and calendar.get("sowing_window"):
            schedule["warnings"].append(
                f"Sowing date {sowing_date.isoformat()} is outside the "
                f"{resolved_season} sowing window "
                f"({calendar['sowing_window']['start']} to "
                f"{calendar['sowing_window']['end']}) for this crop."
            )

        # 6. Assemble the response explicitly.
        return schemas.CropCalendarScheduleResponse(
            crop=calendar["crop"],
            aliases=calendar.get("aliases", []),
            location=calendar.get("location"),
            region_scope=calendar["region_scope"],
            season=calendar["season"],
            season_source=calendar["season_source"],
            seasons_available=calendar.get("seasons_available", []),
            sowing_window=calendar.get("sowing_window"),
            crop_duration_days=calendar["crop_duration_days"],
            growth_stages=calendar["growth_stages"],
            notes=calendar.get("notes", []),
            data_source=calendar["data_source"],
            is_reference_data=calendar["is_reference_data"],
            reference_note=calendar.get("reference_note"),
            fallback_used=calendar.get("fallback_used", False),
            fallback_reason=calendar.get("fallback_reason"),
            data_timestamp=calendar["data_timestamp"],
            sowing_date=schedule["sowing_date"],
            as_of_date=schedule["as_of_date"],
            scheduled_growth_stages=[
                {
                    "stage": stage["stage"],
                    "duration_days": stage["duration_days"],
                    "activities": stage["activities"],
                    "start_date": stage["start_date"],
                    "end_date": stage["end_date"],
                    "is_current": (
                        schedule["current_stage"] is not None
                        and stage["stage"] == schedule["current_stage"]
                    ),
                }
                for stage in schedule["scheduled_growth_stages"]
            ],
            current_stage=schedule["current_stage"],
            current_stage_progress_percent=(
                schedule["current_stage_progress_percent"]
            ),
            next_stage=schedule["next_stage"],
            harvest_window=schedule["harvest_window"],
            days_to_harvest_estimate=schedule["days_to_harvest_estimate"],
            upcoming_activities=schedule["upcoming_activities"],
            sowing_window_compliant=sowing_window_compliant,
            warnings=schedule["warnings"],
        )

    except ValueError as e:
        logger.warning(f"Invalid crop schedule request parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except crop_calendar_service.CropNotFoundError as e:
        logger.warning(f"Unsupported crop requested: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except crop_calendar_service.CropCalendarServiceError as e:
        logger.error(f"Upstream crop calendar provider failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Crop calendar data provider is currently unavailable",
        )
    except Exception as e:
        logger.error(f"Unexpected error building crop schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while building the crop schedule",
        )
