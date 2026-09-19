"""
Test the crop calendar service with mocked external API calls.

The ExternalCropCalendarClient uses urllib (not httpx) for external
provider requests, so these tests mock urllib.request.urlopen, following
the same convention as the weather and market service tests. No test in
this file contacts a live API or requires a real API key.
"""

import asyncio
import json
import logging
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from app.services.crop_calendar_service import (
    EXTERNAL_DATA_SOURCE,
    CropCalendarService,
    CropCalendarServiceError,
    CropNotFoundError,
    ExternalCropCalendarClient,
)
from app.services.crop_calendar_reference_data import (
    REFERENCE_DATA_SOURCE,
    get_reference_dataset,
)


def _payload_response(payload) -> MagicMock:
    """Build a mock for urlopen() used as a context manager."""
    mock_response = MagicMock()
    mock_response.read.return_value.decode.return_value = json.dumps(payload)
    return mock_response


TEST_API_KEY = "test-crop-calendar-key-12345"
TEST_BASE_URL = "https://provider.example.test"

# Mirrors the verified Spora "GET /harvest/{location}" response shape: one
# location object containing a "crops" list, each entry carrying planting/
# harvest day-of-year + "M/D" date fields and the provider's own
# season_length_days metric. Values are illustrative only.
EXTERNAL_PAYLOAD = {
    "id": "india",
    "location": "India",
    "crops": [
        {
            "id": 1,
            "location_id": "india",
            "crop": "Rice",
            "qualifier": None,
            "crop_name": "Rice",
            "planting_start_doy": 152,
            "planting_end_doy": 212,
            "planting_start_date": "6/1",
            "planting_end_date": "7/31",
            "harvest_start_doy": 255,
            "harvest_end_doy": 362,
            "harvest_start_date": "9/12",
            "harvest_end_date": "12/28",
            "season_length_days": 135,
            "growth_stages": [
                {"stage": "nursery", "duration_days": 25},
                {"stage": "growing", "duration_days": 110},
            ],
            "source": "MWCACP",
            "notes": "provider note",
        },
        {
            "id": 2,
            "location_id": "india",
            "crop": "Rapeseed",
            "qualifier": "Winter",
            "crop_name": "Rapeseed",
            "planting_start_date": "10/1",
            "planting_end_date": "12/26",
            "harvest_start_date": "3/16",
            "harvest_end_date": "5/21",
            "season_length_days": 156,
            "source": "MWCACP",
        },
    ],
}


@pytest.fixture
def api_client():
    """Create an external client with no retry sleeping for fast tests."""
    return ExternalCropCalendarClient(
        base_url=TEST_BASE_URL,
        api_key=TEST_API_KEY,
        retry_delay=0.0,
    )


class TestReferenceData:
    """Test the bundled reference dataset integrity."""

    def test_dataset_crops(self):
        dataset = get_reference_dataset()
        assert set(dataset) == {"rice", "wheat", "maize", "cotton"}

    def test_stage_durations_sum_to_crop_duration(self):
        for entry in get_reference_dataset().values():
            for season, calendar in entry["seasons"].items():
                stage_sum = sum(
                    stage["duration_days"]
                    for stage in calendar["growth_stages"]
                )
                assert stage_sum == calendar["crop_duration_days"], (
                    f"{entry} {season}: stage durations do not sum to the "
                    f"crop duration"
                )


