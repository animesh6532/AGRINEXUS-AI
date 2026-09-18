"""
Pydantic schemas for the Weather Intelligence API.

Describes the normalized weather data exposed by the backend. The backend
never forwards the raw Open-Meteo response; it is normalized into these
schemas instead.

Conventions follow the existing market schemas (Pydantic v2, Field with
examples, Base/Response style).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class WeatherLocation(BaseModel):
    """Location information attached to weather data."""

    latitude: float = Field(..., ge=-90, le=90, example=19.0760)
    longitude: float = Field(..., ge=-180, le=180, example=72.8777)
    timezone: str = Field(default="UTC", example="Asia/Kolkata")


class CurrentWeatherResponse(WeatherLocation):
    """
    Current weather observation for a location.

    Units follow Open-Meteo defaults:
    - temperature: degrees Celsius
    - precipitation: millimetres
    - wind_speed: km/h
    - wind_direction: degrees (0 = north, 90 = east)
    - weather_code: WMO weather interpretation code
    """

    observation_time: Optional[str] = Field(
        None, example="2026-09-18T10:30"
    )
    temperature: Optional[float] = Field(None, example=28.5)
    relative_humidity: Optional[float] = Field(
        None, ge=0, le=100, example=75.0
    )
    precipitation: Optional[float] = Field(None, ge=0, example=0.0)
    wind_speed: Optional[float] = Field(None, ge=0, example=10.0)
    wind_direction: Optional[float] = Field(None, ge=0, le=360, example=180.0)
    weather_code: Optional[int] = Field(None, example=0)
    data_source: str = Field(default="open-meteo", example="open-meteo")


class HourlyForecastPoint(BaseModel):
    """A single hourly forecast point."""

    time: Optional[str] = Field(None, example="2026-09-18T11:00")
    temperature: Optional[float] = Field(None, example=29.0)
    relative_humidity: Optional[float] = Field(
        None, ge=0, le=100, example=70.0
    )
    precipitation: Optional[float] = Field(None, ge=0, example=0.0)
    wind_speed: Optional[float] = Field(None, ge=0, example=15.0)
    weather_code: Optional[int] = Field(None, example=1)


class DailyForecastPoint(BaseModel):
    """A single daily forecast point."""

    date: Optional[str] = Field(None, example="2026-09-19")
    temperature_max: Optional[float] = Field(None, example=32.0)
    temperature_min: Optional[float] = Field(None, example=24.0)
    precipitation_sum: Optional[float] = Field(None, ge=0, example=5.0)
    precipitation_probability_max: Optional[float] = Field(
        None, ge=0, le=100, example=60
    )
    wind_speed_max: Optional[float] = Field(None, ge=0, example=20.0)
    weather_code: Optional[int] = Field(None, example=2)
    sunrise: Optional[str] = Field(None, example="2026-09-19T06:15")
    sunset: Optional[str] = Field(None, example="2026-09-19T18:45")



class WeatherForecastResponse(WeatherLocation):
    """
    Weather forecast for a location.

    Contains a short hourly window (for near-term decisions) and daily
    aggregates for the requested horizon.
    """

    forecast_days: int = Field(..., ge=1, le=16, example=7)
    hourly: List[HourlyForecastPoint] = Field(default_factory=list)
    daily: List[DailyForecastPoint] = Field(default_factory=list)
    data_source: str = Field(default="open-meteo", example="open-meteo")


class WeatherInsight(BaseModel):
    """
    A deterministic, explainable weather insight.

    Weather insights describe observed/forecast weather conditions and
    their direct weather implications only. They are NOT crop, disease,
    pest, irrigation, fertilizer, or yield predictions.
    """

    type: str = Field(..., example="heavy_rain")
    severity: str = Field(
        ..., pattern="^(low|medium|high)$", example="high"
    )
    title: str = Field(..., example="Heavy Rain Expected")
    description: str = Field(
        ...,
        example=(
            "Heavy precipitation is forecast. Field operations may be "
            "affected."
        ),
    )
    relevant_value: Optional[float] = Field(
        None, example=15.0, description="Measured/forecast value behind the insight"
    )
    threshold_used: Optional[float] = Field(
        None, example=10.0, description="Rule threshold that triggered the insight"
    )
    timestamp: Optional[str] = Field(
        None,
        example="2026-09-18T10:30",
        description="Observation time or relevant forecast date/period",
    )


class WeatherInsightsResponse(WeatherLocation):
    """Weather intelligence signals for a location."""

    timestamp: datetime = Field(..., example="2026-09-18T10:30:00Z")
    forecast_days: int = Field(default=7, ge=1, le=16, example=7)
    insights: List[WeatherInsight] = Field(default_factory=list)
    data_source: str = Field(default="open-meteo", example="open-meteo")


class WeatherHealthResponse(BaseModel):
    """Health check response for the weather module."""

    status: str = Field(..., example="healthy")
    service: str = Field(..., example="agrinexus-weather-intelligence")
    version: str = Field(..., example="1.0.0")
    timestamp: str = Field(..., example="2026-09-18T10:30:00+00:00")
    api_connectivity: bool = Field(
        ...,
        example=True,
        description="Whether Open-Meteo responded to a connectivity probe",
    )