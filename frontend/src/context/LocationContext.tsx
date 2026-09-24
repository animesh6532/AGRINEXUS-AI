import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { UserLocation, LocationPermissionState, LocationSearchResult } from '../types/location';
import { locationService } from '../services/location';

const STORAGE_KEY = 'agrinexus.location.v1';
const RECENT_KEY = 'agrinexus.recent_locations.v1';

function isValidUserLocation(obj: any): obj is UserLocation {
  if (!obj || typeof obj !== 'object') return false;
  if (typeof obj.latitude !== 'number' || isNaN(obj.latitude) || obj.latitude < -90 || obj.latitude > 90) return false;
  if (typeof obj.longitude !== 'number' || isNaN(obj.longitude) || obj.longitude < -180 || obj.longitude > 180) return false;
  if (!obj.displayName || typeof obj.displayName !== 'string' || obj.displayName.trim() === '') return false;
  
  // Section 27: Never restore a fake location like "Punjab, India" without valid real coordinates
  if (obj.displayName.toLowerCase().includes('punjab, india') && (obj.latitude === 0 || obj.longitude === 0)) {
    return false;
  }
  return true;
}

interface LocationContextType {
  location: UserLocation | null;
  pendingLocation: UserLocation | null;
  permissionState: LocationPermissionState;
  isLoading: boolean;
  error: string | null;
  hasLocation: boolean;
  recentLocations: UserLocation[];
  isPickerOpen: boolean;

  requestCurrentLocation: () => Promise<UserLocation | null>;
  searchLocations: (query: string, signal?: AbortSignal) => Promise<LocationSearchResult[]>;
  selectSearchResult: (result: LocationSearchResult) => Promise<UserLocation | null>;
  selectMapLocation: (latitude: number, longitude: number) => Promise<UserLocation | null>;
  setPendingLocation: (loc: UserLocation | null) => void;
  saveLocation: (location: UserLocation) => void;
  clearLocation: () => void;
  refreshLocation: () => Promise<void>;
  openPicker: () => void;
  closePicker: () => void;
  clearRecentLocations: () => void;
}

const LocationContext = createContext<LocationContextType | undefined>(undefined);

