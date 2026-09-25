"""
Weather service for fetching weather data from the Open-Meteo API.

Part of the Weather Intelligence module (external API integration, NOT an
ML model). This module handles HTTP requests to Open-Meteo, response
validation, and normalization into the internal weather data format.

Networking approach: Python urllib executed via asyncio.to_thread, which is
consistent with the existing market service (httpx has proven unreliable
for outbound requests in the current Windows environment).
"""

import asyncio
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from ..core.logging import logger


class WeatherServiceError(Exception):
    """
    Raised when the upstream weather API fails or returns an unusable
    response (network failure, HTTP error, invalid JSON, missing response
    fields). The API layer maps this to HTTP 502, while invalid user input
    is signalled with ValueError and mapped to HTTP 400.
    """


# Open-Meteo request configuration
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Variables requested from Open-Meteo (kept explicit for reviewability).
CURRENT_VARIABLES = (
    "temperature_2m,relative_humidity_2m,precipitation,"
    "wind_speed_10m,wind_direction_10m,weather_code,is_day,"
    "apparent_temperature,cloud_cover,wind_gusts_10m"
)
HOURLY_VARIABLES = (
    "temperature_2m,relative_humidity_2m,precipitation,"
    "wind_speed_10m,wind_direction_10m,weather_code,is_day,"
    "cloud_cover,apparent_temperature"
)
DAILY_VARIABLES = (
    "weather_code,temperature_2m_max,temperature_2m_min,"
    "precipitation_sum,precipitation_probability_max,"
    "wind_speed_10m_max,sunrise,sunset"
)

MAX_FORECAST_DAYS = 16       # Open-Meteo forecast horizon limit
MAX_HOURLY_ENTRIES = 48      # Keep the hourly response manageable (2 days)
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 3


