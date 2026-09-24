import React, { useState, useEffect } from 'react';
import { CloudSun, Wind, Droplets, Thermometer, AlertCircle, RefreshCw, MapPin } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { useLocationContext } from '../context/LocationContext';
import { LocationBadge } from '../components/location/LocationBadge';
import { LocationEmptyState } from '../components/location/LocationEmptyState';
import { api } from '../services/api';
import { CurrentWeatherResponse, WeatherForecastResponse, WeatherInsightsResponse } from '../types/api';

export const WeatherPage: React.FC = () => {
  const { location, openPicker } = useLocationContext();

  const [current, setCurrent] = useState<CurrentWeatherResponse | null>(null);
  const [forecast, setForecast] = useState<WeatherForecastResponse | null>(null);
  const [insights, setInsights] = useState<WeatherInsightsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWeatherForLocation = async (latitude: number, longitude: number) => {
    setLoading(true);
    setError(null);
    setCurrent(null);
    setForecast(null);
    setInsights(null);

    try {
      const [cData, fData, iData] = await Promise.all([
        api.getWeatherCurrent(latitude, longitude),
        api.getWeatherForecast(latitude, longitude, 7),
        api.getWeatherInsights(latitude, longitude),
      ]);
      setCurrent(cData);
      setForecast(fData);
      setInsights(iData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch Open-Meteo weather telemetry for location.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (location && typeof location.latitude === 'number' && typeof location.longitude === 'number') {
      fetchWeatherForLocation(location.latitude, location.longitude);
    } else {
      setCurrent(null);
      setForecast(null);
      setInsights(null);
      setLoading(false);
    }
  }, [location?.latitude, location?.longitude]);

  const forecastChartData =
    forecast?.daily.map((d) => ({
      date: d.date.split('-').slice(1).join('/'),
      MaxTemp: d.temperature_max,
      MinTemp: d.temperature_min,
      Rain: d.precipitation_sum,
    })) || [];

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="FIELD SIGNALS"
        title="Weather Telemetry Center"
        description="Open-Meteo live observation telemetry, 7-day agricultural forecast trends, and automated field operation disruption signals tailored to your selected field location."
        imageSrc="/images/weather-intelligence.webp"
      >
        <div className="flex items-center gap-3 bg-black/40 backdrop-blur-md px-4 py-2 rounded-2xl border border-white/10 flex-wrap">
          <LocationBadge variant="pill" />
          {location && (
            <Button
              variant="lime"
              size="sm"
              onClick={() => fetchWeatherForLocation(location.latitude, location.longitude)}
              isLoading={loading}
              icon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Refresh Telemetry
            </Button>
          )}
        </div>
      </AgriculturalPageHero>

      {/* Empty State Banner if no location is configured */}
      {!location && (
        <LocationEmptyState
          title="FIELD LOCATION REQUIRED FOR WEATHER"
          subtitle="Please set your field location to view real-time Open-Meteo telemetry, 7-day temperature forecasts and spraying disruption risk signals."
        />
      )}

      {/* Loading Skeleton */}
      {loading && (
        <GlassCard variant="solid" className="p-10 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-[#112316] border border-[#D4E768]/40 text-[#D4E768] flex items-center justify-center mx-auto animate-spin">
            <RefreshCw className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
              Updating weather telemetry...
            </h3>
            <p className="text-xs text-[#536056] mt-1">
              Fetching Open-Meteo observations for{' '}
              <strong className="text-[#2F6B3C]">{location?.displayName || 'selected location'}</strong>
            </p>
          </div>
        </GlassCard>
      )}

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={openPicker}
            className="px-3 py-1 rounded-xl bg-rose-200 text-rose-900 font-bold hover:bg-rose-300"
          >
            Change Location
          </button>
        </div>
      )}

      {/* Current Observations Grid */}
      {!loading && current && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs px-1">
            <span className="font-bold text-[#536056] uppercase tracking-wider">
              CURRENT CONDITIONS — {location?.displayName}
            </span>
            <span className="text-[11px] text-[#2F6B3C] font-mono">
              {location?.latitude.toFixed(4)}° N, {location?.longitude.toFixed(4)}° E
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <GlassCard variant="cream" className="p-5 flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-black">
                <Thermometer className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">
                  Air Temperature
                </span>
                <span className="text-2xl font-black font-editorial text-[#0B1C10]">
                  {current.temperature}°C
                </span>
              </div>
            </GlassCard>

            <GlassCard variant="cream" className="p-5 flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] flex items-center justify-center font-black">
                <Droplets className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">
                  Relative Humidity
                </span>
                <span className="text-2xl font-black font-editorial text-[#0B1C10]">
                  {current.relative_humidity}%
                </span>
              </div>
            </GlassCard>

            <GlassCard variant="cream" className="p-5 flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] flex items-center justify-center font-black">
                <CloudSun className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">
                  Precipitation
                </span>
                <span className="text-2xl font-black font-editorial text-[#0B1C10]">
                  {current.precipitation} mm
                </span>
              </div>
            </GlassCard>

            <GlassCard variant="cream" className="p-5 flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] flex items-center justify-center font-black">
                <Wind className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">
                  Wind Velocity
                </span>
                <span className="text-2xl font-black font-editorial text-[#0B1C10]">
                  {current.wind_speed} km/h
                </span>
              </div>
            </GlassCard>
          </div>
        </div>
      )}

      {/* 7-Day Forecast Temperature & Rain Chart */}
      {!loading && forecastChartData.length > 0 && (
        <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                7-DAY FORECAST TELEMETRY
              </span>
              <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">
                Temperature & Precipitation Trends
              </h3>
            </div>
            <span className="text-xs text-[#2F6B3C] font-bold">Open-Meteo Engine</span>
          </div>

          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={forecastChartData}>
                <XAxis dataKey="date" stroke="#536056" fontSize={11} tickLine={false} />
                <YAxis stroke="#536056" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1C10',
                    color: '#FAFBF7',
                    borderRadius: '16px',
                    borderColor: '#D4E768',
                    fontSize: '12px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="MaxTemp"
                  stroke="#2F6B3C"
                  fill="#2F6B3C"
                  fillOpacity={0.2}
                  strokeWidth={2}
                  name="Max Temp (°C)"
                />
                <Area
                  type="monotone"
                  dataKey="Rain"
                  stroke="#D4E768"
                  fill="#D4E768"
                  fillOpacity={0.3}
                  strokeWidth={2}
                  name="Rainfall (mm)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      )}

      {/* Field Disruption Risk Signals */}
      {!loading && insights && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
              Agricultural Field Operation Insights
            </h3>
            <span className="text-xs text-[#2F6B3C] font-semibold">
              {insights.insights.length} Signals Evaluated
            </span>
          </div>

          {insights.insights.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {insights.insights.map((ins, idx) => (
                <GlassCard
                  key={idx}
                  variant="solid"
                  className="p-6 space-y-3 border-l-4 border-l-[#2F6B3C]"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                      {ins.title}
                    </h4>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        ins.severity === 'high'
                          ? 'bg-rose-500/10 text-rose-800 border border-rose-500/20'
                          : ins.severity === 'medium'
                          ? 'bg-amber-500/10 text-amber-800 border border-amber-500/20'
                          : 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                      }`}
                    >
                      {ins.severity} Severity
                    </span>
                  </div>
                  <p className="text-xs text-[#536056] leading-relaxed font-sans">
                    {ins.description}
                  </p>
                </GlassCard>
              ))}
            </div>
          ) : (
            <GlassCard variant="cream" className="p-8 text-center text-xs text-[#536056]">
              No severe field-disruption weather signals detected for this forecast window.
            </GlassCard>
          )}
        </div>
      )}
    </div>
  );
};
