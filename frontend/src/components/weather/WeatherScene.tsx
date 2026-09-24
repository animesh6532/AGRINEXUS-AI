import React from 'react';
import { WeatherVisualizationState } from '../../types/weatherVisualization';
import { WeatherSky } from './WeatherSky';
import { WeatherClouds } from './WeatherClouds';
import { WeatherCanvas } from './WeatherCanvas';

interface WeatherSceneProps {
  state: WeatherVisualizationState;
  children?: React.ReactNode;
}

/**
 * WeatherScene coordinates atmospheric visual layers and provides the background engine for the page.
 */
export const WeatherScene: React.FC<WeatherSceneProps> = ({ state, children }) => {
  const { condition, isDay, intensity } = state;

  return (
    <div className="relative w-full rounded-3xl overflow-hidden shadow-2xl border border-white/10 bg-[#0B192C] min-h-[420px] lg:min-h-[480px] flex flex-col justify-between">
      {/* Layer 0: Sky Gradient & Celestial Elements (z-0) */}
      <WeatherSky condition={condition} isDay={isDay} sunVisibility={intensity.sunVisibility} />

      {/* Layer 1: Multi-layer Parallax Clouds (z-1) */}
      <WeatherClouds
        cloudDensity={intensity.cloudDensity}
        windSpeed={state.windSpeed}
        windDirection={state.windDirection}
        isDay={isDay}
      />

      {/* Layer 2: Canvas 2D Particle Engine (Rain, Splashes, Snow, Wind, Lightning) (z-2) */}
      <WeatherCanvas intensity={intensity} />

      {/* Layer 3: Layered Translucent Fog Atmospheric Gradient (z-3) */}
      {intensity.fogIntensity > 0.05 && (
        <div
          className="absolute inset-0 bg-gradient-to-t from-slate-300/40 via-slate-400/20 to-transparent pointer-events-none transition-opacity duration-1000 z-3"
          style={{ opacity: intensity.fogIntensity }}
        />
      )}

      {/* Layer 4: Telemetry UI Overlay & Controls (relative z-10) */}
      <div className="relative z-10 p-6 sm:p-8 md:p-10">{children}</div>
    </div>
  );
};
