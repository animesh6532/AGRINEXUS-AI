import React from 'react';
import { MapPin, Navigation, ChevronDown } from 'lucide-react';
import { useLocationContext } from '../../context/LocationContext';

interface LocationBadgeProps {
  variant?: 'pill' | 'button' | 'card' | 'compact' | 'sidebar' | 'sidebar-collapsed';
  className?: string;
}

export const LocationBadge: React.FC<LocationBadgeProps> = ({ variant = 'pill', className = '' }) => {
  const { location, openPicker, isLoading } = useLocationContext();

  const getSourceLabel = (src?: string) => {
    switch (src) {
      case 'device':
        return 'Current Device Location';
      case 'search':
        return 'Search Result';
      case 'map':
        return 'Map Selection';
      case 'manual':
        return 'Manual Entry';
      default:
        return 'Field Location';
    }
  };

  const displayName = location
    ? location.city && location.state
      ? `${location.city}, ${location.state}`
      : location.displayName
    : 'Set Location';

  const shortCity = location
    ? location.city || location.displayName.split(',')[0]
    : 'Location not set';

  if (variant === 'sidebar-collapsed') {
    return (
      <button
        onClick={openPicker}
        className={`w-10 h-10 mx-auto rounded-2xl bg-[#112316] hover:bg-white/10 border border-white/10 flex items-center justify-center text-[#D4E768] transition-all group ${className}`}
        title={location ? `Field Location: ${location.displayName}` : 'Change field location'}
      >
        <MapPin className="w-4 h-4 group-hover:scale-110 transition-transform" />
      </button>
    );
  }

  if (variant === 'sidebar') {
    return (
      <button
        onClick={openPicker}
        className={`w-full p-3 rounded-2xl bg-[#112316] hover:bg-[#162a1c] border border-white/10 hover:border-[#D4E768]/30 transition-all flex items-center justify-between text-left group ${className}`}
        title="Click to select or update field location"
      >
        <div className="flex items-center gap-2.5 min-w-0 pr-2">
          <div className="w-7 h-7 rounded-xl bg-[#D4E768]/15 text-[#D4E768] flex items-center justify-center shrink-0">
            <MapPin className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${location ? 'bg-[#D4E768]' : 'bg-white/30'}`} />
              <span className="text-[10px] font-bold uppercase tracking-wider text-white/50 block truncate">
                FIELD LOCATION
              </span>
            </div>
            <p className="text-xs font-bold text-[#FAFBF7] truncate">
              {isLoading ? 'Locating...' : shortCity}
            </p>
          </div>
        </div>
        <ChevronDown className="w-3.5 h-3.5 text-white/50 group-hover:text-white shrink-0 transition-transform" />
      </button>
    );
  }

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
                  {getSourceLabel(location.source)}
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

