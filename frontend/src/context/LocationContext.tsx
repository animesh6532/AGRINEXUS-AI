import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { UserLocation, LocationPermissionState } from '../types/location';
import { locationService } from '../services/location';

const STORAGE_KEY = 'agrinexus.location.v1';
const RECENT_KEY = 'agrinexus.recent_locations.v1';

interface LocationContextType {
  location: UserLocation | null;
  permissionState: LocationPermissionState;
  isLoading: boolean;
  error: string | null;
  recentLocations: UserLocation[];
  isPickerOpen: boolean;
  requestCurrentLocation: () => Promise<UserLocation | null>;
  setManualLocation: (loc: UserLocation) => void;
  selectLocation: (loc: UserLocation) => void;
  clearLocation: () => void;
  refreshLocation: () => Promise<void>;
  openPicker: () => void;
  closePicker: () => void;
  clearRecentLocations: () => void;
}

const LocationContext = createContext<LocationContextType | undefined>(undefined);

export const LocationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [location, setLocation] = useState<UserLocation | null>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as UserLocation;
        if (typeof parsed.latitude === 'number' && typeof parsed.longitude === 'number') {
          return parsed;
        }
      }
    } catch {
      // Ignore invalid JSON
    }
    return null;
  });

  const [recentLocations, setRecentLocations] = useState<UserLocation[]>(() => {
    try {
      const saved = localStorage.getItem(RECENT_KEY);
      if (saved) {
        return JSON.parse(saved) as UserLocation[];
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

  // Check initial browser permission status if supported
  useEffect(() => {
    if (navigator.permissions && navigator.permissions.query) {
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

  // Save location to localStorage
  const saveLocationToStorage = useCallback((loc: UserLocation | null) => {
    if (loc) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(loc));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  // Add to recent locations history
  const addRecentLocation = useCallback((loc: UserLocation) => {
    setRecentLocations((prev) => {
      const filtered = prev.filter(
        (item) =>
          Math.abs(item.latitude - loc.latitude) > 0.005 ||
          Math.abs(item.longitude - loc.longitude) > 0.005
      );
      const updated = [loc, ...filtered].slice(0, 5);
      localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Set / select location manually
  const selectLocation = useCallback(
    (loc: UserLocation) => {
      const updatedLoc: UserLocation = {
        ...loc,
        timestamp: Date.now(),
      };
      setLocation(updatedLoc);
      saveLocationToStorage(updatedLoc);
      addRecentLocation(updatedLoc);
      setError(null);
    },
    [saveLocationToStorage, addRecentLocation]
  );

  const setManualLocation = useCallback(
    (loc: UserLocation) => {
      selectLocation({
        ...loc,
        source: 'manual',
      });
    },
    [selectLocation]
  );

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

      setLocation(newLocation);
      saveLocationToStorage(newLocation);
      addRecentLocation(newLocation);
      return newLocation;
    } catch (err: any) {
      const message = err.message || 'Failed to acquire current location.';
      setError(message);
      if (message.includes('denied')) {
        setPermissionState('denied');
      } else if (message.includes('unavailable')) {
        setPermissionState('unavailable');
      } else if (message.includes('timed out')) {
        setPermissionState('timeout');
      }
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [saveLocationToStorage, addRecentLocation]);

  // Refresh current location if location source is 'device'
  const refreshLocation = useCallback(async () => {
    if (location?.source === 'device') {
      await requestCurrentLocation();
    } else if (location) {
      setIsLoading(true);
      try {
        const geocoded = await locationService.reverseGeocode(location.latitude, location.longitude);
        const updated: UserLocation = {
          ...location,
          ...geocoded,
          timestamp: Date.now(),
        };
        setLocation(updated);
        saveLocationToStorage(updated);
      } finally {
        setIsLoading(false);
      }
    }
  }, [location, requestCurrentLocation, saveLocationToStorage]);

  // Clear saved location
  const clearLocation = useCallback(() => {
    setLocation(null);
    saveLocationToStorage(null);
    setError(null);
  }, [saveLocationToStorage]);

  const clearRecentLocations = useCallback(() => {
    setRecentLocations([]);
    localStorage.removeItem(RECENT_KEY);
  }, []);

  const openPicker = useCallback(() => setIsPickerOpen(true), []);
  const closePicker = useCallback(() => setIsPickerOpen(false), []);

  return (
    <LocationContext.Provider
      value={{
        location,
        permissionState,
        isLoading,
        error,
        recentLocations,
        isPickerOpen,
        requestCurrentLocation,
        setManualLocation,
        selectLocation,
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
