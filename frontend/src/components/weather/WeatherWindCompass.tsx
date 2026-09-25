import React from 'react';
import { Navigation } from 'lucide-react';

interface WeatherWindCompassProps {
  windSpeed: number; // km/h
  windDirection: number; // degrees 0-360
  windGusts?: number; // km/h
}

export const WeatherWindCompass: React.FC<WeatherWindCompassProps> = ({
  windSpeed,
  windDirection,
  windGusts,
}) => {
  // Map degrees to compass cardinal direction
  const getCardinalDirection = (deg: number): string => {
    const normalized = (deg % 360 + 360) % 360;
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(normalized / 45) % 8;
    return directions[index];
  };

  const cardinal = getCardinalDirection(windDirection);

  return (
    <div className="bg-black/30 backdrop-blur-md border border-white/10 rounded-2xl p-5 flex items-center justify-between gap-4 text-white">
      <div>
        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
          Wind Velocity & Direction
        </span>
        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-3xl font-black font-editorial text-white">
            {windSpeed}
          </span>
          <span className="text-xs text-slate-300 font-medium">km/h</span>
          <span className="ml-2 text-sm font-extrabold text-[#D4E768] bg-[#D4E768]/10 px-2 py-0.5 rounded-lg border border-[#D4E768]/20">
            {cardinal} ({windDirection.toFixed(0)}°)
          </span>
        </div>

        {windGusts !== undefined && (
          <span className="text-xs text-slate-400 mt-1 block">
            Wind Gusts: <strong className="text-slate-200">{windGusts} km/h</strong>
          </span>
        )}
      </div>

      {/* Dynamic Rotatable Compass Dial */}
      <div className="relative w-16 h-16 shrink-0 rounded-full border-2 border-white/20 flex items-center justify-center bg-black/40 shadow-inner">
        {/* Cardinal Markers */}
        <span className="absolute top-0.5 text-[9px] font-black text-slate-400">N</span>
        <span className="absolute right-1 text-[9px] font-black text-slate-400">E</span>
        <span className="absolute bottom-0.5 text-[9px] font-black text-slate-400">S</span>
        <span className="absolute left-1 text-[9px] font-black text-slate-400">W</span>

        {/* Rotating Compass Pointer */}
        <div
          className="transition-transform duration-700 ease-out flex items-center justify-center"
          style={{ transform: `rotate(${windDirection}deg)` }}
        >
          <Navigation className="w-7 h-7 text-[#D4E768] fill-[#D4E768]/30 drop-shadow-[0_0_8px_rgba(212,231,104,0.6)]" />
        </div>
      </div>
    </div>
  );
};
