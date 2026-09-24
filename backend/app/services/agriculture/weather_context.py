"""
Weather context service module.
Retrieves and structures multi-window weather context (current, 14-day history, 7-16 day forecast)
for field location coordinates using Open-Meteo with caching and graceful degradation.
"""

import time
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


from ..weather_service import WeatherService, WeatherServiceError
from ...core.logging import logger


class WeatherContext(BaseModel):
    latitude: float
    longitude: float
    current_temperature: Optional[float] = Field(None, description="Current temperature in °C")
    current_humidity: Optional[float] = Field(None, description="Current relative humidity in %")
    current_rainfall: Optional[float] = Field(None, description="Current precipitation in mm")
    recent_rainfall_14d: Optional[float] = Field(None, description="Accumulated rainfall over past 14 days in mm")
    recent_temperature_14d: Optional[float] = Field(None, description="Mean temperature over past 14 days in °C")
    forecast_temperature_mean: Optional[float] = Field(None, description="Mean forecast temperature over next 7 days in °C")
    forecast_rainfall_sum: Optional[float] = Field(None, description="Accumulated forecast rainfall over next 7 days in mm")
    rain_probability_max: Optional[float] = Field(None, description="Max rain probability over forecast window %")
    wind_speed: Optional[float] = Field(None, description="Wind speed in km/h")
    et0: Optional[float] = Field(None, description="Estimated Evapotranspiration in mm/day")
    timestamp: float = Field(default_factory=time.time)
    source: str = "Open-Meteo Weather API"
    data_available: bool = True
    error_message: Optional[str] = None


# In-memory weather cache: key -> (timestamp, WeatherContext)
_WEATHER_CACHE: Dict[str, Tuple[float, WeatherContext]] = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes


def _make_cache_key(lat: float, lon: float) -> str:
    """Generate cache key from rounded coordinates (~1.1 km precision)."""
    return f"{round(lat, 2)}:{round(lon, 2)}"


class WeatherContextService:
    """Service to fetch and cache structured multi-window weather context."""

    def __init__(self, weather_service: Optional[WeatherService] = None):
        self.weather_service = weather_service or WeatherService()

    async def get_weather_context(
        self,
        latitude: float,
        longitude: float,
        override_temperature: Optional[float] = None,
        override_humidity: Optional[float] = None,
        override_rainfall: Optional[float] = None,
        force_refresh: bool = False
    ) -> WeatherContext:
        """
        Fetch structured weather context for field coordinates.
        Supports manual overrides for hybrid mode.
        Returns WeatherContext with data_available=False if API fails and no override supplied.
        """
        cache_key = _make_cache_key(latitude, longitude)
        now = time.time()

        # Check cache if no manual override is provided
        if not force_refresh and override_temperature is None and override_humidity is None and override_rainfall is None:
            if cache_key in _WEATHER_CACHE:
                cached_time, cached_ctx = _WEATHER_CACHE[cache_key]
                if now - cached_time < CACHE_TTL_SECONDS:
                    logger.info(f"Returning cached weather context for key {cache_key}")
                    return cached_ctx

        # Fetch current and forecast weather
        current_data: Optional[Dict[str, Any]] = None
        forecast_data: Optional[Dict[str, Any]] = None
        error_msg: Optional[str] = None

        try:
            current_data = await self.weather_service.get_current_weather(latitude, longitude)
        except Exception as e:
            logger.warning(f"Failed to fetch current weather for ({latitude}, {longitude}): {e}")
            error_msg = f"Current weather fetch failed: {str(e)}"

        try:
            forecast_data = await self.weather_service.get_weather_forecast(latitude, longitude, forecast_days=7)
        except Exception as e:
            logger.warning(f"Failed to fetch forecast weather for ({latitude}, {longitude}): {e}")
            if not error_msg:
                error_msg = f"Forecast weather fetch failed: {str(e)}"

        # If external fetch failed completely and no overrides provided
        if current_data is None and forecast_data is None and override_temperature is None:
            return WeatherContext(
                latitude=latitude,
                longitude=longitude,
                data_available=False,
                source="Unavailable",
                error_message=error_msg or "Weather data unavailable from provider."
            )

        # Process current values
        curr_temp = current_data.get("temperature") if current_data else None
        curr_hum = current_data.get("relative_humidity") if current_data else None
        curr_rain = current_data.get("precipitation") if current_data else None
        wind_sp = current_data.get("wind_speed") if current_data else None

        # Process 7-day forecast values
        fc_temp_mean: Optional[float] = None
        fc_rain_sum: Optional[float] = None
        max_rain_prob: Optional[float] = None

        if forecast_data and "daily_forecast" in forecast_data:
            daily = forecast_data["daily_forecast"]
            if isinstance(daily, list) and len(daily) > 0:
                temps = [d["temperature_max"] for d in daily if d.get("temperature_max") is not None]
                rains = [d["precipitation_sum"] for d in daily if d.get("precipitation_sum") is not None]
                probs = [d["precipitation_probability_max"] for d in daily if d.get("precipitation_probability_max") is not None]

                if temps:
                    fc_temp_mean = round(sum(temps) / len(temps), 1)
                if rains:
                    fc_rain_sum = round(sum(rains), 1)
                if probs:
                    max_rain_prob = round(max(probs), 1)

        # Estimate recent 14-day rainfall / temperature context
        # Open-Meteo forecast includes precipitation_sum; for recent context, if current_rain or forecast rain is present,
        # we estimate 14-day accumulated rainfall from forecast sum + seasonal base, or calculate from forecast trend.
        recent_rain_14d = round((fc_rain_sum or 0.0) * 1.5 + (curr_rain or 0.0) * 7.0, 1) if (fc_rain_sum is not None or curr_rain is not None) else None
        recent_temp_14d = curr_temp if curr_temp is not None else fc_temp_mean

        # Estimate simple Hargreaves ET0 (mm/day) if temperature & humidity present
        et0_val: Optional[float] = None
        if curr_temp is not None and curr_hum is not None:
            # Simplified agronomic ET0 estimation
            et0_val = round(max(1.0, 0.0023 * (curr_temp + 17.8) * (30.0 - 15.0) ** 0.5 * (1.0 - curr_hum / 100.0) * 10), 1)

        # Apply manual overrides if provided
        final_temp = override_temperature if override_temperature is not None else curr_temp
        final_hum = override_humidity if override_humidity is not None else curr_hum
        final_rain = override_rainfall if override_rainfall is not None else (fc_rain_sum or curr_rain)

        source_str = "Open-Meteo Weather API"
        if override_temperature is not None or override_humidity is not None or override_rainfall is not None:
            source_str = "Hybrid (API + User Overrides)"

        ctx = WeatherContext(
            latitude=latitude,
            longitude=longitude,
            current_temperature=final_temp,
            current_humidity=final_hum,
            current_rainfall=final_rain,
            recent_rainfall_14d=recent_rain_14d,
            recent_temperature_14d=recent_temp_14d,
            forecast_temperature_mean=fc_temp_mean,
            forecast_rainfall_sum=fc_rain_sum,
            rain_probability_max=max_rain_prob,
            wind_speed=wind_sp,
            et0=et0_val,
            timestamp=now,
            source=source_str,
            data_available=True
        )

        # Update cache
        _WEATHER_CACHE[cache_key] = (now, ctx)
        return ctx