class TestCropCalendarServiceReference:
    """Test reference-mode service behaviour."""

    @pytest.fixture
    def service(self):
        # The external provider is explicitly disabled so these tests are
        # deterministic and never depend on (or contact) the real provider
        # using a developer's local SPORA_API_KEY.
        return CropCalendarService(
            external_client=ExternalCropCalendarClient(
                base_url=None, api_key=None
            )
        )

    def test_reference_mode_by_default(self, service):
        assert service.is_external_provider_configured is False
        assert service.get_active_data_source() == REFERENCE_DATA_SOURCE

    def test_get_supported_crops(self, service):
        catalog = service.get_supported_crops()
        assert catalog["total"] == 4
        names = [c["crop"] for c in catalog["crops"]]
        assert names == ["rice", "wheat", "maize", "cotton"]
        assert catalog["is_reference_data"] is True
        assert catalog["external_provider_configured"] is False

    def test_get_crop_calendar_default_season(self, service):
        result = asyncio.run(service.get_crop_calendar("rice"))
        assert result["crop"] == "rice"
        assert result["season"] == "kharif"
        assert result["season_source"] == "default"
        assert result["crop_duration_days"] == 135
        assert result["is_reference_data"] is True
        assert result["reference_note"]
        assert len(result["growth_stages"]) == 6

    def test_get_crop_calendar_alias_and_case(self, service):
        result = asyncio.run(service.get_crop_calendar(" PADDY "))
        assert result["crop"] == "rice"

    def test_get_crop_calendar_explicit_season(self, service):
        result = asyncio.run(
            service.get_crop_calendar("rice", season=" KHARIF ")
        )
        assert result["season"] == "kharif"
        assert result["season_source"] == "provided"

    def test_get_crop_calendar_location_echo(self, service):
        result = asyncio.run(
            service.get_crop_calendar("rice", location=" West Bengal ")
        )
        assert result["location"] == "West Bengal"

    def test_get_crop_calendar_unknown_crop(self, service):
        with pytest.raises(CropNotFoundError, match="tomato"):
            asyncio.run(service.get_crop_calendar("tomato"))

    def test_get_crop_calendar_unsupported_season_for_crop(self, service):
        with pytest.raises(ValueError, match="wheat"):
            asyncio.run(
                service.get_crop_calendar("wheat", season="kharif")
            )

    def test_get_crop_calendar_invalid_season_name(self, service):
        with pytest.raises(ValueError, match="Unsupported season"):
            asyncio.run(
                service.get_crop_calendar("rice", season="monsoon")
            )

    def test_get_crop_calendar_empty_crop(self, service):
        with pytest.raises(ValueError, match="required|empty"):
            asyncio.run(service.get_crop_calendar("   "))

    def test_get_crop_calendar_too_long_crop(self, service):
        with pytest.raises(ValueError, match="too long"):
            asyncio.run(service.get_crop_calendar("x" * 60))

    def test_get_crop_season_info_reference(self, service):
        info = service.get_crop_season_info("cotton")
        assert info["crop"] == "cotton"
        assert info["external_provider_active"] is False
        assert info["seasons_available"] == ["kharif"]
        assert info["sowing_windows"]["kharif"] == {
            "start": "05-15",
            "end": "06-30",
        }


