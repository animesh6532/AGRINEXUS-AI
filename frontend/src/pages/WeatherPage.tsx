import React, { useState, useEffect } from 'react';
import { CloudSun, Wind, Droplets, Thermometer, AlertCircle, MapPin, RefreshCw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
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
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
            <CloudSun className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Weather Intelligence</h1>
            <p className="text-xs text-slate-500">
              Open-Meteo current observations, 7-day forecast trends, and agricultural field disruption insights.
            </p>
          </div>
        </div>

        {/* Location Form */}
        <div className="flex items-center gap-2">
          <Input
            type="number"
            step="0.001"
            value={lat}
            onChange={(e) => setLat(parseFloat(e.target.value) || 0)}
            placeholder="Lat"
            className="w-24 text-xs"
          />
          <Input
            type="number"
            step="0.001"
            value={lon}
            onChange={(e) => setLon(parseFloat(e.target.value) || 0)}
            placeholder="Lon"
            className="w-24 text-xs"
          />
          <Button variant="outline" size="sm" onClick={fetchWeather} isLoading={loading} icon={<RefreshCw className="w-3.5 h-3.5" />}>
            Update
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Current Observations Grid */}
      {current && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <GlassCard className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center">
              <Thermometer className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Temperature</span>
              <span className="text-xl font-extrabold text-slate-900">{current.temperature}°C</span>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center">
              <Droplets className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Humidity</span>
              <span className="text-xl font-extrabold text-slate-900">{current.relative_humidity}%</span>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center">
              <CloudSun className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Precipitation</span>
              <span className="text-xl font-extrabold text-slate-900">{current.precipitation} mm</span>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center">
              <Wind className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Wind Speed</span>
              <span className="text-xl font-extrabold text-slate-900">{current.wind_speed} km/h</span>
            </div>
          </GlassCard>
        </div>
      )}

      {/* 7-Day Forecast Temperature & Rain Chart */}
      {forecastChartData.length > 0 && (
        <GlassCard variant="strong" className="p-6 space-y-4">
          <h3 className="text-sm font-bold text-slate-900">7-Day Agricultural Forecast Trend</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={forecastChartData}>
                <XAxis dataKey="date" stroke="#94A3B8" fontSize={11} />
                <YAxis stroke="#94A3B8" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '12px', borderColor: '#E2E8F0' }}
                />
                <Area type="monotone" dataKey="MaxTemp" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.15} name="Max Temp (°C)" />
                <Area type="monotone" dataKey="Rain" stroke="#06B6D4" fill="#06B6D4" fillOpacity={0.25} name="Rainfall (mm)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      )}

      {/* Field Disruption Risk Signals */}
      {insights && (
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Agricultural Field Operation Insights</h3>
          {insights.insights.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {insights.insights.map((ins, idx) => (
                <GlassCard key={idx} className="p-4 space-y-2 border-l-4 border-l-sky-500">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-900">{ins.title}</h4>
                    <Badge variant={ins.severity === 'high' ? 'danger' : ins.severity === 'medium' ? 'warning' : 'info'}>
                      {ins.severity} severity
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{ins.description}</p>
                </GlassCard>
              ))}
            </div>
          ) : (
            <GlassCard className="p-6 text-center text-xs text-slate-500">
              No severe field-disruption weather signals detected for this forecast window.
            </GlassCard>
          )}
        </div>
      )}
    </div>
  );
};
