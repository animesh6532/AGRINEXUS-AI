import React, { useState, useEffect, useRef } from 'react';
import { LocateFixed, Plus, Minus, Navigation } from 'lucide-react';
import { UserLocation } from '../../types/location';
import { locationService } from '../../services/location';

interface LocationMapProps {
  location: UserLocation | null;
  onSelectCoordinates: (lat: number, lng: number) => void;
  onRequestCurrentLocation?: () => void;
  isLocating?: boolean;
}

export const LocationMap: React.FC<LocationMapProps> = ({
  location,
  onSelectCoordinates,
  onRequestCurrentLocation,
  isLocating = false,
}) => {
  const [zoom, setZoom] = useState<number>(12);
  const [centerLat, setCenterLat] = useState<number>(location?.latitude || 22.5726);
  const [centerLng, setCenterLng] = useState<number>(location?.longitude || 88.3639);
  const mapContainerRef = useRef<HTMLDivElement>(null);

  // Sync center when location prop changes
  useEffect(() => {
    if (location && typeof location.latitude === 'number' && typeof location.longitude === 'number') {
      setCenterLat(location.latitude);
      setCenterLng(location.longitude);
    }
  }, [location?.latitude, location?.longitude]);

  // Convert lat/lng to tile coordinates
  const lat2tile = (lat: number, z: number) => {
    return (
      ((1 -
        Math.log(
          Math.tan((lat * Math.PI) / 180) + 1 / Math.cos((lat * Math.PI) / 180)
        ) /
          Math.PI) /
        2) *
      Math.pow(2, z)
    );
  };

  const lon2tile = (lon: number, z: number) => {
    return ((lon + 180) / 360) * Math.pow(2, z);
  };

  const tileX = Math.floor(lon2tile(centerLng, zoom));
  const tileY = Math.floor(lat2tile(centerLat, zoom));

  // Handle click on map container to select new coordinates
  const handleMapClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!mapContainerRef.current) return;
    const rect = mapContainerRef.current.getBoundingClientRect();
    const offsetX = e.clientX - rect.left - rect.width / 2;
    const offsetY = e.clientY - rect.top - rect.height / 2;

    // Approximate coordinate shift per pixel at current zoom
    const degreesPerPixelLng = 360 / (256 * Math.pow(2, zoom));
    const degreesPerPixelLat = (360 / (256 * Math.pow(2, zoom))) * Math.cos((centerLat * Math.PI) / 180);

    const newLng = centerLng + offsetX * degreesPerPixelLng;
    const newLat = centerLat - offsetY * degreesPerPixelLat;

    const clampedLat = Math.max(-85, Math.min(85, newLat));
    const clampedLng = Math.max(-180, Math.min(180, newLng));

    setCenterLat(clampedLat);
    setCenterLng(clampedLng);
    onSelectCoordinates(clampedLat, clampedLng);
  };

  const tilesToRender = [];
  for (let dx = -1; dx <= 1; dx++) {
    for (let dy = -1; dy <= 1; dy++) {
      const x = tileX + dx;
      const y = tileY + dy;
      const subdomains = ['a', 'b', 'c'];
      const sub = subdomains[Math.abs(x + y) % 3];
      const url = `https://${sub}.tile.openstreetmap.org/${zoom}/${x}/${y}.png`;
      tilesToRender.push({ x: dx, y: dy, url, key: `${x}-${y}-${zoom}` });
    }
  }

  return (
    <div className="relative w-full h-[280px] sm:h-[340px] rounded-3xl overflow-hidden bg-[#112316] border border-[#E2E7DA]/20 shadow-inner group">
      {/* Map Tile Canvas */}
      <div
        ref={mapContainerRef}
        onClick={handleMapClick}
        className="absolute inset-0 cursor-crosshair select-none flex items-center justify-center overflow-hidden"
      >
        <div className="relative w-[768px] h-[768px] flex items-center justify-center pointer-events-none">
          {tilesToRender.map((tile) => (
            <img
              key={tile.key}
              src={tile.url}
              alt="Map Tile"
              className="absolute w-[256px] h-[256px] opacity-85 contrast-[1.05] brightness-[0.95] saturate-[0.85] transition-opacity duration-300"
              style={{
                transform: `translate(${tile.x * 256}px, ${tile.y * 256}px)`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Grid Overlay Texture for Editorial Aesthetic */}
      <div className="absolute inset-0 bg-[#0B1C10]/15 pointer-events-none" />

      {/* Selected Location Marker Pin */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none z-10 flex flex-col items-center">
        <div className="relative flex items-center justify-center">
          <div className="w-8 h-8 rounded-full bg-[#0B1C10] border-2 border-[#D4E768] shadow-xl flex items-center justify-center animate-bounce">
            <div className="w-3 h-3 rounded-full bg-[#D4E768]" />
          </div>
          <div className="absolute -inset-2 rounded-full border border-[#D4E768]/40 animate-ping pointer-events-none" />
        </div>
        <div className="w-2.5 h-1 bg-[#0B1C10]/40 rounded-full blur-[1px] mt-0.5" />
      </div>

      {/* Map Header Instructions Badge */}
      <div className="absolute top-3 left-3 bg-[#0B1C10]/85 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 text-[11px] font-semibold text-[#FAFBF7] flex items-center gap-1.5 pointer-events-none z-10 shadow-md">
        <Navigation className="w-3 h-3 text-[#D4E768]" />
        <span>Click map to place field pin</span>
      </div>

      {/* Controls Overlay (Zoom + Current Location) */}
      <div className="absolute bottom-3 right-3 flex flex-col gap-2 z-10">
        {onRequestCurrentLocation && (
          <button
            type="button"
            onClick={onRequestCurrentLocation}
            disabled={isLocating}
            className="w-10 h-10 rounded-2xl bg-[#0B1C10]/90 hover:bg-[#0B1C10] text-[#D4E768] border border-white/20 shadow-lg flex items-center justify-center transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
            title="Use my current location"
          >
            <LocateFixed className={`w-5 h-5 ${isLocating ? 'animate-spin' : ''}`} />
          </button>
        )}

        <div className="flex flex-col rounded-2xl bg-[#0B1C10]/90 border border-white/20 shadow-lg overflow-hidden">
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(18, z + 1))}
            className="w-10 h-9 flex items-center justify-center text-[#FAFBF7] hover:bg-white/10 transition-colors border-b border-white/10"
            title="Zoom In"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(3, z - 1))}
            className="w-10 h-9 flex items-center justify-center text-[#FAFBF7] hover:bg-white/10 transition-colors"
            title="Zoom Out"
          >
            <Minus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Coordinates Display Pill */}
      <div className="absolute bottom-3 left-3 bg-[#0B1C10]/85 backdrop-blur-md px-3 py-1.5 rounded-2xl border border-white/10 text-[10px] font-mono text-[#D4E768] z-10 shadow-md">
        {centerLat.toFixed(4)}° N, {centerLng.toFixed(4)}° E
      </div>
    </div>
  );
};
