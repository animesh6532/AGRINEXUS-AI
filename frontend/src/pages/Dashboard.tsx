import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sprout,
  Stethoscope,
  Bug,
  FlaskConical,
  Droplets,
  Mountain,
  TrendingUp,
  Camera,
  CloudSun,
  BarChart3,
  Calendar,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useAuth } from '../context/AuthContext';
import { useHealth } from '../context/HealthContext';
import { api } from '../services/api';
import { CurrentWeatherResponse, MarketPriceRecord, CropCalendarItem } from '../types/api';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { isApiConnected, isModelSystemReady, modelStatus } = useHealth();

  const [weather, setWeather] = useState<CurrentWeatherResponse | null>(null);
  const [market, setMarket] = useState<MarketPriceRecord | null>(null);
  const [catalogue, setCatalogue] = useState<CropCalendarItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [wData, mData, cData] = await Promise.allSettled([
          api.getWeatherCurrent(19.076, 72.8777),
          api.getMarketCurrent('Paddy(Common)'),
          api.getCropCalendarCatalogue()
        ]);

        if (wData.status === 'fulfilled') setWeather(wData.value);
        if (mData.status === 'fulfilled') setMarket(mData.value);
        if (cData.status === 'fulfilled') setCatalogue(cData.value);
      } catch {
        // Safe fallback
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const quickActions = [
    { label: 'Recommend Crop', path: '/crop', icon: <Sprout className="w-5 h-5 text-agri-600" />, color: 'bg-agri-50 border-agri-200' },
    { label: 'Scan Leaf Disease', path: '/disease', icon: <Stethoscope className="w-5 h-5 text-primary-600" />, color: 'bg-primary-50 border-primary-200' },
    { label: 'Check Pest Risk', path: '/pest', icon: <Bug className="w-5 h-5 text-amber-600" />, color: 'bg-amber-50 border-amber-200' },
    { label: 'Fertilizer Advisor', path: '/fertilizer', icon: <FlaskConical className="w-5 h-5 text-purple-600" />, color: 'bg-purple-50 border-purple-200' },
    { label: 'Check Irrigation', path: '/irrigation', icon: <Droplets className="w-5 h-5 text-sky-600" />, color: 'bg-sky-50 border-sky-200' },
    { label: 'Analyze Soil', path: '/soil', icon: <Mountain className="w-5 h-5 text-emerald-600" />, color: 'bg-emerald-50 border-emerald-200' },
    { label: 'Predict Yield', path: '/yield', icon: <TrendingUp className="w-5 h-5 text-indigo-600" />, color: 'bg-indigo-50 border-indigo-200' },
    { label: 'Live Camera CV', path: '/live', icon: <Camera className="w-5 h-5 text-rose-600" />, color: 'bg-rose-50 border-rose-200' },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Welcome back, {user?.name || 'Farmer'}! 👋
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 mt-1">
            Here is your real-time agricultural intelligence overview and ML system status.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/live">
            <Button variant="secondary" size="md" icon={<Camera className="w-4 h-4" />}>
              Open Live Vision
            </Button>
          </Link>
        </div>
      </div>

      {/* Backend & Model System Readiness Banner */}
      <GlassCard variant={isModelSystemReady ? 'light' : 'strong'} className="p-4 sm:p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white ${
              isModelSystemReady ? 'bg-emerald-600' : 'bg-amber-500'
            }`}>
              {isModelSystemReady ? <ShieldCheck className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                {isModelSystemReady ? 'All 8 ML Inference Services Ready' : 'ML Model System Notice'}
              </h3>
              <p className="text-xs text-slate-600 mt-0.5">
                {isModelSystemReady
                  ? '7 frozen artifacts loaded successfully across Crop, Disease, Pest, Fertilizer, Irrigation, Soil, and Yield.'
                  : 'Backend connected, checking model readiness...'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant={isApiConnected ? 'success' : 'danger'} dot>
              {isApiConnected ? 'FastAPI Connected' : 'API Unreachable'}
            </Badge>
            <Badge variant={isModelSystemReady ? 'primary' : 'warning'}>
              {isModelSystemReady ? '8/8 READY' : 'Status Check'}
            </Badge>
          </div>
        </div>
      </GlassCard>

      {/* Quick Actions Grid */}
      <div className="space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">Quick Intelligence Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {quickActions.map((act, idx) => (
            <Link key={idx} to={act.path}>
              <div className={`p-3.5 rounded-2xl border transition-all duration-200 hover:-translate-y-1 hover:shadow-md flex flex-col items-center text-center space-y-2 ${act.color}`}>
                <div className="p-2 rounded-xl bg-white shadow-sm">{act.icon}</div>
                <span className="text-[11px] font-bold text-slate-800 leading-tight">{act.label}</span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Intelligence Snapshot Row (Weather, Market, Crop Calendar) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Weather Snapshot */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200/60 pb-3">
            <div className="flex items-center gap-2">
              <CloudSun className="w-5 h-5 text-sky-600" />
              <h3 className="text-sm font-bold text-slate-900">Current Weather</h3>
            </div>
            <Link to="/weather" className="text-xs text-primary-600 hover:underline font-semibold">View All</Link>
          </div>

          {weather ? (
            <div className="space-y-3">
              <div className="flex items-baseline justify-between">
                <span className="text-3xl font-extrabold text-slate-900">{weather.temperature}°C</span>
                <span className="text-xs font-medium text-slate-500">Humidity: {weather.relative_humidity}%</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded-lg bg-white/70 border border-slate-100">
                  <span className="text-slate-400 block text-[10px]">Precipitation</span>
                  <span className="font-semibold text-slate-800">{weather.precipitation} mm</span>
                </div>
                <div className="p-2 rounded-lg bg-white/70 border border-slate-100">
                  <span className="text-slate-400 block text-[10px]">Wind Speed</span>
                  <span className="font-semibold text-slate-800">{weather.wind_speed} km/h</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400 italic">Loading Open-Meteo weather...</div>
          )}
        </GlassCard>

        {/* Market Price Snapshot */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200/60 pb-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900">Mandi Market Price</h3>
            </div>
            <Link to="/market" className="text-xs text-primary-600 hover:underline font-semibold">View Mandi</Link>
          </div>

          {market ? (
            <div className="space-y-3">
              <div>
                <span className="text-xs font-semibold text-slate-500">{market.commodity} ({market.state})</span>
                <div className="text-2xl font-extrabold text-slate-900 mt-0.5">₹{market.modal_price} <span className="text-xs font-normal text-slate-500">/ quintal</span></div>
              </div>
              <div className="flex justify-between text-xs text-slate-600 pt-1 border-t border-slate-100">
                <span>Min: ₹{market.min_price}</span>
                <span>Max: ₹{market.max_price}</span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400 italic">Fetching Mandi market observations...</div>
          )}
        </GlassCard>

        {/* Crop Calendar Overview */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200/60 pb-3">
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-amber-600" />
              <h3 className="text-sm font-bold text-slate-900">Crop Catalogue</h3>
            </div>
            <Link to="/crop-calendar" className="text-xs text-primary-600 hover:underline font-semibold">View Calendar</Link>
          </div>

          {catalogue.length > 0 ? (
            <div className="space-y-2">
              {catalogue.slice(0, 3).map((c, i) => (
                <div key={i} className="flex items-center justify-between text-xs p-2 rounded-lg bg-white/70 border border-slate-100">
                  <span className="font-semibold text-slate-800 capitalize">{c.crop}</span>
                  <Badge variant="neutral">{c.primary_season}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-400 italic">Loading Crop Catalogue...</div>
          )}
        </GlassCard>
      </div>
    </div>
  );
};
