import React from 'react';
import { useLocation } from 'react-router-dom';
import { MapPin, RefreshCw, Bell, User as UserIcon } from 'lucide-react';
import { useHealth } from '../../context/HealthContext';
import { useAuth } from '../../context/AuthContext';
import { Badge } from '../ui/Badge';

export const Topbar: React.FC = () => {
  const location = useLocation();
  const { isApiConnected, isModelSystemReady, refreshHealth, isLoading } = useHealth();
  const { user } = useAuth();

  const routeTitles: Record<string, { title: string; subtitle: string }> = {
    '/dashboard': { title: 'Dashboard', subtitle: 'Farm operational overview & active ML intelligence' },
    '/crop': { title: 'Crop Recommendation', subtitle: 'Soil and climate feature-based crop matching' },
    '/disease': { title: 'Plant Disease Detection', subtitle: 'ResNet18 computer vision leaf diagnosis & Grad-CAM' },
    '/pest': { title: 'Pest Intelligence', subtitle: 'Insect visual classification & outbreak risk modeling' },
    '/fertilizer': { title: 'Fertilizer Advisor', subtitle: 'Target product formulation recommendation' },
    '/irrigation': { title: 'Irrigation Predictor', subtitle: 'Soil Water Content 3h ML vs Persistence baseline' },
    '/soil': { title: 'Soil Analysis', subtitle: 'Soil Organic Carbon estimation with 95% intervals' },
    '/yield': { title: 'Yield Prediction', subtitle: 'Crop yield estimation with uncertainty intervals' },
    '/live': { title: 'Live Camera Vision', subtitle: 'Real-time video frame inference with OpenCV quality gates' },
    '/weather': { title: 'Weather Intelligence', subtitle: 'Open-Meteo forecasts and field disruption signals' },
    '/market': { title: 'Market Intelligence', subtitle: 'Mandi pricing, ETS/ARIMA forecasts & market signals' },
    '/crop-calendar': { title: 'Crop Calendar', subtitle: 'Growth stages, sowing windows, and agronomic tasks' },
    '/history': { title: 'Analysis History', subtitle: 'Local session analysis records & summary exports' },
    '/profile': { title: 'Farmer Profile', subtitle: 'Farm location and agricultural preferences' },
    '/settings': { title: 'Platform Settings', subtitle: 'System status, theme preferences, and API configs' },
  };

  const currentInfo = routeTitles[location.pathname] || {
    title: 'AgriNexus-AI Platform',
    subtitle: 'Smart Agricultural Decision Support System',
  };

  return (
    <header className="h-16 px-6 glass-panel-strong border-b border-slate-200/80 sticky top-0 z-20 flex items-center justify-between">
      {/* Title & Context */}
      <div>
        <h2 className="text-base font-bold text-slate-900 tracking-tight">{currentInfo.title}</h2>
        <p className="text-xs text-slate-500 hidden sm:block">{currentInfo.subtitle}</p>
      </div>

      {/* Controls & Live Indicators */}
      <div className="flex items-center gap-3">
        {/* Location Selector */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/70 border border-slate-200/60 text-xs font-medium text-slate-700">
          <MapPin className="w-3.5 h-3.5 text-primary-600" />
          <span>{user?.location || 'Punjab, India'}</span>
        </div>

        {/* Backend API Connectivity Status */}
        <Badge variant={isApiConnected ? 'success' : 'danger'} dot>
          {isApiConnected ? 'API Connected' : 'API Offline'}
        </Badge>

        {/* Model Readiness Status */}
        <Badge variant={isModelSystemReady ? 'primary' : 'warning'} dot className="hidden md:inline-flex">
          {isModelSystemReady ? 'Model System Ready' : 'Models Degraded'}
        </Badge>

        {/* Manual Health Refresh */}
        <button
          onClick={refreshHealth}
          disabled={isLoading}
          className="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-white/80 transition-colors"
          title="Refresh Backend Connection & Model Status"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>

        {/* Profile Avatar */}
        {user && (
          <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center font-bold text-xs shadow-sm ml-1">
            {user.name.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
    </header>
  );
};
