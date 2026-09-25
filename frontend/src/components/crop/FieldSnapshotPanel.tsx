import React from 'react';
import { MapPin, CloudSun, Layers, Calendar, Edit3, AlertTriangle, Sparkles, CheckCircle2 } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { UserLocation } from '../../types/location';
import { SmartCropResponse } from '../../types/api';

interface FieldSnapshotPanelProps {
  location: UserLocation | null;
  smartResponse: SmartCropResponse | null;
  onOpenLocationPicker: () => void;
  onOpenHybridEdit?: () => void;
}

export const FieldSnapshotPanel: React.FC<FieldSnapshotPanelProps> = ({
  location,
  smartResponse,
  onOpenLocationPicker,
  onOpenHybridEdit,
}) => {
  const weather = smartResponse?.weather;
  const soil = smartResponse?.soil;
  const season = smartResponse?.season;
  const completeness = smartResponse?.data_completeness ?? (location ? 0.8 : 0.0);

  const isPhosphorusMissing = !soil?.phosphorus?.value;
  const isPotassiumMissing = !soil?.potassium?.value;
  const hasSoilWarning = isPhosphorusMissing || isPotassiumMissing;

  return (
    <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6 border-[#2F6B3C]/20 bg-gradient-to-br from-[#FAFBF7] to-[#F4F8EE] shadow-md">
      {/* Header Row: Title & Data Completeness Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-[#2F6B3C] text-white flex items-center justify-center font-extrabold shadow-sm">
            <Sparkles className="w-4 h-4 text-[#D4E768]" />
          </div>
          <div>
            <h3 className="text-lg font-black font-editorial text-[#0B1C10] tracking-tight">
              FIELD INTELLIGENCE SNAPSHOT
            </h3>
            <p className="text-xs text-[#536056] font-sans">
              Aggregated real-time location, atmospheric telemetry, soil context & crop calendar
            </p>
          </div>
        </div>

        {/* Data Completeness Indicator */}
        <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-2xl border border-[#E2E7DA] shadow-xs shrink-0">
          <div className="text-right">
            <span className="text-[10px] uppercase font-bold text-[#536056] block tracking-wider">
              Data Completeness
            </span>
            <span className="text-sm font-black font-mono text-[#2F6B3C]">
              {(completeness * 100).toFixed(0)}%
            </span>
          </div>
          <div className="w-16 bg-[#E2E7DA] rounded-full h-2 overflow-hidden">
            <div
              className="bg-[#2F6B3C] h-full transition-all duration-500 rounded-full"
              style={{ width: `${Math.min(100, Math.max(10, completeness * 100))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Grid: Location Header + 3-Column Telemetry Grid */}
      <div className="space-y-6">
        {/* Location Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white/80 p-4 rounded-2xl border border-[#E2E7DA]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] flex items-center justify-center font-bold shrink-0">
              <MapPin className="w-5 h-5 text-[#2F6B3C]" />
            </div>
            <div>
              <h4 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                {location?.displayName || 'No field location selected'}
              </h4>
              {location ? (
                <p className="text-xs font-mono text-[#536056]">
                  {location.latitude.toFixed(4)}° N, {location.longitude.toFixed(4)}° E • {location.source === 'device' ? 'GPS' : 'Map Selected'}
                </p>
              ) : (
                <p className="text-xs text-amber-800 font-medium">Click to select your field location on the map.</p>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={onOpenLocationPicker}
            className="px-4 py-2 rounded-xl bg-[#FAFBF7] hover:bg-[#EEF3E8] border border-[#E2E7DA] text-xs font-bold text-[#2F6B3C] transition-colors flex items-center gap-1.5 shrink-0 self-start sm:self-auto"
          >
            <MapPin className="w-3.5 h-3.5" />
            <span>Change Location</span>
          </button>
        </div>

        {/* 3-Column Editorial Grid: Weather | Soil | Season */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Column 1: Weather Telemetry */}
          <div className="bg-white p-5 rounded-2xl border border-[#E2E7DA] space-y-3">
            <div className="flex items-center justify-between border-b border-[#E2E7DA]/60 pb-2">
              <span className="text-xs font-extrabold uppercase tracking-wider text-[#536056] flex items-center gap-1.5">
                <CloudSun className="w-4 h-4 text-[#2F6B3C]" />
                WEATHER
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
                {weather?.source || 'Open-Meteo'}
              </span>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Air Temperature</span>
                <span className="font-extrabold font-editorial text-sm text-[#0B1C10]">
                  {weather?.current_temperature != null ? `${weather.current_temperature.toFixed(1)}°C` : '—'}
                </span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Relative Humidity</span>
                <span className="font-extrabold font-editorial text-sm text-[#0B1C10]">
                  {weather?.current_humidity != null ? `${weather.current_humidity}%` : '—'}
                </span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Forecast Rain (7d)</span>
                <span className="font-extrabold font-editorial text-sm text-[#0B1C10]">
                  {weather?.forecast_rainfall_sum != null ? `${weather.forecast_rainfall_sum.toFixed(1)} mm` : '—'}
                </span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Max Rain Chance</span>
                <span className="font-extrabold font-editorial text-sm font-mono text-[#2F6B3C]">
                  {weather?.rain_probability_max != null ? `${weather.rain_probability_max}%` : '—'}
                </span>
              </div>
            </div>
          </div>

          {/* Column 2: Soil Context */}
          <div className="bg-white p-5 rounded-2xl border border-[#E2E7DA] space-y-3">
            <div className="flex items-center justify-between border-b border-[#E2E7DA]/60 pb-2">
              <span className="text-xs font-extrabold uppercase tracking-wider text-[#536056] flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-[#2F6B3C]" />
                SOIL CONTEXT
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
                {soil?.data_source?.includes('Hybrid') ? 'Hybrid' : 'Geospatial'}
              </span>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Soil pH</span>
                <span className="font-extrabold font-editorial text-sm text-[#0B1C10]">
                  {soil?.ph?.value != null ? soil.ph.value.toFixed(1) : '—'}{' '}
                  <span className="text-[10px] font-normal text-[#536056]">
                    {soil?.ph?.is_estimated ? '(Est)' : '(Lab)'}
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Total Nitrogen (N)</span>
                <span className="font-extrabold font-editorial text-sm text-[#0B1C10]">
                  {soil?.nitrogen?.value != null ? `${soil.nitrogen.value.toFixed(0)} mg/kg` : '—'}
                </span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Phosphorus (P)</span>
                {soil?.phosphorus?.value != null ? (
                  <span className="font-extrabold font-editorial text-sm text-[#0B1C10]">{soil.phosphorus.value} mg/kg</span>
                ) : (
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                    Needs test
                  </span>
                )}
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Potassium (K)</span>
                {soil?.potassium?.value != null ? (
                  <span className="font-extrabold font-editorial text-sm text-[#0B1C10]">{soil.potassium.value} mg/kg</span>
                ) : (
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                    Needs test
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Column 3: Season & Sowing Window */}
          <div className="bg-white p-5 rounded-2xl border border-[#E2E7DA] space-y-3">
            <div className="flex items-center justify-between border-b border-[#E2E7DA]/60 pb-2">
              <span className="text-xs font-extrabold uppercase tracking-wider text-[#536056] flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-[#2F6B3C]" />
                SEASON & TIMING
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
                {season?.season || 'Kharif'}
              </span>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Regional Season</span>
                <span className="font-extrabold font-editorial text-sm text-[#0B1C10]">
                  {season?.regional_season || 'Monsoon Kharif'}
                </span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Sowing Window</span>
                <span className="font-mono text-[#0B1C10] font-bold">{season?.sowing_window || 'June – July'}</span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Harvest Window</span>
                <span className="font-mono text-[#0B1C10] font-bold">{season?.harvest_window || 'Oct – Nov'}</span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-[#536056]">Current Month</span>
                <span className="font-extrabold text-[#2F6B3C]">{season?.current_month || 'Active'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Banner & Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2 border-t border-[#E2E7DA]/70">
          <div className="flex items-center gap-2 text-xs">
            {hasSoilWarning ? (
              <span className="inline-flex items-center gap-1.5 text-amber-800 font-semibold bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-700 shrink-0" />
                <span>P & K nutrients require lab test verification for complete ML model evaluation.</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-emerald-800 font-semibold bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                <span>Full field telemetry & lab test data active.</span>
              </span>
            )}
          </div>

          {onOpenHybridEdit && (
            <button
              type="button"
              onClick={onOpenHybridEdit}
              className="px-4 py-2 rounded-xl bg-[#2F6B3C] hover:bg-[#23522d] text-white text-xs font-bold transition-colors flex items-center gap-1.5 shrink-0 shadow-sm"
            >
              <Edit3 className="w-3.5 h-3.5 text-[#D4E768]" />
              <span>Enter Lab Soil Test</span>
            </button>
          )}
        </div>
      </div>
    </GlassCard>
  );
};
