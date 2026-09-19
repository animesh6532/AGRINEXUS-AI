"""
Test the weather intelligence layer (rule-based, deterministic).

These tests exercise the threshold rules directly with fixture data;
they do not perform any network access.
"""

import pytest

from app.intelligence.weather_intelligence import WeatherIntelligence


@pytest.fixture
def intel():
    """Create a weather intelligence instance for testing."""
    return WeatherIntelligence()


BENIGN_CURRENT = {
    "temperature": 22.0,
    "relative_humidity": 55.0,
    "precipitation": 0.0,
    "wind_speed": 8.0,
    "weather_code": 1,
    "observation_time": "2026-09-18T10:30",
}


def _types(insights):
    return {i["type"] for i in insights}


class TestCurrentWeatherRules:
    """Tests for insights derived from current weather."""

    def test_extreme_heat(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "temperature": 42.0,
        })
        heat = next(i for i in insights if i["type"] == "extreme_heat")
        assert heat["severity"] == "high"
        assert heat["relevant_value"] == 42.0
        assert heat["threshold_used"] == 40.0
        assert heat["timestamp"] == BENIGN_CURRENT["observation_time"]

    def test_high_temperature(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "temperature": 36.0,
        })
        heat = next(i for i in insights if i["type"] == "high_temperature")
        assert heat["severity"] == "medium"
        assert heat["relevant_value"] == 36.0
        assert heat["threshold_used"] == 35.0

    def test_freezing_conditions(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "temperature": -2.0,
        })
        freezing = next(
            i for i in insights if i["type"] == "freezing_conditions"
        )
        assert freezing["severity"] == "high"
        assert freezing["relevant_value"] == -2.0
        assert freezing["threshold_used"] == 0.0

    def test_low_temperature(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "temperature": 3.0,
        })
        low = next(i for i in insights if i["type"] == "low_temperature")
        assert low["severity"] == "medium"
        assert low["threshold_used"] == 5.0

    def test_very_high_humidity(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "relative_humidity": 92.0,
        })
        humidity = next(
            i for i in insights if i["type"] == "very_high_humidity"
        )
        assert humidity["severity"] == "medium"
        assert humidity["threshold_used"] == 90.0

    def test_low_humidity(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "relative_humidity": 25.0,
        })
        humidity = next(i for i in insights if i["type"] == "low_humidity")
        assert humidity["severity"] == "low"
        assert humidity["threshold_used"] == 30.0

    def test_heavy_rain_and_disruption(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "precipitation": 25.0,
        })
        rain = next(i for i in insights if i["type"] == "heavy_rain")
        assert rain["severity"] == "high"
        assert rain["threshold_used"] == 20.0
        assert "field_operations_disruption" in _types(insights)

    def test_moderate_rain(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "precipitation": 12.0,
        })
        rain = next(i for i in insights if i["type"] == "moderate_rain")
        assert rain["severity"] == "medium"
        assert rain["threshold_used"] == 10.0

    def test_light_rain(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "precipitation": 4.0,
        })
        rain = next(i for i in insights if i["type"] == "light_rain")
        assert rain["severity"] == "low"
        assert rain["threshold_used"] == 2.5


    def test_dry_conditions(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "precipitation": 0.0, "relative_humidity": 30.0,
        })
        dry = next(i for i in insights if i["type"] == "dry_conditions")
        assert dry["severity"] == "medium"
        assert dry["relevant_value"] == 30.0

    def test_strong_wind_and_disruption(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "wind_speed": 55.0,
        })
        wind = next(i for i in insights if i["type"] == "strong_wind")
        assert wind["severity"] == "high"
        assert wind["threshold_used"] == 50.0
        assert "field_operations_disruption" in _types(insights)

    def test_moderate_wind(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "wind_speed": 35.0,
        })
        wind = next(i for i in insights if i["type"] == "moderate_wind")
        assert wind["severity"] == "medium"
        assert wind["threshold_used"] == 30.0

    def test_thunderstorm_code(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "weather_code": 95,
        })
        storm = next(i for i in insights if i["type"] == "thunderstorm")
        assert storm["severity"] == "high"
        assert "field_operations_disruption" in _types(insights)

    def test_fog_code(self, intel):
        insights = intel.analyze_current_weather({
            **BENIGN_CURRENT, "weather_code": 45,
        })
        fog = next(i for i in insights if i["type"] == "fog")
        assert fog["severity"] == "low"
        assert "field_operations_disruption" not in _types(insights)

    def test_benign_conditions_produce_no_insights(self, intel):
        insights = intel.analyze_current_weather(BENIGN_CURRENT)
        assert insights == []

    def test_missing_data_produces_no_insights(self, intel):
        assert intel.analyze_current_weather({}) == []
        assert intel.analyze_current_weather({"temperature": None}) == []


def _day(date_str, precip=0.0, tmax=28.0, tmin=18.0, wind=10.0, code=1):
    """Build a daily forecast entry for tests."""
    return {
        "date": date_str,
        "temperature_max": tmax,
        "temperature_min": tmin,
        "precipitation_sum": precip,
        "precipitation_probability_max": 40,
        "wind_speed_max": wind,
        "weather_code": code,
        "sunrise": None,
        "sunset": None,
    }


