import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Search,
  LocateFixed,
  MapPin,
  History,
  Trash2,
  Check,
  Navigation,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useLocationContext } from '../../context/LocationContext';
import { UserLocation, LocationSearchResult } from '../../types/location';
import { locationService } from '../../services/location';
import { LocationMap } from './LocationMap';

export const LocationPicker: React.FC = () => {
  const {
    location: globalSavedLocation,
    isPickerOpen,
    closePicker,
    selectLocation,
    requestCurrentLocation,
    recentLocations,
    clearLocation,
    clearRecentLocations,
    isLoading: isGlobalLocating,
  } = useLocationContext();

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<LocationSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Temporary selected location state inside modal (not committed until user clicks "Use This Location")
  const [selectedLocation, setSelectedLocation] = useState<UserLocation | null>(
    globalSavedLocation
  );

  const [isGeocodingMapClick, setIsGeocodingMapClick] = useState<boolean>(false);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Synchronize modal state when modal opens
  useEffect(() => {
    if (isPickerOpen) {
      setSelectedLocation(globalSavedLocation);
      setSearchQuery('');
      setSearchResults([]);
      setSearchError(null);
    }
  }, [isPickerOpen, globalSavedLocation]);

  // Debounced search effect
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!searchQuery || searchQuery.trim().length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    setSearchError(null);

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const results = await locationService.searchLocations(searchQuery);
        setSearchResults(results);
        if (results.length === 0) {
          setSearchError('No locations found for your query.');
        }
      } catch {
        setSearchError('Location search is temporarily unavailable.');
      } finally {
        setIsSearching(false);
      }
    }, 350);

    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    };
  }, [searchQuery]);

  if (!isPickerOpen) return null;

  // Handle click on a search result item
  const handleSelectSearchResult = (result: LocationSearchResult) => {
    const newTempLocation: UserLocation = {
      latitude: result.latitude,
      longitude: result.longitude,
      displayName: result.displayName,
      city: result.city || result.primaryName,
      district: result.district,
      state: result.state,
      country: result.country,
      postalCode: result.postalCode,
      source: 'manual',
      timestamp: Date.now(),
    };
    setSelectedLocation(newTempLocation);
    setSearchResults([]);
    setSearchQuery('');
  };

  // Handle map click coordinates selection
  const handleMapSelectCoordinates = async (lat: number, lng: number) => {
    setIsGeocodingMapClick(true);
    try {
      const geocoded = await locationService.reverseGeocode(lat, lng);
      const newTempLocation: UserLocation = {
        latitude: lat,
        longitude: lng,
        displayName: geocoded.displayName || `${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E`,
        city: geocoded.city,
        locality: geocoded.locality,
        district: geocoded.district,
        state: geocoded.state,
        country: geocoded.country,
        postalCode: geocoded.postalCode,
        source: 'map',
        timestamp: Date.now(),
      };
      setSelectedLocation(newTempLocation);
    } catch {
      setSelectedLocation({
        latitude: lat,
        longitude: lng,
        displayName: `${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E`,
        source: 'map',
      });
    } finally {
      setIsGeocodingMapClick(false);
    }
  };

  // Handle device location button click inside modal
  const handleRequestCurrentLocation = async () => {
    const loc = await requestCurrentLocation();
    if (loc) {
      setSelectedLocation(loc);
    }
  };

  // Confirm selection CTA
  const handleConfirmLocation = () => {
    if (selectedLocation) {
      selectLocation(selectedLocation);
      closePicker();
    }
  };

  const handleClearSavedLocation = () => {
    clearLocation();
    setSelectedLocation(null);
    closePicker();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Backdrop */}
      <div
        onClick={closePicker}
        className="fixed inset-0 bg-[#0B1C10]/80 backdrop-blur-md transition-opacity"
      />

      {/* Modal Container */}
      <div className="relative w-full max-w-2xl bg-[#0B1C10] text-[#FAFBF7] rounded-3xl border border-[#D4E768]/30 shadow-2xl overflow-hidden flex flex-col max-h-[90vh] z-10">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-[#112316]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-bold">
              <MapPin className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-extrabold text-base font-editorial tracking-tight text-[#FAFBF7]">
                SELECT FIELD LOCATION
              </h3>
              <p className="text-[10px] text-[#D4E768] font-bold tracking-wider uppercase">
                Search village, town, city or click map
              </p>
            </div>
          </div>

          <button
            onClick={closePicker}
            className="p-2 rounded-full text-white/60 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-5 flex-1">
          {/* Search Box */}
          <div className="relative">
            <div className="relative flex items-center">
              <Search className="w-4 h-4 text-[#536056] absolute left-4 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search city, village, district, state or postal code..."
                className="w-full pl-11 pr-10 py-3 rounded-2xl bg-[#112316] border border-white/15 text-xs text-[#FAFBF7] placeholder-[#536056] focus:outline-none focus:border-[#D4E768] transition-colors"
              />
              {isSearching && (
                <Loader2 className="w-4 h-4 text-[#D4E768] animate-spin absolute right-3" />
              )}
            </div>

            {/* Search Suggestions Dropdown */}
            {searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-[#112316] border border-[#D4E768]/30 rounded-2xl shadow-2xl overflow-hidden z-30 max-h-60 overflow-y-auto">
                {searchResults.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleSelectSearchResult(item)}
                    className="px-4 py-3 border-b border-white/5 hover:bg-[#0B1C10] cursor-pointer transition-colors flex items-start gap-3"
                  >
                    <MapPin className="w-4 h-4 text-[#D4E768] shrink-0 mt-0.5" />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold text-[#FAFBF7] truncate">
                        {item.primaryName}
                      </p>
                      {item.secondaryName && (
                        <p className="text-[11px] text-white/60 truncate">
                          {item.secondaryName}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {searchError && searchQuery.length >= 2 && !isSearching && (
              <div className="mt-2 text-[11px] text-amber-400 flex items-center gap-1.5 px-2">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>{searchError}</span>
              </div>
            )}
          </div>

          {/* Quick Current Location Action Button */}
          <div className="flex items-center justify-between gap-3">
            <button
              onClick={handleRequestCurrentLocation}
              disabled={isGlobalLocating}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl bg-[#112316] hover:bg-white/10 border border-[#D4E768]/30 text-xs font-bold text-[#D4E768] transition-all"
            >
              <LocateFixed className={`w-4 h-4 ${isGlobalLocating ? 'animate-spin' : ''}`} />
              <span>
                {isGlobalLocating ? 'Acquiring GPS...' : 'Use My Current Location'}
              </span>
            </button>
          </div>

          {/* Interactive Map Component */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs px-1">
              <span className="font-bold text-white/80">Interactive Map Selector</span>
              {isGeocodingMapClick && (
                <span className="text-[10px] text-[#D4E768] animate-pulse">
                  Updating address details...
                </span>
              )}
            </div>
            <LocationMap
              location={selectedLocation}
              onSelectCoordinates={handleMapSelectCoordinates}
              onRequestCurrentLocation={handleRequestCurrentLocation}
              isLocating={isGlobalLocating}
            />
          </div>

          {/* Selected Location Summary Box */}
          {selectedLocation ? (
            <div className="p-4 rounded-2xl bg-[#112316] border border-[#D4E768]/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#D4E768]">
                  SELECTED FIELD LOCATION
                </span>
                <span className="text-[10px] text-white/60 font-mono flex items-center gap-1">
                  <Navigation className="w-3 h-3 text-[#D4E768]" />
                  {selectedLocation.source === 'device' ? 'Device GPS' : 'Map/Search'}
                </span>
              </div>

              <p className="text-sm font-extrabold text-[#FAFBF7]">
                {selectedLocation.displayName}
              </p>

              <div className="grid grid-cols-2 gap-2 text-[11px] text-white/70 pt-1 border-t border-white/10 font-mono">
                <div>
                  <span className="text-white/40 block">LATITUDE</span>
                  <span>{selectedLocation.latitude.toFixed(5)}° N</span>
                </div>
                <div>
                  <span className="text-white/40 block">LONGITUDE</span>
                  <span>{selectedLocation.longitude.toFixed(5)}° E</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-[#112316]/60 border border-dashed border-white/10 text-center text-xs text-white/50">
              No location selected yet. Click the map or search above.
            </div>
          )}

          {/* Recent Locations History */}
          {recentLocations.length > 0 && (
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between text-xs px-1">
                <span className="font-bold text-white/70 flex items-center gap-1.5">
                  <History className="w-3.5 h-3.5 text-[#D4E768]" />
                  Recent Locations
                </span>
                <button
                  onClick={clearRecentLocations}
                  className="text-[10px] text-white/40 hover:text-rose-400 transition-colors"
                >
                  Clear history
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {recentLocations.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedLocation(item)}
                    className="p-3 rounded-2xl bg-[#112316]/80 hover:bg-[#112316] border border-white/10 hover:border-[#D4E768]/40 cursor-pointer transition-all flex items-center justify-between"
                  >
                    <div className="min-w-0 pr-2">
                      <p className="text-xs font-bold text-[#FAFBF7] truncate">
                        {item.city || item.displayName.split(',')[0]}
                      </p>
                      <p className="text-[10px] text-white/50 truncate">
                        {item.state || item.displayName}
                      </p>
                    </div>
                    {selectedLocation?.latitude === item.latitude && (
                      <Check className="w-4 h-4 text-[#D4E768] shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Actions */}
        <div className="px-6 py-4 bg-[#112316] border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3">
          {globalSavedLocation && (
            <button
              onClick={handleClearSavedLocation}
              className="text-xs text-rose-400 hover:text-rose-300 font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear Saved Location</span>
            </button>
          )}

          <div className="flex items-center gap-3 w-full sm:w-auto ml-auto">
            <button
              onClick={closePicker}
              className="px-4 py-2.5 rounded-2xl bg-white/10 hover:bg-white/15 text-xs font-bold text-white transition-colors"
            >
              Cancel
            </button>

            <button
              onClick={handleConfirmLocation}
              disabled={!selectedLocation}
              className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-2xl bg-[#D4E768] text-[#0B1C10] text-xs font-extrabold hover:bg-[#c8db5b] disabled:opacity-50 transition-all shadow-lg active:scale-98"
            >
              <Check className="w-4 h-4" />
              <span>Use This Location</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
