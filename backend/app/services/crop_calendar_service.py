"""
Crop Calendar service for retrieving agricultural calendar data.

Responsibility boundary (mirrors the Weather/Market service pattern):
- This module handles DATA RETRIEVAL and normalization. Derived
  calendar/date logic lives in the intelligence layer; HTTP concerns live
  in the API layer.

Data source strategy:
- By default the module serves a small, clearly-labelled BUNDLED REFERENCE
  dataset (see crop_calendar_reference_data). It is non-authoritative and
  every response built from it is flagged accordingly.
- When SPORA_API_KEY is configured, the module fetches calendar data from
  the VERIFIED external provider Spora (https://spora.engineer):

    - Base URL:   https://api.spora.engineer
    - Auth:       "X-Api-Key" request header (key alone is sufficient;
                  no username/password)
    - Endpoint:   GET /harvest/{location} - the crop planting and harvest
                  calendar for a location. ``location`` is a lowercase
                  country slug (e.g. "italy", "france", "kenya", "india").
    - Response:   {"id", "location", "lat", "lon", "crops": [...]} where
                  each crop entry carries "crop"/"crop_name", planting
                  window ("planting_start_date" like "6/1",
                  "planting_end_date" like "7/31"), harvest window
                  ("harvest_start_date"/"harvest_end_date"),
                  "season_length_days", "qualifier" (e.g. "Winter"),
                  and a data "source" (e.g. "MWCACP").
    - Errors:     JSON {"error": <code>, "message": <msg>, "status": <n>}
                  with codes such as missing_api_key / invalid_api_key /
                  api_key_expired (401), plan_not_supported (403),
                  not_found (404), rate_limit_exceeded (429, with
                  "retry_after"), internal_error (500),
                  service_unavailable (503).
    - Limits:     "X-RateLimit-Limit" / "X-RateLimit-Remaining" /
                  "X-RateLimit-Reset" response headers; "Retry-After" on
                  429. Free tier: 1,000 data requests/day, 10 req/min.

  The provider publishes ONE annual planting/harvest window per crop (no
  kharif/rabi/zaid split and no stage-level breakdown), so the client
  derives ``crop_duration_days`` from the provider's
  ``season_length_days`` (falling back to window arithmetic) and models
  the growing period as a single aggregate growth stage. Every such
  derivation is disclosed in the response ``notes`` and the data is
  labelled ``is_reference_data=False`` / ``data_source="spora_harvest_api"``.
  The key is sent only as the "X-Api-Key" header - never logged, never in
  URLs, never in API responses.

Networking approach: Python urllib executed via asyncio.to_thread, which
is consistent with the existing weather and market services (httpx has
proven unreliable for outbound requests in the current Windows
environment).
"""

import asyncio
import calendar as calendar_module
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ..core.config import settings
from ..core.logging import logger
from .crop_calendar_reference_data import (
    REFERENCE_DATA_SOURCE,
    REFERENCE_NOTE,
    REGION_SCOPE,
    get_reference_dataset,
)

# Data-source identifiers used in responses
EXTERNAL_DATA_SOURCE = "spora_harvest_api"

# Non-leap reference year used for day-of-year -> (month, day) mapping
_DOW_REFERENCE_YEAR = 2001

# Sentinel distinguishing "argument not supplied" (fall back to the
# AgriNexus configuration) from an explicit ``None`` (provider disabled).
_UNSET = object()

# Default location slug used when the caller provides no location. The
# module's reference dataset is India-generic, so the Spora calendar for
# India is the natural provider default.
DEFAULT_EXTERNAL_LOCATION = "india"

# Month-name -> month-number map for the provider's documented simplified
# window form ("Mar", "Apr 1", ...).
_MONTH_NAME_TO_NUMBER = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _doy_to_mmdd(doy: Any) -> Optional[str]:
    """
    Convert a provider day-of-year value (e.g. ``planting_start_doy``,
    ``harvest_end_doy``) into an 'MM-DD' string using a non-leap
    reference year (day-of-year values are year-agnostic).
    """
    if isinstance(doy, (int, float)) and 1 <= int(doy) <= 365:
        day = date(_DOW_REFERENCE_YEAR, 1, 1) + timedelta(days=int(doy) - 1)
        return f"{day.month:02d}-{day.day:02d}"
    return None


