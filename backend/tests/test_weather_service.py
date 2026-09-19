"""
Test the weather service with mocked Open-Meteo API calls.

The OpenMeteoClient uses urllib (not httpx) for Open-Meteo requests, so
these tests mock urllib.request.urlopen, following the same convention as
the market service tests. No test in this file contacts the live API.
"""

import asyncio
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from app.services.weather_service import (
    MAX_HOURLY_ENTRIES,
    OpenMeteoClient,
    WeatherService,
    WeatherServiceError,
)


def _payload_response(payload) -> MagicMock:
    """Build a mock for urlopen() used as a context manager."""
    mock_response = MagicMock()
    mock_response.read.return_value.decode.return_value = json.dumps(payload)
    return mock_response


CURRENT_PAYLOAD = {
    "latitude": 19.076,
    "longitude": 72.8777,
    "timezone": "Asia/Kolkata",
    "current": {
        "time": "2026-09-18T10:30",
        "interval": 900,
        "temperature_2m": 28.5,
        "relative_humidity_2m": 75,
        "precipitation": 0.0,
        "wind_speed_10m": 10.2,
        "wind_direction_10m": 180,
        "weather_code": 0,
    },
}

FORECAST_PAYLOAD = {
    "latitude": 19.076,
    "longitude": 72.8777,
    "timezone": "Asia/Kolkata",
    "hourly": {
        "time": ["2026-09-18T00:00", "2026-09-18T01:00"],
        "temperature_2m": [27.0, 26.5],
        "relative_humidity_2m": [80, 82],
        "precipitation": [0.0, 0.5],
        "wind_speed_10m": [8.0, 9.0],
        "weather_code": [1, 2],
    },
    "daily": {
        "time": ["2026-09-18", "2026-09-19"],
        "weather_code": [1, 61],
        "temperature_2m_max": [32.0, 31.0],
        "temperature_2m_min": [24.0, 23.5],
        "precipitation_sum": [0.5, 12.0],
        "precipitation_probability_max": [10, 80],
        "wind_speed_10m_max": [18.0, 25.0],
        "sunrise": ["2026-09-18T06:20", "2026-09-19T06:20"],
        "sunset": ["2026-09-18T18:40", "2026-09-19T18:39"],
    },
}