class TestForecastRules:
    """Tests for insights derived from forecast data."""

    def test_heavy_rain_forecast(self, intel):
        forecast = {
            "forecast_days": 3,
            "daily_forecast": [
                _day("2026-09-18", precip=1.0),
                _day("2026-09-19", precip=25.0),
                _day("2026-09-20", precip=0.0),
            ],
        }
        insights = intel.analyze_forecast_weather(forecast)
        rain = next(
            i for i in insights if i["type"] == "heavy_rain_forecast"
        )
        assert rain["severity"] == "high"
        assert rain["relevant_value"] == 25.0
        assert rain["timestamp"] == "2026-09-19"
        assert "field_operations_disruption_forecast" in _types(insights)

    def test_moderate_rain_forecast(self, intel):
        forecast = {
            "forecast_days": 2,
            "daily_forecast": [
                _day("2026-09-18", precip=12.0),
                _day("2026-09-19", precip=0.0),
            ],
        }
        insights = intel.analyze_forecast_weather(forecast)
        rain = next(
            i for i in insights if i["type"] == "moderate_rain_forecast"
        )
        assert rain["severity"] == "medium"
        assert rain["threshold_used"] == 10.0

    def test_precipitation_opportunity(self, intel):
        forecast = {
            "forecast_days": 2,
            "daily_forecast": [
                _day("2026-09-18", precip=0.0),
                _day("2026-09-19", precip=4.0),
            ],
        }
        insights = intel.analyze_forecast_weather(forecast)
        opp = next(
            i for i in insights if i["type"] == "precipitation_opportunity"
        )
        assert opp["severity"] == "low"
        assert opp["timestamp"] == "2026-09-19"


    def test_extreme_heat_forecast(self, intel):
        forecast = {
            "forecast_days": 2,
            "daily_forecast": [
                _day("2026-09-18", precip=1.5, tmax=41.0),
                _day("2026-09-19", precip=1.5, tmax=30.0),
            ],
        }
        insights = intel.analyze_forecast_weather(forecast)
        heat = next(
            i for i in insights if i["type"] == "extreme_heat_forecast"
        )
        assert heat["severity"] == "high"
        assert heat["relevant_value"] == 41.0

    def test_freezing_forecast(self, intel):
        forecast = {
            "forecast_days": 2,
            "daily_forecast": [
                _day("2026-09-18", precip=1.5, tmin=-3.0),
                _day("2026-09-19", precip=1.5, tmin=0.0),
            ],
        }
        insights = intel.analyze_forecast_weather(forecast)
        freezing = next(
            i for i in insights
            if i["type"] == "freezing_conditions_forecast"
        )
        assert freezing["severity"] == "high"
        assert freezing["relevant_value"] == -3.0

    def test_strong_wind_forecast(self, intel):
        forecast = {
            "forecast_days": 2,
            "daily_forecast": [
                _day("2026-09-18", precip=1.5, wind=60.0),
                _day("2026-09-19", precip=1.5, wind=12.0),
            ],
        }
        insights = intel.analyze_forecast_weather(forecast)
        wind = next(
            i for i in insights if i["type"] == "strong_wind_forecast"
        )
        assert wind["severity"] == "high"
        assert wind["threshold_used"] == 50.0
        assert "field_operations_disruption_forecast" in _types(insights)

    def test_dry_spell_forecast(self, intel):
        forecast = {
            "forecast_days": 4,
            "daily_forecast": [
                _day("2026-09-18", precip=0.0),
                _day("2026-09-19", precip=0.2),
                _day("2026-09-20", precip=0.0),
                _day("2026-09-21", precip=6.0),
            ],
        }
        insights = intel.analyze_forecast_weather(forecast)
        dry = next(i for i in insights if i["type"] == "dry_spell_forecast")
        assert dry["severity"] == "medium"
        assert dry["relevant_value"] == 3.0

    def test_benign_forecast_produces_no_insights(self, intel):
        forecast = {
            "forecast_days": 3,
            "daily_forecast": [
                _day(f"2026-09-{day}", precip=1.5, tmax=30.0, tmin=20.0,
                     wind=15.0)
                for day in (18, 19, 20)
            ],
        }
        assert intel.analyze_forecast_weather(forecast) == []

    def test_empty_forecast_produces_no_insights(self, intel):
        assert intel.analyze_forecast_weather({}) == []
        assert intel.analyze_forecast_weather({"daily_forecast": []}) == []


class TestCombinedInsights:
    """Tests for the combined insight entry point."""

    def test_combines_current_and_forecast(self, intel):
        current = {**BENIGN_CURRENT, "temperature": 41.0}
        forecast = {
            "forecast_days": 2,
            "daily_forecast": [
                _day("2026-09-19", precip=25.0),
                _day("2026-09-20", precip=1.5),
            ],
        }
        insights = intel.get_weather_insights(
            current_weather=current, forecast_weather=forecast
        )

        types_found = _types(insights)
        assert "extreme_heat" in types_found
        assert "heavy_rain_forecast" in types_found

    def test_insights_sorted_by_severity(self, intel):
        current = {
            **BENIGN_CURRENT,
            "temperature": 36.0,       # medium
            "wind_speed": 55.0,        # high
            "relative_humidity": 25.0,  # low
        }
        insights = intel.get_weather_insights(current_weather=current)
        severities = [i["severity"] for i in insights]
        assert severities[0] == "high"
        assert severities.index("medium") < severities.index("low")

    def test_no_data_returns_empty(self, intel):
        assert intel.get_weather_insights() == []