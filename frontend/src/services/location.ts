import { UserLocation, LocationSearchResult } from '../types/location';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';

/**
 * Service providing Geolocation, Reverse Geocoding, and Location Search capabilities.
 */
export const locationService = {
  /**
   * One-time acquisition of device coordinates using browser Geolocation API.
   */
  async getCurrentDeviceLocation(): Promise<{ latitude: number; longitude: number; accuracy?: number }> {
    if (!navigator.geolocation) {
      throw new Error('Geolocation is not supported by your browser.');
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
              reject(new Error('Location access permission was denied.'));
              break;
            case error.POSITION_UNAVAILABLE:
              reject(new Error('Device location information is currently unavailable.'));
              break;
            case error.TIMEOUT:
              reject(new Error('Location acquisition request timed out.'));
              break;
            default:
              reject(new Error('An unexpected error occurred while requesting device location.'));
              break;
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000,
        }
      );
    });
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
            let district: string | undefined;
            let state: string | undefined;
            let country: string | undefined;
            let postalCode: string | undefined;

            context.forEach((c: any) => {
              if (c.id.startsWith('place')) city = c.text;
              if (c.id.startsWith('district')) district = c.text;
              if (c.id.startsWith('region')) state = c.text;
              if (c.id.startsWith('country')) country = c.text;
              if (c.id.startsWith('postcode')) postalCode = c.text;
            });

            return {
              latitude,
              longitude,
              displayName: first.place_name || first.text,
              city: city || first.text,
              district: district || city,
              state,
              country,
              postalCode,
            };
          }
        }
      }

      // OpenStreetMap Nominatim Fallback API
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
      const district = addr.state_district || addr.county || addr.district || city;
      const state = addr.state || addr.region;
      const country = addr.country;
      const postalCode = addr.postcode;

      const primary = city || addr.suburb || addr.road || 'Selected Location';
      const secondaryParts = [district, state, country].filter(Boolean);
      const displayName = secondaryParts.length > 0 ? `${primary}, ${secondaryParts.join(', ')}` : primary;

      return {
        latitude,
        longitude,
        displayName,
        city,
        locality: addr.suburb || addr.village || addr.neighbourhood,
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

  /**
   * Searches locations using Mapbox Geocoding or Nominatim search API.
   */
  async searchLocations(query: string): Promise<LocationSearchResult[]> {
    if (!query || query.trim().length < 2) return [];

    const cleanQuery = query.trim();

    try {
      if (MAPBOX_TOKEN) {
        const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(cleanQuery)}.json?access_token=${MAPBOX_TOKEN}&autocomplete=true&limit=6`;
        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          return (data.features || []).map((f: any) => {
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

      // Nominatim Search API
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(cleanQuery)}&addressdetails=1&limit=6`;
      const response = await fetch(url, {
        headers: { 'Accept-Language': 'en' },
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
        const parts = [district, state, country].filter(p => p && p !== primaryName);
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
    } catch {
      return [];
    }
  },
};
