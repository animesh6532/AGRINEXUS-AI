"""
Test the crop calendar API endpoints with mocked/fake services, plus
smoke tests verifying that Weather and Market endpoints remain
registered.

The default data source is the bundled reference dataset, which makes no
network calls; external-provider behaviour is exercised with fake
services and mocked urllib only. No test in this file contacts a live
API or requires a real API key.
"""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.crop_calendar import (
    get_crop_calendar_intelligence_service,
    get_crop_calendar_service,
)
from app.main import app
from app.services.crop_calendar_service import (
    CropCalendarServiceError,
    CropNotFoundError,
    ExternalCropCalendarClient,
)

test_client = TestClient(app)

FAKE_API_KEY = "fake-key-should-never-appear-98765"


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    """Ensure dependency overrides never leak between tests."""
    yield
    app.dependency_overrides.clear()


def override_services(service=None, intelligence=None):
    """Register dependency overrides for the crop calendar endpoints."""
    if service is not None:
        app.dependency_overrides[get_crop_calendar_service] = (
            lambda: service
        )
    if intelligence is not None:
        app.dependency_overrides[
            get_crop_calendar_intelligence_service
        ] = (lambda: intelligence)


class FakeExternalClient:
    """Test double standing in for ExternalCropCalendarClient."""

    def __init__(self, configured=True, api_key=FAKE_API_KEY, connectivity=True):
        self._configured = configured
        self.api_key = api_key
        self._connectivity = connectivity

    @property
    def is_configured(self):
        return self._configured

    async def check_connectivity(self):
        return self._connectivity


DEFAULT_FAKE_CATALOG = {
    "crops": [
        {
            "crop": "rice",
            "aliases": ["paddy"],
            "seasons": ["kharif"],
            "crop_duration_days": {"kharif": 135},
        }
    ],
    "total": 1,
    "region_scope": "india_generic",
    "data_source": "reference_dataset",
    "is_reference_data": True,
    "external_provider_configured": False,
    "note": None,
    "data_timestamp": "2026-01-01T00:00:00+00:00",
}


class FakeCropCalendarService:
    """Test double standing in for CropCalendarService."""

    def __init__(
        self,
        calendar=None,
        catalog=None,
        season_info=None,
        error=None,
        not_found=None,
        external_client=None,
    ):
        self.calendar = calendar
        self.catalog = (
            catalog if catalog is not None else DEFAULT_FAKE_CATALOG
        )
        self.season_info = season_info
        self.error = error
        self.not_found = not_found
        self.external_client = external_client or FakeExternalClient(
            configured=False, api_key=None
        )

    @property
    def is_external_provider_configured(self):
        return self.external_client.is_configured

    @property
    def is_external_api_key_configured(self):
        return bool(
            self.external_client.api_key
            and self.external_client.api_key.strip()
        )

    def get_active_data_source(self):
        return (
            "external_crop_calendar_api"
            if self.is_external_provider_configured
            else "reference_dataset"
        )

    async def get_crop_calendar(self, crop, season=None, location=None):
        if self.not_found is not None:
            raise self.not_found
        if self.error is not None:
            raise self.error
        return self.calendar

    def get_supported_crops(self):
        if self.error is not None:
            raise self.error
        return self.catalog

    def get_crop_season_info(self, crop):
        if self.not_found is not None:
            raise self.not_found
        return self.season_info


class TestCropCatalogEndpoint:
    """Test GET /api/crop-calendar (catalogue)."""

    def test_catalog_returns_supported_crops(self):
        response = test_client.get("/api/crop-calendar")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert [c["crop"] for c in data["crops"]] == [
            "rice", "wheat", "maize", "cotton",
        ]
        assert data["is_reference_data"] is True
        assert data["external_provider_configured"] is False
        assert data["region_scope"] == "india_generic"
        rice = data["crops"][0]
        assert rice["aliases"] == ["paddy", "dhan"]
        assert rice["seasons"] == ["kharif", "rabi"]
        assert rice["crop_duration_days"]["kharif"] == 135

    def test_catalog_lists_no_secrets(self):
        response = test_client.get("/api/crop-calendar")
        assert FAKE_API_KEY not in response.text


