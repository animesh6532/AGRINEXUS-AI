import React from 'react';
import { RefreshCw, MapPin, Clock, AlertTriangle, ShieldCheck } from 'lucide-react';
import { WeatherVisualizationState } from '../../types/weatherVisualization';
import { getWeatherCodeDetails } from '../../utils/weatherCodeMapper';
import { Button } from '../ui/Button';

interface WeatherHeroProps {
  state: WeatherVisualizationState;
  onRefresh: () => void;
  isLoading: boolean;
  onOpenLocationPicker: () => void;
}

export const WeatherHero: React.FC<WeatherHeroProps> = ({
  state,
  onRefresh,
  isLoading,
  onOpenLocationPicker,
}) => {
  const details = getWeatherCodeDetails(state.weatherCode, state.isDay);

  const getFreshnessLabel = () => {
    if (state.isStale) {
      return `Updated ${state.dataAgeMinutes} min ago (Stale Data)`;
    }
    if (state.dataAgeMinutes <= 1) {
      return '● LIVE OBSERVATION';
    }
    return `Updated ${state.dataAgeMinutes} min ago`;
  };

  return (
    <div className="space-y-6 text-white">
      {/* Top Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenLocationPicker}
            className="flex items-center gap-2 bg-black/40 hover:bg-black/60 backdrop-blur-md px-4 py-2 rounded-2xl border border-white/20 transition text-sm font-semibold"
          >
            <MapPin className="w-4 h-4 text-[#D4E768]" />
            <span>{state.locationName}</span>
          </button>

          <span className="text-xs font-mono bg-black/30 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 text-slate-300 hidden sm:inline-block">
            {state.latitude.toFixed(4)}° N, {state.longitude.toFixed(4)}° E
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Freshness Badge */}
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-bold font-mono backdrop-blur-md border ${
              state.isStale
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
            }`}
          >
            {state.isStale ? (
              <AlertTriangle className="w-3.5 h-3.5" />
            ) : (
              <Clock className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
            )}
            <span>{getFreshnessLabel()}</span>
          </div>

          <Button
            variant="lime"
            size="sm"
            onClick={onRefresh}
            isLoading={isLoading}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Main Temperature & Condition Display */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end pt-4">
        <div>
          <div className="flex items-baseline gap-4">
            <span className="text-6xl sm:text-7xl font-black font-editorial tracking-tight drop-shadow-md">
              {state.temperature.toFixed(1)}°
            </span>
            <span className="text-2xl sm:text-3xl font-bold text-slate-200">C</span>
          </div>

          <div className="mt-2 space-y-1">
            <h2 className="text-2xl sm:text-3xl font-extrabold font-editorial text-[#D4E768] tracking-wide">
              {details.label}
            </h2>
            <p className="text-xs sm:text-sm text-slate-200/90 leading-relaxed max-w-md font-sans">
              {details.description}
            </p>
          </div>
        </div>

        {/* Secondary Telemetry Quick Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {state.apparentTemperature !== undefined && (
            <div className="bg-black/30 backdrop-blur-md border border-white/10 p-3 rounded-2xl">
              <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
                Feels Like
              </span>
              <span className="text-xl font-bold font-editorial text-white">
                {state.apparentTemperature.toFixed(1)}°C
              </span>
            </div>
          )}

          <div className="bg-black/30 backdrop-blur-md border border-white/10 p-3 rounded-2xl">
            <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
              Humidity
            </span>
            <span className="text-xl font-bold font-editorial text-white">
              {state.humidity}%
            </span>
          </div>

          <div className="bg-black/30 backdrop-blur-md border border-white/10 p-3 rounded-2xl">
            <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
              Precipitation
            </span>
            <span className="text-xl font-bold font-editorial text-white">
              {state.precipitation} <span className="text-xs font-sans font-normal text-slate-300">mm</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
