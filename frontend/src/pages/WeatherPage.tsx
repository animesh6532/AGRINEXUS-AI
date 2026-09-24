import React, { useState, useEffect } from 'react';
import { CloudSun, Wind, Droplets, Thermometer, AlertCircle, RefreshCw, Layers } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { api } from '../services/api';
import { CurrentWeatherResponse, WeatherForecastResponse, WeatherInsightsResponse } from '../types/api';

export const WeatherPage: React.FC = () => {
  const [lat, setLat] = useState<number>(19.076);
  const [lon, setLon] = useState<number>(72.8777);

  const [current, setCurrent] = useState<CurrentWeatherResponse | null>(null);
  const [forecast, setForecast] = useState<WeatherForecastResponse | null>(null);
  const [insights, setInsights] = useState<WeatherInsightsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWeather = async () => {
    setLoading(true);
    setError(null);
    try {
      const [cData, fData, iData] = await Promise.all([
        api.getWeatherCurrent(lat, lon),
        api.getWeatherForecast(lat, lon, 7),
        api.getWeatherInsights(lat, lon),
      ]);
      setCurrent(cData);
      setForecast(fData);
      setInsights(iData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch Open-Meteo weather data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather();
  }, []);

  const forecastChartData = forecast?.daily.map((d) => ({
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
        description="Open-Meteo live observation telemetry, 7-day agricultural forecast trends, and automated field operation disruption signals."
        imageSrc="/images/weather-intelligence.webp"
      >
        <div className="flex items-center gap-2 bg-black/40 backdrop-blur-md p-2 rounded-2xl border border-white/10">
          <Input
            type="number"
            step="0.001"
            value={lat}
            onChange={(e) => setLat(parseFloat(e.target.value) || 0)}
            placeholder="Lat"
            className="w-24 text-xs bg-[#0B1C10] text-[#FAFBF7] border-white/20"
          />
          <Input
            type="number"
            step="0.001"
            value={lon}
            onChange={(e) => setLon(parseFloat(e.target.value) || 0)}
            placeholder="Lon"
            className="w-24 text-xs bg-[#0B1C10] text-[#FAFBF7] border-white/20"
          />
          <Button variant="lime" size="sm" onClick={fetchWeather} isLoading={loading} icon={<RefreshCw className="w-3.5 h-3.5" />}>
            Update Location
          </Button>
        </div>
      </AgriculturalPageHero>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Current Observations Grid */}
      {current && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <GlassCard variant="cream" className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-black">
              <Thermometer className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">Air Temperature</span>
              <span className="text-2xl font-black font-editorial text-[#0B1C10]">{current.temperature}°C</span>
            </div>
          </GlassCard>

          <GlassCard variant="cream" className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] flex items-center justify-center font-black">
              <Droplets className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">Relative Humidity</span>
              <span className="text-2xl font-black font-editorial text-[#0B1C10]">{current.relative_humidity}%</span>
            </div>
          </GlassCard>

          <GlassCard variant="cream" className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] flex items-center justify-center font-black">
              <CloudSun className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">Precipitation</span>
              <span className="text-2xl font-black font-editorial text-[#0B1C10]">{current.precipitation} mm</span>
            </div>
          </GlassCard>

          <GlassCard variant="cream" className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] flex items-center justify-center font-black">
              <Wind className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">Wind Velocity</span>
              <span className="text-2xl font-black font-editorial text-[#0B1C10]">{current.wind_speed} km/h</span>
            </div>
          </GlassCard>
        </div>
      )}

      {/* 7-Day Forecast Temperature & Rain Chart */}
      {forecastChartData.length > 0 && (
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
                    fontSize: '12px'
                  }}
                />
                <Area type="monotone" dataKey="MaxTemp" stroke="#2F6B3C" fill="#2F6B3C" fillOpacity={0.2} strokeWidth={2} name="Max Temp (°C)" />
                <Area type="monotone" dataKey="Rain" stroke="#D4E768" fill="#D4E768" fillOpacity={0.3} strokeWidth={2} name="Rainfall (mm)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      )}

      {/* Field Disruption Risk Signals */}
      {insights && (
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
                <GlassCard key={idx} variant="solid" className="p-6 space-y-3 border-l-4 border-l-[#2F6B3C]">
                  <div className="flex items-center justify-between">
                    <h4 className="text-base font-extrabold font-editorial text-[#0B1C10]">{ins.title}</h4>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                      ins.severity === 'high'
                        ? 'bg-rose-500/10 text-rose-800 border border-rose-500/20'
                        : ins.severity === 'medium'
                        ? 'bg-amber-500/10 text-amber-800 border border-amber-500/20'
                        : 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                    }`}>
                      {ins.severity} Severity
                    </span>
                  </div>
                  <p className="text-xs text-[#536056] leading-relaxed font-sans">{ins.description}</p>
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
