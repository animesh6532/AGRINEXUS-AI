import { useState, useMemo } from 'react';
import { CurrentWeatherResponse, WeatherForecastResponse, HourlyForecastItem } from '../types/api';
import { WeatherVisualizationState } from '../types/weatherVisualization';
import { calculateWeatherIntensity } from '../utils/weatherIntensity';
import { mapWeatherCodeToVisualState } from '../utils/weatherCodeMapper';

interface UseWeatherVisualizationProps {
  current: CurrentWeatherResponse | null;
  forecast: WeatherForecastResponse | null;
  locationName: string;
}

export function useWeatherVisualization({
  current,
  forecast,
  locationName,
}: UseWeatherVisualizationProps) {
  const [selectedForecastHour, setSelectedForecastHour] = useState<HourlyForecastItem | null>(null);

  // Compute visualization state dynamically based on active selection (Current vs Hourly Forecast preview)
  const visualizationState = useMemo<WeatherVisualizationState | null>(() => {
    if (!current) return null;

    // Determine target telemetry: selected forecast hour preview or live current observation
    const activeTelemetry = selectedForecastHour || current;

    // Determine Day/Night status
    const isDay =
      activeTelemetry.is_day !== undefined
        ? Boolean(activeTelemetry.is_day)
        : (() => {
            if ('observation_time' in activeTelemetry && activeTelemetry.observation_time) {
              const hour = new Date(activeTelemetry.observation_time).getHours();
              return hour >= 6 && hour < 18;
            }
            if ('time' in activeTelemetry && activeTelemetry.time) {
              const hour = new Date(activeTelemetry.time).getHours();
              return hour >= 6 && hour < 18;
            }
            return true;
          })();

    const weatherCode = activeTelemetry.weather_code ?? 0;
    const condition = mapWeatherCodeToVisualState(weatherCode, isDay);

    const temperature = activeTelemetry.temperature ?? 0;
    const apparentTemperature = activeTelemetry.apparent_temperature;
    const humidity = activeTelemetry.relative_humidity ?? 0;
    const precipitation = activeTelemetry.precipitation ?? 0;
    const cloudCover = activeTelemetry.cloud_cover ?? (condition === 'OVERCAST' ? 95 : condition === 'PARTLY_CLOUDY_DAY' ? 40 : 10);
    const windSpeed = activeTelemetry.wind_speed ?? 0;
    const windDirection = activeTelemetry.wind_direction ?? ('wind_direction' in current ? current.wind_direction : 180);
    const windGusts = 'wind_gusts' in current ? current.wind_gusts : undefined;

    // Calculate intensity parameters
    const intensity = calculateWeatherIntensity({
      weatherCode,
      precipitation,
      cloudCover,
      windSpeed,
      windDirection,
      isDay,
    });

    // Calculate data freshness
    const obsTime = current.observation_time ? new Date(current.observation_time).getTime() : Date.now();
    const dataAgeMinutes = Math.max(0, Math.floor((Date.now() - obsTime) / (1000 * 60)));
    const isStale = dataAgeMinutes > 30; // Data older than 30 minutes marked stale

    return {
      condition,
      weatherCode,
      isDay,
      temperature,
      apparentTemperature,
      humidity,
      precipitation,
      cloudCover,
      windSpeed,
      windDirection,
      windGusts,
      observationTime: current.observation_time || new Date().toISOString(),
      dataAgeMinutes,
      isStale,
      locationName,
      latitude: current.latitude,
      longitude: current.longitude,
      intensity,
    };
  }, [current, forecast, selectedForecastHour, locationName]);

  const selectForecastHour = (item: HourlyForecastItem | null) => {
    setSelectedForecastHour(item);
  };

  const resetToCurrent = () => {
    setSelectedForecastHour(null);
  };

  return {
    visualizationState,
    selectedForecastHour,
    selectForecastHour,
    resetToCurrent,
  };
}
