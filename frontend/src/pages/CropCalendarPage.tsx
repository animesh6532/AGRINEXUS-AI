import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertCircle, Sprout } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Select } from '../components/ui/Select';
import { Input } from '../components/ui/Input';
import { api } from '../services/api';
import { CropScheduleResponse } from '../types/api';

export const CropCalendarPage: React.FC = () => {
  const [crop, setCrop] = useState<string>('rice');
  const [sowingDate, setSowingDate] = useState<string>('2026-06-15');
  const [schedule, setSchedule] = useState<CropScheduleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSchedule() {
      setError(null);
      try {
        const res = await api.getCropSchedule(crop, sowingDate);
        setSchedule(res);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch crop schedule.');
      }
    }
    fetchSchedule();
  }, [crop, sowingDate]);

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="FIELD SIGNALS"
        title="Field Season Calendar & Growth Planner"
        description="Calculate growth stages, sowing window compliance, field tasks, and estimated harvest dates dynamically from sowing date."
        imageSrc="/images/crop-calendar.webp"
      >
        <div className="flex items-center gap-3 bg-black/40 backdrop-blur-md p-2 rounded-2xl border border-white/10 flex-wrap">
          <Select
            value={crop}
            onChange={(e) => setCrop(e.target.value)}
            options={[
              { value: 'rice', label: 'Rice / Paddy' },
              { value: 'wheat', label: 'Wheat' },
              { value: 'maize', label: 'Maize' },
              { value: 'cotton', label: 'Cotton' },
            ]}
          />
          <Input
            type="date"
            value={sowingDate}
            onChange={(e) => setSowingDate(e.target.value)}
            className="w-44 text-xs bg-[#0B1C10] text-[#FAFBF7] border-white/20"
          />
        </div>
      </AgriculturalPageHero>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Derived Schedule Display */}
      {schedule && (
        <GlassCard variant="solid" className="p-6 sm:p-8 space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                AGRONOMIC SCHEDULE ({schedule.crop.toUpperCase()} • {schedule.season.toUpperCase()} SEASON)
              </span>
              <h2 className="text-3xl font-black font-editorial text-[#0B1C10] mt-1 flex items-center gap-3 capitalize">
                <Sprout className="w-8 h-8 text-[#2F6B3C]" />
                Current Stage: {schedule.current_stage.replace(/_/g, ' ')}
              </h2>
            </div>
            <div className="sm:text-right">
              <span className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold ${
                schedule.sowing_window_compliant
                  ? 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                  : 'bg-amber-500/10 text-amber-900 border border-amber-500/25'
              }`}>
                {schedule.sowing_window_compliant ? '● Optimal Sowing Window' : '● Off-Window Warning'}
              </span>
              <p className="text-xs font-medium text-[#536056] mt-1 font-mono">Duration: {schedule.crop_duration_days} Days</p>
            </div>
          </div>

          {/* Harvest Window & Next Stage Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-widest text-[#2F6B3C] block">
                ESTIMATED HARVEST WINDOW
              </span>
              <p className="font-extrabold text-[#0B1C10] text-base font-editorial">
                {schedule.harvest_window.start_date} → {schedule.harvest_window.end_date}
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                NEXT UPCOMING GROWTH STAGE
              </span>
              <p className="font-extrabold text-[#0B1C10] text-base font-editorial capitalize">
                {schedule.next_stage.replace(/_/g, ' ')}
              </p>
            </div>
          </div>

          {/* Organic Growth Stage Timeline */}
          <div className="space-y-4 pt-2">
            <h3 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
              Seasonal Growth Stages & Task Timeline
            </h3>

            <div className="relative border-l-2 border-[#2F6B3C]/30 ml-4 pl-6 space-y-8">
              {schedule.scheduled_growth_stages.map((stg, idx) => (
                <div key={idx} className="relative group">
                  {/* Timeline Dot */}
                  <div
                    className={`absolute -left-[31px] top-1.5 w-4 h-4 rounded-full border-2 border-[#0B1C10] transition-all ${
                      stg.is_current ? 'bg-[#D4E768] scale-125 shadow-md' : 'bg-[#EEF3E8]'
                    }`}
                  />

                  <div className={`p-6 rounded-3xl border transition-all ${
                    stg.is_current
                      ? 'bg-[#EEF3E8] border-[#2F6B3C] shadow-md'
                      : 'bg-white border-[#E2E7DA]'
                  }`}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E2E7DA]/60 pb-3">
                      <span className="font-extrabold font-editorial text-lg text-[#0B1C10] capitalize flex items-center gap-2">
                        {stg.is_current && <CheckCircle2 className="w-5 h-5 text-[#2F6B3C]" />}
                        {stg.stage.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs font-mono font-bold text-[#2F6B3C]">
                        {stg.start_date} → {stg.end_date} ({stg.duration_days} days)
                      </span>
                    </div>

                    {stg.activities && stg.activities.length > 0 && (
                      <div className="mt-3 space-y-2 pt-2">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                          Recommended Agronomic Tasks:
                        </span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {stg.activities.map((act, i) => (
                            <div key={i} className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-semibold text-[#162018] flex items-center gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#2F6B3C]" />
                              <span>{act}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  );
};
