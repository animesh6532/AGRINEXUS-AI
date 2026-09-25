import React, { useState, useEffect, useCallback } from 'react';
import { CloudSun, Wind, Droplets, Thermometer, AlertCircle, RefreshCw, Eye, Cloud } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { useLocationContext } from '../context/LocationContext';
import { LocationBadge } from '../components/location/LocationBadge';
import { LocationEmptyState } from '../components/location/LocationEmptyState';
import { api } from '../services/api';
import { CurrentWeatherResponse, WeatherForecastResponse, WeatherInsightsResponse, HourlyForecastItem } from '../types/api';
import { useWeatherVisualization } from '../hooks/useWeatherVisualization';
import { WeatherScene } from '../components/weather/WeatherScene';
import { WeatherHero } from '../components/weather/WeatherHero';
import { WeatherWindCompass } from '../components/weather/WeatherWindCompass';
import { WeatherHourlyTimeline } from '../components/weather/WeatherHourlyTimeline';
import { AgrometInsightsPanel } from '../components/weather/AgrometInsightsPanel';

export const WeatherPage: React.FC = () => {
  const { location, openPicker } = useLocationContext();

  const [current, setCurrent] = useState<CurrentWeatherResponse | null>(null);
  const [forecast, setForecast] = useState<WeatherForecastResponse | null>(null);
  const [insights, setInsights] = useState<WeatherInsightsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWeatherForLocation = useCallback(async (latitude: number, longitude: number) => {
    setLoading(true);
    setError(null);

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
  }, []);

  useEffect(() => {
    if (location && typeof location.latitude === 'number' && typeof location.longitude === 'number') {
      fetchWeatherForLocation(location.latitude, location.longitude);

      // Auto refresh weather data every 10 minutes (600,000 ms)
      const interval = setInterval(() => {
        fetchWeatherForLocation(location.latitude, location.longitude);
      }, 600000);

      return () => clearInterval(interval);
    } else {
      setCurrent(null);
      setForecast(null);
      setInsights(null);
      setLoading(false);
    }
  }, [location?.latitude, location?.longitude, fetchWeatherForLocation]);

  const locationName = location?.displayName || 'Selected Field';

  const {
    visualizationState,
    selectedForecastHour,
    selectForecastHour,
    resetToCurrent,
  } = useWeatherVisualization({
    current,
    forecast,
    locationName,
  });

  const forecastChartData =
    forecast?.daily.map((d) => ({
      date: d.date.split('-').slice(1).join('/'),
      MaxTemp: d.temperature_max,
      MinTemp: d.temperature_min,
      Rain: d.precipitation_sum,
    })) || [];

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero Header */}
      <AgriculturalPageHero
        category="LIVE ATMOSPHERIC TELEMETRY"
        title="Weather Telemetry Engine"
        description="Real-time Open-Meteo observation telemetry, dynamic atmospheric visual scene engine, 24-hour interactive forecast strip, and agricultural operational disruption insights."
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
          title="FIELD LOCATION REQUIRED FOR WEATHER TELEMETRY"
          subtitle="Please set your field location to view real-time Open-Meteo telemetry, dynamic visual atmospheric scenes, and field operation disruption signals."
        />
      )}

      {/* Loading Skeleton */}
      {loading && !current && (
        <GlassCard variant="solid" className="p-12 text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-[#112316] border border-[#D4E768]/40 text-[#D4E768] flex items-center justify-center mx-auto animate-spin">
            <RefreshCw className="w-7 h-7" />
          </div>
          <div>
            <h3 className="text-lg font-extrabold font-editorial text-[#0B1C10]">
              Connecting to Live Weather Telemetry Engine...
            </h3>
            <p className="text-xs text-[#536056] mt-1">
              Fetching Open-Meteo observations for{' '}
              <strong className="text-[#2F6B3C]">{locationName}</strong>
            </p>
          </div>
        </GlassCard>
      )}

      {/* Error State Banner */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={openPicker}
            className="px-3 py-1 rounded-xl bg-rose-200 text-rose-900 font-bold hover:bg-rose-300 transition"
          >
            Change Location
          </button>
        </div>
      )}

      {/* Main Atmospheric Scene Container */}
      {!loading && visualizationState && (
        <div className="space-y-6">
          <WeatherScene state={visualizationState}>
            <div className="space-y-8">
              {/* Weather Hero Card */}
              <WeatherHero
                state={visualizationState}
                onRefresh={() => fetchWeatherForLocation(visualizationState.latitude, visualizationState.longitude)}
                isLoading={loading}
                onOpenLocationPicker={openPicker}
              />

              {/* Reset to current observation banner if previewing forecast hour */}
              {selectedForecastHour && (
                <div className="flex items-center justify-between bg-black/50 backdrop-blur-md px-4 py-2.5 rounded-2xl border border-[#D4E768]/40 text-xs text-white">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#D4E768] animate-ping" />
                    <span>
                      Previewing Forecast Scene for{' '}
                      <strong>
                        {new Date(selectedForecastHour.time).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </strong>
                    </span>
                  </div>
                  <button
                    onClick={resetToCurrent}
                    className="px-3 py-1 rounded-xl bg-[#D4E768] text-[#0B1C10] font-extrabold hover:bg-lime-300 transition text-[11px]"
                  >
                    Reset to Live Now
                  </button>
                </div>
              )}

              {/* 24-Hour Interactive Timeline */}
              {forecast?.hourly && forecast.hourly.length > 0 && (
                <WeatherHourlyTimeline
                  hourly={forecast.hourly}
                  selectedTime={selectedForecastHour?.time || null}
                  onSelectHour={selectForecastHour}
                />
              )}
            </div>
          </WeatherScene>

          {/* Primary Weather Metrics Grid (4 Columns Desktop / 2 Columns Tablet & Mobile) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <GlassCard variant="cream" className="p-5 flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-black">
                <Thermometer className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">
                  Air Temperature
                </span>
                <span className="text-2xl font-black font-editorial text-[#0B1C10]">
                  {visualizationState.temperature.toFixed(1)}°C
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
                  {visualizationState.humidity}%
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
                  {visualizationState.precipitation} mm
                </span>
              </div>
            </GlassCard>

            <GlassCard variant="cream" className="p-5 flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] flex items-center justify-center font-black">
                <Wind className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">
                  Wind Speed
                </span>
                <span className="text-2xl font-black font-editorial text-[#0B1C10]">
                  {visualizationState.windSpeed} km/h
                </span>
              </div>
            </GlassCard>
          </div>

          {/* Secondary Telemetry Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Wind Directional Compass */}
            <WeatherWindCompass
              windSpeed={visualizationState.windSpeed}
              windDirection={visualizationState.windDirection}
              windGusts={visualizationState.windGusts}
            />

            {/* Cloud Cover Card */}
            <GlassCard variant="cream" className="p-5 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] flex items-center justify-center font-black">
                  <Cloud className="w-6 h-6" />
                </div>
                <div>
                  <span className="text-[10px] text-[#536056] font-bold uppercase tracking-wider block">
                    Cloud Density & Coverage
                  </span>
                  <span className="text-2xl font-black font-editorial text-[#0B1C10]">
                    {visualizationState.cloudCover.toFixed(0)}%
                  </span>
                </div>
              </div>

              <div className="text-right">
                <span className="text-[10px] text-[#536056] font-bold uppercase block">Condition</span>
                <span className="text-sm font-extrabold text-[#2F6B3C] font-editorial">
                  {visualizationState.condition.replace(/_/g, ' ')}
                </span>
              </div>
            </GlassCard>
          </div>

          {/* 7-Day Forecast Temperature & Rain Chart */}
          {forecastChartData.length > 0 && (
            <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
              <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                    7-DAY FORECAST TELEMETRY TRENDS
                  </span>
                  <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">
                    Temperature & Rainfall Projections
                  </h3>
                </div>
                <span className="text-xs text-[#2F6B3C] font-bold">Open-Meteo Forecast</span>
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

          {/* Agromet & Operational Insights Panel */}
          <AgrometInsightsPanel
            insightsResponse={insights}
            temperature={visualizationState.temperature}
            humidity={visualizationState.humidity}
            windSpeed={visualizationState.windSpeed}
            precipitation={visualizationState.precipitation}
          />
        </div>
      )}
    </div>
  );
};
