import { UserLocation, LocationSearchResult, LocationSource } from '../types/location';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';

let currentSessionToken: string = '';

function getSearchSessionToken(): string {
  if (!currentSessionToken) {
    currentSessionToken = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  }
  return currentSessionToken;
}

export function resetSearchSessionToken(): void {
  currentSessionToken = '';
}

/**
 * Service providing Geolocation API, Reverse Geocoding, Mapbox Search Box, and Nominatim search capabilities.
 */
export const locationService = {
  /**
   * One-time acquisition of device coordinates using browser Geolocation API.
   */
  async getCurrentDeviceLocation(): Promise<{ latitude: number; longitude: number; accuracy?: number }> {
    if (typeof window === 'undefined' || !navigator || !navigator.geolocation) {
      throw new Error('Location services are not supported by this browser.');
    }

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          });
        },
        (error) => {
          switch (error.code) {
            case error.PERMISSION_DENIED:
              reject(new Error('Location access is blocked. You can still search for your location manually.'));
              break;
            case error.POSITION_UNAVAILABLE:
              reject(new Error('Device location information is currently unavailable.'));
              break;
            case error.TIMEOUT:
              reject(new Error('Location acquisition request timed out. Please try again.'));
              break;
            default:
              reject(new Error('An unexpected error occurred while requesting device location.'));
              break;
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 15000,
          maximumAge: 300000,
        }
      );
    });
  },

  /**
   * Searches location suggestions using Mapbox Search Box /suggest endpoint or Nominatim fallback.
   */
  async searchLocations(query: string, signal?: AbortSignal): Promise<LocationSearchResult[]> {
    if (!query || query.trim().length < 2) return [];

    const cleanQuery = query.trim();
    const sessionToken = getSearchSessionToken();

    try {
      if (MAPBOX_TOKEN) {
        // 1. Try Mapbox Search Box /suggest API
        const suggestUrl = `https://api.mapbox.com/search/searchbox/v1/suggest?q=${encodeURIComponent(
          cleanQuery
        )}&access_token=${MAPBOX_TOKEN}&session_token=${sessionToken}&language=en&limit=6`;

        const response = await fetch(suggestUrl, { signal });
        if (response.ok) {
          const data = await response.json();
          if (data.suggestions && data.suggestions.length > 0) {
            return data.suggestions.map((s: any) => {
              const primaryName = s.name || s.name_preferred || cleanQuery;
              const secondaryName = s.place_formatted || s.full_address || '';
              return {
                id: s.mapbox_id || Math.random().toString(),
                displayName: secondaryName ? `${primaryName}, ${secondaryName}` : primaryName,
                primaryName,
                secondaryName,
                mapboxId: s.mapbox_id,
              };
            });
          }
        }

        // 2. Fallback to Mapbox Geocoding v5 if Search Box yields no items
        const geocodeUrl = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(
          cleanQuery
        )}.json?access_token=${MAPBOX_TOKEN}&autocomplete=true&limit=6`;
        const geoRes = await fetch(geocodeUrl, { signal });
        if (geoRes.ok) {
          const geoData = await geoRes.json();
          if (geoData.features && geoData.features.length > 0) {
            return geoData.features.map((f: any) => {
              const coords = f.geometry?.coordinates || [0, 0];
              const primaryName = f.text || f.place_name;
              const secondaryName = f.place_name.replace(`${primaryName}, `, '');

              return {
                id: f.id,
                displayName: f.place_name,
                primaryName,
                secondaryName: secondaryName !== primaryName ? secondaryName : '',
                latitude: coords[1],
                longitude: coords[0],
              };
            });
          }
        }
      }

      // 3. Fallback to OpenStreetMap Nominatim API
      const nominatimUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
        cleanQuery
      )}&addressdetails=1&limit=6`;
      const response = await fetch(nominatimUrl, {
        headers: { 'Accept-Language': 'en' },
        signal,
      });

      if (!response.ok) return [];

      const data = await response.json();
      return (data || []).map((item: any) => {
        const addr = item.address || {};
        const city = addr.city || addr.town || addr.village || addr.municipality || addr.suburb;
        const district = addr.state_district || addr.county || addr.district || city;
        const state = addr.state;
        const country = addr.country;

        const primaryName = city || item.display_name.split(',')[0];
        const parts = [district, state, country].filter((p) => p && p !== primaryName);
        const secondaryName = parts.join(', ');

        return {
          id: String(item.place_id),
          displayName: item.display_name,
          primaryName,
          secondaryName,
          latitude: parseFloat(item.lat),
          longitude: parseFloat(item.lon),
          city,
          district,
          state,
          country,
          postalCode: addr.postcode,
        };
      });
    } catch (err: any) {
      if (err.name === 'AbortError') throw err;
      return [];
    }
  },

  /**
   * Retrieves full feature coordinates for a Mapbox Search Box suggestion using mapbox_id.
   */
  async retrieveLocation(result: LocationSearchResult): Promise<UserLocation> {
    const sessionToken = getSearchSessionToken();

    // If result already has latitude & longitude (from Nominatim or Geocoding v5)
    if (typeof result.latitude === 'number' && typeof result.longitude === 'number') {
      const geocoded = await this.reverseGeocode(result.latitude, result.longitude);
      resetSearchSessionToken();
      return {
        latitude: result.latitude,
        longitude: result.longitude,
        displayName: result.displayName || geocoded.displayName || result.primaryName,
        city: result.city || geocoded.city || result.primaryName,
        locality: geocoded.locality,
        district: result.district || geocoded.district,
        state: result.state || geocoded.state,
        country: result.country || geocoded.country,
        postalCode: result.postalCode || geocoded.postalCode,
        source: 'search',
        timestamp: Date.now(),
      };
    }

    // Call Mapbox Search Box /retrieve API using mapboxId
    if (result.mapboxId && MAPBOX_TOKEN) {
      try {
        const url = `https://api.mapbox.com/search/searchbox/v1/retrieve/${
          result.mapboxId
        }?access_token=${MAPBOX_TOKEN}&session_token=${sessionToken}`;
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          if (data.features && data.features.length > 0) {
            const feat = data.features[0];
            const coords = feat.geometry?.coordinates || [0, 0];
            const props = feat.properties || {};

            const latitude = coords[1];
            const longitude = coords[0];

            resetSearchSessionToken();

            // Reverse geocode to ensure complete address components
            const geocoded = await this.reverseGeocode(latitude, longitude);

            return {
              latitude,
              longitude,
              displayName: props.full_address || props.name || result.displayName,
              city: props.context?.place?.name || props.context?.locality?.name || geocoded.city || result.primaryName,
              locality: props.context?.neighborhood?.name || props.context?.locality?.name || geocoded.locality,
              district: props.context?.district?.name || geocoded.district,
              state: props.context?.region?.name || geocoded.state,
              country: props.context?.country?.name || geocoded.country,
              postalCode: props.context?.postcode?.name || geocoded.postalCode,
              source: 'search',
              timestamp: Date.now(),
            };
          }
        }
      } catch {
        // Fall back below if retrieve fails
      }
    }

    // Last resort fallback
    resetSearchSessionToken();
    throw new Error('Unable to retrieve location coordinates.');
  },

  /**
   * Reverse geocodes latitude & longitude into structured address components.
   */
  async reverseGeocode(latitude: number, longitude: number): Promise<Partial<UserLocation>> {
    try {
      if (MAPBOX_TOKEN) {
        const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${longitude},${latitude}.json?access_token=${MAPBOX_TOKEN}&types=region,district,place,locality,neighborhood,postcode`;
        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          if (data.features && data.features.length > 0) {
            const first = data.features[0];
            const context = first.context || [];

            let city: string | undefined;
            let locality: string | undefined;
            let district: string | undefined;
            let state: string | undefined;
            let country: string | undefined;
            let postalCode: string | undefined;

            if (first.id.startsWith('place')) city = first.text;
            if (first.id.startsWith('locality') || first.id.startsWith('neighborhood')) locality = first.text;

            context.forEach((c: any) => {
              if (c.id.startsWith('place') && !city) city = c.text;
              if (c.id.startsWith('locality') && !locality) locality = c.text;
              if (c.id.startsWith('district')) district = c.text;
              if (c.id.startsWith('region')) state = c.text;
              if (c.id.startsWith('country')) country = c.text;
              if (c.id.startsWith('postcode')) postalCode = c.text;
            });

            const primary = locality || city || first.text;
            const secondary = [district, state, country].filter(Boolean).join(', ');
            const displayName = secondary ? `${primary}, ${secondary}` : first.place_name || first.text;

            return {
              latitude,
              longitude,
              displayName,
              city: city || primary,
              locality,
              district: district || city,
              state,
              country,
              postalCode,
            };
          }
        }
      }

      // OpenStreetMap Nominatim Reverse Geocoding Fallback
      const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=14&addressdetails=1`;
      const response = await fetch(url, {
        headers: { 'Accept-Language': 'en' },
      });

      if (!response.ok) {
        throw new Error('Failed to reverse geocode location.');
      }

      const data = await response.json();
      const addr = data.address || {};

      const city = addr.city || addr.town || addr.village || addr.municipality || addr.suburb || addr.county;
      const locality = addr.suburb || addr.village || addr.neighbourhood;
      const district = addr.state_district || addr.county || addr.district || city;
      const state = addr.state || addr.region;
      const country = addr.country;
      const postalCode = addr.postcode;

      const primary = locality || city || addr.road || 'Selected Field Location';
      const secondaryParts = [district, state, country].filter((p) => p && p !== primary);
      const displayName = secondaryParts.length > 0 ? `${primary}, ${secondaryParts.join(', ')}` : primary;

      return {
        latitude,
        longitude,
        displayName,
        city,
        locality,
        district,
        state,
        country,
        postalCode,
      };
    } catch {
      return {
        latitude,
        longitude,
        displayName: `${latitude.toFixed(4)}° N, ${longitude.toFixed(4)}° E`,
      };
    }
  },
};

