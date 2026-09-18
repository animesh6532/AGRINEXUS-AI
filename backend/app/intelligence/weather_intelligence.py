"""
Weather intelligence layer for the Weather Intelligence module.

Derives deterministic, explainable weather insights from normalized
Open-Meteo data using fixed threshold rules.

IMPORTANT SCOPE NOTE:
This is NOT an ML model. It is a rule-based signal layer describing
weather conditions and their direct weather implications (rain, heat,
wind, humidity, field-operation disruption). It does NOT perform crop
recommendation, soil analysis, disease detection, pest prediction,
fertilizer recommendation, irrigation prediction, or yield prediction;
those belong to other modules.
"""

from typing import Any, Dict, List, Optional

from ..core.logging import logger


class WeatherIntelligence:
    """
    Rule-based weather intelligence.

    Every insight is derived from an explicit, documented threshold so the
    result is deterministic and explainable. Missing input values simply
    produce no insight - nothing is fabricated.
    """

    # ---- Current-weather thresholds -------------------------------------
    FREEZING_TEMPERATURE_C = 0.0        # at or below -> freezing_conditions
    LOW_TEMPERATURE_C = 5.0             # at or below -> low_temperature
    HIGH_TEMPERATURE_C = 35.0           # at or above -> high_temperature
    EXTREME_HEAT_C = 40.0               # at or above -> extreme_heat

    VERY_HIGH_HUMIDITY_PCT = 90.0       # at or above -> very_high_humidity
    LOW_HUMIDITY_PCT = 30.0             # at or below -> low_humidity

    HEAVY_RAIN_MM = 20.0                # at or above -> heavy_rain
    MODERATE_RAIN_MM = 10.0             # at or above -> moderate_rain
    LIGHT_RAIN_MM = 2.5                 # at or above -> light_rain

    STRONG_WIND_KMH = 50.0              # at or above -> strong_wind
    MODERATE_WIND_KMH = 30.0            # at or above -> moderate_wind

    DRY_CONDITIONS_MAX_HUMIDITY_PCT = 40.0

    # WMO weather interpretation codes of interest
    THUNDERSTORM_CODES = {95, 96, 99}
    RAIN_SHOWER_CODES = {61, 63, 65, 66, 67, 80, 81, 82}
    FOG_CODES = {45, 48}

    # ---- Forecast thresholds --------------------------------------------
    DRY_SPELL_MIN_DAYS = 3              # consecutive days with < 1 mm
    DRY_DAY_MAX_MM = 1.0

    def __init__(self):
        logger.debug("Initialized WeatherIntelligence service")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _insight(
        insight_type: str,
        severity: str,
        title: str,
        description: str,
        relevant_value: Optional[float],
        threshold_used: Optional[float],
        timestamp: Optional[str],
    ) -> Dict[str, Any]:
        """Build a normalized insight dictionary."""
        return {
            "type": insight_type,
            "severity": severity,
            "title": title,
            "description": description,
            "relevant_value": (
                float(relevant_value) if relevant_value is not None else None
            ),
            "threshold_used": (
                float(threshold_used) if threshold_used is not None else None
            ),
            "timestamp": timestamp,
        }

    @staticmethod
    def _severity_order(severity: str) -> int:
        """Sort key: high first, then medium, then low."""
        return {"high": 0, "medium": 1, "low": 2}.get(severity, 3)


    # ------------------------------------------------------------------
    # Current weather analysis
    # ------------------------------------------------------------------
    def analyze_current_weather(
        self, current_weather: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Derive insights from normalized current weather data.

        Args:
            current_weather: Normalized current weather dictionary from the
                weather service

        Returns:
            List of weather insight dictionaries (may be empty)
        """
        insights: List[Dict[str, Any]] = []

        try:
            temperature = current_weather.get("temperature")
            relative_humidity = current_weather.get("relative_humidity")
            precipitation = current_weather.get("precipitation")
            wind_speed = current_weather.get("wind_speed")
            weather_code = current_weather.get("weather_code")
            observation_time = current_weather.get("observation_time")

            # Temperature insights
            if temperature is not None:
                if temperature <= self.FREEZING_TEMPERATURE_C:
                    insights.append(self._insight(
                        "freezing_conditions", "high",
                        "Freezing Conditions",
                        f"Freezing temperatures observed "
                        f"({temperature:.1f} degrees C). Frost may form on "
                        f"exposed surfaces.",
                        temperature, self.FREEZING_TEMPERATURE_C,
                        observation_time,
                    ))
                elif temperature <= self.LOW_TEMPERATURE_C:
                    insights.append(self._insight(
                        "low_temperature", "medium",
                        "Low Temperature",
                        f"Low temperatures observed ({temperature:.1f} "
                        f"degrees C). Conditions are near freezing.",
                        temperature, self.LOW_TEMPERATURE_C,
                        observation_time,
                    ))
                elif temperature >= self.EXTREME_HEAT_C:
                    insights.append(self._insight(
                        "extreme_heat", "high",
                        "Extreme Heat",
                        f"Extreme heat observed ({temperature:.1f} degrees "
                        f"C). Heat stress conditions are present.",
                        temperature, self.EXTREME_HEAT_C,
                        observation_time,
                    ))
                elif temperature >= self.HIGH_TEMPERATURE_C:
                    insights.append(self._insight(
                        "high_temperature", "medium",
                        "High Temperature",
                        f"High temperatures observed ({temperature:.1f} "
                        f"degrees C). Hot conditions may persist through "
                        f"the day.",
                        temperature, self.HIGH_TEMPERATURE_C,
                        observation_time,
                    ))

            # Humidity insights
            if relative_humidity is not None:
                if relative_humidity >= self.VERY_HIGH_HUMIDITY_PCT:
                    insights.append(self._insight(
                        "very_high_humidity", "medium",
                        "Very High Humidity",
                        f"Very high humidity observed "
                        f"({relative_humidity:.0f}%). Surfaces may remain "
                        f"wet for extended periods.",
                        relative_humidity, self.VERY_HIGH_HUMIDITY_PCT,
                        observation_time,
                    ))
                elif relative_humidity <= self.LOW_HUMIDITY_PCT:
                    insights.append(self._insight(
                        "low_humidity", "low",
                        "Low Humidity",
                        f"Low humidity observed "
                        f"({relative_humidity:.0f}%). Air is very dry and "
                        f"evaporation rates are elevated.",
                        relative_humidity, self.LOW_HUMIDITY_PCT,
                        observation_time,
                    ))


            # Precipitation insights
            if precipitation is not None:
                if precipitation >= self.HEAVY_RAIN_MM:
                    insights.append(self._insight(
                        "heavy_rain", "high",
                        "Heavy Rain",
                        f"Heavy precipitation observed "
                        f"({precipitation:.1f} mm). Field operations may be "
                        f"affected.",
                        precipitation, self.HEAVY_RAIN_MM,
                        observation_time,
                    ))
                elif precipitation >= self.MODERATE_RAIN_MM:
                    insights.append(self._insight(
                        "moderate_rain", "medium",
                        "Moderate Rain",
                        f"Moderate precipitation observed "
                        f"({precipitation:.1f} mm). Field operations may "
                        f"need to be rescheduled.",
                        precipitation, self.MODERATE_RAIN_MM,
                        observation_time,
                    ))
                elif precipitation >= self.LIGHT_RAIN_MM:
                    insights.append(self._insight(
                        "light_rain", "low",
                        "Light Rain",
                        f"Light precipitation observed "
                        f"({precipitation:.1f} mm).",
                        precipitation, self.LIGHT_RAIN_MM,
                        observation_time,
                    ))
                elif (
                    precipitation <= 0.0
                    and relative_humidity is not None
                    and relative_humidity <= self.DRY_CONDITIONS_MAX_HUMIDITY_PCT
                ):
                    insights.append(self._insight(
                        "dry_conditions", "medium",
                        "Dry Conditions",
                        f"No precipitation and low humidity "
                        f"({relative_humidity:.0f}%). Dry conditions "
                        f"prevail.",
                        relative_humidity,
                        self.DRY_CONDITIONS_MAX_HUMIDITY_PCT,
                        observation_time,
                    ))

            # Wind insights
            if wind_speed is not None:
                if wind_speed >= self.STRONG_WIND_KMH:
                    insights.append(self._insight(
                        "strong_wind", "high",
                        "Strong Wind",
                        f"Strong winds observed ({wind_speed:.1f} km/h). "
                        f"Field operations may be disrupted.",
                        wind_speed, self.STRONG_WIND_KMH,
                        observation_time,
                    ))
                elif wind_speed >= self.MODERATE_WIND_KMH:
                    insights.append(self._insight(
                        "moderate_wind", "medium",
                        "Moderate Wind",
                        f"Moderate winds observed ({wind_speed:.1f} km/h). "
                        f"Spray operations may drift at this wind speed.",
                        wind_speed, self.MODERATE_WIND_KMH,
                        observation_time,
                    ))


            # Weather-code insights (WMO codes)
            if weather_code is not None:
                if weather_code in self.THUNDERSTORM_CODES:
                    insights.append(self._insight(
                        "thunderstorm", "high",
                        "Thunderstorm",
                        "Thunderstorm conditions observed. Field "
                        "operations should be paused until conditions "
                        "improve.",
                        float(weather_code), 95.0,
                        observation_time,
                    ))
                elif weather_code in self.RAIN_SHOWER_CODES:
                    insights.append(self._insight(
                        "rain_showers", "medium",
                        "Rain Showers",
                        "Rain shower conditions observed. Intermittent "
                        "precipitation is likely.",
                        float(weather_code), 61.0,
                        observation_time,
                    ))
                elif weather_code in self.FOG_CODES:
                    insights.append(self._insight(
                        "fog", "low",
                        "Fog",
                        "Fog observed. Visibility may be reduced for "
                        "field operations.",
                        float(weather_code), 45.0,
                        observation_time,
                    ))

            # Field-operation disruption signal (derived from the above)
            triggered_types = {i["type"] for i in insights}
            if triggered_types & {
                "heavy_rain", "strong_wind", "thunderstorm"
            }:
                insights.append(self._insight(
                    "field_operations_disruption", "high",
                    "Field Operations May Be Disrupted",
                    "Current conditions (heavy precipitation, strong "
                    "wind, or thunderstorm) may disrupt field operations.",
                    None, None, observation_time,
                ))

        except Exception as e:
            logger.error(f"Error analyzing current weather: {e}")
            return []

        return insights


    # ------------------------------------------------------------------
    # Forecast analysis
    # ------------------------------------------------------------------
    def analyze_forecast_weather(
        self, forecast_weather: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Derive insights from normalized forecast data (daily aggregates).

        Args:
            forecast_weather: Normalized forecast dictionary from the
                weather service

        Returns:
            List of weather insight dictionaries (may be empty)
        """
        insights: List[Dict[str, Any]] = []

        try:
            daily_forecast = forecast_weather.get("daily_forecast") or []
            forecast_days = forecast_weather.get("forecast_days", 0)
            period_label = f"forecast period ({forecast_days} days)"

            if not daily_forecast:
                return insights

            # Precipitation forecast insights
            max_precip_day = max(
                daily_forecast,
                key=lambda d: d.get("precipitation_sum") or 0.0,
            )
            max_precip = max_precip_day.get("precipitation_sum")
            if max_precip is not None:
                if max_precip >= self.HEAVY_RAIN_MM:
                    insights.append(self._insight(
                        "heavy_rain_forecast", "high",
                        "Heavy Rain Expected",
                        f"Heavy precipitation is forecast "
                        f"({max_precip:.1f} mm on "
                        f"{max_precip_day.get('date')}). Field operations "
                        f"may be affected.",
                        max_precip, self.HEAVY_RAIN_MM,
                        max_precip_day.get("date"),
                    ))
                elif max_precip >= self.MODERATE_RAIN_MM:
                    insights.append(self._insight(
                        "moderate_rain_forecast", "medium",
                        "Moderate Rain Expected",
                        f"Moderate precipitation is forecast "
                        f"({max_precip:.1f} mm on "
                        f"{max_precip_day.get('date')}). Field operations "
                        f"may need to be rescheduled.",
                        max_precip, self.MODERATE_RAIN_MM,
                        max_precip_day.get("date"),
                    ))

            # Precipitation opportunity
            rain_days = [
                day for day in daily_forecast
                if (day.get("precipitation_sum") or 0.0) >= self.LIGHT_RAIN_MM
            ]
            if rain_days:
                first_rain_day = rain_days[0]
                insights.append(self._insight(
                    "precipitation_opportunity", "low",
                    "Precipitation Expected",
                    f"Natural precipitation is forecast on "
                    f"{first_rain_day.get('date')} "
                    f"({first_rain_day.get('precipitation_sum') or 0:.1f} "
                    f"mm expected).",
                    first_rain_day.get("precipitation_sum"),
                    self.LIGHT_RAIN_MM,
                    first_rain_day.get("date"),
                ))


            # Temperature extremes in forecast
            max_temp = max(
                (day.get("temperature_max") for day in daily_forecast
                 if day.get("temperature_max") is not None),
                default=None,
            )
            min_temp = min(
                (day.get("temperature_min") for day in daily_forecast
                 if day.get("temperature_min") is not None),
                default=None,
            )

            if max_temp is not None:
                if max_temp >= self.EXTREME_HEAT_C:
                    insights.append(self._insight(
                        "extreme_heat_forecast", "high",
                        "Extreme Heat Expected",
                        f"Extreme heat is forecast (up to {max_temp:.1f} "
                        f"degrees C) within the {period_label}.",
                        max_temp, self.EXTREME_HEAT_C, period_label,
                    ))
                elif max_temp >= self.HIGH_TEMPERATURE_C:
                    insights.append(self._insight(
                        "high_temperature_forecast", "medium",
                        "High Temperature Expected",
                        f"High temperatures are forecast (up to "
                        f"{max_temp:.1f} degrees C) within the "
                        f"{period_label}.",
                        max_temp, self.HIGH_TEMPERATURE_C, period_label,
                    ))

            if min_temp is not None:
                if min_temp <= self.FREEZING_TEMPERATURE_C:
                    insights.append(self._insight(
                        "freezing_conditions_forecast", "high",
                        "Freezing Conditions Expected",
                        f"Freezing temperatures are forecast (down to "
                        f"{min_temp:.1f} degrees C) within the "
                        f"{period_label}. Frost may form.",
                        min_temp, self.FREEZING_TEMPERATURE_C,
                        period_label,
                    ))
                elif min_temp <= self.LOW_TEMPERATURE_C:
                    insights.append(self._insight(
                        "low_temperature_forecast", "medium",
                        "Low Temperature Expected",
                        f"Low temperatures are forecast (down to "
                        f"{min_temp:.1f} degrees C) within the "
                        f"{period_label}.",
                        min_temp, self.LOW_TEMPERATURE_C, period_label,
                    ))

            # Wind forecast insights
            max_wind = max(
                (day.get("wind_speed_max") for day in daily_forecast
                 if day.get("wind_speed_max") is not None),
                default=None,
            )
            if max_wind is not None:
                if max_wind >= self.STRONG_WIND_KMH:
                    insights.append(self._insight(
                        "strong_wind_forecast", "high",
                        "Strong Wind Expected",
                        f"Strong winds are forecast (up to "
                        f"{max_wind:.1f} km/h) within the {period_label}. "
                        f"Field operations may be disrupted.",
                        max_wind, self.STRONG_WIND_KMH, period_label,
                    ))
                elif max_wind >= self.MODERATE_WIND_KMH:
                    insights.append(self._insight(
                        "moderate_wind_forecast", "medium",
                        "Moderate Wind Expected",
                        f"Moderate winds are forecast (up to "
                        f"{max_wind:.1f} km/h) within the {period_label}.",
                        max_wind, self.MODERATE_WIND_KMH, period_label,
                    ))


            # Dry spell detection (consecutive days with < DRY_DAY_MAX_MM)
            dry_spell_days = 0
            for day in daily_forecast:
                precip = day.get("precipitation_sum")
                if precip is None or precip < self.DRY_DAY_MAX_MM:
                    dry_spell_days += 1
                else:
                    break
            if dry_spell_days >= self.DRY_SPELL_MIN_DAYS:
                insights.append(self._insight(
                    "dry_spell_forecast", "medium",
                    "Dry Spell Expected",
                    f"{dry_spell_days} consecutive days with minimal "
                    f"precipitation (<{self.DRY_DAY_MAX_MM:.0f} mm) are "
                    f"forecast.",
                    float(dry_spell_days), self.DRY_SPELL_MIN_DAYS,
                    period_label,
                ))

            # Field-operation disruption signal for the forecast window
            triggered_types = {i["type"] for i in insights}
            if triggered_types & {
                "heavy_rain_forecast", "strong_wind_forecast"
            }:
                insights.append(self._insight(
                    "field_operations_disruption_forecast", "medium",
                    "Field Operations May Be Disrupted",
                    f"Forecast conditions (heavy precipitation or strong "
                    f"wind) may disrupt field operations during the "
                    f"{period_label}.",
                    None, None, period_label,
                ))

        except Exception as e:
            logger.error(f"Error analyzing forecast weather: {e}")
            return []

        return insights

    # ------------------------------------------------------------------
    # Combined insights
    # ------------------------------------------------------------------
    def get_weather_insights(
        self,
        current_weather: Optional[Dict[str, Any]] = None,
        forecast_weather: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Combine current-weather and forecast insights.

        Args:
            current_weather: Normalized current weather data (optional)
            forecast_weather: Normalized forecast data (optional)

        Returns:
            Insights sorted by severity (high first), then by type
        """
        insights: List[Dict[str, Any]] = []

        if current_weather:
            insights.extend(self.analyze_current_weather(current_weather))
        if forecast_weather:
            insights.extend(self.analyze_forecast_weather(forecast_weather))

        insights.sort(
            key=lambda i: (
                self._severity_order(i.get("severity", "low")),
                i.get("type", ""),
            )
        )
        return insights