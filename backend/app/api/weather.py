"""
Weather Intelligence API endpoints.

Exposes weather data from Open-Meteo through the FastAPI backend:
current conditions, forecasts, derived weather-only insights, and a
module health check.

Error handling contract:
- 400: invalid request parameters caught at the service layer (ValueError)
- 422: request parameter validation failures (FastAPI/Pydantic)
- 500: unexpected internal errors (no stack trace is exposed)
- 502: upstream Open-Meteo failures (WeatherServiceError)
"""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.logging import logger
from ..intelligence import weather_intelligence
from ..schemas import weather as schemas
from ..services import weather_service

# Create router
router = APIRouter(
    prefix="/api/weather",
    tags=["weather"],
    responses={404: {"description": "Not found"}},
)

SERVICE_NAME = "agrinexus-weather-intelligence"
SERVICE_VERSION = "1.0.0"


# Dependency injection
def get_weather_service() -> weather_service.WeatherService:
    """Dependency to get the weather service."""
    return weather_service.WeatherService()


def get_weather_intelligence_service(
) -> weather_intelligence.WeatherIntelligence:
    """Dependency to get the weather intelligence service."""
    return weather_intelligence.WeatherIntelligence()


def _utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


@router.get(
    "/current",
    response_model=schemas.CurrentWeatherResponse,
    summary="Get current weather for a location",
    description=(
        "Retrieve the current weather observation (temperature, humidity, "
        "precipitation, wind, weather code) for any latitude/longitude from "
        "Open-Meteo."
    ),
)
async def get_current_weather(
    latitude: float = Query(
        ..., ge=-90, le=90, description="Latitude in decimal degrees",
        example=19.0760,
    ),
    longitude: float = Query(
        ..., ge=-180, le=180, description="Longitude in decimal degrees",
        example=72.8777,
    ),
    weather_svc: weather_service.WeatherService = Depends(get_weather_service),
):
    """
    Get current weather for a location.

    Data is fetched live from Open-Meteo and normalized into the backend
    schema. No weather values are cached or fabricated.
    """
    logger.info(
        f"Fetching current weather for latitude={latitude}, "
        f"longitude={longitude}"
    )

    try:
        return await weather_svc.get_current_weather(
            latitude=latitude, longitude=longitude
        )
    except ValueError as e:
        logger.warning(f"Invalid weather request parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except weather_service.WeatherServiceError as e:
        logger.error(f"Upstream weather API failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Weather data provider is currently unavailable",
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching current weather: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching weather data",
        )



@router.get(
    "/forecast",
    response_model=schemas.WeatherForecastResponse,
    summary="Get weather forecast for a location",
    description=(
        "Retrieve a normalized weather forecast (hourly window plus daily "
        "aggregates: temperature, precipitation, precipitation probability, "
        "wind, weather code, sunrise/sunset) for any latitude/longitude."
    ),
)
async def get_weather_forecast(
    latitude: float = Query(
        ..., ge=-90, le=90, description="Latitude in decimal degrees",
        example=19.0760,
    ),
    longitude: float = Query(
        ..., ge=-180, le=180, description="Longitude in decimal degrees",
        example=72.8777,
    ),
    forecast_days: int = Query(
        7, ge=1, le=16,
        description="Forecast horizon in days", example=7,
    ),
    weather_svc: weather_service.WeatherService = Depends(get_weather_service),
):
    """
    Get a weather forecast for a location.

    Hourly entries cover the first 48 hours of the window to keep the
    response manageable; daily aggregates cover the full horizon.
    """
    logger.info(
        f"Fetching {forecast_days}-day forecast for latitude={latitude}, "
        f"longitude={longitude}"
    )

    try:
        forecast = await weather_svc.get_weather_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
        )
        # Map service keys to the response schema explicitly rather than
        # relying on FastAPI's model filtering.
        return schemas.WeatherForecastResponse(
            latitude=forecast["latitude"],
            longitude=forecast["longitude"],
            timezone=forecast.get("timezone", "UTC"),
            forecast_days=forecast["forecast_days"],
            hourly=forecast["hourly_forecast"],
            daily=forecast["daily_forecast"],
            data_source=forecast.get("data_source", "open-meteo"),
        )
    except ValueError as e:
        logger.warning(f"Invalid forecast request parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except weather_service.WeatherServiceError as e:
        logger.error(f"Upstream weather API failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Weather data provider is currently unavailable",
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching weather forecast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching forecast data",
        )



@router.get(
    "/insights",
    response_model=schemas.WeatherInsightsResponse,
    summary="Get weather intelligence insights",
    description=(
        "Derive deterministic, rule-based weather insights (rain, heat, "
        "wind, humidity, field-operation disruption) from live Open-Meteo "
        "data. These signals describe weather conditions and their direct "
        "weather implications only - they are not crop, disease, pest, "
        "irrigation, fertilizer, or yield predictions."
    ),
)
async def get_weather_insights(
    latitude: float = Query(
        ..., ge=-90, le=90, description="Latitude in decimal degrees",
        example=19.0760,
    ),
    longitude: float = Query(
        ..., ge=-180, le=180, description="Longitude in decimal degrees",
        example=72.8777,
    ),
    forecast_days: int = Query(
        7, ge=1, le=16,
        description="Forecast horizon to analyse in days", example=7,
    ),
    weather_svc: weather_service.WeatherService = Depends(get_weather_service),
    intel_svc: weather_intelligence.WeatherIntelligence = Depends(
        get_weather_intelligence_service
    ),
):
    """
    Get weather intelligence insights for a location.

    Fetches current conditions and the forecast concurrently and applies
    explainable threshold rules. If one dataset fails but the other is
    available, insights are derived from the available dataset.
    """
    logger.info(
        f"Generating weather insights for latitude={latitude}, "
        f"longitude={longitude}, forecast_days={forecast_days}"
    )

    try:
        current_task = weather_svc.get_current_weather(
            latitude=latitude, longitude=longitude
        )
        forecast_task = weather_svc.get_weather_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
        )
        current_weather, forecast_weather = await asyncio.gather(
            current_task, forecast_task, return_exceptions=True
        )

        current_data = (
            current_weather
            if isinstance(current_weather, dict) else None
        )
        forecast_data = (
            forecast_weather
            if isinstance(forecast_weather, dict) else None
        )

        if isinstance(current_weather, Exception):
            logger.warning(
                f"Current weather unavailable for insights: "
                f"{current_weather}"
            )
        if isinstance(forecast_weather, Exception):
            logger.warning(
                f"Forecast unavailable for insights: {forecast_weather}"
            )

        if current_data is None and forecast_data is None:
            raise weather_service.WeatherServiceError(
                "Both current weather and forecast requests failed"
            )

        insights = intel_svc.get_weather_insights(
            current_weather=current_data,
            forecast_weather=forecast_data,
        )

        return schemas.WeatherInsightsResponse(
            latitude=latitude,
            longitude=longitude,
            timezone=(
                (current_data or forecast_data).get("timezone", "UTC")
            ),
            timestamp=datetime.now(timezone.utc),
            forecast_days=forecast_days,
            insights=insights,
        )

    except ValueError as e:
        logger.warning(f"Invalid insights request parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except weather_service.WeatherServiceError as e:
        logger.error(f"Upstream weather API failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Weather data provider is currently unavailable",
        )
    except Exception as e:
        logger.error(f"Error generating weather insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while generating weather insights",
        )



@router.get(
    "/health",
    response_model=schemas.WeatherHealthResponse,
    summary="Health check for the weather module",
    description=(
        "Check whether the weather intelligence module is operational and "
        "whether Open-Meteo is currently reachable."
    ),
)
async def weather_health_check(
    weather_svc: weather_service.WeatherService = Depends(get_weather_service),
):
    """Report module status and Open-Meteo connectivity."""
    api_connectivity = await weather_svc.check_api_connectivity()
    return schemas.WeatherHealthResponse(
        status="healthy" if api_connectivity else "degraded",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        timestamp=_utc_now_iso(),
        api_connectivity=api_connectivity,
    )