class TestExternalCropCalendarClient:
    """Test the external provider client (mocked urllib)."""

    def test_not_configured_by_default(self):
        client = ExternalCropCalendarClient(base_url=None, api_key=None)
        assert client.is_configured is False

    def test_fetch_without_base_url_raises(self):
        client = ExternalCropCalendarClient(base_url=None, api_key="k")
        with pytest.raises(
            CropCalendarServiceError, match="not configured"
        ):
            asyncio.run(client.fetch_crop_calendar("rice"))

    def test_fetch_without_api_key_raises_before_network_call(self):
        client = ExternalCropCalendarClient(
            base_url=TEST_BASE_URL, api_key=None
        )
        with patch("urllib.request.urlopen") as mock_urlopen:
            with pytest.raises(
                CropCalendarServiceError, match="CROP_CALENDAR_API_KEY"
            ):
                asyncio.run(client.fetch_crop_calendar("rice"))
        mock_urlopen.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_fetch_success_and_normalization(self, mock_urlopen, api_client):
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            EXTERNAL_PAYLOAD
        )

        result = asyncio.run(api_client.fetch_crop_calendar("rice", "kharif"))

        assert result["crop"] == "rice"
        assert result["season"] == "kharif"
        assert result["data_source"] == EXTERNAL_DATA_SOURCE
        assert result["is_reference_data"] is False
        assert result["region_scope"] == "external_provider"
        assert result["crop_duration_days"] == 135
        assert result["sowing_window"] == {"start": "06-01", "end": "07-31"}
        assert len(result["growth_stages"]) == 2
        assert result["growth_stages"][0]["duration_days"] == 25

    @patch("urllib.request.urlopen")
    def test_request_url_excludes_api_key(self, mock_urlopen, api_client):
        """The API key must never appear in the request URL."""
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            EXTERNAL_PAYLOAD
        )

        asyncio.run(api_client.fetch_crop_calendar("rice", "kharif"))

        request = mock_urlopen.call_args[0][0]
        assert TEST_API_KEY not in request.full_url
        assert "crop=rice" in request.full_url
        assert request.get_header("X-api-key") == TEST_API_KEY

    @patch("urllib.request.urlopen")
    def test_fetch_network_failure(self, mock_urlopen, api_client):
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")

        with pytest.raises(CropCalendarServiceError, match="unreachable"):
            asyncio.run(api_client.fetch_crop_calendar("rice"))

    @patch("urllib.request.urlopen")
    def test_fetch_timeout(self, mock_urlopen, api_client):
        mock_urlopen.side_effect = TimeoutError("timed out")

        with pytest.raises(CropCalendarServiceError, match="unreachable"):
            asyncio.run(api_client.fetch_crop_calendar("rice"))

    @patch("urllib.request.urlopen")
    def test_fetch_auth_failure_no_retry(self, mock_urlopen, api_client):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            TEST_BASE_URL, 401, "Unauthorized", {}, None
        )

        with pytest.raises(CropCalendarServiceError, match="credentials"):
            asyncio.run(api_client.fetch_crop_calendar("rice"))
        assert mock_urlopen.call_count == 1

    @patch("urllib.request.urlopen")
    def test_fetch_rate_limit_no_retry(self, mock_urlopen, api_client):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            TEST_BASE_URL, 429, "Too Many Requests", {}, None
        )

        with pytest.raises(CropCalendarServiceError, match="rate limit"):
            asyncio.run(api_client.fetch_crop_calendar("rice"))

    @patch("urllib.request.urlopen")
    def test_fetch_server_error_retries_then_fails(
        self, mock_urlopen, api_client
    ):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            TEST_BASE_URL, 500, "Server Error", {}, None
        )

        with pytest.raises(CropCalendarServiceError, match="HTTP 500"):
            asyncio.run(api_client.fetch_crop_calendar("rice"))
        assert mock_urlopen.call_count == api_client.max_retries

    @patch("urllib.request.urlopen")
    def test_fetch_invalid_json(self, mock_urlopen, api_client):
        mock_response = MagicMock()
        mock_response.read.return_value.decode.return_value = "not-json{"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with pytest.raises(
            CropCalendarServiceError, match="invalid response"
        ):
            asyncio.run(api_client.fetch_crop_calendar("rice"))

    @patch("urllib.request.urlopen")
    def test_fetch_missing_growth_stages(self, mock_urlopen, api_client):
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            {"crop": "rice", "crop_duration_days": 135}
        )

        with pytest.raises(CropCalendarServiceError, match="growth stages"):
            asyncio.run(api_client.fetch_crop_calendar("rice"))

    @patch("urllib.request.urlopen")
    def test_fetch_invalid_stage_entry(self, mock_urlopen, api_client):
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            {
                "crop": "rice",
                "crop_duration_days": 135,
                "growth_stages": [{"stage": "x", "duration_days": -1}],
            }
        )

        with pytest.raises(
            CropCalendarServiceError, match="invalid growth stage"
        ):
            asyncio.run(api_client.fetch_crop_calendar("rice"))

    @patch("urllib.request.urlopen")
    def test_fetch_missing_duration(self, mock_urlopen, api_client):
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            {
                "crop": "rice",
                "growth_stages": [{"stage": "x", "duration_days": 10}],
            }
        )

        with pytest.raises(
            CropCalendarServiceError, match="crop_duration_days"
        ):
            asyncio.run(api_client.fetch_crop_calendar("rice"))

    @patch("urllib.request.urlopen")
    def test_duration_mismatch_adds_note(self, mock_urlopen, api_client):
        payload = {
            "crop": "rice",
            "crop_duration_days": 100,
            "growth_stages": [
                {"stage": "a", "duration_days": 60},
                {"stage": "b", "duration_days": 60},
            ],
        }
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            payload
        )

        result = asyncio.run(api_client.fetch_crop_calendar("rice"))
        assert any("does not match" in n for n in result["notes"])

    @patch("urllib.request.urlopen")
    def test_api_key_never_logged(self, mock_urlopen, api_client, caplog):
        """The API key must not appear in any log record."""
        caplog.set_level(logging.DEBUG)
        mock_urlopen.side_effect = urllib.error.URLError("boom")

        with pytest.raises(CropCalendarServiceError):
            asyncio.run(api_client.fetch_crop_calendar("rice"))

        assert TEST_API_KEY not in caplog.text

    @patch("urllib.request.urlopen")
    def test_check_connectivity_success(self, mock_urlopen, api_client):
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            {}
        )
        assert asyncio.run(api_client.check_connectivity()) is True

    @patch("urllib.request.urlopen")
    def test_check_connectivity_http_error_is_reachable(
        self, mock_urlopen, api_client
    ):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            TEST_BASE_URL, 404, "Not Found", {}, None
        )
        assert asyncio.run(api_client.check_connectivity()) is True

    @patch("urllib.request.urlopen")
    def test_check_connectivity_network_failure(
        self, mock_urlopen, api_client
    ):
        mock_urlopen.side_effect = urllib.error.URLError("no route")
        assert asyncio.run(api_client.check_connectivity()) is False

    def test_check_connectivity_not_configured(self):
        client = ExternalCropCalendarClient(base_url=None)
        assert asyncio.run(client.check_connectivity()) is False


