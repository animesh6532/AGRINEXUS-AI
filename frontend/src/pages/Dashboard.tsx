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
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  MapPin,
  RefreshCw,
} from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { useFarmerProfile } from '../context/FarmerProfileContext';
import { useGreeting } from '../utils/greeting';
import { useHealth } from '../context/HealthContext';
import { useLocationContext } from '../context/LocationContext';
import { LocationEmptyState } from '../components/location/LocationEmptyState';
import { LocationBadge } from '../components/location/LocationBadge';
import { api } from '../services/api';
import { CurrentWeatherResponse, MarketPriceRecord, CropCalendarItem } from '../types/api';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { farmer } = useFarmerProfile();
  const { fullGreeting } = useGreeting(farmer, user);
  const { isApiConnected, isModelSystemReady } = useHealth();
  const { location, openPicker } = useLocationContext();

  const [weather, setWeather] = useState<CurrentWeatherResponse | null>(null);
  const [market, setMarket] = useState<MarketPriceRecord | null>(null);
  const [catalogue, setCatalogue] = useState<CropCalendarItem[]>([]);
  const [isRefreshingWeather, setIsRefreshingWeather] = useState<boolean>(false);

  useEffect(() => {
    async function loadData() {
      setIsRefreshingWeather(true);
      try {
        const promises: Promise<any>[] = [api.getCropCalendarCatalogue()];

        if (location) {
          promises.push(api.getWeatherCurrent(location.latitude, location.longitude));
          promises.push(api.getMarketCurrent('Paddy(Common)', location.state));
        }

        const results = await Promise.allSettled(promises);
        if (results[0].status === 'fulfilled') setCatalogue(results[0].value);

        if (location) {
          if (results[1] && results[1].status === 'fulfilled') setWeather(results[1].value);
          if (results[2] && results[2].status === 'fulfilled') setMarket(results[2].value);
        } else {
          setWeather(null);
          setMarket(null);
        }
      } catch {
        // Safe fallback
      } finally {
        setIsRefreshingWeather(false);
      }
    }
    loadData();
  }, [location?.latitude, location?.longitude, location?.state]);

  const quickActions = [
    { label: 'Recommend Crop', path: '/crop', icon: <Sprout className="w-5 h-5 text-[#2F6B3C]" /> },
    { label: 'Scan Leaf Disease', path: '/disease', icon: <Stethoscope className="w-5 h-5 text-[#2F6B3C]" /> },
    { label: 'Check Pest Risk', path: '/pest', icon: <Bug className="w-5 h-5 text-amber-700" /> },
    { label: 'Fertilizer Advisor', path: '/fertilizer', icon: <FlaskConical className="w-5 h-5 text-purple-700" /> },
    { label: 'Predict Irrigation', path: '/irrigation', icon: <Droplets className="w-5 h-5 text-sky-700" /> },
    { label: 'Analyze Soil SOC', path: '/soil', icon: <Mountain className="w-5 h-5 text-emerald-800" /> },
    { label: 'Forecast Yield', path: '/yield', icon: <TrendingUp className="w-5 h-5 text-indigo-700" /> },
    { label: 'Live Camera Vision', path: '/live', icon: <Camera className="w-5 h-5 text-rose-700" /> },
  ];

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* 1. Large Greeting Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-[#E2E7DA] pb-6">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
            COMMAND CENTER OVERVIEW
          </span>
          <h1 className="text-3xl sm:text-5xl font-black font-editorial tracking-tight text-[#0B1C10] mt-1">
            {fullGreeting}
          </h1>
          <p className="text-xs sm:text-sm text-[#536056] mt-1 font-sans">
            Here is what your field intelligence & active model signals look like today.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/live">
            <Button variant="lime" size="md" icon={<Camera className="w-4 h-4" />}>
              Open Live Vision Studio
            </Button>
          </Link>
        </div>
      </div>

      {/* Location Onboarding Banner if location is not configured */}
      {!location && <LocationEmptyState />}

      {/* 2. Hero Section: Cinematic Farmland Overlay Panel */}
      <div className="relative rounded-3xl overflow-hidden bg-[#0B1C10] text-[#FAFBF7] p-8 sm:p-12 border border-[#E2E7DA]/20 shadow-xl min-h-[260px] flex flex-col justify-between group">
        <div className="absolute inset-0 z-0 overflow-hidden">
          <img
            src="/images/hero-farmland.webp"
            alt="Farm Hero Background"
            className="w-full h-full object-cover object-center opacity-40 transition-transform duration-1000 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#0B1C10] via-[#0B1C10]/80 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10] via-transparent to-transparent" />
        </div>

        <div className="relative z-10 space-y-4 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#D4E768] text-[#0B1C10] text-xs font-extrabold uppercase tracking-widest">
            FARM INTELLIGENCE SYSTEM
          </div>

          <h2 className="text-2xl sm:text-4xl font-extrabold font-editorial tracking-tight text-[#FAFBF7]">
            {isModelSystemReady ? '8/8 Inference Services Ready' : 'ML Model Readiness Check'}
          </h2>

          <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-sans">
            {location ? (
              <>
                Your agricultural intelligence is currently personalized for{' '}
                <strong className="text-[#D4E768] font-semibold">{location.displayName}</strong>.
              </>
            ) : (
              'Set your field location to unlock localized weather, mandi prices and pest outbreak risk signals.'
            )}
          </p>
        </div>

        <div className="relative z-10 pt-6 flex items-center justify-between border-t border-white/10 flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 border border-white/15 text-white">
              {isModelSystemReady ? (
                <ShieldCheck className="w-4 h-4 text-[#D4E768]" />
              ) : (
                <ShieldAlert className="w-4 h-4 text-amber-400" />
              )}
              {isModelSystemReady ? 'All Models Operational' : 'Degraded Operational State'}
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 border border-white/15 text-white">
              {isApiConnected ? '● FastAPI Online' : '● API Offline'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {location ? (
              <button
                onClick={openPicker}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#D4E768]/20 border border-[#D4E768]/40 text-[#D4E768] font-bold hover:bg-[#D4E768] hover:text-[#0B1C10] transition-all"
              >
                <MapPin className="w-3.5 h-3.5" />
                <span>📍 {location.city || location.displayName.split(',')[0]}</span>
              </button>
            ) : (
              <button
                onClick={openPicker}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/20 border border-amber-400/40 text-amber-300 font-bold hover:bg-amber-400 hover:text-[#0B1C10] transition-all"
              >
                <MapPin className="w-3.5 h-3.5" />
                <span>📍 Set Field Location</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 3. Quick Actions Pill Navigation */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
            Field Intelligence Workspaces
          </h2>
          <span className="text-xs text-[#2F6B3C] font-semibold">8 Active Services</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {quickActions.map((act, idx) => (
            <Link key={idx} to={act.path}>
              <div className="p-4 rounded-2xl bg-white border border-[#E2E7DA] hover:border-[#D4E768] hover:shadow-card-hover transition-all duration-300 flex flex-col items-center text-center space-y-2 group">
                <div className="p-3 rounded-xl bg-[#EEF3E8] group-hover:bg-[#D4E768] transition-colors">
                  {act.icon}
                </div>
                <span className="text-xs font-bold text-[#162018] group-hover:text-[#2F6B3C] leading-tight">
                  {act.label}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* 4. Three Major Editorial Panels: Weather, Market, Crop Calendar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Weather Telemetry Panel */}
        <GlassCard variant="cream" className="p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
            <div className="flex items-center gap-2">
              <CloudSun className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                Weather Telemetry
              </h3>
            </div>
            <Link
              to="/weather"
              className="text-xs text-[#2F6B3C] hover:underline font-bold flex items-center gap-0.5"
            >
              <span>View</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {isRefreshingWeather ? (
            <div className="text-xs text-[#536056] py-8 text-center flex flex-col items-center gap-2">
              <RefreshCw className="w-5 h-5 text-[#2F6B3C] animate-spin" />
              <span>Updating weather telemetry for location...</span>
            </div>
          ) : weather ? (
            <div className="space-y-4">
              <div className="flex items-baseline justify-between">
                <div>
                  <span className="text-4xl font-extrabold font-editorial text-[#0B1C10]">
                    {weather.temperature}°C
                  </span>
                  <span className="text-xs text-[#536056] block">Air Temperature</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold text-[#2F6B3C]">
                    {weather.relative_humidity}%
                  </span>
                  <span className="text-[10px] text-[#536056] block uppercase tracking-wider">
                    Humidity
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-[#E2E7DA]">
                <div className="p-2.5 rounded-xl bg-white border border-[#E2E7DA]">
                  <span className="text-[#536056] block text-[10px] uppercase font-bold">
                    Rainfall
                  </span>
                  <span className="font-extrabold text-[#0B1C10]">
                    {weather.precipitation} mm
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-white border border-[#E2E7DA]">
                  <span className="text-[#536056] block text-[10px] uppercase font-bold">
                    Wind Speed
                  </span>
                  <span className="font-extrabold text-[#0B1C10]">
                    {weather.wind_speed} km/h
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-[#536056] py-6 text-center space-y-2">
              <p>Set a field location to view real-time weather telemetry.</p>
              <button
                onClick={openPicker}
                className="px-3 py-1.5 rounded-xl bg-[#EEF3E8] border border-[#E2E7DA] text-xs font-bold text-[#2F6B3C] hover:bg-[#D4E768] hover:text-[#0B1C10] transition-colors"
              >
                Set Location
              </button>
            </div>
          )}
        </GlassCard>

        {/* Mandi Market Intelligence Panel */}
        <GlassCard variant="cream" className="p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                Mandi Market Price
              </h3>
            </div>
            <Link
              to="/market"
              className="text-xs text-[#2F6B3C] hover:underline font-bold flex items-center gap-0.5"
            >
              <span>View</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {market ? (
            <div className="space-y-4">
              <div>
                <span className="text-xs font-bold text-[#536056] uppercase tracking-wider block">
                  {market.commodity} ({market.state})
                </span>
                <div className="text-3xl font-black font-editorial text-[#0B1C10] mt-1">
                  ₹{market.modal_price}{' '}
                  <span className="text-xs font-sans font-medium text-[#536056]">/ quintal</span>
                </div>
              </div>

              <div className="flex justify-between text-xs font-semibold text-[#162018] pt-3 border-t border-[#E2E7DA]">
                <span>Min: ₹{market.min_price}</span>
                <span className="text-[#2F6B3C]">Modal: ₹{market.modal_price}</span>
                <span>Max: ₹{market.max_price}</span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-[#536056] italic py-6 text-center">
              Fetching Mandi market prices...
            </div>
          )}
        </GlassCard>

        {/* Crop Calendar Panel */}
        <GlassCard variant="cream" className="p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                Crop Catalogue
              </h3>
            </div>
            <Link
              to="/crop-calendar"
              className="text-xs text-[#2F6B3C] hover:underline font-bold flex items-center gap-0.5"
            >
              <span>View</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {catalogue.length > 0 ? (
            <div className="space-y-2.5">
              {catalogue.slice(0, 3).map((c, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-xs p-2.5 rounded-xl bg-white border border-[#E2E7DA]"
                >
                  <span className="font-bold text-[#0B1C10] capitalize">{c.crop}</span>
                  <span className="px-2 py-0.5 rounded-full bg-[#EEF3E8] text-[#2F6B3C] text-[10px] font-bold uppercase">
                    {c.primary_season}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-[#536056] italic py-6 text-center">
              Loading Crop Catalogue...
            </div>
          )}
        </GlassCard>
      </div>

      {/* 5. Field Intelligence Summary Indicators */}
      <div className="p-6 rounded-3xl bg-[#0B1C10] text-[#FAFBF7] space-y-4 border border-white/10">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-widest text-[#D4E768]">
            FIELD INTELLIGENCE SUMMARY
          </span>
          <span className="text-xs text-white/60">Live Signal Telemetry</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-[#112316] border border-white/10">
            <span className="text-[10px] font-bold uppercase tracking-wider text-white/50 block">
              SOIL SOC
            </span>
            <span className="text-sm font-extrabold text-[#FAFBF7] mt-1 block">
              Optimal Organic Content
            </span>
            <span className="text-[10px] text-[#D4E768]">SOC Prediction Model Active</span>
          </div>

          <div className="p-4 rounded-2xl bg-[#112316] border border-white/10">
            <span className="text-[10px] font-bold uppercase tracking-wider text-white/50 block">
              WATER / SWC
            </span>
            <span className="text-sm font-extrabold text-[#FAFBF7] mt-1 block">
              3h Forecast Ready
            </span>
            <span className="text-[10px] text-[#D4E768]">ML vs Persistence Active</span>
          </div>

          <div className="p-4 rounded-2xl bg-[#112316] border border-white/10">
            <span className="text-[10px] font-bold uppercase tracking-wider text-white/50 block">
              WEATHER
            </span>
            <span className="text-sm font-extrabold text-[#FAFBF7] mt-1 block">
              {location ? 'Open-Meteo Synced' : 'Location Not Set'}
            </span>
            <span className="text-[10px] text-[#D4E768]">
              {location ? location.displayName.split(',')[0] : 'Set field location'}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-[#112316] border border-white/10">
            <span className="text-[10px] font-bold uppercase tracking-wider text-white/50 block">
              MARKET TREND
            </span>
            <span className="text-sm font-extrabold text-[#FAFBF7] mt-1 block">
              Paddy Mandi Signals
            </span>
            <span className="text-[10px] text-[#D4E768]">ETS Forecast Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
};
