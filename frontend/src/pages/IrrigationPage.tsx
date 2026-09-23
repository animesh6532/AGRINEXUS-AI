import React, { useState } from 'react';
import { Droplets, AlertTriangle, Activity, BarChart2 } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { api } from '../services/api';
import { IrrigationPredictionResponse } from '../types/api';

export const IrrigationPage: React.FC = () => {
  const [formData, setFormData] = useState({
    SWC: 0.22,
    SWC_lag1h: 0.225,
    SWC_lag2h: 0.23,
    SWC_lag3h: 0.235,
    SWC_roll6h_mean: 0.23,
    Rainfall_mm: 0.0,
    Rain_roll6h_sum: 0.0,
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<IrrigationPredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictIrrigation(formData);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate irrigation prediction.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
          <Droplets className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Irrigation Predictor</h1>
          <p className="text-xs text-slate-500">
            3-hour Soil Water Content prediction evaluated against persistence baseline SWC benchmark.
          </p>
        </div>
      </div>

      <ScopeWarning
        type="info"
        message="Evaluates 3-hour horizon Soil Water Content (SWC). Note that the persistence baseline (SWC_t+3h = SWC_t) serves as the primary benchmark reference alongside the ML model."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Inputs */}
        <GlassCard variant="strong" className="p-6 lg:col-span-1 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Activity className="w-4 h-4 text-sky-600" /> Soil Water Content Observations
          </h3>

          <form onSubmit={handleSubmit} className="space-y-3">
            <Input
              label="Current Soil Water Content (SWC)"
              type="number"
              step="0.001"
              min="0"
              max="1"
              value={formData.SWC}
              onChange={(e) => setFormData({ ...formData, SWC: parseFloat(e.target.value) || 0 })}
              required
            />

            <div className="grid grid-cols-3 gap-2">
              <Input
                label="Lag 1h"
                type="number"
                step="0.001"
                value={formData.SWC_lag1h}
                onChange={(e) => setFormData({ ...formData, SWC_lag1h: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Lag 2h"
                type="number"
                step="0.001"
                value={formData.SWC_lag2h}
                onChange={(e) => setFormData({ ...formData, SWC_lag2h: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Lag 3h"
                type="number"
                step="0.001"
                value={formData.SWC_lag3h}
                onChange={(e) => setFormData({ ...formData, SWC_lag3h: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <Input
              label="6-Hour Mean SWC"
              type="number"
              step="0.001"
              value={formData.SWC_roll6h_mean}
              onChange={(e) => setFormData({ ...formData, SWC_roll6h_mean: parseFloat(e.target.value) || 0 })}
              required
            />

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Rainfall (mm)"
                type="number"
                step="0.1"
                value={formData.Rainfall_mm}
                onChange={(e) => setFormData({ ...formData, Rainfall_mm: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="6h Rain Sum"
                type="number"
                step="0.1"
                value={formData.Rain_roll6h_sum}
                onChange={(e) => setFormData({ ...formData, Rain_roll6h_sum: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <Button type="submit" variant="secondary" size="md" className="w-full mt-2" isLoading={loading}>
              Predict 3h SWC Horizon
            </Button>
          </form>
        </GlassCard>

        {/* Prediction Results & Comparison */}
        <div className="lg:col-span-2 space-y-6">
          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {result ? (
            <GlassCard variant="strong" className="p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-200/60 pb-4">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">Agronomic Recommendation</span>
                  <h2 className="text-xl font-black text-slate-900 mt-1">
                    {result.agronomic_status.status_message}
                  </h2>
                </div>
                <Badge variant={result.agronomic_status.irrigation_needed ? 'danger' : 'success'} dot>
                  {result.agronomic_status.irrigation_needed ? 'Irrigation Needed' : 'Adequate Moisture'}
                </Badge>
              </div>

              {/* Side-by-Side Comparison Display */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-sky-50/80 border border-sky-200/60 space-y-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-sky-800 block">
                    ML Model Prediction (3h)
                  </span>
                  <div className="text-3xl font-black text-sky-900">
                    {result.ml_predicted_swc_3h} <span className="text-xs font-normal text-slate-500">SWC</span>
                  </div>
                  <p className="text-[10px] text-sky-700">Scaled Ridge Regression Model</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-100/80 border border-slate-200 space-y-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700 block">
                    Persistence Baseline (3h)
                  </span>
                  <div className="text-3xl font-black text-slate-900">
                    {result.persistence_swc_3h} <span className="text-xs font-normal text-slate-500">SWC</span>
                  </div>
                  <p className="text-[10px] text-slate-500">SWC(t+3h) = SWC(t) Reference Benchmark</p>
                </div>
              </div>

              {/* Agronomic Threshold Metrics */}
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-white/70 border border-slate-100 text-center">
                  <span className="text-slate-400 block text-[10px]">Field Capacity</span>
                  <span className="font-bold text-slate-800">{result.agronomic_status.field_capacity}</span>
                </div>
                <div className="p-3 rounded-lg bg-white/70 border border-slate-100 text-center">
                  <span className="text-slate-400 block text-[10px]">Critical Threshold</span>
                  <span className="font-bold text-amber-700">{result.agronomic_status.critical_threshold}</span>
                </div>
                <div className="p-3 rounded-lg bg-white/70 border border-slate-100 text-center">
                  <span className="text-slate-400 block text-[10px]">Wilting Point</span>
                  <span className="font-bold text-rose-700">{result.agronomic_status.wilting_point}</span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 text-[11px] text-slate-600 leading-relaxed border border-slate-200/50">
                <span className="font-bold text-slate-900 block mb-0.5">Evaluation Note:</span>
                {result.agronomic_status.decision_note}
              </div>
            </GlassCard>
          ) : (
            <GlassCard className="p-12 text-center space-y-3">
              <Droplets className="w-10 h-10 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">No Irrigation Prediction Calculated</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Enter current SWC and lag observations on the left to evaluate 3-hour moisture prediction.
              </p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
