/**
 * Types and interfaces for the Live Weather Telemetry Visualization Engine.
 */

export type VisualWeatherCondition =
  | 'CLEAR_DAY'
  | 'CLEAR_NIGHT'
  | 'PARTLY_CLOUDY_DAY'
  | 'PARTLY_CLOUDY_NIGHT'
  | 'CLOUDY'
  | 'OVERCAST'
  | 'DRIZZLE'
  | 'RAIN'
  | 'HEAVY_RAIN'
  | 'THUNDERSTORM'
  | 'SNOW'
  | 'HEAVY_SNOW'
  | 'FOG'
  | 'UNKNOWN';

export interface WeatherIntensityParameters {
  /** Scene type */
  scene: VisualWeatherCondition;
  /** Overall intensity from 0.0 to 1.0 */
  intensity: number;
  /** Cloud density from 0.0 to 1.0 */
  cloudDensity: number;
  /** Rain particle intensity from 0.0 to 1.0 */
  rainIntensity: number;
  /** Snow particle intensity from 0.0 to 1.0 */
  snowIntensity: number;
  /** Fog atmospheric opacity from 0.0 to 1.0 */
  fogIntensity: number;
  /** Wind strength index from 0.0 to 1.0 */
  windStrength: number;
  /** Wind direction angle in degrees (0 = North, 90 = East, etc.) */
  windDirection: number;
  /** Lightning probability per frame (0.0 to 1.0, rare WMO 95/96/99) */
  lightningProbability: number;
  /** Sun/Moon visual clarity from 0.0 to 1.0 */
  sunVisibility: number;
  /** General atmospheric haze/opacity */
  atmosphericOpacity: number;
}

export interface WeatherVisualizationState {
  condition: VisualWeatherCondition;
  weatherCode: number;
  isDay: boolean;
  temperature: number;
  apparentTemperature?: number;
  humidity: number;
  precipitation: number;
  cloudCover: number;
  windSpeed: number;
  windDirection: number;
  windGusts?: number;
  observationTime: string;
  dataAgeMinutes: number;
  isStale: boolean;
  locationName: string;
  latitude: number;
  longitude: number;
  intensity: WeatherIntensityParameters;
}
