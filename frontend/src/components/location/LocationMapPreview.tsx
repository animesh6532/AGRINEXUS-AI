import React from 'react';
import { MapPin, Navigation } from 'lucide-react';
import { UserLocation } from '../../types/location';

interface LocationMapPreviewProps {
  location: UserLocation | null;
  className?: string;
  onClick?: () => void;
}

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';

export const LocationMapPreview: React.FC<LocationMapPreviewProps> = ({
  location,
  className = '',
  onClick,
}) => {
  if (!location) {
    return (
      <div
        onClick={onClick}
        className={`w-full h-40 rounded-3xl bg-[#112316]/50 border border-dashed border-[#E2E7DA]/30 flex flex-col items-center justify-center p-4 text-center cursor-pointer hover:bg-[#112316] transition-colors ${className}`}
      >
        <MapPin className="w-8 h-8 text-[#536056] mb-2" />
        <p className="text-xs font-bold text-[#FAFBF7]">No Field Location Set</p>
        <p className="text-[11px] text-[#536056] mt-1">Click to select location on map</p>
      </div>
    );
  }

  const lat = location.latitude;
  const lng = location.longitude;
  const zoom = 12;

  const lat2tile = (l: number, z: number) =>
    Math.floor(
      ((1 -
        Math.log(Math.tan((l * Math.PI) / 180) + 1 / Math.cos((l * Math.PI) / 180)) /
          Math.PI) /
        2) *
        Math.pow(2, z)
    );

  const lon2tile = (l: number, z: number) => Math.floor(((l + 180) / 360) * Math.pow(2, z));

  const tileX = lon2tile(lng, zoom);
  const tileY = lat2tile(lat, zoom);
  
  const mapTileUrl = MAPBOX_TOKEN
    ? `https://api.mapbox.com/styles/v1/mapbox/outdoors-v12/tiles/${zoom}/${tileX}/${tileY}?access_token=${MAPBOX_TOKEN}`
    : `https://a.tile.openstreetmap.org/${zoom}/${tileX}/${tileY}.png`;

  return (
    <div
      onClick={onClick}
      className={`relative w-full h-44 rounded-3xl overflow-hidden bg-[#112316] border border-[#E2E7DA]/20 shadow-md group cursor-pointer ${className}`}
    >
      <img
        src={mapTileUrl}
        alt="Field Map Preview"
        className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-500"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10] via-transparent to-transparent opacity-80" />

      {/* Marker Center Pin */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
        <div className="w-7 h-7 rounded-full bg-[#0B1C10] border-2 border-[#D4E768] shadow-lg flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-[#D4E768]" />
        </div>
      </div>

      {/* Location Name & Source Badge */}
      <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
        <div className="min-w-0 pr-2">
          <p className="text-xs font-bold text-[#FAFBF7] truncate drop-shadow">
            📍 {location.displayName}
          </p>
          <p className="text-[10px] text-[#D4E768] font-mono">
            {lat.toFixed(4)}° N, {lng.toFixed(4)}° E
          </p>
        </div>
        <span className="shrink-0 px-2 py-1 rounded-full bg-[#0B1C10]/90 border border-white/10 text-[9px] font-bold text-[#FAFBF7] flex items-center gap-1">
          <Navigation className="w-2.5 h-2.5 text-[#D4E768]" />
          {location.source === 'device' ? 'GPS' : 'Map/Search'}
        </span>
      </div>
    </div>
  );
};