class TestCropCalendarServiceExternal:
    """Test service dispatch to the external provider."""

    @pytest.fixture
    def external_service(self):
        return CropCalendarService(
            external_client=ExternalCropCalendarClient(
                base_url=TEST_BASE_URL,
                api_key=TEST_API_KEY,
                retry_delay=0.0,
            )
        )

    def test_external_mode_flags(self, external_service):
        assert external_service.is_external_provider_configured is True
        assert external_service.is_external_api_key_configured is True
        assert external_service.get_active_data_source() == (
            EXTERNAL_DATA_SOURCE
        )

    def test_get_crop_season_info_external(self, external_service):
        info = external_service.get_crop_season_info("anything")
        assert info["external_provider_active"] is True
        assert info["seasons_available"] is None
        assert info["sowing_windows"] is None

    @patch("urllib.request.urlopen")
    def test_get_crop_calendar_delegates_to_external(
        self, mock_urlopen, external_service
    ):
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            EXTERNAL_PAYLOAD
        )

        result = asyncio.run(
            external_service.get_crop_calendar("rice", season="kharif")
        )
        assert result["data_source"] == EXTERNAL_DATA_SOURCE
        assert result["is_reference_data"] is False
        assert result["location"] is None

    def test_get_crop_calendar_external_failure_propagates(
        self, external_service
    ):
        class FailingClient:
            is_configured = True

            async def fetch_crop_calendar(self, *args, **kwargs):
                raise CropCalendarServiceError("provider down")

        external_service.external_client = FailingClient()
        external_service.fallback_to_reference_data = False
        with pytest.raises(CropCalendarServiceError, match="provider down"):
            asyncio.run(
                external_service.get_crop_calendar("rice", season="kharif")
            )

    def test_catalogue_notes_external_mode(self, external_service):
        catalog = external_service.get_supported_crops()
        assert catalog["external_provider_configured"] is True
        assert "reference dataset" in catalog["note"]