class TestOpenMeteoClient:
    """Test the OpenMeteoClient HTTP layer."""

    @pytest.fixture
    def api_client(self):
        """Create an API client with no retry sleeping for fast tests."""
        return OpenMeteoClient(retry_delay=0.0)

    @patch("urllib.request.urlopen")
    def test_fetch_current_success(self, mock_urlopen, api_client):
        """Test a successful current-weather fetch and parse."""
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            CURRENT_PAYLOAD
        )

        data = asyncio.run(api_client.fetch_weather_data(
            latitude=19.076,
            longitude=72.8777,
            include_current=True,
            include_hourly=False,
            include_daily=False,
            forecast_days=1,
        ))

        assert data["latitude"] == 19.076
        assert data["timezone"] == "Asia/Kolkata"
        assert data["current"]["temperature_2m"] == 28.5

    @patch("urllib.request.urlopen")
    def test_request_url_contains_expected_params(
        self, mock_urlopen, api_client
    ):
        """Test that the request URL is built safely with expected params."""
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            CURRENT_PAYLOAD
        )

        asyncio.run(api_client.fetch_weather_data(
            latitude=19.076,
            longitude=72.8777,
            include_current=True,
            include_hourly=False,
            include_daily=False,
            forecast_days=1,
        ))

        request = mock_urlopen.call_args[0][0]
        url = request.full_url
        assert "latitude=19.076" in url
        assert "longitude=72.8777" in url
        assert "timezone=auto" in url
        assert "forecast_days=1" in url
        assert "current=temperature_2m" in url
        assert "hourly" not in url
        assert request.headers.get("User-agent") == "AgriNexus-AI/1.0"
        assert request.headers.get("Accept") == "application/json"

    @patch("urllib.request.urlopen")
    def test_fetch_api_error_payload(self, mock_urlopen, api_client):
        """Test handling of the Open-Meteo error payload."""
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            {"error": True, "reason": "Invalid parameter: latitude"}
        )

        with pytest.raises(
            WeatherServiceError, match="Open-Meteo API error"
        ):
            asyncio.run(api_client.fetch_weather_data(
                latitude=19.076, longitude=72.8777
            ))

    @patch("urllib.request.urlopen")
    def test_fetch_http_error(self, mock_urlopen, api_client):
        """Test handling of an HTTP 500 error from Open-Meteo."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.open-meteo.com/v1/forecast",
            500,
            "Internal Server Error",
            {},
            None,
        )

        with pytest.raises(WeatherServiceError, match="HTTP error 500"):
            asyncio.run(api_client.fetch_weather_data(
                latitude=19.076, longitude=72.8777
            ))


    @patch("urllib.request.urlopen")
    def test_fetch_rate_limit_retries_then_raises(
        self, mock_urlopen, api_client
    ):
        """Test that 429 responses are retried before failing."""
        mock_urlopen.side_effect = [
            urllib.error.HTTPError(
                "https://api.open-meteo.com/v1/forecast",
                429, "Too Many Requests", {}, None,
            )
        ] * api_client.max_retries

        with pytest.raises(WeatherServiceError, match="HTTP error 429"):
            asyncio.run(api_client.fetch_weather_data(
                latitude=19.076, longitude=72.8777
            ))

        assert mock_urlopen.call_count == api_client.max_retries

    @patch("urllib.request.urlopen")
    def test_fetch_network_error_retries_then_raises(
        self, mock_urlopen, api_client
    ):
        """Test that network (DNS/connection) failures are retried."""
        mock_urlopen.side_effect = urllib.error.URLError(
            "Name or service not known"
        )

        with pytest.raises(WeatherServiceError, match="Network error"):
            asyncio.run(api_client.fetch_weather_data(
                latitude=19.076, longitude=72.8777
            ))

        assert mock_urlopen.call_count == api_client.max_retries

    @patch("urllib.request.urlopen")
    def test_fetch_timeout(self, mock_urlopen, api_client):
        """Test handling of request timeouts."""
        mock_urlopen.side_effect = TimeoutError("timed out")

        with pytest.raises(WeatherServiceError, match="timed out"):
            asyncio.run(api_client.fetch_weather_data(
                latitude=19.076, longitude=72.8777
            ))

    @patch("urllib.request.urlopen")
    def test_fetch_invalid_json(self, mock_urlopen, api_client):
        """Test handling of an invalid JSON body."""
        mock_response = MagicMock()
        mock_response.read.return_value.decode.return_value = (
            "<html>not json</html>"
        )
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with pytest.raises(WeatherServiceError, match="invalid JSON"):
            asyncio.run(api_client.fetch_weather_data(
                latitude=19.076, longitude=72.8777
            ))

    def test_fetch_invalid_latitude(self, api_client):
        """Test latitude validation."""
        with pytest.raises(ValueError, match="Latitude must be between"):
            asyncio.run(api_client.fetch_weather_data(
                latitude=95.0, longitude=72.8777
            ))

    def test_fetch_invalid_longitude(self, api_client):
        """Test longitude validation."""
        with pytest.raises(ValueError, match="Longitude must be between"):
            asyncio.run(api_client.fetch_weather_data(
                latitude=19.076, longitude=185.0
            ))

    def test_fetch_invalid_forecast_days(self, api_client):
        """Test forecast-days validation."""
        with pytest.raises(ValueError, match="Forecast days must be between"):
            asyncio.run(api_client.fetch_weather_data(
                latitude=19.076, longitude=72.8777, forecast_days=20
            ))

    def test_fetch_no_data_blocks_requested(self, api_client):
        """Test that requesting no data blocks is rejected."""
        with pytest.raises(ValueError, match="At least one"):
            asyncio.run(api_client.fetch_weather_data(
                latitude=19.076,
                longitude=72.8777,
                include_current=False,
                include_hourly=False,
                include_daily=False,
            ))

    @patch("urllib.request.urlopen")
    def test_check_api_connectivity_success(self, mock_urlopen, api_client):
        """Test connectivity probe returns True on a usable response."""
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            CURRENT_PAYLOAD
        )
        assert asyncio.run(api_client.check_api_connectivity()) is True

    @patch("urllib.request.urlopen")
    def test_check_api_connectivity_failure(self, mock_urlopen, api_client):
        """Test connectivity probe returns False when the API fails."""
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")
        assert asyncio.run(api_client.check_api_connectivity()) is False



class TestWeatherService:
    """Test WeatherService normalization on top of the API client."""

    @pytest.fixture
    def weather_service(self):
        """Create a weather service with a fast, non-retrying client."""
        return WeatherService(api_client=OpenMeteoClient(retry_delay=0.0))

    @patch("urllib.request.urlopen")
    def test_get_current_weather_normalization(
        self, mock_urlopen, weather_service
    ):
        """Test current weather is normalized to internal field names."""
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            CURRENT_PAYLOAD
        )

        result = asyncio.run(weather_service.get_current_weather(
            latitude=19.076, longitude=72.8777
        ))

        assert result["latitude"] == 19.076
        assert result["longitude"] == 72.8777
        assert result["timezone"] == "Asia/Kolkata"
        assert result["observation_time"] == "2026-09-18T10:30"
        assert result["temperature"] == 28.5
        assert result["relative_humidity"] == 75
        assert result["precipitation"] == 0.0
        assert result["wind_speed"] == 10.2
        assert result["wind_direction"] == 180
        assert result["weather_code"] == 0
        assert result["data_source"] == "open-meteo"

    @patch("urllib.request.urlopen")
    def test_get_current_weather_missing_current_block(
        self, mock_urlopen, weather_service
    ):
        """Test that a response without a current block is rejected."""
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            {"latitude": 19.076, "longitude": 72.8777, "timezone": "UTC"}
        )

        with pytest.raises(
            WeatherServiceError, match="current weather data"
        ):
            asyncio.run(weather_service.get_current_weather(
                latitude=19.076, longitude=72.8777
            ))

    @patch("urllib.request.urlopen")
    def test_get_current_weather_missing_fields_become_none(
        self, mock_urlopen, weather_service
    ):
        """Test missing fields are None - values are never fabricated."""
        partial = {
            "timezone": "UTC",
            "current": {
                "time": "2026-09-18T10:30",
                "temperature_2m": 21.0,
            },
        }
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            partial
        )

        result = asyncio.run(weather_service.get_current_weather(
            latitude=10.0, longitude=20.0
        ))

        assert result["temperature"] == 21.0
        assert result["relative_humidity"] is None
        assert result["precipitation"] is None
        assert result["wind_speed"] is None
        assert result["weather_code"] is None

    @patch("urllib.request.urlopen")
    def test_get_weather_forecast_normalization(
        self, mock_urlopen, weather_service
    ):
        """Test forecast blocks are normalized correctly."""
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            FORECAST_PAYLOAD
        )

        result = asyncio.run(weather_service.get_weather_forecast(
            latitude=19.076, longitude=72.8777, forecast_days=2
        ))

        assert result["forecast_days"] == 2
        assert result["timezone"] == "Asia/Kolkata"
        assert len(result["hourly_forecast"]) == 2
        assert result["hourly_forecast"][0]["temperature"] == 27.0
        assert result["hourly_forecast"][1]["precipitation"] == 0.5

        assert len(result["daily_forecast"]) == 2
        day0 = result["daily_forecast"][0]
        assert day0["date"] == "2026-09-18"
        assert day0["temperature_max"] == 32.0
        assert day0["temperature_min"] == 24.0
        assert day0["precipitation_sum"] == 0.5
        assert day0["precipitation_probability_max"] == 10
        assert day0["wind_speed_max"] == 18.0
        assert day0["weather_code"] == 1
        assert day0["sunrise"] == "2026-09-18T06:20"
        assert day0["sunset"] == "2026-09-18T18:40"


    @patch("urllib.request.urlopen")
    def test_get_weather_forecast_missing_blocks(
        self, mock_urlopen, weather_service
    ):
        """Test that a response with no hourly/daily data is rejected."""
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            {"latitude": 19.076, "longitude": 72.8777, "timezone": "UTC"}
        )

        with pytest.raises(WeatherServiceError, match="forecast data"):
            asyncio.run(weather_service.get_weather_forecast(
                latitude=19.076, longitude=72.8777, forecast_days=3
            ))

    @patch("urllib.request.urlopen")
    def test_get_weather_forecast_hourly_capped(
        self, mock_urlopen, weather_service
    ):
        """Test that hourly entries are capped to keep responses small."""
        payload = {
            "timezone": "UTC",
            "hourly": {
                "time": [f"2026-09-18T{i:02d}:00" for i in range(60)],
                "temperature_2m": [20.0 + i for i in range(60)],
            },
            "daily": {"time": ["2026-09-18"]},
        }
        mock_urlopen.return_value.__enter__.return_value = _payload_response(
            payload
        )

        result = asyncio.run(weather_service.get_weather_forecast(
            latitude=19.076, longitude=72.8777, forecast_days=1
        ))

        assert len(result["hourly_forecast"]) == MAX_HOURLY_ENTRIES
        assert len(result["daily_forecast"]) == 1

    @patch("urllib.request.urlopen")
    def test_service_error_propagates_from_client(
        self, mock_urlopen, weather_service
    ):
        """Test upstream failures surface as WeatherServiceError."""
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")

        with pytest.raises(WeatherServiceError):
            asyncio.run(weather_service.get_current_weather(
                latitude=19.076, longitude=72.8777
            ))