class TestCropCalendarHealthEndpoint:
    """Test GET /api/crop-calendar/health."""

    def test_health_reference_mode(self):
        response = test_client.get("/api/crop-calendar/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "agrinexus-crop-calendar"
        assert data["version"] == "1.0.0"
        assert data["data_source_active"] == "reference_dataset"
        assert data["external_provider_configured"] is False
        assert data["external_api_key_configured"] is False
        assert data["reference_dataset_available"] is True
        assert data["supported_crops_count"] == 4
        assert data["external_connectivity"] is None
        assert "timestamp" in data

    def test_health_does_not_expose_secrets(self):
        response = test_client.get("/api/crop-calendar/health")
        assert FAKE_API_KEY not in response.text
        assert "CROP_CALENDAR_API_KEY=" not in response.text

    def test_health_external_mode_configured_and_reachable(self):
        fake = FakeCropCalendarService(
            external_client=FakeExternalClient(
                configured=True, api_key=FAKE_API_KEY, connectivity=True
            )
        )
        override_services(service=fake)
        response = test_client.get("/api/crop-calendar/health")
        assert response.status_code == 200
        data = response.json()
        assert data["external_provider_configured"] is True
        assert data["external_api_key_configured"] is True
        assert data["external_connectivity"] is True
        assert data["data_source_active"] == "external_crop_calendar_api"
        # The key value itself must never appear.
        assert FAKE_API_KEY not in response.text

    def test_health_external_mode_unreachable_is_degraded(self):
        fake = FakeCropCalendarService(
            external_client=FakeExternalClient(
                configured=True, api_key=FAKE_API_KEY, connectivity=False
            )
        )
        override_services(service=fake)
        response = test_client.get("/api/crop-calendar/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["external_connectivity"] is False


class TestStaticCropCalendarEndpoint:
    """Test GET /api/crop-calendar/{crop} (static calendar)."""

    def test_static_calendar_valid_request(self):
        response = test_client.get(
            "/api/crop-calendar/rice",
            params={"season": "kharif", "location": "West Bengal"},
        )
        assert response.status_code == 200
        data = response.json()
        # Response contract
        assert data["crop"] == "rice"
        assert data["season"] == "kharif"
        assert data["season_source"] == "provided"
        assert data["location"] == "West Bengal"
        assert data["region_scope"] == "india_generic"
        assert data["crop_duration_days"] == 135
        assert data["sowing_window"] == {"start": "06-01", "end": "07-15"}
        assert data["is_reference_data"] is True
        assert "reference_note" in data
        assert "data_timestamp" in data
        assert len(data["growth_stages"]) == 6
        stage = data["growth_stages"][0]
        assert set(stage) == {"stage", "duration_days", "activities"}
        # No computed dates on the static endpoint
        assert "start_date" not in stage
        assert "current_stage" not in data

    def test_static_calendar_default_season(self):
        response = test_client.get("/api/crop-calendar/wheat")
        assert response.status_code == 200
        data = response.json()
        assert data["season"] == "rabi"
        assert data["season_source"] == "default"
        assert data["seasons_available"] == ["rabi"]

    def test_static_calendar_alias_resolution(self):
        response = test_client.get("/api/crop-calendar/PADDY")
        assert response.status_code == 200
        assert response.json()["crop"] == "rice"

    def test_static_calendar_unknown_crop(self):
        response = test_client.get("/api/crop-calendar/tomato")
        assert response.status_code == 404
        assert "Unsupported crop" in response.json()["detail"]

    def test_static_calendar_unsupported_season(self):
        response = test_client.get(
            "/api/crop-calendar/wheat", params={"season": "kharif"}
        )
        assert response.status_code == 400
        assert "does not have a 'kharif' calendar" in response.json()["detail"]

    def test_static_calendar_invalid_season_name(self):
        response = test_client.get(
            "/api/crop-calendar/rice", params={"season": "not-a-season"}
        )
        assert response.status_code == 400

    def test_static_calendar_location_too_long(self):
        # FastAPI query validation rejects over-long locations (422),
        # consistent with the module's error-handling contract.
        response = test_client.get(
            "/api/crop-calendar/rice", params={"location": "x" * 150}
        )
        assert response.status_code == 422

    def test_static_calendar_upstream_failure(self):
        fake = FakeCropCalendarService(
            error=CropCalendarServiceError("provider down")
        )
        override_services(service=fake)
        response = test_client.get("/api/crop-calendar/rice")
        assert response.status_code == 502
        assert "provider" in response.json()["detail"].lower()

    def test_static_calendar_unexpected_error(self):
        fake = FakeCropCalendarService(error=RuntimeError("boom"))
        override_services(service=fake)
        response = test_client.get("/api/crop-calendar/rice")
        assert response.status_code == 500
        # No stack traces in the response
        assert "boom" not in response.json()["detail"]
        assert "Traceback" not in response.text


class TestCropScheduleEndpoint:
    """Test GET /api/crop-calendar/{crop}/schedule."""

    def test_schedule_valid_request(self):
        response = test_client.get(
            "/api/crop-calendar/rice/schedule",
            params={
                "sowing_date": "2026-06-15",
                "as_of_date": "2026-07-01",
                "location": "West Bengal",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "rice"
        assert data["sowing_date"] == "2026-06-15"
        assert data["as_of_date"] == "2026-07-01"
        # Season inferred from the reference sowing window
        assert data["season"] == "kharif"
        assert data["season_source"] == "inferred_from_sowing_window"
        assert data["sowing_window_compliant"] is True
        # Stage schedule arithmetic
        first = data["scheduled_growth_stages"][0]
        assert first["start_date"] == "2026-06-15"
        assert first["end_date"] == "2026-07-09"
        assert first["is_current"] is True
        assert data["current_stage"] == "nursery_sowing"
        assert data["current_stage_progress_percent"] == 68.0
        assert data["next_stage"] == "transplanting"
        # Exactly one stage flagged as current
        current_flags = [
            s["is_current"] for s in data["scheduled_growth_stages"]
        ]
        assert current_flags.count(True) == 1
        # Harvest window is maturity +/- 10 days
        assert data["harvest_window"]["start_date"] == "2026-10-17"
        assert data["harvest_window"]["end_date"] == "2026-11-06"
        assert data["days_to_harvest_estimate"] == 128
        assert len(data["upcoming_activities"]) >= 1
        assert data["is_reference_data"] is True
        assert data["warnings"] == []

    def test_schedule_explicit_season(self):
        response = test_client.get(
            "/api/crop-calendar/rice/schedule",
            params={"sowing_date": "2026-06-15", "season": "KHARIF"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["season"] == "kharif"
        assert data["season_source"] == "provided"

    def test_schedule_season_inferred_from_month(self):
        # Wheat only supports rabi; 2026-03-20 falls in no sowing window
        # (wheat window is 11-01..12-15) but the month maps to rabi.
        response = test_client.get(
            "/api/crop-calendar/wheat/schedule",
            params={"sowing_date": "2026-03-20", "as_of_date": "2026-04-01"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["season"] == "rabi"
        assert data["season_source"] == "inferred_from_sowing_month"
        assert data["sowing_window_compliant"] is False
        assert any("outside" in w for w in data["warnings"])

    def test_schedule_sowing_window_match_for_wrapped_window(self):
        # Rabi rice window wraps the year: 11-15..01-15
        response = test_client.get(
            "/api/crop-calendar/rice/schedule",
            params={"sowing_date": "2026-12-01", "as_of_date": "2026-12-10"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["season"] == "rabi"
        assert data["season_source"] == "inferred_from_sowing_window"
        assert data["sowing_window_compliant"] is True

    def test_schedule_missing_sowing_date(self):
        response = test_client.get("/api/crop-calendar/rice/schedule")
        assert response.status_code == 422

    def test_schedule_malformed_date(self):
        response = test_client.get(
            "/api/crop-calendar/rice/schedule",
            params={"sowing_date": "15-06-2026"},
        )
        assert response.status_code == 422

    def test_schedule_invalid_date_value(self):
        response = test_client.get(
            "/api/crop-calendar/rice/schedule",
            params={"sowing_date": "2026-13-45"},
        )
        assert response.status_code == 422

    def test_schedule_unknown_crop(self):
        response = test_client.get(
            "/api/crop-calendar/tomato/schedule",
            params={"sowing_date": "2026-06-15"},
        )
        assert response.status_code == 404

    def test_schedule_unsupported_season_for_crop(self):
        response = test_client.get(
            "/api/crop-calendar/wheat/schedule",
            params={"sowing_date": "2026-06-15", "season": "kharif"},
        )
        assert response.status_code == 400
        assert "kharif" in response.json()["detail"]

    def test_schedule_season_unsupported_for_inferred_month(self):
        # June sowing infers kharif; wheat has no kharif calendar.
        response = test_client.get(
            "/api/crop-calendar/wheat/schedule",
            params={"sowing_date": "2026-06-15"},
        )
        assert response.status_code == 400
        assert "kharif" in response.json()["detail"]

    def test_schedule_upstream_failure(self):
        fake = FakeCropCalendarService(
            error=CropCalendarServiceError("provider down"),
            season_info={
                "crop": "rice",
                "external_provider_active": False,
                "seasons_available": ["kharif"],
                "sowing_windows": {
                    "kharif": {"start": "06-01", "end": "07-15"}
                },
                "region_scope": "india_generic",
            },
        )
        override_services(service=fake)
        response = test_client.get(
            "/api/crop-calendar/rice/schedule",
            params={"sowing_date": "2026-06-15"},
        )
        assert response.status_code == 502

    def test_schedule_upstream_unknown_crop(self):
        fake = FakeCropCalendarService(
            not_found=CropNotFoundError("Unsupported crop 'tomato'"),
        )
        override_services(service=fake)
        response = test_client.get(
            "/api/crop-calendar/tomato/schedule",
            params={"sowing_date": "2026-06-15"},
        )
        assert response.status_code == 404

    def test_schedule_no_secrets_in_response(self):
        response = test_client.get(
            "/api/crop-calendar/rice/schedule",
            params={"sowing_date": "2026-06-15"},
        )
        assert FAKE_API_KEY not in response.text


class TestExternalProviderIntegration:
    """End-to-end API tests for the configured-external-provider path."""

    def test_external_success_via_mocked_urllib(self):
        payload = {
            "crop": "rice",
            "season": "kharif",
            "crop_duration_days": 120,
            "sowing_window": {"start": "06-01", "end": "07-15"},
            "growth_stages": [
                {"stage": "stage_a", "duration_days": 120},
            ],
            "seasons_available": ["kharif"],
        }
        service = CropCalendarServiceIntegrationStub(payload)
        override_services(service=service)
        response = test_client.get(
            "/api/crop-calendar/rice/schedule",
            params={"sowing_date": "2026-06-20", "as_of_date": "2026-07-01"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data_source"] in ("spora_harvest_api", "external_crop_calendar_api")
        assert data["is_reference_data"] is False
        assert data["crop_duration_days"] == 120
        # Stage dates derived from the external stage durations
        assert data["scheduled_growth_stages"][0]["start_date"] == "2026-06-20"
        assert data["scheduled_growth_stages"][0]["end_date"] == "2026-10-17"
        assert data["harvest_window"]["start_date"] == "2026-10-07"

    def test_external_failure_maps_to_502(self):
        # Simulates a configured external provider whose calendar fetch
        # fails: the API must map CropCalendarServiceError to 502.
        fake = FakeCropCalendarService(
            error=CropCalendarServiceError("provider unreachable"),
            season_info={
                "crop": "rice",
                "external_provider_active": True,
                "seasons_available": None,
                "sowing_windows": None,
                "region_scope": "external_provider",
            },
        )
        override_services(service=fake)
        response = test_client.get(
            "/api/crop-calendar/rice/schedule",
            params={"sowing_date": "2026-06-15"},
        )
        assert response.status_code == 502


class CropCalendarServiceIntegrationStub(FakeCropCalendarService):
    """
    Fake service that delegates calendar fetching to the real external
    client machinery (with a mocked urlopen).
    """

    def __init__(self, payload):
        super().__init__()
        self.payload = payload
        self.external_client = FakeExternalClient(
            configured=True, api_key=FAKE_API_KEY
        )
        self.season_info = {
            "crop": "rice",
            "external_provider_active": True,
            "seasons_available": None,
            "sowing_windows": None,
            "region_scope": "external_provider",
        }

    async def get_crop_calendar(self, crop, season=None, location=None):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value.decode.return_value = json.dumps(
                self.payload
            )
            mock_urlopen.return_value.__enter__.return_value = mock_response
            client = ExternalCropCalendarClient(
                base_url="https://provider.example.test/crop-calendar",
                api_key=FAKE_API_KEY,
                retry_delay=0.0,
            )
            calendar = await client.fetch_crop_calendar(crop, season)
            calendar["location"] = location
            return calendar


class TestRouterRegistration:
    """Tests verifying crop calendar, weather and market routes exist."""

    def test_crop_calendar_routes_registered(self):
        crop_routes = [
            route.path for route in app.routes
            if route.path.startswith("/api/crop-calendar")
        ]
        assert "/api/crop-calendar" in crop_routes
        assert "/api/crop-calendar/health" in crop_routes
        assert "/api/crop-calendar/{crop}" in crop_routes
        assert "/api/crop-calendar/{crop}/schedule" in crop_routes

    def test_health_route_precedes_crop_route(self):
        """Static routes must be matched before the {crop} path param."""
        crop_routes = [
            route.path for route in app.routes
            if route.path.startswith("/api/crop-calendar")
        ]
        assert crop_routes.index(
            "/api/crop-calendar/health"
        ) < crop_routes.index("/api/crop-calendar/{crop}")

    def test_weather_routes_still_registered(self):
        weather_routes = [
            route.path for route in app.routes
            if route.path.startswith("/api/weather")
        ]
        assert "/api/weather/current" in weather_routes
        assert "/api/weather/health" in weather_routes

    def test_market_routes_still_registered(self):
        market_routes = [
            route.path for route in app.routes
            if route.path.startswith("/api/market")
        ]
        assert "/api/market/health" in market_routes
        assert "/api/market/current" in market_routes

    def test_openapi_contains_crop_calendar_endpoints(self):
        openapi = test_client.get("/openapi.json").json()
        paths = openapi["paths"]
        assert "/api/crop-calendar" in paths
        assert "/api/crop-calendar/health" in paths
        assert "/api/crop-calendar/{crop}" in paths
        assert "/api/crop-calendar/{crop}/schedule" in paths


class TestWeatherAndMarketStillWork:
    """Smoke tests confirming Weather/Market functionality is intact."""

    def test_root_endpoint(self):
        response = test_client.get("/")
        assert response.status_code == 200
        assert "AgriNexus-AI" in response.json()["message"]

    def test_app_health_endpoint(self):
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_weather_health_endpoint(self):
        from app.api.weather import get_weather_service

        class FakeWeatherService:
            async def check_api_connectivity(self):
                return True

        app.dependency_overrides[get_weather_service] = (
            lambda: FakeWeatherService()
        )
        response = test_client.get("/api/weather/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_market_health_endpoint(self):
        response = test_client.get("/api/market/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_market_current_still_works(self):
        response = test_client.get(
            "/api/market/current",
            params={"commodity": "NonExistentCommodity"},
        )
        # 404 (no data) proves the endpoint and DB path are operational
        assert response.status_code == 404
        assert "detail" in response.json()
