import { VisualWeatherCondition } from '../types/weatherVisualization';

export interface WeatherCodeDetails {
  condition: VisualWeatherCondition;
  label: string;
  description: string;
}

/**
 * Maps standard WMO Weather Interpretation Codes (0-99) to normalized VisualWeatherCondition.
 *
 * @param code WMO weather code from Open-Meteo
 * @param isDay Optional boolean flag indicating daylight (defaults to true if unknown)
 */
export function mapWeatherCodeToVisualState(
  code: number | undefined | null,
  isDay: boolean = true
): VisualWeatherCondition {
  if (code === undefined || code === null) {
    return 'UNKNOWN';
  }

  switch (code) {
    case 0: // Clear sky
      return isDay ? 'CLEAR_DAY' : 'CLEAR_NIGHT';

    case 1: // Mainly clear
    case 2: // Partly cloudy
      return isDay ? 'PARTLY_CLOUDY_DAY' : 'PARTLY_CLOUDY_NIGHT';

    case 3: // Overcast
      return 'OVERCAST';

    case 45: // Fog
    case 48: // Depositing rime fog
      return 'FOG';

    case 51: // Light drizzle
    case 53: // Moderate drizzle
    case 55: // Dense drizzle
    case 56: // Light freezing drizzle
    case 57: // Dense freezing drizzle
      return 'DRIZZLE';

    case 61: // Slight rain
    case 80: // Slight rain showers
      return 'RAIN';

    case 63: // Moderate rain
    case 65: // Heavy rain
    case 66: // Light freezing rain
    case 67: // Heavy freezing rain
    case 81: // Moderate rain showers
    case 82: // Violent rain showers
      return 'HEAVY_RAIN';

    case 71: // Slight snow fall
    case 73: // Moderate snow fall
    case 77: // Snow grains
    case 85: // Slight snow showers
      return 'SNOW';

    case 75: // Heavy snow fall
    case 86: // Heavy snow showers
      return 'HEAVY_SNOW';

    case 95: // Thunderstorm: Slight or moderate
    case 96: // Thunderstorm with slight hail
    case 99: // Thunderstorm with heavy hail
      return 'THUNDERSTORM';

    default:
      if (code >= 50 && code < 60) return 'DRIZZLE';
      if (code >= 60 && code < 70) return 'RAIN';
      if (code >= 70 && code < 80) return 'SNOW';
      if (code >= 80 && code < 90) return 'RAIN';
      if (code >= 90) return 'THUNDERSTORM';
      return isDay ? 'CLEAR_DAY' : 'CLEAR_NIGHT';
  }
}

/**
 * Returns human-readable label and meteorological description for a WMO weather code.
 */
export function getWeatherCodeDetails(
  code: number | undefined | null,
  isDay: boolean = true
): WeatherCodeDetails {
  const condition = mapWeatherCodeToVisualState(code, isDay);

  switch (code) {
    case 0:
      return { condition, label: 'Clear Sky', description: 'Sunny, clear conditions with unobstructed sunlight.' };
    case 1:
      return { condition, label: 'Mainly Clear', description: 'Mostly clear skies with brief localized light clouds.' };
    case 2:
      return { condition, label: 'Partly Cloudy', description: 'Scattered clouds with periods of clear sky.' };
    case 3:
      return { condition, label: 'Overcast', description: 'Dense, continuous cloud cover obscuring direct light.' };
    case 45:
    case 48:
      return { condition, label: 'Fog / Mist', description: 'Reduced visibility due to low-altitude atmospheric moisture.' };
    case 51:
    case 53:
    case 55:
      return { condition, label: 'Light Drizzle', description: 'Fine, light precipitation with high relative humidity.' };
    case 61:
    case 80:
      return { condition, label: 'Light Rain', description: 'Active rain showers; gentle surface accumulation.' };
    case 63:
    case 65:
    case 81:
    case 82:
      return { condition, label: 'Heavy Rainfall', description: 'Intense precipitation with active field runoff risk.' };
    case 71:
    case 73:
    case 75:
    case 77:
    case 85:
    case 86:
      return { condition, label: 'Snowfall', description: 'Cold atmospheric precipitation and snow accumulation.' };
    case 95:
    case 96:
    case 99:
      return { condition, label: 'Thunderstorm', description: 'Severe convection with electrical discharges and heavy rain.' };
    default:
      return { condition, label: 'Observed Telemetry', description: 'Real-time observation telemetry from Open-Meteo.' };
  }
}