export const LocationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Saved Location (Single Source of Truth)
  const [location, setLocation] = useState<UserLocation | null>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (isValidUserLocation(parsed)) {
          return parsed;
        }
      }
    } catch {
      // Ignore invalid JSON
    }
    // Clean up malformed or legacy fake locations from storage
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore
    }
    return null;
  });

  // Pending Location (Selected inside LocationPicker modal before confirmation)
  const [pendingLocation, setPendingLocation] = useState<UserLocation | null>(null);

  const [recentLocations, setRecentLocations] = useState<UserLocation[]>(() => {
    try {
      const saved = localStorage.getItem(RECENT_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          return parsed.filter(isValidUserLocation);
        }
      }
    } catch {
      // Ignore
    }
    return [];
  });

  const [permissionState, setPermissionState] = useState<LocationPermissionState>('prompt');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isPickerOpen, setIsPickerOpen] = useState<boolean>(false);

  // Synchronize browser permission state if supported
  useEffect(() => {
    if (typeof window !== 'undefined' && navigator?.permissions?.query) {
      navigator.permissions
        .query({ name: 'geolocation' as PermissionName })
        .then((status) => {
          setPermissionState(status.state as LocationPermissionState);
          status.onchange = () => {
            setPermissionState(status.state as LocationPermissionState);
          };
        })
        .catch(() => {});
    }
  }, []);

  // Save confirmed location to storage & update context
  const saveLocation = useCallback((newLoc: UserLocation) => {
    if (!isValidUserLocation(newLoc)) return;

    const validated: UserLocation = {
      ...newLoc,
      timestamp: Date.now(),
    };

    setLocation(validated);
    setPendingLocation(validated);
    setError(null);

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(validated));
    } catch {
      // Ignore storage errors
    }

    // Add to recent locations history (max 5)
    setRecentLocations((prev) => {
      const filtered = prev.filter(
        (item) =>
          Math.abs(item.latitude - validated.latitude) > 0.001 ||
          Math.abs(item.longitude - validated.longitude) > 0.001
      );
      const updated = [validated, ...filtered].slice(0, 5);
      try {
        localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
      } catch {
        // Ignore
      }
      return updated;
    });
  }, []);

  // Request device current location via browser Geolocation API
  const requestCurrentLocation = useCallback(async (): Promise<UserLocation | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const deviceCoords = await locationService.getCurrentDeviceLocation();
      setPermissionState('granted');

      // Reverse geocode address details
      const geocoded = await locationService.reverseGeocode(
        deviceCoords.latitude,
        deviceCoords.longitude
      );

      const newLocation: UserLocation = {
        latitude: deviceCoords.latitude,
        longitude: deviceCoords.longitude,
        displayName: geocoded.displayName || 'Current Device Location',
        city: geocoded.city,
        locality: geocoded.locality,
        district: geocoded.district,
        state: geocoded.state,
        country: geocoded.country,
        postalCode: geocoded.postalCode,
        accuracy: deviceCoords.accuracy,
        source: 'device',
        timestamp: Date.now(),
      };

      setPendingLocation(newLocation);
      return newLocation;
    } catch (err: any) {
      const message = err.message || 'Failed to acquire current location.';
      setError(message);
      if (message.toLowerCase().includes('blocked') || message.toLowerCase().includes('denied')) {
        setPermissionState('denied');
      } else if (message.toLowerCase().includes('unavailable')) {
        setPermissionState('unavailable');
      } else if (message.toLowerCase().includes('timed out')) {
        setPermissionState('timeout');
      }
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Search locations helper
  const searchLocations = useCallback(async (query: string, signal?: AbortSignal): Promise<LocationSearchResult[]> => {
    return locationService.searchLocations(query, signal);
  }, []);

  // Select search result -> retrieves full feature & updates pending location
  const selectSearchResult = useCallback(async (result: LocationSearchResult): Promise<UserLocation | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const fullLoc = await locationService.retrieveLocation(result);
      setPendingLocation(fullLoc);
      return fullLoc;
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve selected location details.');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Select map coordinates -> reverse geocodes & updates pending location
  const selectMapLocation = useCallback(async (latitude: number, longitude: number): Promise<UserLocation | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const geocoded = await locationService.reverseGeocode(latitude, longitude);
      const newLoc: UserLocation = {
        latitude,
        longitude,
        displayName: geocoded.displayName || `${latitude.toFixed(4)}° N, ${longitude.toFixed(4)}° E`,
        city: geocoded.city,
        locality: geocoded.locality,
        district: geocoded.district,
        state: geocoded.state,
        country: geocoded.country,
        postalCode: geocoded.postalCode,
        source: 'map',
        timestamp: Date.now(),
      };
      setPendingLocation(newLoc);
      return newLoc;
    } catch {
      const fallbackLoc: UserLocation = {
        latitude,
        longitude,
        displayName: `${latitude.toFixed(4)}° N, ${longitude.toFixed(4)}° E`,
        source: 'map',
        timestamp: Date.now(),
      };
      setPendingLocation(fallbackLoc);
      return fallbackLoc;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Refresh saved location telemetry
  const refreshLocation = useCallback(async () => {
    if (location?.source === 'device') {
      const refreshed = await requestCurrentLocation();
      if (refreshed) {
        saveLocation(refreshed);
      }
    } else if (location) {
      setIsLoading(true);
      try {
        const geocoded = await locationService.reverseGeocode(location.latitude, location.longitude);
        const updated: UserLocation = {
          ...location,
          ...geocoded,
          timestamp: Date.now(),
        };
        saveLocation(updated);
      } finally {
        setIsLoading(false);
      }
    }
  }, [location, requestCurrentLocation, saveLocation]);

  // Clear saved location
  const clearLocation = useCallback(() => {
    setLocation(null);
    setPendingLocation(null);
    setError(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore
    }
  }, []);

  const clearRecentLocations = useCallback(() => {
    setRecentLocations([]);
    try {
      localStorage.removeItem(RECENT_KEY);
    } catch {
      // Ignore
    }
  }, []);

  const openPicker = useCallback(() => {
    setPendingLocation(location);
    setIsPickerOpen(true);
  }, [location]);

  const closePicker = useCallback(() => {
    setIsPickerOpen(false);
    setError(null);
  }, []);

  return (
    <LocationContext.Provider
      value={{
        location,
        pendingLocation,
        permissionState,
        isLoading,
        error,
        hasLocation: !!location,
        recentLocations,
        isPickerOpen,
        requestCurrentLocation,
        searchLocations,
        selectSearchResult,
        selectMapLocation,
        setPendingLocation,
        saveLocation,
        clearLocation,
        refreshLocation,
        openPicker,
        closePicker,
        clearRecentLocations,
      }}
    >
      {children}
    </LocationContext.Provider>
  );
};

export const useLocationContext = () => {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error('useLocationContext must be used within a LocationProvider');
  }
  return context;
};