class OpenMeteoClient:
    """
    HTTP client for the Open-Meteo forecast API.

    Responsible only for building requests safely, retrying transient
    network failures, and returning parsed JSON. Normalization/validation
    of the domain data happens in WeatherService.
    """

    def __init__(
        self,
        base_url: str = OPEN_METEO_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _build_request_url(
        self,
        latitude: float,
        longitude: float,
        include_current: bool,
        include_hourly: bool,
        include_daily: bool,
        forecast_days: int,
    ) -> str:
        """Build a safe, URL-encoded Open-Meteo request URL."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "auto",
            "forecast_days": forecast_days,
        }
        if include_current:
            params["current"] = CURRENT_VARIABLES
        if include_hourly:
            params["hourly"] = HOURLY_VARIABLES
        if include_daily:
            params["daily"] = DAILY_VARIABLES

        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"

    async def fetch_weather_data(
        self,
        latitude: float,
        longitude: float,
        include_current: bool = True,
        include_hourly: bool = True,
        include_daily: bool = True,
        forecast_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Fetch weather data from Open-Meteo for a location.

        Args:
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)
            include_current: Include the current weather block
            include_hourly: Include the hourly forecast block
            include_daily: Include the daily forecast block
            forecast_days: Number of forecast days to retrieve (1-16)

        Returns:
            Parsed JSON response as a dictionary

        Raises:
            ValueError: If input parameters are invalid
            WeatherServiceError: On HTTP/network/JSON/API failures
        """
        if not (-90 <= latitude <= 90):
            raise ValueError(
                f"Latitude must be between -90 and 90, got {latitude}"
            )
        if not (-180 <= longitude <= 180):
            raise ValueError(
                f"Longitude must be between -180 and 180, got {longitude}"
            )
        if not (1 <= forecast_days <= MAX_FORECAST_DAYS):
            raise ValueError(
                f"Forecast days must be between 1 and {MAX_FORECAST_DAYS}, "
                f"got {forecast_days}"
            )
        if not (include_current or include_hourly or include_daily):
            raise ValueError(
                "At least one of include_current, include_hourly, "
                "include_daily must be enabled"
            )

        request_url = self._build_request_url(
            latitude=latitude,
            longitude=longitude,
            include_current=include_current,
            include_hourly=include_hourly,
            include_daily=include_daily,
            forecast_days=forecast_days,
        )

        for attempt in range(self.max_retries):
            try:
                def make_request() -> str:
                    request = urllib.request.Request(
                        request_url,
                        headers={
                            "User-Agent": "AgriNexus-AI/1.0",
                            "Accept": "application/json",
                        },
                        method="GET",
                    )
                    with urllib.request.urlopen(
                        request, timeout=self.timeout
                    ) as response:
                        return response.read().decode("utf-8")

                # Run the blocking urllib request without blocking the
                # FastAPI/async event loop.
                response_text = await asyncio.to_thread(make_request)
                data = json.loads(response_text)

                # Open-Meteo signals request problems via an "error" field.
                if data.get("error"):
                    reason = data.get("reason", "unknown reason")
                    logger.error(f"Open-Meteo API error: {reason}")
                    raise WeatherServiceError(
                        f"Open-Meteo API error: {reason}"
                    )

                logger.info(
                    f"Fetched weather data for latitude={latitude}, "
                    f"longitude={longitude}"
                )
                return data

            except urllib.error.HTTPError as e:
                logger.error(
                    f"HTTP error fetching weather data: {e.code} - {e.reason}"
                )
                if e.code == 429 and attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise WeatherServiceError(
                    f"Open-Meteo HTTP error {e.code}: {e.reason}"
                ) from e

            except urllib.error.URLError as e:
                logger.warning(
                    f"Network error fetching weather data "
                    f"(attempt {attempt + 1}/{self.max_retries}): {e.reason}"
                )
                if attempt == self.max_retries - 1:
                    logger.error(
                        "Max retries exceeded for Open-Meteo request"
                    )
                    raise WeatherServiceError(
                        f"Network error contacting Open-Meteo: {e.reason}"
                    ) from e
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

            except TimeoutError as e:
                logger.warning(
                    f"Open-Meteo request timeout "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt == self.max_retries - 1:
                    logger.error(
                        "Max retries exceeded for Open-Meteo request"
                    )
                    raise WeatherServiceError(
                        "Open-Meteo request timed out"
                    ) from e
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from Open-Meteo: {e}")
                raise WeatherServiceError(
                    "Open-Meteo returned an invalid JSON response"
                ) from e

            except WeatherServiceError:
                # Already logged/handled above; do not retry or re-wrap.
                raise

            except Exception as e:
                logger.error(f"Unexpected error fetching weather data: {e}")
                if attempt == self.max_retries - 1:
                    raise WeatherServiceError(
                        f"Unexpected error contacting Open-Meteo: {e}"
                    ) from e
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

        # Should not be reachable, but keeps the return type explicit.
        raise WeatherServiceError(
            "Failed to fetch weather data after all retries"
        )

    async def check_api_connectivity(self) -> bool:
        """
        Perform a lightweight Open-Meteo request to verify connectivity.

        Returns:
            True if the API responded with usable data, False otherwise.
        """
        try:
            data = await self.fetch_weather_data(
                latitude=0.0,
                longitude=0.0,
                include_current=True,
                include_hourly=False,
                include_daily=False,
                forecast_days=1,
            )
            return "current" in data
        except (WeatherServiceError, ValueError) as e:
            logger.warning(f"Open-Meteo connectivity check failed: {e}")
            return False


class WeatherService:
    """
    Weather data service.

    Coordinates Open-Meteo API requests, validates the response structure,
    and normalizes it into the internal weather data format used by the
    schema and intelligence layers. Does not fabricate data: fields missing
    upstream are returned as None.
    """

    def __init__(self, api_client: Optional[OpenMeteoClient] = None):
        self.api_client = api_client or OpenMeteoClient()

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """
        Get normalized current weather data for a location.

        Args:
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)

        Returns:
            Normalized current weather data dictionary

        Raises:
            ValueError: If input parameters are invalid
            WeatherServiceError: If the API fails or the response is unusable
        """
        logger.info(
            f"Fetching current weather for latitude={latitude}, "
            f"longitude={longitude}"
        )

        raw_data = await self.api_client.fetch_weather_data(
            latitude=latitude,
            longitude=longitude,
            include_current=True,
            include_hourly=False,
            include_daily=False,
            forecast_days=1,
        )
        return self._normalize_current_weather(raw_data, latitude, longitude)

    async def get_weather_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get normalized weather forecast data for a location.

        Args:
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)
            forecast_days: Forecast horizon in days (1-16)

        Returns:
            Normalized forecast data dictionary

        Raises:
            ValueError: If input parameters are invalid
            WeatherServiceError: If the API fails or the response is unusable
        """
        logger.info(
            f"Fetching {forecast_days}-day forecast for latitude={latitude}, "
            f"longitude={longitude}"
        )

        raw_data = await self.api_client.fetch_weather_data(
            latitude=latitude,
            longitude=longitude,
            include_current=False,
            include_hourly=True,
            include_daily=True,
            forecast_days=forecast_days,
        )
        return self._normalize_forecast_weather(
            raw_data, latitude, longitude, forecast_days
        )

    async def check_api_connectivity(self) -> bool:
        """Check whether Open-Meteo is reachable (used by /health)."""
        return await self.api_client.check_api_connectivity()


    def _normalize_current_weather(
        self,
        raw_data: Dict[str, Any],
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """
        Normalize an Open-Meteo current weather response.

        Raises:
            WeatherServiceError: If the current weather block is missing.
        """
        current = raw_data.get("current")
        if not isinstance(current, dict) or not current:
            raise WeatherServiceError(
                "Open-Meteo response did not contain current weather data"
            )

        missing = [
            field for field in ("temperature_2m", "time")
            if field not in current
        ]
        if missing:
            logger.warning(
                f"Missing fields in current weather response: {missing}"
            )

        normalized: Dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": raw_data.get("timezone", "UTC"),
            "observation_time": current.get("time"),
            "temperature": current.get("temperature_2m"),  # Celsius
            "relative_humidity": current.get("relative_humidity_2m"),  # %
            "precipitation": current.get("precipitation"),  # mm
            "wind_speed": current.get("wind_speed_10m"),  # km/h
            "wind_direction": current.get("wind_direction_10m"),  # degrees
            "weather_code": current.get("weather_code"),  # WMO code
            "is_day": current.get("is_day"),  # 1 day, 0 night
            "apparent_temperature": current.get("apparent_temperature"),  # Celsius
            "cloud_cover": current.get("cloud_cover"),  # %
            "wind_gusts": current.get("wind_gusts_10m"),  # km/h
            "data_source": "open-meteo",
        }

        logger.debug(f"Normalized current weather data: {normalized}")
        return normalized


    def _normalize_forecast_weather(
        self,
        raw_data: Dict[str, Any],
        latitude: float,
        longitude: float,
        forecast_days: int,
    ) -> Dict[str, Any]:
        """
        Normalize an Open-Meteo forecast response (hourly + daily blocks).

        Raises:
            WeatherServiceError: If neither hourly nor daily data is present.
        """
        hourly = raw_data.get("hourly")
        daily = raw_data.get("daily")

        hourly_is_dict = isinstance(hourly, dict)
        daily_is_dict = isinstance(daily, dict)

        if not hourly_is_dict and not daily_is_dict:
            raise WeatherServiceError(
                "Open-Meteo response did not contain forecast data"
            )

        # Normalize hourly forecast (first MAX_HOURLY_ENTRIES entries to
        # keep the response manageable).
        hourly_forecast: list = []
        if hourly_is_dict and isinstance(hourly.get("time"), list):
            times = hourly["time"]

            def _hourly_value(key: str, index: int) -> Optional[Any]:
                series = hourly.get(key)
                if isinstance(series, list) and index < len(series):
                    return series[index]
                return None

            for i in range(min(len(times), MAX_HOURLY_ENTRIES)):
                hourly_forecast.append({
                    "time": times[i],
                    "temperature": _hourly_value("temperature_2m", i),
                    "relative_humidity": _hourly_value(
                        "relative_humidity_2m", i
                    ),
                    "precipitation": _hourly_value("precipitation", i),
                    "wind_speed": _hourly_value("wind_speed_10m", i),
                    "wind_direction": _hourly_value("wind_direction_10m", i),
                    "weather_code": _hourly_value("weather_code", i),
                    "is_day": _hourly_value("is_day", i),
                    "cloud_cover": _hourly_value("cloud_cover", i),
                    "apparent_temperature": _hourly_value(
                        "apparent_temperature", i
                    ),
                })


        # Normalize daily forecast (limited to the requested horizon).
        daily_forecast: list = []
        if daily_is_dict and isinstance(daily.get("time"), list):
            times = daily["time"]

            def _daily_value(key: str, index: int) -> Optional[Any]:
                series = daily.get(key)
                if isinstance(series, list) and index < len(series):
                    return series[index]
                return None

            for i in range(min(len(times), forecast_days)):
                daily_forecast.append({
                    "date": times[i],
                    "temperature_max": _daily_value("temperature_2m_max", i),
                    "temperature_min": _daily_value("temperature_2m_min", i),
                    "precipitation_sum": _daily_value("precipitation_sum", i),
                    "precipitation_probability_max": _daily_value(
                        "precipitation_probability_max", i
                    ),
                    "wind_speed_max": _daily_value("wind_speed_10m_max", i),
                    "weather_code": _daily_value("weather_code", i),
                    "sunrise": _daily_value("sunrise", i),
                    "sunset": _daily_value("sunset", i),
                })

        normalized = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": raw_data.get("timezone", "UTC"),
            "forecast_days": forecast_days,
            "hourly_forecast": hourly_forecast,
            "daily_forecast": daily_forecast,
            "data_source": "open-meteo",
        }

        logger.debug(
            f"Normalized forecast weather data: {len(hourly_forecast)} "
            f"hourly, {len(daily_forecast)} daily entries"
        )
        return normalized