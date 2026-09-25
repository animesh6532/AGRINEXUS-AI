import React from 'react';
import { MapPin, Navigation, Search, LocateFixed, ShieldCheck } from 'lucide-react';
import { useLocationContext } from '../../context/LocationContext';

interface LocationEmptyStateProps {
  className?: string;
  title?: string;
  subtitle?: string;
}

export const LocationEmptyState: React.FC<LocationEmptyStateProps> = ({
  className = '',
  title = 'WHERE IS YOUR FIELD?',
  subtitle = 'Set your field location to unlock localized weather telemetry, regional mandi pricing, pest outbreak risk modeling and precision nutrient recommendations.',
}) => {
  const { requestCurrentLocation, openPicker, isLoading, error } = useLocationContext();

  return (
    <div
      className={`relative overflow-hidden rounded-3xl bg-[#0B1C10] text-[#FAFBF7] border border-[#D4E768]/30 p-6 sm:p-8 shadow-xl ${className}`}
    >
      {/* Decorative Organic Backdrop Pattern */}
      <div className="absolute top-0 right-0 -mt-10 -mr-10 w-64 h-64 rounded-full bg-[#D4E768]/5 blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-2xl mx-auto text-center space-y-5">
        {/* Icon Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#112316] border border-[#D4E768]/30 text-xs font-bold text-[#D4E768]">
          <MapPin className="w-3.5 h-3.5" />
          <span>FIELD LOCATION REQUIRED</span>
        </div>

        {/* Heading */}
        <h2 className="text-xl sm:text-2xl font-extrabold font-editorial tracking-tight text-[#FAFBF7]">
          {title}
        </h2>

        {/* Subtitle */}
        <p className="text-xs sm:text-sm text-white/70 leading-relaxed max-w-xl mx-auto">
          {subtitle}
        </p>

        {/* Privacy Note */}
        <div className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-2xl bg-white/5 border border-white/10 text-xs text-white/80">
          <ShieldCheck className="w-4 h-4 text-[#D4E768] shrink-0" />
          <span>
            Your location is used strictly to personalize weather, agricultural insights and recommendations. We never continuously track you.
          </span>
        </div>

        {/* Error Message Display if permission was denied or timeout */}
        {error && (
          <div className="p-3 rounded-2xl bg-rose-950/60 border border-rose-500/30 text-xs text-rose-300">
            {error}
          </div>
        )}

        {/* Action CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <button
            onClick={requestCurrentLocation}
            disabled={isLoading}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-2xl bg-[#D4E768] text-[#0B1C10] font-extrabold text-xs tracking-wide hover:bg-[#c8db5b] transition-all shadow-lg active:scale-98 disabled:opacity-50"
          >
            <LocateFixed className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Acquiring GPS Location...' : 'Use My Current Location'}</span>
          </button>

          <button
            onClick={openPicker}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-2xl bg-[#112316] text-[#FAFBF7] border border-white/20 font-bold text-xs tracking-wide hover:bg-white/10 hover:border-[#D4E768]/40 transition-all active:scale-98"
          >
            <Search className="w-4 h-4 text-[#D4E768]" />
            <span>Search Location Manually</span>
          </button>
        </div>
      </div>
    </div>
  );
};
