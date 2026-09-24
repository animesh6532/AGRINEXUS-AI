import React from 'react';
import { useLocation } from 'react-router-dom';
import { MapPin, RefreshCw } from 'lucide-react';
import { useHealth } from '../../context/HealthContext';
import { useAuth } from '../../context/AuthContext';

export const Topbar: React.FC = () => {
  const location = useLocation();
  const { isApiConnected, isModelSystemReady, refreshHealth, isLoading } = useHealth();
  const { user } = useAuth();

  const routeTitles: Record<string, { category: string; title: string; subtitle: string }> = {
    '/dashboard': { category: 'OVERVIEW', title: 'Agricultural Intelligence Command Center', subtitle: 'Real-time telemetry, model readiness and active agronomic signals' },
    '/crop': { category: 'FIELD INTELLIGENCE', title: 'Crop Recommendation', subtitle: 'AI-assisted crop selection from soil NPK and climate signals' },
    '/disease': { category: 'FIELD INTELLIGENCE', title: 'Plant Disease Diagnostics', subtitle: 'ResNet18 computer vision leaf diagnosis and Grad-CAM visual heatmaps' },
    '/pest': { category: 'FIELD INTELLIGENCE', title: 'Pest Intelligence Studio', subtitle: 'Single-insect visual classification and microclimate pest outbreak risk' },
    '/fertilizer': { category: 'FIELD INTELLIGENCE', title: 'Fertilizer Recommendation', subtitle: 'Target nutrient product formulation based on soil deficit analysis' },
    '/irrigation': { category: 'FIELD INTELLIGENCE', title: 'Irrigation Predictor', subtitle: '3-Hour Soil Water Content ML forecast vs persistence reference baseline' },
    '/soil': { category: 'FIELD INTELLIGENCE', title: 'Soil Analysis', subtitle: 'Soil Organic Carbon estimation with 95% uncertainty intervals' },
    '/yield': { category: 'FIELD INTELLIGENCE', title: 'Yield Prediction', subtitle: 'Harvest outlook forecasting with XGBoost & prediction bounds' },
    '/live': { category: 'LIVE VISION', title: 'AI Field Vision Studio', subtitle: 'Real-time video frame inference with OpenCV quality assurance' },
    '/weather': { category: 'FIELD SIGNALS', title: 'Weather Intelligence', subtitle: 'Open-Meteo telemetry and field operation disruption signals' },
    '/market': { category: 'FIELD SIGNALS', title: 'Mandi Market Intelligence', subtitle: 'Real mandi pricing observations, ETS forecasts and market signals' },
    '/crop-calendar': { category: 'FIELD SIGNALS', title: 'Crop Calendar Planner', subtitle: 'Agronomic growth stages, sowing windows and field task timeline' },
    '/history': { category: 'ACTIVITY', title: 'Field Intelligence Timeline', subtitle: 'Chronological record of past field analyses and model inferences' },
    '/profile': { category: 'ACCOUNT', title: 'Farmer Profile', subtitle: 'Farm location, primary crop interests and operational preferences' },
    '/settings': { category: 'ACCOUNT', title: 'Platform Settings', subtitle: 'System readiness, API configuration and model registry status' },
  };

  const currentInfo = routeTitles[location.pathname] || {
    category: 'AGRINEXUS-AI',
    title: 'Agricultural Intelligence Platform',
    subtitle: 'Smart Agricultural Decision Support System',
  };

  return (
    <header className="h-20 px-6 sm:px-8 bg-[#FAFBF7]/85 backdrop-blur-xl border-b border-[#E2E7DA] sticky top-0 z-20 flex items-center justify-between shadow-sm">
      {/* Title & Context */}
      <div>
        <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
          {currentInfo.category}
        </span>
        <h2 className="text-base sm:text-lg font-extrabold text-[#0B1C10] font-editorial tracking-tight">
          {currentInfo.title}
        </h2>
        <p className="text-xs text-[#536056] hidden sm:block font-sans">
          "{currentInfo.subtitle}"
        </p>
      </div>

      {/* Controls & Live Indicators */}
      <div className="flex items-center gap-3">
        {/* Location Selector */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#EEF3E8] border border-[#E2E7DA] text-xs font-semibold text-[#162018]">
          <MapPin className="w-3.5 h-3.5 text-[#2F6B3C]" />
          <span>{user?.location || 'Punjab, India'}</span>
        </div>

        {/* System Health Status Indicator Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#0B1C10] text-[#FAFBF7] border border-white/10 text-xs font-semibold">
          <span className={`w-2 h-2 rounded-full ${isModelSystemReady && isApiConnected ? 'bg-[#D4E768] animate-pulse' : 'bg-amber-400'}`} />
          <span className="hidden sm:inline">
            {isModelSystemReady && isApiConnected ? '● Systems operational' : '● System Degraded'}
          </span>
          <span className="sm:hidden">
            {isModelSystemReady && isApiConnected ? 'Ready' : 'Check'}
          </span>
        </div>

        {/* Manual Health Refresh */}
        <button
          onClick={refreshHealth}
          disabled={isLoading}
          className="p-2 rounded-full text-[#536056] hover:text-[#0B1C10] hover:bg-[#EEF3E8] border border-transparent hover:border-[#E2E7DA] transition-colors"
          title="Refresh System Health & Connection"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>

        {/* User Avatar */}
        {user && (
          <div className="w-9 h-9 rounded-full bg-[#2F6B3C] text-white flex items-center justify-center font-extrabold text-xs shadow-sm">
            {user.name.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
    </header>
  );
};
