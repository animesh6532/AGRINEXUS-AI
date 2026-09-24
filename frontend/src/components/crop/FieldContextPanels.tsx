import React from 'react';
import { MapPin, CloudSun, Layers, Calendar, AlertTriangle, CheckCircle2, Info, Edit3 } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { UserLocation } from '../../types/location';
import { SmartCropResponse } from '../../types/api';

interface FieldContextPanelsProps {
  location: UserLocation | null;
  smartResponse: SmartCropResponse | null;
  onOpenLocationPicker: () => void;
  onOpenHybridEdit?: () => void;
}

export const FieldContextPanels: React.FC<FieldContextPanelsProps> = ({
  location,
  smartResponse,
  onOpenLocationPicker,
  onOpenHybridEdit,
}) => {
  const weather = smartResponse?.weather;
  const soil = smartResponse?.soil;
  const season = smartResponse?.season;
  const completeness = smartResponse?.data_completeness ?? (location ? 0.6 : 0.0);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. FIELD LOCATION CARD */}
      <GlassCard variant="solid" className="p-5 space-y-3 relative flex flex-col justify-between group">
        <div>
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-2.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-[#2F6B3C]" />
              FIELD LOCATION
            </span>
            {location?.source && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
                {location.source === 'device' ? 'GPS Device' : location.source === 'map' ? 'Map Selected' : location.source}
              </span>
            )}
          </div>

          <div className="mt-3 space-y-1">
            <h4 className="text-sm font-extrabold font-editorial text-[#0B1C10] line-clamp-1">
              {location?.displayName || 'No field location selected'}
            </h4>
            {location ? (
              <p className="text-xs font-mono text-[#536056]">
                {location.latitude.toFixed(4)}° N, {location.longitude.toFixed(4)}° E
              </p>
            ) : (
              <p className="text-xs text-amber-700 font-medium">Please select your field location on the map.</p>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={onOpenLocationPicker}
          className="w-full mt-3 py-2 px-3 rounded-xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-bold text-[#2F6B3C] hover:bg-[#EEF3E8] transition-colors flex items-center justify-center gap-1.5"
        >
          <MapPin className="w-3.5 h-3.5" />
          <span>{location ? 'Change Map Location' : 'Select Field on Map'}</span>
        </button>
      </GlassCard>

      {/* 2. WEATHER TELEMETRY CARD */}
      <GlassCard variant="solid" className="p-5 space-y-3 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-2.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] flex items-center gap-1.5">
              <CloudSun className="w-3.5 h-3.5 text-[#2F6B3C]" />
              WEATHER TELEMETRY
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
              {weather?.source || 'Open-Meteo'}
            </span>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-[10px] text-[#536056] block">Temperature</span>
              <span className="font-extrabold text-[#0B1C10] font-mono">
                {weather?.current_temperature != null ? `${weather.current_temperature.toFixed(1)}°C` : '—'}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-[#536056] block">Humidity</span>
              <span className="font-extrabold text-[#0B1C10] font-mono">
                {weather?.current_humidity != null ? `${weather.current_humidity}%` : '—'}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-[#536056] block">Forecast Rain (7d)</span>
              <span className="font-extrabold text-[#0B1C10] font-mono">
                {weather?.forecast_rainfall_sum != null ? `${weather.forecast_rainfall_sum.toFixed(1)} mm` : '—'}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-[#536056] block">Rain Chance</span>
              <span className="font-extrabold text-[#0B1C10] font-mono">
                {weather?.rain_probability_max != null ? `${weather.rain_probability_max}%` : '—'}
              </span>
            </div>
          </div>
        </div>

        {weather?.error_message && (
          <p className="text-[10px] text-amber-700 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 shrink-0" />
            <span>{weather.error_message}</span>
          </p>
        )}
      </GlassCard>

      {/* 3. SOIL CONTEXT CARD */}
      <GlassCard variant="solid" className="p-5 space-y-3 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-2.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-[#2F6B3C]" />
              SOIL CONTEXT
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
              {soil?.data_source?.includes('Hybrid') ? 'Hybrid' : 'Geospatial'}
            </span>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-[10px] text-[#536056] block">Soil pH</span>
              <span className="font-extrabold text-[#0B1C10] font-mono">
                {soil?.ph?.value != null ? `${soil.ph.value.toFixed(1)}` : '—'}
              </span>
              <span className="text-[9px] text-[#536056] block font-mono">
                {soil?.ph?.is_estimated ? '(Estimated)' : '(Measured)'}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-[#536056] block">Total N</span>
              <span className="font-extrabold text-[#0B1C10] font-mono">
                {soil?.nitrogen?.value != null ? `${soil.nitrogen.value.toFixed(0)} mg/kg` : '—'}
              </span>
              <span className="text-[9px] text-[#536056] block font-mono">
                {soil?.nitrogen?.is_estimated ? '(Total N Est)' : '(Measured)'}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-[#536056] block">Phosphorus (P)</span>
              <span className="font-semibold text-amber-800 text-[11px] font-mono">
                {soil?.phosphorus?.value != null ? `${soil.phosphorus.value} mg/kg` : 'Needs test'}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-[#536056] block">Potassium (K)</span>
              <span className="font-semibold text-amber-800 text-[11px] font-mono">
                {soil?.potassium?.value != null ? `${soil.potassium.value} mg/kg` : 'Needs test'}
              </span>
            </div>
          </div>
        </div>

        {onOpenHybridEdit && (
          <button
            type="button"
            onClick={onOpenHybridEdit}
            className="w-full mt-3 py-1.5 px-3 rounded-xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-bold text-[#2F6B3C] hover:bg-[#EEF3E8] transition-colors flex items-center justify-center gap-1.5"
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>Enter / Edit Soil Tests</span>
          </button>
        )}
      </GlassCard>

      {/* 4. SEASON & DATA COMPLETENESS CARD */}
      <GlassCard variant="solid" className="p-5 space-y-3 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-2.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-[#2F6B3C]" />
              SEASON & DATA STATUS
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
              {season?.season || 'Kharif'}
            </span>
          </div>

          <div className="mt-3 space-y-2 text-xs">
            <div>
              <span className="text-[10px] text-[#536056] block">Regional Season</span>
              <span className="font-extrabold text-[#0B1C10]">
                {season?.regional_season || 'Kharif (Monsoon Season)'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-1 text-[11px]">
              <div>
                <span className="text-[10px] text-[#536056] block">Sowing Window</span>
                <span className="font-mono text-[#0B1C10] font-semibold">{season?.sowing_window || 'June - July'}</span>
              </div>
              <div>
                <span className="text-[10px] text-[#536056] block">Harvest Window</span>
                <span className="font-mono text-[#0B1C10] font-semibold">{season?.harvest_window || 'Oct - Nov'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Completeness Bar */}
        <div className="space-y-1 pt-2 border-t border-[#E2E7DA]/60">
          <div className="flex justify-between text-[10px] font-bold">
            <span className="text-[#536056]">Data Completeness</span>
            <span className="font-mono text-[#2F6B3C]">{(completeness * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-[#E2E7DA] rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-[#2F6B3C] h-full transition-all duration-500 rounded-full"
              style={{ width: `${Math.min(100, Math.max(5, completeness * 100))}%` }}
            />
          </div>
        </div>
      </GlassCard>
    </div>
  );
};
