import React from 'react';

interface WeatherCloudsProps {
  cloudDensity: number; // 0.0 to 1.0
  windSpeed: number; // km/h
  windDirection: number; // degrees
  isDay: boolean;
}

/**
 * Multi-layer atmospheric CSS parallax cloud engine.
 * Cloud visibility and layer opacities respond dynamically to cloudDensity.
 * Movement duration is scaled according to windSpeed.
 */
export const WeatherClouds: React.FC<WeatherCloudsProps> = ({
  cloudDensity,
  windSpeed,
  windDirection,
  isDay,
}) => {
  if (cloudDensity < 0.05) {
    return null;
  }

  // Calculate drift direction (positive or negative horizontal drift)
  const isBlowingEast = windDirection >= 0 && windDirection < 180;
  const directionMultiplier = isBlowingEast ? 1 : -1;

  // Animation durations (seconds for full cycle), inverse of wind speed
  const baseSpeed = Math.max(5, windSpeed);
  const durationFar = `${Math.max(30, Math.round(1800 / baseSpeed))}s`;
  const durationMid = `${Math.max(20, Math.round(1200 / baseSpeed))}s`;
  const durationNear = `${Math.max(12, Math.round(700 / baseSpeed))}s`;

  // Layer Opacities derived from cloudDensity
  const farOpacity = Math.min(0.85, cloudDensity * 0.9);
  const midOpacity = Math.min(0.75, Math.max(0, (cloudDensity - 0.2) * 1.1));
  const nearOpacity = Math.min(0.65, Math.max(0, (cloudDensity - 0.4) * 1.3));

  const cloudColorClass = isDay
    ? cloudDensity > 0.8
      ? 'bg-slate-400/60'
      : 'bg-white/40'
    : 'bg-slate-700/50';

  return (
    <div className="absolute inset-0 z-1 overflow-hidden pointer-events-none transition-opacity duration-1000">
      {/* Layer 1: Far Distance Clouds */}
      {farOpacity > 0.05 && (
        <div
          className="absolute inset-x-0 -top-10 h-64 blur-2xl transition-opacity duration-1000"
          style={{
            opacity: farOpacity,
            animation: `cloudDrift ${durationFar} linear infinite`,
            transform: directionMultiplier < 0 ? 'scaleX(-1)' : 'none',
          }}
        >
          <div className={`w-[140%] h-full ${cloudColorClass} rounded-[100%] transform -translate-x-1/4`} />
        </div>
      )}

      {/* Layer 2: Mid-level Atmospheric Cloud Formations */}
      {midOpacity > 0.05 && (
        <div
          className="absolute inset-x-0 top-0 h-80 blur-xl transition-opacity duration-1000"
          style={{
            opacity: midOpacity,
            animation: `cloudDrift ${durationMid} linear infinite reverse`,
            transform: directionMultiplier < 0 ? 'scaleX(-1)' : 'none',
          }}
        >
          <div className={`w-[120%] h-3/4 ${cloudColorClass} rounded-full transform translate-x-10`} />
        </div>
      )}

      {/* Layer 3: Near Foreground Clouds */}
      {nearOpacity > 0.05 && (
        <div
          className="absolute inset-x-0 top-10 h-96 blur-lg transition-opacity duration-1000"
          style={{
            opacity: nearOpacity,
            animation: `cloudDrift ${durationNear} linear infinite`,
          }}
        >
          <div className={`w-[160%] h-2/3 ${cloudColorClass} rounded-full transform -translate-x-1/3`} />
        </div>
      )}

      <style>{`
        @keyframes cloudDrift {
          0% { transform: translateX(-10%); }
          50% { transform: translateX(5%); }
          100% { transform: translateX(-10%); }
        }
      `}</style>
    </div>
  );
};
