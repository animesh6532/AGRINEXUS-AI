import React from 'react';
import { VisualWeatherCondition } from '../../types/weatherVisualization';

interface WeatherSkyProps {
  condition: VisualWeatherCondition;
  isDay: boolean;
  sunVisibility: number;
}

/**
 * WeatherSky provides the base atmospheric background gradient with dynamic CSS transitions.
 */
export const WeatherSky: React.FC<WeatherSkyProps> = ({
  condition,
  isDay,
  sunVisibility,
}) => {
  // Determine gradient based on weather condition and day/night state
  const getSkyGradient = (): string => {
    if (!isDay) {
      switch (condition) {
        case 'THUNDERSTORM':
        case 'HEAVY_RAIN':
          return 'from-[#030712] via-[#0B1528] to-[#040A14]';
        case 'RAIN':
        case 'DRIZZLE':
          return 'from-[#070F1E] via-[#0F1B2D] to-[#0A1220]';
        case 'SNOW':
        case 'HEAVY_SNOW':
          return 'from-[#0B132B] via-[#1C2541] to-[#0F172A]';
        case 'FOG':
          return 'from-[#0F172A] via-[#1E293B] to-[#111827]';
        case 'OVERCAST':
        case 'CLOUDY':
          return 'from-[#0B1320] via-[#152238] to-[#0C1524]';
        case 'CLEAR_NIGHT':
        default:
          return 'from-[#0B192C] via-[#1E3E62] to-[#0B1528]';
      }
    } else {
      switch (condition) {
        case 'THUNDERSTORM':
          return 'from-[#1E293B] via-[#334155] to-[#0F172A]';
        case 'HEAVY_RAIN':
          return 'from-[#334155] via-[#475569] to-[#1E293B]';
        case 'RAIN':
        case 'DRIZZLE':
          return 'from-[#475569] via-[#64748B] to-[#334155]';
        case 'OVERCAST':
          return 'from-[#64748B] via-[#94A3B8] to-[#475569]';
        case 'CLOUDY':
          return 'from-[#38BDF8] via-[#60A5FA] to-[#475569]';
        case 'PARTLY_CLOUDY_DAY':
          return 'from-[#0EA5E9] via-[#38BDF8] to-[#93C5FD]';
        case 'FOG':
          return 'from-[#94A3B8] via-[#CBD5E1] to-[#64748B]';
        case 'SNOW':
        case 'HEAVY_SNOW':
          return 'from-[#94A3B8] via-[#E2E8F0] to-[#64748B]';
        case 'CLEAR_DAY':
        default:
          return 'from-[#0284C7] via-[#38BDF8] to-[#BAE6FD]';
      }
    }
  };

  return (
    <div
      className={`absolute inset-0 bg-gradient-to-b ${getSkyGradient()} transition-colors duration-1000 overflow-hidden pointer-events-none`}
    >
      {/* Sun / Celestial Glow (Daytime) */}
      {isDay && sunVisibility > 0.05 && (
        <div
          className="absolute top-[10%] right-[15%] w-72 h-72 rounded-full bg-gradient-to-tr from-amber-200/40 via-yellow-100/20 to-transparent blur-3xl pointer-events-none transition-opacity duration-1000"
          style={{ opacity: sunVisibility }}
        >
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-28 h-28 rounded-full bg-yellow-100/70 shadow-[0_0_80px_rgba(255,230,150,0.6)]" />
        </div>
      )}

      {/* Moon & Subtle Stars (Nighttime) */}
      {!isDay && (
        <>
          <div
            className="absolute top-[12%] right-[18%] w-24 h-24 rounded-full bg-slate-100/90 shadow-[0_0_50px_rgba(255,255,255,0.4)] pointer-events-none transition-opacity duration-1000"
            style={{ opacity: Math.max(0.3, sunVisibility) }}
          >
            <div className="absolute top-2 right-2 w-20 h-20 rounded-full bg-[#0B192C]/40" />
          </div>

          {/* Celestial background stars */}
          <div className="absolute inset-0 opacity-40 pointer-events-none bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:32px_32px]" />
        </>
      )}

      {/* Soft Horizon Blend for UI Contrast */}
      <div className="absolute bottom-0 inset-x-0 h-48 bg-gradient-to-t from-black/60 via-black/20 to-transparent pointer-events-none" />
    </div>
  );
};
