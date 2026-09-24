import React from 'react';
import { AlertCircle, CheckCircle2, ShieldAlert, Thermometer, Wind, Droplets, Activity } from 'lucide-react';
import { WeatherInsightsResponse } from '../../types/api';
import { GlassCard } from '../ui/GlassCard';

interface AgrometInsightsPanelProps {
  insightsResponse: WeatherInsightsResponse | null;
  temperature: number;
  humidity: number;
  windSpeed: number;
  precipitation: number;
}

export const AgrometInsightsPanel: React.FC<AgrometInsightsPanelProps> = ({
  insightsResponse,
  temperature,
  humidity,
  windSpeed,
  precipitation,
}) => {
  // Compute Vapor Pressure Deficit (VPD in kPa) using standard FAO agrometeorology formulas
  const calcVPD = (T: number, RH: number): number => {
    const es = 0.61078 * Math.exp((17.27 * T) / (T + 237.3)); // Saturation vapor pressure (kPa)
    const ea = es * (RH / 100); // Actual vapor pressure (kPa)
    return Math.max(0, es - ea);
  };

  const vpd = calcVPD(temperature, humidity);

  const getVPDStatus = (val: number) => {
    if (val < 0.4) {
      return {
        label: 'Low VPD (<0.4 kPa)',
        color: 'text-amber-700 bg-amber-50 border-amber-200',
        note: 'Low atmospheric demand. Fungal spore germination risk elevated if wet.',
      };
    } else if (val <= 1.2) {
      return {
        label: 'Optimal Transpiration (0.4–1.2 kPa)',
        color: 'text-emerald-800 bg-emerald-50 border-emerald-200',
        note: 'Ideal atmospheric vapor deficit for crop stomatal conductance & growth.',
      };
    } else if (val <= 2.0) {
      return {
        label: 'Moderate Stress (1.2–2.0 kPa)',
        color: 'text-amber-800 bg-amber-50 border-amber-200',
        note: 'Elevated atmospheric evaporation. Monitor soil moisture levels.',
      };
    } else {
      return {
        label: 'High Atmospheric Stress (>2.0 kPa)',
        color: 'text-rose-800 bg-rose-50 border-rose-200',
        note: 'High vapor pressure deficit. Potential crop stomatal closure & heat stress.',
      };
    }
  };

  const vpdStatus = getVPDStatus(vpd);
  const insights = insightsResponse?.insights || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-widest text-[#536056] flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#2F6B3C]" />
          AGRICULTURAL METEOROLOGY & FIELD DISRUPTION SIGNALS
        </h3>
        <span className="text-xs text-[#2F6B3C] font-semibold">
          Open-Meteo Agromet Telemetry
        </span>
      </div>

      {/* Agromet Indicators Grid (VPD & Field Operations) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* VPD Card */}
        <GlassCard variant="cream" className="p-6 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#536056]">
              Vapor Pressure Deficit (VPD)
            </span>
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${vpdStatus.color}`}>
              {vpdStatus.label}
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black font-editorial text-[#0B1C10]">
              {vpd.toFixed(2)}
            </span>
            <span className="text-sm font-bold text-[#536056]">kPa</span>
          </div>

          <p className="text-xs text-[#536056] leading-relaxed font-sans border-t border-[#E2E7DA] pt-2">
            {vpdStatus.note}
          </p>
        </GlassCard>

        {/* Operational Field Insight summary */}
        <GlassCard variant="cream" className="p-6 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#536056]">
              Field Operation Operational Guidance
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
              Real Telemetry
            </span>
          </div>

          <p className="text-sm font-bold font-editorial text-[#0B1C10]">
            {precipitation > 0
              ? 'Rainfall active. Spraying & heavy field machinery operations disrupted.'
              : windSpeed > 20
              ? 'High wind velocity detected (>20 km/h). High spray drift risk.'
              : 'Conditions currently favorable for planned field operations.'}
          </p>

          <p className="text-xs text-[#536056] leading-relaxed border-t border-[#E2E7DA] pt-2">
            {precipitation > 0
              ? 'Soil surface saturation likely. Delay chemical applications and tillage to protect soil structure.'
              : windSpeed > 20
              ? 'Abate foliar pesticide applications to prevent off-target spray drift.'
              : 'Ambient temperature and wind speed fall within optimal windows for routine operations.'}
          </p>
        </GlassCard>
      </div>

      {/* Specific Signals from Open-Meteo Insights API */}
      {insights.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {insights.map((ins, idx) => (
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
      )}
    </div>
  );
};
