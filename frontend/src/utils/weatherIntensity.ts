import { VisualWeatherCondition, WeatherIntensityParameters } from '../types/weatherVisualization';
import { mapWeatherCodeToVisualState } from './weatherCodeMapper';

interface CalculateIntensityInput {
  weatherCode?: number;
  precipitation?: number;
  cloudCover?: number;
  windSpeed?: number;
  windDirection?: number;
  isDay?: boolean;
}

/**
 * Calculates normalized (0.0 - 1.0) visualization parameters derived strictly from real telemetry data.
 */
export function calculateWeatherIntensity(
  input: CalculateIntensityInput
): WeatherIntensityParameters {
  const isDay = input.isDay !== undefined ? Boolean(input.isDay) : true;
  const weatherCode = input.weatherCode ?? 0;
  const scene = mapWeatherCodeToVisualState(weatherCode, isDay);
  const precipitation = Math.max(0, input.precipitation ?? 0);
  const windSpeed = Math.max(0, input.windSpeed ?? 0);
  const windDirection = input.windDirection ?? 180;

  // 1. Cloud Density (0.0 to 1.0)
  let cloudDensity = 0.1;
  if (input.cloudCover !== undefined && input.cloudCover !== null) {
    cloudDensity = Math.min(1, Math.max(0, input.cloudCover / 100));
  } else {
    switch (scene) {
      case 'CLEAR_DAY':
      case 'CLEAR_NIGHT':
        cloudDensity = 0.05;
        break;
      case 'PARTLY_CLOUDY_DAY':
      case 'PARTLY_CLOUDY_NIGHT':
        cloudDensity = 0.35;
        break;
      case 'CLOUDY':
        cloudDensity = 0.7;
        break;
      case 'OVERCAST':
        cloudDensity = 0.95;
        break;
      case 'DRIZZLE':
        cloudDensity = 0.75;
        break;
      case 'RAIN':
        cloudDensity = 0.85;
        break;
      case 'HEAVY_RAIN':
      case 'THUNDERSTORM':
        cloudDensity = 0.95;
        break;
      case 'SNOW':
        cloudDensity = 0.8;
        break;
      case 'HEAVY_SNOW':
        cloudDensity = 0.95;
        break;
      case 'FOG':
        cloudDensity = 0.65;
        break;
      default:
        cloudDensity = 0.2;
    }
  }

  // 2. Rain Particle Intensity (0.0 to 1.0)
  let rainIntensity = 0;
  if (
    scene === 'DRIZZLE' ||
    scene === 'RAIN' ||
    scene === 'HEAVY_RAIN' ||
    scene === 'THUNDERSTORM' ||
    precipitation > 0
  ) {
    if (precipitation > 0) {
      // Threshold mapping based on precipitation mm
      if (precipitation < 0.5) {
        rainIntensity = 0.15 + (precipitation / 0.5) * 0.15; // 0.15 - 0.30 (Light Drizzle/Rain)
      } else if (precipitation < 2.5) {
        rainIntensity = 0.30 + ((precipitation - 0.5) / 2.0) * 0.30; // 0.30 - 0.60 (Moderate Rain)
      } else if (precipitation < 10.0) {
        rainIntensity = 0.60 + ((precipitation - 2.5) / 7.5) * 0.25; // 0.60 - 0.85 (Heavy Rain)
      } else {
        rainIntensity = Math.min(1.0, 0.85 + (precipitation - 10.0) * 0.015); // 0.85 - 1.0 (Torrential)
      }
    } else {
      // Fallback code-driven default when precipitation is 0 but code indicates rain
      if (scene === 'DRIZZLE') rainIntensity = 0.2;
      else if (scene === 'RAIN') rainIntensity = 0.45;
      else if (scene === 'HEAVY_RAIN') rainIntensity = 0.8;
      else if (scene === 'THUNDERSTORM') rainIntensity = 0.9;
    }
  }

  // 3. Snow Particle Intensity (0.0 to 1.0)
  let snowIntensity = 0;
  if (scene === 'SNOW' || scene === 'HEAVY_SNOW') {
    if (precipitation > 0) {
      snowIntensity = Math.min(1.0, 0.3 + (precipitation / 5.0) * 0.7);
    } else {
      snowIntensity = scene === 'HEAVY_SNOW' ? 0.85 : 0.45;
    }
  }

  // 4. Fog Opacity (0.0 to 1.0)
  let fogIntensity = 0;
  if (scene === 'FOG') {
    fogIntensity = 0.75;
  } else if (cloudDensity > 0.85 && (scene === 'DRIZZLE' || scene === 'RAIN')) {
    fogIntensity = 0.25;
  }

  // 5. Wind Strength (0.0 to 1.0)
  // Mapping wind speed: 0 km/h -> 0, 15 km/h -> 0.3, 40 km/h -> 0.75, 70+ km/h -> 1.0
  const windStrength = Math.min(1.0, Math.max(0.05, windSpeed / 60.0));

  // 6. Lightning Probability (per frame trigger check)
  let lightningProbability = 0;
  if (scene === 'THUNDERSTORM') {
    lightningProbability = 0.008; // ~Once every 2-4 seconds at 60fps
  }

  // 7. Sun / Moon Visibility
  const sunVisibility = isDay
    ? Math.max(0, 1 - cloudDensity * 0.85 - fogIntensity * 0.7)
    : Math.max(0, 1 - cloudDensity * 0.7 - fogIntensity * 0.6);

  // 8. Overall Atmosphere Opacity
  const atmosphericOpacity = Math.min(
    1.0,
    0.2 + cloudDensity * 0.5 + fogIntensity * 0.3 + (scene === 'THUNDERSTORM' ? 0.2 : 0)
  );

  // Overall combined scene intensity score
  const intensity = Math.max(
    cloudDensity,
    rainIntensity,
    snowIntensity,
    fogIntensity,
    windStrength
  );

  return {
    scene,
    intensity,
    cloudDensity,
    rainIntensity,
    snowIntensity,
    fogIntensity,
    windStrength,
    windDirection,
    lightningProbability,
    sunVisibility,
    atmosphericOpacity,
  };
}
