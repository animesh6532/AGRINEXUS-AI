import React, { useState, useEffect } from 'react';
import { Calendar, CheckCircle2, Clock, AlertCircle, Sprout, ArrowRight } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Select } from '../components/ui/Select';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { api } from '../services/api';
import { CropScheduleResponse, CropCalendarItem } from '../types/api';

export const CropCalendarPage: React.FC = () => {
  const [crop, setCrop] = useState<string>('rice');
  const [sowingDate, setSowingDate] = useState<string>('2026-06-15');
  const [catalogue, setCatalogue] = useState<CropCalendarItem[]>([]);
  const [schedule, setSchedule] = useState<CropScheduleResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCatalogue() {
      try {
        const cat = await api.getCropCalendarCatalogue();
        setCatalogue(cat);
      } catch {
        // Fallback
      }
    }
    loadCatalogue();
  }, []);

  const fetchSchedule = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getCropSchedule(crop, sowingDate);
      setSchedule(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch crop schedule.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedule();
  }, [crop, sowingDate]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
            <Calendar className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Crop Calendar Schedule</h1>
            <p className="text-xs text-slate-500">
              Growth stage schedules, sowing windows, and field operations calculated from sowing date.
            </p>
          </div>
        </div>

        {/* Inputs */}
        <div className="flex items-center gap-3">
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
            className="w-40 text-xs"
          />
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Schedule Summary Banner */}
      {schedule && (
        <GlassCard variant="strong" className="p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/60 pb-4">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
                Derived Schedule ({schedule.crop.toUpperCase()} • {schedule.season.toUpperCase()} SEASON)
              </span>
              <h2 className="text-2xl font-black text-slate-900 mt-1 capitalize flex items-center gap-2">
                <Sprout className="w-6 h-6 text-agri-600" />
                Current Stage: {schedule.current_stage.replace(/_/g, ' ')}
              </h2>
            </div>
            <div className="text-right">
              <Badge variant={schedule.sowing_window_compliant ? 'success' : 'warning'}>
                {schedule.sowing_window_compliant ? 'Optimal Sowing Window' : 'Sowing Window Warning'}
              </Badge>
              <p className="text-xs text-slate-500 mt-1">Duration: {schedule.crop_duration_days} days</p>
            </div>
          </div>

          {/* Harvest Window & Next Stage */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-white/80 border border-slate-100 space-y-1">
              <span className="text-slate-400 font-bold uppercase block text-[10px]">Estimated Harvest Window</span>
              <p className="font-bold text-slate-900 text-sm">{schedule.harvest_window.start_date} to {schedule.harvest_window.end_date}</p>
            </div>
            <div className="p-4 rounded-xl bg-white/80 border border-slate-100 space-y-1">
              <span className="text-slate-400 font-bold uppercase block text-[10px]">Next Growth Stage</span>
              <p className="font-bold text-slate-900 text-sm capitalize">{schedule.next_stage.replace(/_/g, ' ')}</p>
            </div>
          </div>

          {/* Growth Stage Timeline */}
          <div className="space-y-3 pt-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Scheduled Growth Stages & Field Tasks</h3>
            <div className="space-y-3">
              {schedule.scheduled_growth_stages.map((stg, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border transition-all ${
                    stg.is_current
                      ? 'bg-agri-50/90 border-agri-300 shadow-sm'
                      : 'bg-white/60 border-slate-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-sm capitalize flex items-center gap-2">
                      {stg.is_current && <CheckCircle2 className="w-4 h-4 text-agri-600" />}
                      {stg.stage.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs font-medium text-slate-500">
                      {stg.start_date} → {stg.end_date} ({stg.duration_days} days)
                    </span>
                  </div>

                  {stg.activities && stg.activities.length > 0 && (
                    <div className="mt-2 text-xs text-slate-600 space-y-1 pt-2 border-t border-slate-200/50">
                      <span className="font-semibold text-slate-700 text-[10px] uppercase block">Recommended Tasks:</span>
                      <ul className="list-disc list-inside space-y-0.5">
                        {stg.activities.map((act, i) => (
                          <li key={i}>{act}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  );
};
