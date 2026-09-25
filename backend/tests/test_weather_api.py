"""
Test the weather API endpoints with mocked services, plus smoke tests
verifying that the Market endpoints remain registered.

External calls are replaced via FastAPI dependency overrides, so no test
in this file contacts the live Open-Meteo API.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.weather import (
    get_weather_intelligence_service,
    get_weather_service,
)
from app.main import app
from app.services.weather_service import WeatherServiceError

test_client = TestClient(app)

CURRENT_DATA = {
    "latitude": 19.076,
    "longitude": 72.8777,
    "timezone": "Asia/Kolkata",
    "observation_time": "2026-09-18T10:30",
    "temperature": 28.5,
    "relative_humidity": 75.0,
    "precipitation": 0.0,
    "wind_speed": 10.2,
    "wind_direction": 180.0,
    "weather_code": 0,
    "data_source": "open-meteo",
}

FORECAST_DATA = {
    "latitude": 19.076,
    "longitude": 72.8777,
    "timezone": "Asia/Kolkata",
    "forecast_days": 2,
    "hourly_forecast": [
        {
            "time": "2026-09-18T11:00",
            "temperature": 29.0,
            "relative_humidity": 70.0,
            "precipitation": 0.0,
            "wind_speed": 12.0,
            "weather_code": 1,
        }
    ],
    "daily_forecast": [
        {
            "date": "2026-09-18",
            "temperature_max": 32.0,
            "temperature_min": 24.0,
            "precipitation_sum": 0.0,
            "precipitation_probability_max": 10,
            "wind_speed_max": 20.0,
            "weather_code": 1,
            "sunrise": "2026-09-18T06:20",
            "sunset": "2026-09-18T18:40",
        },
        {
            "date": "2026-09-19",
            "temperature_max": 31.0,
            "temperature_min": 23.5,
            "precipitation_sum": 25.0,
            "precipitation_probability_max": 80,
            "wind_speed_max": 25.0,
            "weather_code": 61,
            "sunrise": "2026-09-19T06:20",
            "sunset": "2026-09-19T18:39",
        },
    ],
    "data_source": "open-meteo",
}


class FakeWeatherService:
    """Test double standing in for WeatherService."""

    def __init__(
        self,
        current=None,
        forecast=None,
        current_error=None,
        forecast_error=None,
        connected=True,
    ):
        self.current = current
        self.forecast = forecast
        self.current_error = current_error
        self.forecast_error = forecast_error
        self.connected = connected

    async def get_current_weather(self, latitude, longitude):
        if self.current_error is not None:
            raise self.current_error
        return self.current

    async def get_weather_forecast(
        self, latitude, longitude, forecast_days=7
    ):
        if self.forecast_error is not None:
            raise self.forecast_error
        return self.forecast

    async def check_api_connectivity(self):
        return self.connected


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    """Ensure dependency overrides never leak between tests."""
    yield
    app.dependency_overrides.clear()


def override_services(weather_svc, intel_svc=None):
    """Register dependency overrides for the weather endpoints."""
    app.dependency_overrides[get_weather_service] = lambda: weather_svc
    if intel_svc is not None:
        app.dependency_overrides[get_weather_intelligence_service] = (
            lambda: intel_svc
        )



class TestWeatherCurrentEndpoint:
    """Tests for GET /api/weather/current."""

    def test_current_weather_success(self):
        override_services(FakeWeatherService(current=CURRENT_DATA))
        response = test_client.get(
            "/api/weather/current",
            params={"latitude": 19.076, "longitude": 72.8777},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["latitude"] == 19.076
        assert data["longitude"] == 72.8777
        assert data["temperature"] == 28.5
        assert data["relative_humidity"] == 75.0
        assert data["precipitation"] == 0.0
        assert data["wind_speed"] == 10.2
        assert data["wind_direction"] == 180.0
        assert data["weather_code"] == 0
        assert data["data_source"] == "open-meteo"

    def test_current_weather_invalid_latitude(self):
        response = test_client.get(
            "/api/weather/current",
            params={"latitude": 95.0, "longitude": 72.8777},
        )
        assert response.status_code == 422

    def test_current_weather_invalid_longitude(self):
        response = test_client.get(
            "/api/weather/current",
            params={"latitude": 19.076, "longitude": 200.0},
        )
        assert response.status_code == 422

    def test_current_weather_missing_parameters(self):
        response = test_client.get("/api/weather/current")
        assert response.status_code == 422

    def test_current_weather_upstream_failure(self):
        override_services(FakeWeatherService(
            current_error=WeatherServiceError("Network error")
        ))
        response = test_client.get(
            "/api/weather/current",
            params={"latitude": 19.076, "longitude": 72.8777},
        )
        assert response.status_code == 502
        assert "detail" in response.json()

    def test_current_weather_bad_request(self):
        override_services(FakeWeatherService(
            current_error=ValueError("Latitude must be between -90 and 90")
        ))
        response = test_client.get(
            "/api/weather/current",
            params={"latitude": 45.0, "longitude": 72.8777},
        )
        assert response.status_code == 400
        assert "Latitude must be between" in response.json()["detail"]


class TestWeatherForecastEndpoint:
    """Tests for GET /api/weather/forecast."""

    def test_forecast_success(self):
        override_services(FakeWeatherService(forecast=FORECAST_DATA))
        response = test_client.get(
            "/api/weather/forecast",
            params={
                "latitude": 19.076, "longitude": 72.8777, "forecast_days": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["forecast_days"] == 2
        assert len(data["hourly"]) == 1
        assert data["hourly"][0]["temperature"] == 29.0
        assert len(data["daily"]) == 2
        assert data["daily"][0]["temperature_max"] == 32.0
        assert data["daily"][1]["precipitation_sum"] == 25.0
        assert data["daily"][1]["weather_code"] == 61

    def test_forecast_invalid_days_too_large(self):
        response = test_client.get(
            "/api/weather/forecast",
            params={
                "latitude": 19.076, "longitude": 72.8777, "forecast_days": 20,
            },
        )
        assert response.status_code == 422

    def test_forecast_invalid_days_zero(self):
        response = test_client.get(
            "/api/weather/forecast",
            params={
                "latitude": 19.076, "longitude": 72.8777, "forecast_days": 0,
            },
        )
        assert response.status_code == 422

    def test_forecast_upstream_failure(self):
        override_services(FakeWeatherService(
            forecast_error=WeatherServiceError("Invalid JSON response")
        ))
        response = test_client.get(
            "/api/weather/forecast",
            params={"latitude": 19.076, "longitude": 72.8777},
        )
        assert response.status_code == 502



class TestWeatherInsightsEndpoint:
    """Tests for GET /api/weather/insights."""

    def test_insights_success_with_signals(self):
        from app.intelligence.weather_intelligence import WeatherIntelligence

        override_services(
            FakeWeatherService(current=CURRENT_DATA, forecast=FORECAST_DATA),
            intel_svc=WeatherIntelligence(),
        )
        response = test_client.get(
            "/api/weather/insights",
            params={"latitude": 19.076, "longitude": 72.8777},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["latitude"] == 19.076
        assert data["forecast_days"] == 7
        insight_types = {i["type"] for i in data["insights"]}
        # FORECAST_DATA contains 25 mm rain on 2026-09-19
        assert "heavy_rain_forecast" in insight_types
        for insight in data["insights"]:
            assert insight["severity"] in ("low", "medium", "high")
            assert "title" in insight and "description" in insight

    def test_insights_benign_data_empty_list(self):
        from app.intelligence.weather_intelligence import WeatherIntelligence

        benign_current = dict(CURRENT_DATA)
        benign_current.update({
            "temperature": 22.0,
            "wind_speed": 8.0,
        })
        benign_forecast = {
            "forecast_days": 2,
            "daily_forecast": [
                {
                    "date": "2026-09-18",
                    "temperature_max": 30.0, "temperature_min": 20.0,
                    "precipitation_sum": 1.0,
                    "precipitation_probability_max": 10,
                    "wind_speed_max": 15.0, "weather_code": 1,
                    "sunrise": None, "sunset": None,
                }
            ],
        }
        override_services(
            FakeWeatherService(
                current=benign_current, forecast=benign_forecast,
            ),
            intel_svc=WeatherIntelligence(),
        )
        response = test_client.get(
            "/api/weather/insights",
            params={"latitude": 19.076, "longitude": 72.8777},
        )
        assert response.status_code == 200
        assert response.json()["insights"] == []

    def test_insights_partial_failure_still_returns_available(
        self,
    ):
        """If one dataset fails, insights still derive from the other."""
        from app.intelligence.weather_intelligence import WeatherIntelligence

        override_services(
            FakeWeatherService(
                current=CURRENT_DATA,
                forecast_error=WeatherServiceError("forecast failed"),
            ),
            intel_svc=WeatherIntelligence(),
        )
        response = test_client.get(
            "/api/weather/insights",
            params={"latitude": 19.076, "longitude": 72.8777},
        )
        assert response.status_code == 200
        assert response.json()["insights"] == []

    def test_insights_total_failure_is_502(self):
        override_services(FakeWeatherService(
            current_error=WeatherServiceError("down"),
            forecast_error=WeatherServiceError("down"),
        ))
        response = test_client.get(
            "/api/weather/insights",
            params={"latitude": 19.076, "longitude": 72.8777},
        )
        assert response.status_code == 502


class TestWeatherHealthEndpoint:
    """Tests for GET /api/weather/health."""

    def test_health_healthy(self):
        override_services(FakeWeatherService(connected=True))
        response = test_client.get("/api/weather/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "agrinexus-weather-intelligence"
        assert data["api_connectivity"] is True
        assert "timestamp" in data

    def test_health_degraded(self):
        override_services(FakeWeatherService(connected=False))
        response = test_client.get("/api/weather/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["api_connectivity"] is False



class TestRouterRegistration:
    """Tests verifying weather and market routes are registered."""

    def test_weather_routes_registered(self):
        weather_routes = [
            route.path for route in app.routes
            if route.path.startswith("/api/weather")
        ]
        assert "/api/weather/current" in weather_routes
        assert "/api/weather/forecast" in weather_routes
        assert "/api/weather/insights" in weather_routes
        assert "/api/weather/health" in weather_routes

    def test_market_routes_still_registered(self):
        market_routes = [
            route.path for route in app.routes
            if route.path.startswith("/api/market")
        ]
        assert "/api/market/health" in market_routes
        assert "/api/market/current" in market_routes
        assert "/api/market/history" in market_routes

    def test_core_routes_still_registered(self):
        core_routes = [route.path for route in app.routes]
        assert "/" in core_routes
        assert "/health" in core_routes

    def test_openapi_contains_weather_endpoints(self):
        openapi = test_client.get("/openapi.json").json()
        paths = openapi["paths"]
        assert "/api/weather/current" in paths
        assert "/api/weather/forecast" in paths
        assert "/api/weather/insights" in paths
        assert "/api/weather/health" in paths


class TestMarketEndpointsStillWork:
    """Smoke tests confirming Market Forecast functionality is intact."""

    def test_root_endpoint(self):
        response = test_client.get("/")
        assert response.status_code == 200
        assert "AgriNexus-AI" in response.json()["message"]

    def test_app_health_endpoint(self):
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_market_health_endpoint(self):
        response = test_client.get("/api/market/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "market_forecast"

    def test_market_current_still_works(self):
        response = test_client.get(
            "/api/market/current",
            params={"commodity": "NonExistentCommodity"},
        )
        # 404 (no data) proves the endpoint and DB path are operational
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_market_history_still_works(self):
        response = test_client.get(
            "/api/market/history",
            params={"commodity": "NonExistentCommodity"},
        )
        assert response.status_code == 200
        assert response.json() == []