def _parse_provider_window_value(value: Any, is_end: bool) -> Optional[str]:
    """
    Normalize one provider window value into an 'MM-DD' string.

    Supported provider forms (verified against the official docs and the
    live API):
    - "M/D": planting/harvest dates like "6/1", "7/31", "12/28"
    - month names, optionally with a day: "Mar", "Apr 1" (documented
      simplified form). A bare END month maps to the month's LAST day;
      a bare START month maps to day 1.
    - already-normalized "MM-DD"
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    parts = text.replace(",", " ").split()
    if len(parts) == 1 and "/" in parts[0]:
        month_text, _, day_text = parts[0].partition("/")
        if month_text.isdigit() and day_text.isdigit():
            month, day = int(month_text), int(day_text)
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{month:02d}-{day:02d}"
        return None
    if len(parts) == 1 and "-" in parts[0]:
        month_text, _, day_text = parts[0].partition("-")
        if (
            month_text.isdigit() and day_text.isdigit()
            and len(month_text) == 2 and len(day_text) == 2
        ):
            month, day = int(month_text), int(day_text)
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{month:02d}-{day:02d}"
        return None
    month_number = _MONTH_NAME_TO_NUMBER.get(parts[0][:3].lower())
    if month_number is not None:
        if len(parts) > 1 and parts[1].isdigit():
            day = int(parts[1])
        elif is_end:
            # End of the named month (non-leap reference year is fine
            # because month lengths do not depend on the year here).
            day = calendar_module.monthrange(
                _DOW_REFERENCE_YEAR, month_number
            )[1]
        else:
            day = 1
        return f"{month_number:02d}-{day:02d}"
    return None


def _days_between_mmdd(start_mmdd: str, end_mmdd: str) -> Optional[int]:
    """
    Inclusive day count between two 'MM-DD' values in a non-leap year,
    wrapping the calendar year when the window crosses December 31st.
    """
    start = _parse_provider_window_value(start_mmdd, is_end=False)
    end = _parse_provider_window_value(end_mmdd, is_end=True)
    if not start or not end:
        return None

    def to_date(mmdd: str) -> date:
        month_text, day_text = mmdd.split("-")
        return date(_DOW_REFERENCE_YEAR, int(month_text), int(day_text))

    delta = (to_date(end) - to_date(start)).days
    if delta < 0:
        delta += 365
    return delta + 1

# External request configuration
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY_SECONDS = 1.0

MAX_CROP_NAME_LENGTH = 50
MAX_LOCATION_LENGTH = 100

SUPPORTED_SEASON_NAMES = ("kharif", "rabi", "zaid")


class CropCalendarServiceError(Exception):
    """
    Raised when the external crop-calendar provider fails or returns an
    unusable response (network failure, HTTP error, invalid JSON, missing
    fields, configuration problems). The API layer maps this to HTTP 502,
    while invalid user input is signalled with ValueError and mapped to
    HTTP 400, and unknown crops are signalled with CropNotFoundError and
    mapped to HTTP 404.
    """


class CropNotFoundError(CropCalendarServiceError, LookupError):
    """
    Raised when the requested crop (or alias) is not available from the
    active data source. The API layer maps this to HTTP 404.

    It subclasses CropCalendarServiceError so provider failures surface
    through the service's existing fallback path while still mapping to
    the module's 404 contract at the API layer.
    """


class ExternalCropCalendarClient:
    """
    HTTP client for the verified external crop-calendar provider (Spora).

    Verified integration contract (official docs at
    https://spora.engineer/docs and the official ``spora-sdk`` package):
    - GET ``{SPORA_API_BASE_URL}/harvest/{location}`` where ``location``
      is a lowercase country slug (e.g. "italy", "france", "kenya",
      "india"). The endpoint returns the planting/harvest calendar for
      ALL crops at that location; the requested crop is filtered from
      the response locally (the endpoint takes no crop parameter).
    - The API key is sent ONLY as an ``X-Api-Key`` request header
      (key alone is sufficient; no username/password).
    - The response is JSON: ``{"id", "location", "lat", "lon",
      "crops": [...]}``. Each crop entry carries ``crop``/``crop_name``,
      planting window (``planting_start_date`` like "6/1",
      ``planting_end_date`` like "7/31"), harvest window
      (``harvest_start_date``/``harvest_end_date``),
      ``season_length_days``, optional ``qualifier`` (e.g. "Winter") and
      a data ``source`` (e.g. "MWCACP"). Documentation also lists a
      simplified month-granular form (``sow_start``/``sow_end``/
      ``harvest_start``/``harvest_end``/``notes``); both shapes are
      normalized.
    - Errors are JSON ``{"error", "message", "status"}``: 401
      missing_api_key/invalid_api_key/api_key_expired, 403
      plan_not_supported, 404 not_found, 429 rate_limit_exceeded
      (with "retry_after") / monthly_quota_exceeded, 500
      internal_error, 503 service_unavailable. Rate-limit state is
      exposed via ``X-RateLimit-*`` response headers.
    - The provider publishes ONE annual window per crop (no kharif/
      rabi/zaid split, no growth-stage breakdown); the client derives
      ``crop_duration_days`` from ``season_length_days`` (fallback:
      window arithmetic) and models the growing period as a single
      aggregate stage. All derivations are disclosed in ``notes``.

    The client is inactive unless SPORA_API_KEY is set in the
    environment (the base URL defaults to the official endpoint). The
    key is never logged, never included in URLs, and never returned in
    API responses.
    """

    def __init__(
        self,
        base_url: Any = _UNSET,
        api_key: Any = _UNSET,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY_SECONDS,
    ):
        # Explicit constructor arguments win over configuration so tests
        # can inject a fake provider without touching the environment.
        # ``None`` means "deliberately absent" and disables the provider
        # (this keeps tests independent of the developer's real .env);
        # only an omitted argument falls back to configuration.
        self.base_url = (
            settings.SPORA_API_BASE_URL if base_url is _UNSET else base_url
        )
        self.api_key = (
            settings.SPORA_API_KEY if api_key is _UNSET else api_key
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @property
    def is_configured(self) -> bool:
        """
        Whether the external provider is configured.

        The base URL has an official documented default, so the API key
        is the configuration switch: external mode is active only when
        a key is present (and a base URL is set).
        """
        return bool(
            self.base_url and self.base_url.strip()
            and self.api_key and self.api_key.strip()
        )

    def _validate_configuration(self) -> None:
        """Fail fast on configuration problems (before any network call)."""
        if not self.base_url or not self.base_url.strip():
            raise CropCalendarServiceError(
                "External crop-calendar provider is not configured "
                "(SPORA_API_BASE_URL is not set)"
            )
        if not self.api_key or not self.api_key.strip():
            raise CropCalendarServiceError(
                "CROP_CALENDAR_API_KEY / SPORA_API_KEY is required to use the external "
                "crop-calendar provider"
            )

    @staticmethod
    def _location_slug(location: Optional[str]) -> str:
        """
        Normalize an optional user location into the provider's
        lowercase country-slug form (e.g. "India" -> "india",
        "West Bengal" -> "west bengal" - the provider may 404 on
        non-country slugs, which is surfaced as HTTP 404 upstream).
        Falls back to DEFAULT_EXTERNAL_LOCATION when no location is
        provided.
        """
        if location is None or not str(location).strip():
            return DEFAULT_EXTERNAL_LOCATION
        return urllib.parse.quote(str(location).strip().lower())

    def _build_request_url(
        self,
        crop: str,
        season: Optional[str],
        location: Optional[str],
    ) -> str:
        """
        Build the provider request URL (never includes the key).

        GET /harvest/{location} is a location-level endpoint that returns
        the calendar for ALL crops at that location; crop and season are
        filtered locally from the response (the endpoint takes no crop or
        season parameter).
        """
        slug = self._location_slug(location)
        url = f"{self.base_url.rstrip('/')}/harvest/{slug}"
        return url

    async def fetch_crop_calendar(
        self,
        crop: str,
        season: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch and normalize a crop calendar from the external provider.

        Raises:
            CropCalendarServiceError: On configuration problems, network
                failures, HTTP errors, invalid JSON, or unusable payloads
        """
        self._validate_configuration()
        request_url = self._build_request_url(crop, season, location)

        for attempt in range(self.max_retries):
            try:
                def make_request() -> str:
                    headers = {
                        "User-Agent": "AgriNexus-AI/1.0",
                        "Accept": "application/json",
                    }
                    if self.api_key:
                        # Header-based key (provider contract: "X-Api-Key"):
                        # never appears in URLs or logs
                        headers["X-Api-Key"] = self.api_key
                    request = urllib.request.Request(
                        request_url, headers=headers, method="GET"
                    )
                    with urllib.request.urlopen(
                        request, timeout=self.timeout
                    ) as response:
                        return response.read().decode("utf-8")

                response_text = await asyncio.to_thread(make_request)
                data = json.loads(response_text)
                return self._normalize_response(
                    data, crop, season, location
                )

            except CropNotFoundError:
                # Crop/location filter miss: a 404 contract, never a
                # retryable provider failure. Listed BEFORE the base
                # CropCalendarServiceError (its parent) so the 404
                # contract is never re-wrapped as a 502.
                raise
            except CropCalendarServiceError:
                # Already logged/handled; do not retry or re-wrap.
                raise
            except json.JSONDecodeError as e:
                logger.error(
                    "External crop-calendar API returned invalid JSON"
                )
                raise CropCalendarServiceError(
                    "External crop-calendar provider returned an invalid "
                    "response"
                ) from e
            except urllib.error.HTTPError as e:
                provider_error = self._read_provider_error(e)
                logger.error(
                    f"External crop-calendar API HTTP error: {e.code} "
                    f"(provider error: {provider_error or 'unknown'})"
                )
                if e.code == 401:
                    # Authentication failure: invalid/missing/expired key.
                    # Report the credential problem only - never the key.
                    raise CropCalendarServiceError(
                        "External crop-calendar provider rejected the "
                        "configured API key "
                        f"(HTTP 401; provider error: "
                        f"{provider_error or 'invalid_api_key'})"
                    ) from e
                if e.code == 403:
                    # Plan/quota failure: authenticated but not authorized.
                    raise CropCalendarServiceError(
                        "External crop-calendar provider denied the "
                        "request for the current plan/quota "
                        f"(HTTP 403; provider error: "
                        f"{provider_error or 'plan_not_supported'})"
                    ) from e
                if e.code == 404:
                    # Provider has no calendar for this location (or the
                    # slug is unknown); mapped to the module's 404
                    # contract. The crop may simply not be covered.
                    raise CropNotFoundError(
                        "No crop calendar returned by the external "
                        f"provider for location "
                        f"'{self._location_slug(location)}' "
                        f"(HTTP 404 not found; provider error: "
                        f"{provider_error or 'not_found'})"
                    ) from e
                if e.code == 429:
                    # Documented rate-limit response (X-RateLimit-Reset /
                    # Retry-After headers). Retrying immediately would
                    # only deepen the limit - surface it to the caller.
                    raise CropCalendarServiceError(
                        "External crop-calendar provider rate limit "
                        "exceeded (provider error: "
                        f"{provider_error or 'rate_limit_exceeded'})"
                    ) from e
                if attempt == self.max_retries - 1:
                    raise CropCalendarServiceError(
                        f"External crop-calendar provider returned HTTP "
                        f"{e.code}"
                    ) from e
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                logger.warning(
                    f"External crop-calendar API request failed "
                    f"(attempt {attempt + 1}/{self.max_retries}): "
                    f"{e.__class__.__name__}"
                )
                if attempt == self.max_retries - 1:
                    raise CropCalendarServiceError(
                        "External crop-calendar provider is currently "
                        "unreachable"
                    ) from e
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
            except Exception as e:
                logger.error(
                    f"Unexpected error contacting external crop-calendar "
                    f"provider: {e}"
                )
                if attempt == self.max_retries - 1:
                    raise CropCalendarServiceError(
                        "Unexpected error contacting the external "
                        "crop-calendar provider"
                    ) from e
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

        raise CropCalendarServiceError(
            "Failed to fetch crop calendar data after all retries"
        )

    def _normalize_response(
        self,
        data: Any,
        crop: str,
        season: Optional[str],
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Normalize a Spora ``/harvest/{location}`` payload or flat single-crop payload
        into the internal calendar format for the requested crop.
        """
        if not isinstance(data, dict):
            raise CropCalendarServiceError(
                "External crop-calendar provider returned an unexpected "
                "response structure"
            )

        crops_raw = data.get("crops")

        # Scenario 1: Spora location payload with 'crops' list
        if isinstance(crops_raw, list) and crops_raw:
            entry = self._find_provider_crop(crops_raw, crop)
            if entry is None:
                available = sorted({
                    str(c.get("crop_name") or c.get("crop")).strip().lower()
                    for c in crops_raw
                    if isinstance(c, dict)
                    and (c.get("crop_name") or c.get("crop"))
                })
                raise CropNotFoundError(
                    f"Crop '{crop}' is not available from the external "
                    f"provider for location "
                    f"'{self._location_slug(location)}'. Crops available "
                    f"from the provider at this location: "
                    f"{', '.join(available) if available else 'none listed'}"
                )

            planting_window = self._extract_window_mmdd(
                entry,
                start_keys=("planting_start_date", "sow_start"),
                end_keys=("planting_end_date", "sow_end"),
                start_doy_key="planting_start_doy",
                end_doy_key="planting_end_doy",
            )
            harvest_window = self._extract_window_mmdd(
                entry,
                start_keys=("harvest_start_date", "harvest_start"),
                end_keys=("harvest_end_date", "harvest_end"),
                start_doy_key="harvest_start_doy",
                end_doy_key="harvest_end_doy",
            )

            crop_duration, duration_mismatch_note = self._derive_duration_days(
                entry, planting_window, harvest_window
            )
            if crop_duration is None:
                raise CropCalendarServiceError(
                    "External crop-calendar provider response did not "
                    "contain a usable season length or planting/harvest "
                    "windows"
                )

            response_crop = str(
                entry.get("crop_name") or entry.get("crop") or crop
            ).strip().lower()

            provider_notes_raw = entry.get("notes")
            if isinstance(provider_notes_raw, str) and provider_notes_raw.strip():
                stage_activities: List[str] = [provider_notes_raw.strip()]
            elif isinstance(provider_notes_raw, list):
                stage_activities = [
                    str(n) for n in provider_notes_raw if str(n).strip()
                ]
            else:
                stage_activities = []

            growth_stages_raw = entry.get("growth_stages")
            if isinstance(growth_stages_raw, list) and growth_stages_raw:
                growth_stages = growth_stages_raw
            else:
                growth_stages = [{
                    "stage": "growing_period",
                    "duration_days": crop_duration,
                    "activities": stage_activities,
                }]

            if season is not None:
                resolved_season = self._normalize_season(season)
                season_source = "provided"
            else:
                resolved_season = "annual"
                season_source = "default"

            normalization_notes = self._build_normalization_notes(
                entry, crop_duration, planting_window,
                resolved_season if season is not None else None,
                duration_mismatch_note,
            )

            return {
                "crop": response_crop,
                "aliases": [],
                "season": resolved_season,
                "season_source": season_source,
                "seasons_available": ["annual"],
                "sowing_window": (
                    {"start": planting_window[0], "end": planting_window[1]}
                    if planting_window else None
                ),
                "crop_duration_days": crop_duration,
                "growth_stages": growth_stages,
                "notes": normalization_notes,
                "region_scope": "external_provider",
                "data_source": EXTERNAL_DATA_SOURCE,
                "is_reference_data": False,
                "reference_note": None,
                "data_timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Scenario 2: Flat direct crop response dictionary
        if "growth_stages" in data or "crop_duration_days" in data or "crop" in data:
            growth_stages_raw = data.get("growth_stages")
            if not isinstance(growth_stages_raw, list) or not growth_stages_raw:
                raise CropCalendarServiceError(
                    "External crop-calendar provider response missing valid growth stages"
                )

            crop_duration = data.get("crop_duration_days")
            if not isinstance(crop_duration, (int, float)) or crop_duration <= 0:
                raise CropCalendarServiceError(
                    "External crop-calendar provider response missing valid crop_duration_days"
                )
            crop_duration = int(crop_duration)

            validated_stages = []
            stage_duration_sum = 0
            for stage_entry in growth_stages_raw:
                if not isinstance(stage_entry, dict):
                    raise CropCalendarServiceError(
                        "External provider returned invalid growth stage format"
                    )
                dur = stage_entry.get("duration_days")
                if not isinstance(dur, (int, float)) or dur <= 0:
                    raise CropCalendarServiceError(
                        "External provider returned invalid growth stage duration"
                    )
                validated_stages.append(stage_entry)
                stage_duration_sum += int(dur)

            notes = list(data.get("notes", [])) if isinstance(data.get("notes"), list) else []
            if stage_duration_sum != crop_duration:
                notes.append(
                    f"Growth stage duration sum ({stage_duration_sum}) does not match crop duration ({crop_duration})"
                )

            res_season = season if season else data.get("season", "annual")
            try:
                res_season = self._normalize_season(res_season)
            except ValueError:
                res_season = "annual"

            return {
                "crop": str(data.get("crop", crop)).strip().lower(),
                "aliases": data.get("aliases", []),
                "season": res_season,
                "season_source": "provided" if season else "default",
                "seasons_available": data.get("seasons_available", [res_season]),
                "sowing_window": data.get("sowing_window"),
                "crop_duration_days": crop_duration,
                "growth_stages": validated_stages,
                "notes": notes,
                "region_scope": "external_provider",
                "data_source": EXTERNAL_DATA_SOURCE,
                "is_reference_data": False,
                "reference_note": None,
                "data_timestamp": datetime.now(timezone.utc).isoformat(),
            }

        raise CropCalendarServiceError(
            "External crop-calendar provider response did not contain a 'crops' list or valid crop data"
        )
    @staticmethod
    def _normalize_season(season: str) -> str:
        """Normalize a season name; raises ValueError on unknown names."""
        normalized = str(season).strip().lower()
        if not normalized:
            raise ValueError("Season must not be empty")
        if normalized not in SUPPORTED_SEASON_NAMES:
            raise ValueError(
                f"Unsupported season '{season}'. Supported seasons: "
                f"{', '.join(SUPPORTED_SEASON_NAMES)}"
            )
        return normalized

    @staticmethod
    def _read_provider_error(e: urllib.error.HTTPError) -> Optional[str]:
        """
        Extract the provider's machine-readable error code from an error
        response body (documented shape: {"error", "message", "status"}).
        Returns the error CODE only - never the key or the raw body.
        """
        try:
            payload = json.loads(e.read().decode("utf-8", errors="replace"))
            if isinstance(payload, dict):
                error = payload.get("error")
                if isinstance(error, str) and error.strip():
                    return error.strip()
        except Exception:
            pass
        return None

    @staticmethod
    def _find_provider_crop(
        crops: List[Any],
        crop: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Find the provider crop entry matching the requested crop name
        (case-insensitive on "crop_name"/"crop"; a "qualifier" such as
        "Winter" also matches a "winter <name>" request - e.g. the India
        calendar lists "Rapeseed" with qualifier "Winter").
        """
        target = str(crop).strip().lower()
        for entry in crops:
            if not isinstance(entry, dict):
                continue
            names = [
                str(entry.get(key)).strip().lower()
                for key in ("crop_name", "crop")
                if isinstance(entry.get(key), str)
                and str(entry.get(key)).strip()
            ]
            qualifier = entry.get("qualifier")
            qualifier_text = (
                qualifier.strip().lower()
                if isinstance(qualifier, str) and qualifier.strip()
                else None
            )
            for name in names:
                if name == target:
                    return entry
                if qualifier_text and (
                    f"{qualifier_text} {name}" == target
                ):
                    return entry
        return None

    @staticmethod
    def _extract_window_mmdd(
        entry: Dict[str, Any],
        start_keys: "tuple[str, ...]",
        end_keys: "tuple[str, ...]",
        start_doy_key: str,
        end_doy_key: str,
    ) -> "Optional[tuple[str, str]]":
        """
        Extract a (start, end) 'MM-DD' window from a provider crop
        entry: live "M/D" date fields first, then the documented
        month-name form, then the day-of-year fields.
        """
        for start_key, end_key in zip(start_keys, end_keys):
            start = _parse_provider_window_value(
                entry.get(start_key), is_end=False
            )
            end = _parse_provider_window_value(
                entry.get(end_key), is_end=True
            )
            if start and end:
                return start, end
        start = _doy_to_mmdd(entry.get(start_doy_key))
        end = _doy_to_mmdd(entry.get(end_doy_key))
        if start and end:
            return start, end
        return None

    @staticmethod
    def _derive_duration_days(
        entry: Dict[str, Any],
        planting_window: "Optional[tuple[str, str]]",
        harvest_window: "Optional[tuple[str, str]]",
    ) -> "tuple[Optional[int], Optional[str]]":
        """
        Derive the crop duration in days.

        Preference order (verified provider fields):
        1. ``season_length_days`` - the provider's own growing-season
           length metric (median planting to median harvest)
        2. inclusive day count from planting start to harvest end
           (calendar-year wrap aware, for winter crops such as India's
           winter rapeseed)

        Returns ``(duration_days, mismatch_note)`` where ``mismatch_note``
        describes a ``season_length_days``/window-span disagreement (or
        ``None`` when they agree / no comparison is possible).
        """
        season_length = entry.get("season_length_days")
        window_span: Optional[int] = None
        if planting_window and harvest_window:
            window_span = _days_between_mmdd(
                planting_window[0], harvest_window[1]
            )
        elif planting_window:
            window_span = _days_between_mmdd(
                planting_window[0], planting_window[1]
            )
        elif harvest_window:
            window_span = _days_between_mmdd(
                harvest_window[0], harvest_window[1]
            )
        if isinstance(season_length, (int, float)) and season_length >= 1:
            duration = int(round(season_length))
            mismatch_note = None
            if window_span and abs(duration - window_span) > 7:
                mismatch_note = (
                    "The provider's season_length_days "
                    f"({duration} days) does not match the "
                    "planting-to-harvest window span "
                    f"({window_span} days); season_length_days is used "
                    "for crop_duration_days."
                )
            return duration, mismatch_note
        if window_span:
            return window_span, None
        return None, None

    @staticmethod
    def _build_normalization_notes(
        entry: Dict[str, Any],
        crop_duration: int,
        planting_window: "Optional[tuple[str, str]]",
        requested_season: Optional[str],
        duration_mismatch_note: Optional[str] = None,
    ) -> List[str]:
        """Provenance/derivation notes disclosed in every response."""
        notes: List[str] = []
        qualifier = entry.get("qualifier")
        if isinstance(qualifier, str) and qualifier.strip():
            notes.append(f"Provider qualifier: {qualifier.strip()}")
        source = entry.get("source")
        if isinstance(source, str) and source.strip():
            notes.append(f"Provider data source: {source.strip()}")
        season_length = entry.get("season_length_days")
        if isinstance(season_length, (int, float)) and season_length >= 1:
            notes.append(
                "crop_duration_days uses the provider's "
                f"season_length_days ({int(season_length)} days, the "
                "provider's median planting-to-harvest season length)."
            )
        else:
            notes.append(
                "crop_duration_days derived from the provider "
                "planting/harvest windows (inclusive day count, "
                "calendar-year wrap aware)."
            )
        if duration_mismatch_note:
            notes.append(duration_mismatch_note)
        if planting_window:
            notes.append(
                "Sowing window derived from the provider planting "
                f"window ({planting_window[0]} to {planting_window[1]}); "
                "the provider may publish month-level granularity."
            )
        notes.append(
            "The external provider publishes a single annual "
            "planting/harvest window per crop; kharif/rabi/zaid season "
            "splits and growth-stage breakdowns are not available from "
            "this provider, so a single aggregate growing-period stage "
            "is reported."
        )
        if requested_season is not None:
            notes.append(
                f"Requested season '{requested_season}' is echoed for "
                "API compatibility; the returned window is the "
                "provider's general calendar for this crop and is NOT "
                "season-specific."
            )
        return notes

    async def check_connectivity(self) -> bool:
        """
        Perform a lightweight probe to verify the provider is reachable.

        Any HTTP response (including 4xx) counts as reachable; network
        failures count as not reachable. Returns False when not configured.
        """
        if not self.is_configured:
            return False
        # Probe the documented calendar endpoint for the default location:
        # it is the same path the module actually uses, so a successful
        # response proves both reachability and that the key is accepted.
        # No request parameters beyond the location slug are sent.
        request_url = (
            f"{self.base_url.rstrip('/')}/harvest/{DEFAULT_EXTERNAL_LOCATION}"
        )
        try:
            def make_request() -> str:
                headers = {
                    "User-Agent": "AgriNexus-AI/1.0",
                    "Accept": "application/json",
                }
                if self.api_key:
                    headers["X-Api-Key"] = self.api_key
                request = urllib.request.Request(
                    request_url, headers=headers, method="GET"
                )
                with urllib.request.urlopen(
                    request, timeout=self.timeout
                ) as response:
                    return response.read().decode("utf-8")

            await asyncio.to_thread(make_request)
            return True
        except urllib.error.HTTPError:
            # The server responded; connectivity itself is fine.
            return True
        except Exception as e:
            logger.warning(
                f"External crop-calendar connectivity check failed: "
                f"{e.__class__.__name__}"
            )
            return False


class CropCalendarService:
    """
    Crop calendar data service.

    Serves static/reference crop-calendar information from the active
    data source: the bundled reference dataset by default, or the
    external Spora /harvest provider when SPORA_API_KEY is set.
    Derived date/stage logic is NOT implemented here - it belongs to the
    intelligence layer.
    """

    def __init__(
        self,
        external_client: Optional[ExternalCropCalendarClient] = None,
        fallback_to_reference_data: Optional[bool] = None,
    ):
        self.external_client = (
            external_client
            if external_client is not None
            else ExternalCropCalendarClient()
        )
        self.fallback_to_reference_data = (
            fallback_to_reference_data
            if fallback_to_reference_data is not None
            else settings.CROP_CALENDAR_FALLBACK_TO_REFERENCE_DATA
        )
        logger.debug("Initialized CropCalendarService")

    # ------------------------------------------------------------------
    # Data source status
    # ------------------------------------------------------------------
    @property
    def is_external_provider_configured(self) -> bool:
        """Whether an external crop-calendar provider is configured."""
        return self.external_client.is_configured

    @property
    def is_external_api_key_configured(self) -> bool:
        """Whether an external provider API key is set (status only)."""
        return bool(
            self.external_client.api_key
            and self.external_client.api_key.strip()
        )

    async def check_external_connectivity(self) -> bool:
        """
        Probe the external provider once (used by GET /health).

        Returns False when no external provider is configured; otherwise
        the connectivity probe result. Never exposes credentials.
        """
        return await self.external_client.check_connectivity()

    def get_active_data_source(self) -> str:
        """Identifier of the currently active calendar data source."""
        if self.is_external_provider_configured:
            return EXTERNAL_DATA_SOURCE
        return REFERENCE_DATA_SOURCE

    # ------------------------------------------------------------------
    # Input normalization / validation
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_crop_name(crop: str) -> str:
        """Normalize a crop name; raises ValueError on invalid input."""
        if crop is None:
            raise ValueError("Crop name is required")
        name = str(crop).strip().lower()
        if not name:
            raise ValueError("Crop name must not be empty")
        if len(name) > MAX_CROP_NAME_LENGTH:
            raise ValueError(
                f"Crop name is too long (maximum {MAX_CROP_NAME_LENGTH} "
                f"characters)"
            )
        return name

    @staticmethod
    def _normalize_location(location: Optional[str]) -> Optional[str]:
        """Normalize an optional location string."""
        if location is None:
            return None
        normalized = str(location).strip()
        if not normalized:
            return None
        if len(normalized) > MAX_LOCATION_LENGTH:
            raise ValueError(
                f"Location is too long (maximum {MAX_LOCATION_LENGTH} "
                f"characters)"
            )
        return normalized

    @staticmethod
    def _normalize_season(season: str) -> str:
        """Normalize a season name; raises ValueError on unknown names."""
        if season is None:
            raise ValueError("Season is required")
        normalized = str(season).strip().lower()
        if not normalized:
            raise ValueError("Season must not be empty")
        if normalized not in SUPPORTED_SEASON_NAMES:
            raise ValueError(
                f"Unsupported season '{season}'. Supported seasons: "
                f"{', '.join(SUPPORTED_SEASON_NAMES)}"
            )
        return normalized

    def _resolve_crop_entry(
        self, crop: str
    ) -> "tuple[str, Dict[str, Any]]":
        """
        Resolve a crop name or alias to its reference dataset entry.

        Raises:
            ValueError: On empty/invalid crop input
            CropNotFoundError: When the crop is not in the dataset
        """
        name = self._normalize_crop_name(crop)
        dataset = get_reference_dataset()
        if name in dataset:
            return name, dataset[name]
        for canonical, entry in dataset.items():
            aliases = [
                str(alias).strip().lower()
                for alias in entry.get("aliases", [])
            ]
            if name in aliases:
                return canonical, entry
        raise CropNotFoundError(
            f"Unsupported crop '{crop}'. Supported crops: "
            f"{', '.join(sorted(dataset))}. Use GET /api/crop-calendar "
            f"to list supported crops."
        )

    # ------------------------------------------------------------------
    # Catalogue and season info
    # ------------------------------------------------------------------
    def get_supported_crops(self) -> Dict[str, Any]:
        """
        Catalogue of crops available from the active data source.

        The catalogue always reflects the bundled reference dataset; when
        an external provider is active, a note explains that the provider
        may support a different set of crops.
        """
        dataset = get_reference_dataset()
        crops = []
        for canonical, entry in dataset.items():
            crops.append({
                "crop": canonical,
                "aliases": list(entry.get("aliases", [])),
                "seasons": list(entry["seasons"].keys()),
                "crop_duration_days": {
                    season: cal["crop_duration_days"]
                    for season, cal in entry["seasons"].items()
                },
            })

        return {
            "crops": crops,
            "total": len(crops),
            "region_scope": REGION_SCOPE,
            "data_source": self.get_active_data_source(),
            "is_reference_data": not self.is_external_provider_configured,
            "external_provider_configured":
                self.is_external_provider_configured,
            "note": (
                "Catalogue reflects the bundled reference dataset; the "
                "configured external provider may support a different "
                "set of crops."
                if self.is_external_provider_configured
                else REFERENCE_NOTE
            ),
            "data_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_crop_season_info(self, crop: str) -> Dict[str, Any]:
        """
        Season/sowing-window information for a crop, used by the API layer
        for season inference and validation.

        Raises:
            ValueError: On empty/invalid crop input
            CropNotFoundError: When the crop is not in the reference dataset
        """
        if self.is_external_provider_configured:
            # With an external provider active, availability is validated
            # by the provider; local validation is skipped deliberately.
            return {
                "crop": self._normalize_crop_name(crop),
                "external_provider_active": True,
                "seasons_available": None,
                "sowing_windows": None,
                "region_scope": "external_provider",
            }

        canonical, entry = self._resolve_crop_entry(crop)
        return {
            "crop": canonical,
            "external_provider_active": False,
            "seasons_available": list(entry["seasons"].keys()),
            "sowing_windows": {
                season: cal.get("sowing_window")
                for season, cal in entry["seasons"].items()
            },
            "region_scope": REGION_SCOPE,
        }

    # ------------------------------------------------------------------
    # Static calendar retrieval
    # ------------------------------------------------------------------
    def _build_reference_calendar(
        self,
        crop: str,
        season: Optional[str],
        location: Optional[str],
        fallback_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the static calendar from the bundled reference dataset.

        ``fallback_reason`` is set only when this data is being served
        because the configured external provider failed. The response is
        then explicitly labelled (``fallback_used``/``fallback_reason``)
        so reference data is never presented as external provider data.
        """
        canonical, entry = self._resolve_crop_entry(crop)

        if season is not None:
            resolved_season = self._normalize_season(season)
            if resolved_season not in entry["seasons"]:
                raise ValueError(
                    f"Crop '{canonical}' does not have a "
                    f"'{resolved_season}' calendar. Available seasons: "
                    f"{', '.join(entry['seasons'].keys())}"
                )
            season_source = "provided"
        else:
            resolved_season = next(iter(entry["seasons"]))
            season_source = "default"

        calendar = entry["seasons"][resolved_season]

        notes = list(calendar.get("notes", []))
        if fallback_reason:
            notes.insert(
                0,
                "REFERENCE DATA FALLBACK: the configured external "
                f"crop-calendar provider could not be used ({fallback_reason}), "
                "so the bundled, non-authoritative reference calendar is "
                "served instead. This is NOT external provider data.",
            )

        return {
            "crop": canonical,
            "aliases": list(entry.get("aliases", [])),
            "location": self._normalize_location(location),
            "region_scope": REGION_SCOPE,
            "season": resolved_season,
            "season_source": season_source,
            "seasons_available": list(entry["seasons"].keys()),
            "sowing_window": calendar.get("sowing_window"),
            "crop_duration_days": calendar["crop_duration_days"],
            "growth_stages": [
                {
                    "stage": stage["stage"],
                    "duration_days": stage["duration_days"],
                    "activities": list(stage.get("activities", [])),
                }
                for stage in calendar["growth_stages"]
            ],
            "notes": notes,
            "data_source": REFERENCE_DATA_SOURCE,
            "is_reference_data": True,
            "reference_note": REFERENCE_NOTE,
            "fallback_used": fallback_reason is not None,
            "fallback_reason": fallback_reason,
            "data_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_crop_calendar(
        self,
        crop: str,
        season: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the static calendar for a crop and season from the active
        data source.

        When the external provider is configured it is always preferred.
        If it fails and ``CROP_CALENDAR_FALLBACK_TO_REFERENCE_DATA`` is
        enabled, the bundled reference calendar is served instead, with
        an explicit ``fallback_used``/``fallback_reason`` label and a
        leading note - fabricated external data is never returned.

        Raises:
            ValueError: On invalid crop/season/location input
            CropNotFoundError: When the crop is not available
            CropCalendarServiceError: When the external provider fails
                and no reference fallback is available/enabled
        """
        logger.info(
            f"Fetching crop calendar for crop={crop}, season={season}, "
            f"location={'provided' if location else 'not provided'}"
        )

        if self.is_external_provider_configured:
            normalized_crop = self._normalize_crop_name(crop)
            normalized_location = self._normalize_location(location)
            normalized_season = (
                self._normalize_season(season) if season is not None else None
            )
            try:
                calendar = await self.external_client.fetch_crop_calendar(
                    crop=normalized_crop,
                    season=normalized_season,
                    location=normalized_location,
                )
            except CropNotFoundError as e:
                # The requested crop is not available upstream. Serve the
                # labelled reference calendar when it covers this crop;
                # otherwise surface the provider's 404 unchanged.
                if not settings.CROP_CALENDAR_FALLBACK_TO_REFERENCE_DATA:
                    raise
                try:
                    return self._build_reference_calendar(
                        crop, season, location,
                        fallback_reason=self._safe_fallback_reason(e),
                    )
                except (CropNotFoundError, ValueError):
                    raise e from None
            except CropCalendarServiceError as e:
                # The provider could not be used (network/auth/rate-limit/
                # malformed payload). Serve labelled reference data when
                # enabled; otherwise propagate.
                reason = self._safe_fallback_reason(e)
                if not self.fallback_to_reference_data:
                    raise
                logger.warning(
                    "External crop-calendar provider unavailable "
                    f"({reason}); serving labelled reference data"
                )
                try:
                    return self._build_reference_calendar(
                        crop, season, location, fallback_reason=reason
                    )
                except (CropNotFoundError, ValueError):
                    # No reference entry to fall back to (or the caller's
                    # season/location is invalid for it): surface the
                    # original upstream failure unchanged.
                    raise e from None

            calendar["location"] = normalized_location
            calendar.setdefault("fallback_used", False)
            calendar.setdefault("fallback_reason", None)
            return calendar

        return self._build_reference_calendar(crop, season, location)

    @staticmethod
    def _safe_fallback_reason(e: CropCalendarServiceError) -> str:
        """
        Build a credential-safe, client-safe reason string.

        Only the error's machine-readable provider code (when present) is
        surfaced; the API key never appears in this text.
        """
        message = str(e).strip() or "provider error"
        provider_code = None
        marker = "(provider error:"
        if marker in message:
            provider_code = message.split(marker, 1)[1].strip(" )")
        if provider_code:
            return f"provider error: {provider_code}"
        return "provider unavailable"
