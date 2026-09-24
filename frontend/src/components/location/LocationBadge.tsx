import React from 'react';
import { MapPin, Navigation, ChevronDown } from 'lucide-react';
import { useLocationContext } from '../../context/LocationContext';

interface LocationBadgeProps {
  variant?: 'pill' | 'button' | 'card' | 'compact';
  className?: string;
}

export const LocationBadge: React.FC<LocationBadgeProps> = ({ variant = 'pill', className = '' }) => {
  const { location, openPicker, isLoading } = useLocationContext();

  const displayName = location
    ? location.city && location.state
      ? `${location.city}, ${location.state}`
      : location.displayName
    : 'Set Field Location';

  if (variant === 'compact') {
    return (
      <button
        onClick={openPicker}
        className={`inline-flex items-center gap-1.5 text-xs font-semibold text-[#2F6B3C] hover:text-[#0B1C10] transition-colors ${className}`}
        title="Change location"
      >
        <MapPin className="w-3.5 h-3.5" />
        <span className="truncate max-w-[140px]">{displayName}</span>
      </button>
    );
  }

  if (variant === 'card') {
    return (
      <div
        onClick={openPicker}
        className={`p-4 rounded-2xl bg-[#112316] border border-white/10 hover:border-[#D4E768]/40 transition-all cursor-pointer group ${className}`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#D4E768]/15 text-[#D4E768] flex items-center justify-center border border-[#D4E768]/30 group-hover:scale-105 transition-transform">
              <MapPin className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-widest text-[#D4E768]/80 block">
                Field Location
              </span>
              <p className="text-sm font-bold text-[#FAFBF7] truncate max-w-[200px] sm:max-w-[280px]">
                {location ? location.displayName : 'No field location set'}
              </p>
              {location?.source && (
                <span className="text-[10px] text-white/50 flex items-center gap-1 mt-0.5">
                  <Navigation className="w-2.5 h-2.5 text-[#D4E768]" />
                  {location.source === 'device' ? 'Device Geolocation' : 'Manually Selected'}
                </span>
              )}
            </div>
          </div>
          <button className="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-[#D4E768] hover:text-[#0B1C10] text-xs font-bold text-[#FAFBF7] transition-colors">
            {location ? 'Change' : 'Set Location'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={openPicker}
      className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EEF3E8] hover:bg-[#E2E7DA] border border-[#E2E7DA] text-xs font-bold text-[#0B1C10] transition-all duration-200 group ${className}`}
      title="Click to select or update field location"
    >
      <MapPin className="w-3.5 h-3.5 text-[#2F6B3C] group-hover:scale-110 transition-transform" />
      <span className="truncate max-w-[160px] sm:max-w-[220px]">
        {isLoading ? 'Locating...' : displayName}
      </span>
      <ChevronDown className="w-3 h-3 text-[#536056] group-hover:translate-y-0.5 transition-transform" />
    </button>
  );
};
