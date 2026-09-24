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
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useLocationContext } from '../../context/LocationContext';
import { UserLocation, LocationSearchResult } from '../../types/location';
import { LocationMap } from './LocationMap';

export const LocationPicker: React.FC = () => {
  const {
    location: globalSavedLocation,
    pendingLocation,
    setPendingLocation,
    isPickerOpen,
    closePicker,
    saveLocation,
    requestCurrentLocation,
    searchLocations,
    selectSearchResult,
    selectMapLocation,
    recentLocations,
    clearLocation,
    clearRecentLocations,
    isLoading: isContextLoading,
    permissionState,
  } = useLocationContext();

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<LocationSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Step-by-step geolocation progress message (Section 57)
  const [locatingStep, setLocatingStep] = useState<string | null>(null);

  // Advanced coordinates collapsed panel (Section 39)
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [manualLatStr, setManualLatStr] = useState<string>('');
  const [manualLngStr, setManualLngStr] = useState<string>('');

  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Synchronize modal state when opened
  useEffect(() => {
    if (isPickerOpen) {
      setPendingLocation(globalSavedLocation);
      setSearchQuery('');
      setSearchResults([]);
      setSearchError(null);
      setLocatingStep(null);
      if (globalSavedLocation) {
        setManualLatStr(globalSavedLocation.latitude.toString());
        setManualLngStr(globalSavedLocation.longitude.toString());
      }
    }
  }, [isPickerOpen, globalSavedLocation, setPendingLocation]);

  // Debounced Search Effect with AbortController (Section 17 & 53)
  useEffect(() => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    if (abortControllerRef.current) abortControllerRef.current.abort();

    if (!searchQuery || searchQuery.trim().length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    setSearchError(null);

    searchTimeoutRef.current = setTimeout(async () => {
      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const results = await searchLocations(searchQuery, controller.signal);
        setSearchResults(results);
        if (results.length === 0) {
          setSearchError('No matching locations found. Try entering a city or district name.');
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          setSearchError('Location search is temporarily unavailable. Please select from map or use GPS.');
        }
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, [searchQuery, searchLocations]);

  if (!isPickerOpen) return null;

  // Handle clicking a search result (Section 15, 18)
  const handleSelectSearchResult = async (result: LocationSearchResult) => {
    setSearchResults([]);
    setSearchQuery('');
    setSearchError(null);

    await selectSearchResult(result);
  };

  // Handle map click selection (Section 20)
  const handleMapSelectCoordinates = async (lat: number, lng: number) => {
    setManualLatStr(lat.toFixed(5));
    setManualLngStr(lng.toFixed(5));
    await selectMapLocation(lat, lng);
  };

  // Handle step-by-step device location request (Section 57)
  const handleRequestCurrentLocation = async () => {
    setLocatingStep('Locating your device...');
    try {
      const timer1 = setTimeout(() => setLocatingStep('Location found...'), 800);
      const timer2 = setTimeout(() => setLocatingStep('Finding place name...'), 1600);

      const loc = await requestCurrentLocation();
      clearTimeout(timer1);
      clearTimeout(timer2);

      if (loc) {
        setLocatingStep(`📍 ${loc.displayName}`);
        setManualLatStr(loc.latitude.toFixed(5));
        setManualLngStr(loc.longitude.toFixed(5));
        setTimeout(() => setLocatingStep(null), 3000);
      } else {
        setLocatingStep(null);
      }
    } catch {
      setLocatingStep(null);
    }
  };

  // Manual lat/lng submission (Section 39)
  const handleApplyManualCoords = async () => {
    const lat = parseFloat(manualLatStr);
    const lng = parseFloat(manualLngStr);
    if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
      await selectMapLocation(lat, lng);
    }
  };

  // Confirm selection CTA (Section 49)
  const handleConfirmLocation = () => {
    if (pendingLocation) {
      saveLocation(pendingLocation);
      closePicker();
    }
  };

  const handleClearSavedLocation = () => {
    clearLocation();
    closePicker();
  };

  const handleClearSearchInput = () => {
    setSearchQuery('');
    setSearchResults([]);
    setSearchError(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 overflow-y-auto selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Backdrop */}
      <div
        onClick={closePicker}
        className="fixed inset-0 bg-[#0B1C10]/85 backdrop-blur-md transition-opacity"
      />

      {/* Modal Container (Section 63: Desktop ~950px, Mobile sheet) */}
      <div className="relative w-full max-w-4xl bg-[#0B1C10] text-[#FAFBF7] rounded-3xl border border-[#D4E768]/30 shadow-2xl overflow-hidden flex flex-col max-h-[92vh] z-10 my-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-[#112316]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-2xl bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-extrabold shadow-sm">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-extrabold text-base sm:text-lg font-editorial tracking-tight text-[#FAFBF7]">
                SELECT FIELD LOCATION
              </h3>
              <p className="text-[10px] sm:text-xs text-[#D4E768] font-bold tracking-wider uppercase">
                Search village, town, district or select directly on map
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

        {/* Modal Body: Two-Column Responsive Layout */}
        <div className="p-5 sm:p-6 overflow-y-auto flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Search & Location Details (5 cols) */}
          <div className="lg:col-span-5 space-y-4 flex flex-col">
            {/* Search Box (Section 13, 17, 50) */}
            <div className="relative">
              <label className="text-[10px] font-bold uppercase tracking-wider text-white/70 block mb-1.5">
                Location Autocomplete Search
              </label>
              <div className="relative flex items-center">
                <Search className="w-4 h-4 text-[#536056] absolute left-4 pointer-events-none" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search village, city, district (e.g. Barasat, Kolkata)..."
                  className="w-full pl-11 pr-10 py-3 rounded-2xl bg-[#112316] border border-white/15 text-xs text-[#FAFBF7] placeholder-[#536056] focus:outline-none focus:border-[#D4E768] transition-colors"
                />
                {isSearching ? (
                  <Loader2 className="w-4 h-4 text-[#D4E768] animate-spin absolute right-3" />
                ) : searchQuery ? (
                  <button
                    type="button"
                    onClick={handleClearSearchInput}
                    className="p-1 rounded-full text-white/50 hover:text-white absolute right-3"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                ) : null}
              </div>

              {/* Search Suggestions Dropdown (Section 18) */}
              {searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-[#112316] border border-[#D4E768]/40 rounded-2xl shadow-2xl overflow-hidden z-30 max-h-60 overflow-y-auto">
                  <div className="px-3 py-1.5 bg-[#0B1C10] border-b border-white/10 text-[9px] font-bold uppercase tracking-widest text-[#D4E768]">
                    SEARCH RESULTS
                  </div>
                  {searchResults.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleSelectSearchResult(item)}
                      className="px-4 py-3 border-b border-white/5 hover:bg-[#0B1C10] cursor-pointer transition-colors flex items-start gap-3 group"
                    >
                      <MapPin className="w-4 h-4 text-[#D4E768] shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-bold text-[#FAFBF7] truncate">
                          📍 {item.primaryName}
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
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>{searchError}</span>
                </div>
              )}
            </div>

            {/* Geolocation Button & Status Steps (Section 7, 21, 57) */}
            <div className="space-y-2">
              <button
                type="button"
                onClick={handleRequestCurrentLocation}
                disabled={isContextLoading}
                className="w-full inline-flex items-center justify-center gap-2.5 px-4 py-3 rounded-2xl bg-[#112316] hover:bg-[#1a3321] border border-[#D4E768]/40 text-xs font-bold text-[#D4E768] transition-all shadow-sm active:scale-98 disabled:opacity-50"
              >
                <LocateFixed className={`w-4 h-4 ${isContextLoading ? 'animate-spin' : ''}`} />
                <span>
                  {locatingStep ? locatingStep : 'Use My Current Location'}
                </span>
              </button>

              {permissionState === 'denied' && (
                <div className="p-3 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs space-y-2">
                  <p className="leading-tight">
                    Location access is blocked. You can still search for your location manually or select on the map.
                  </p>
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      onClick={handleRequestCurrentLocation}
                      className="px-3 py-1 rounded-xl bg-rose-900/60 hover:bg-rose-900 text-[11px] font-bold text-white transition-colors"
                    >
                      Try Again
                    </button>
                    <button
                      onClick={() => {
                        const inputEl = document.querySelector('input[placeholder*="Search"]') as HTMLInputElement;
                        if (inputEl) inputEl.focus();
                      }}
                      className="px-3 py-1 rounded-xl bg-white/10 hover:bg-white/20 text-[11px] font-bold text-white transition-colors"
                    >
                      Search Manually
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Selected / Pending Location Card (Section 19, 47, 48) */}
            {pendingLocation ? (
              <div className="p-4 rounded-2xl bg-[#112316] border border-[#D4E768]/50 space-y-3 shadow-md">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#D4E768] flex items-center gap-1.5">
                    <Navigation className="w-3 h-3" />
                    SELECTED FIELD LOCATION
                  </span>
                  <span className="text-[10px] text-white/70 font-mono px-2 py-0.5 rounded-full bg-white/10">
                    {pendingLocation.source === 'device'
                      ? 'Current Device Location'
                      : pendingLocation.source === 'search'
                      ? 'Search Result'
                      : 'Map Selection'}
                  </span>
                </div>

                <p className="text-sm font-black text-[#FAFBF7]">
                  📍 {pendingLocation.displayName}
                </p>

                <div className="grid grid-cols-2 gap-2 text-[11px] text-white/80 pt-2 border-t border-white/10 font-mono">
                  <div>
                    <span className="text-white/40 block text-[9px]">LATITUDE</span>
                    <span>{pendingLocation.latitude.toFixed(5)}° N</span>
                  </div>
                  <div>
                    <span className="text-white/40 block text-[9px]">LONGITUDE</span>
                    <span>{pendingLocation.longitude.toFixed(5)}° E</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-2xl bg-[#112316]/50 border border-dashed border-white/15 text-center text-xs text-white/50 space-y-1">
                <MapPin className="w-6 h-6 mx-auto text-white/30" />
                <p>No location selected yet.</p>
                <p className="text-[11px] text-white/40">Search above or click anywhere on the map to set pin.</p>
              </div>
            )}

            {/* Collapsed Advanced Manual Coordinates (Section 39) */}
            <div className="pt-1">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-xs text-white/60 hover:text-white font-semibold flex items-center gap-1 transition-colors"
              >
                {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                <span>Advanced Coordinates</span>
              </button>

              {showAdvanced && (
                <div className="mt-2 p-3 rounded-2xl bg-[#112316] border border-white/10 space-y-3 animate-fade-in">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <label className="text-[10px] text-white/60 block mb-1">Latitude (-90 to 90)</label>
                      <input
                        type="number"
                        step="0.00001"
                        value={manualLatStr}
                        onChange={(e) => setManualLatStr(e.target.value)}
                        placeholder="22.7200"
                        className="w-full px-3 py-1.5 rounded-xl bg-[#0B1C10] border border-white/15 text-xs text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-white/60 block mb-1">Longitude (-180 to 180)</label>
                      <input
                        type="number"
                        step="0.00001"
                        value={manualLngStr}
                        onChange={(e) => setManualLngStr(e.target.value)}
                        placeholder="88.4800"
                        className="w-full px-3 py-1.5 rounded-xl bg-[#0B1C10] border border-white/15 text-xs text-white font-mono"
                      />
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleApplyManualCoords}
                    className="w-full py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-bold text-white transition-colors"
                  >
                    Set Coords
                  </button>
                </div>
              )}
            </div>

            {/* Recent Locations History (Section 51) */}
            {recentLocations.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-white/10">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-white/70 flex items-center gap-1.5">
                    <History className="w-3.5 h-3.5 text-[#D4E768]" />
                    Recent Locations
                  </span>
                  <button
                    onClick={clearRecentLocations}
                    className="text-[10px] text-white/40 hover:text-rose-400 transition-colors"
                  >
                    Clear
                  </button>
                </div>

                <div className="space-y-1.5 max-h-32 overflow-y-auto">
                  {recentLocations.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => setPendingLocation(item)}
                      className="p-2.5 rounded-xl bg-[#112316]/70 hover:bg-[#112316] border border-white/10 hover:border-[#D4E768]/40 cursor-pointer transition-all flex items-center justify-between text-xs"
                    >
                      <div className="min-w-0 pr-2">
                        <p className="font-bold text-[#FAFBF7] truncate">
                          {item.city || item.displayName.split(',')[0]}
                        </p>
                        <p className="text-[10px] text-white/50 truncate">
                          {item.state || item.displayName}
                        </p>
                      </div>
                      {pendingLocation?.latitude === item.latitude && pendingLocation?.longitude === item.longitude && (
                        <Check className="w-4 h-4 text-[#D4E768] shrink-0" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Interactive Map Component (7 cols) */}
          <div className="lg:col-span-7 space-y-2 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-white/80">Interactive Map Pin Selector</span>
              {isContextLoading && (
                <span className="text-[10px] text-[#D4E768] animate-pulse">
                  Retrieving location details...
                </span>
              )}
            </div>

            <LocationMap
              location={pendingLocation}
              onSelectCoordinates={handleMapSelectCoordinates}
              onRequestCurrentLocation={handleRequestCurrentLocation}
              isLocating={isContextLoading}
            />
          </div>
        </div>

        {/* Modal Footer Actions (Section 49) */}
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
              disabled={!pendingLocation}
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

