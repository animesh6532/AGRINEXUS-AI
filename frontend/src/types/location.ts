export type LocationSource = 'device' | 'manual' | 'map' | 'unknown';

export type LocationPermissionState = 'granted' | 'prompt' | 'denied' | 'unavailable' | 'timeout';

export interface UserLocation {
  latitude: number;
  longitude: number;
  displayName: string;
  city?: string;
  locality?: string;
  district?: string;
  state?: string;
  country?: string;
  postalCode?: string;
  accuracy?: number;
  source: LocationSource;
  timestamp?: number;
}

export interface LocationSearchResult {
  id: string;
  displayName: string;
  primaryName: string;
  secondaryName: string;
  latitude: number;
  longitude: number;
  city?: string;
  locality?: string;
  district?: string;
  state?: string;
  country?: string;
  postalCode?: string;
}
