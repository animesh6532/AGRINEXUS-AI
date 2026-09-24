import React, { useState } from 'react';
import { Droplets, AlertTriangle, Activity } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
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
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="FIELD INTELLIGENCE"
        title="Irrigation & Water Predictor"
        description="Soil water, predicted ahead. 3-hour horizon Soil Water Content (SWC) forecasting evaluated side-by-side with persistence reference baselines."
        imageSrc="/images/irrigation.webp"
      />

      <ScopeWarning
        type="info"
        message="Evaluates 3-hour horizon Soil Water Content (SWC). On held-out testing, the persistence baseline (SWC_t+3h = SWC_t) serves as the primary benchmark reference alongside the ML model."
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Form Inputs (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
            <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-4">
              <Activity className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                Soil Water Content Telemetry
              </h3>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
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

              <div className="grid grid-cols-3 gap-3">
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
                label="6-Hour Rolling Mean SWC"
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

              <Button
                type="submit"
                variant="lime"
                size="lg"
                className="w-full mt-2 shadow-md hover:shadow-glow"
                isLoading={loading}
                icon={<Droplets className="w-4 h-4" />}
              >
                Predict 3h SWC Horizon
              </Button>
            </form>
          </GlassCard>
        </div>

        {/* Prediction Results (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {error && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {result ? (
            <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-6">
                <div>
                  <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                    AGRONOMIC STATUS & ADVISORY
                  </span>
                  <h2 className="text-2xl font-black font-editorial text-[#0B1C10] mt-1">
                    {result.agronomic_status.status_message}
                  </h2>
                </div>
                <span className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold ${
                  result.agronomic_status.irrigation_needed
                    ? 'bg-amber-500/10 text-amber-900 border border-amber-500/25'
                    : 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                }`}>
                  {result.agronomic_status.irrigation_needed ? '● Irrigation Recommended' : '● Moisture Adequate'}
                </span>
              </div>

              {/* Side-by-Side Comparison Display */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-5 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-2">
                  <span className="text-xs font-bold uppercase tracking-widest text-[#2F6B3C] block">
                    ML Model Forecast (3h Horizon)
                  </span>
                  <div className="text-4xl font-black font-editorial text-[#0B1C10]">
                    {result.ml_predicted_swc_3h}{' '}
                    <span className="text-xs font-sans font-medium text-[#536056]">SWC</span>
                  </div>
                  <p className="text-[10px] text-[#536056]">Scaled Ridge Regression Model</p>
                </div>

                <div className="p-5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-2">
                  <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                    Persistence Reference (3h)
                  </span>
                  <div className="text-4xl font-black font-editorial text-[#0B1C10]">
                    {result.persistence_swc_3h}{' '}
                    <span className="text-xs font-sans font-medium text-[#536056]">SWC</span>
                  </div>
                  <p className="text-[10px] text-[#536056]">SWC(t+3h) = SWC(t) Reference Baseline</p>
                </div>
              </div>

              {/* Agronomic Threshold Metrics */}
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div className="p-3.5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-center">
                  <span className="text-[#536056] block text-[10px] uppercase font-bold">Field Capacity</span>
                  <span className="font-extrabold text-[#0B1C10] text-base">{result.agronomic_status.field_capacity}</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-center">
                  <span className="text-[#536056] block text-[10px] uppercase font-bold">Critical Threshold</span>
                  <span className="font-extrabold text-amber-700 text-base">{result.agronomic_status.critical_threshold}</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-center">
                  <span className="text-[#536056] block text-[10px] uppercase font-bold">Wilting Point</span>
                  <span className="font-extrabold text-rose-700 text-base">{result.agronomic_status.wilting_point}</span>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#EEF3E8] text-xs text-[#162018] leading-relaxed border border-[#E2E7DA]">
                <span className="font-bold text-[#0B1C10] block mb-1">Agronomic Transparency Note:</span>
                {result.agronomic_status.decision_note}
              </div>
            </GlassCard>
          ) : (
            <div className="relative rounded-3xl overflow-hidden border border-[#E2E7DA] bg-[#FAFBF7] p-8 sm:p-12 text-center space-y-6 flex flex-col items-center justify-center min-h-[380px] group">
              <div className="w-14 h-14 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-extrabold text-xl shadow-sm">
                <Droplets className="w-7 h-7" />
              </div>

              <div className="space-y-2 max-w-md">
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                  Ready for Water Content Prediction
                </h3>
                <p className="text-xs text-[#536056] leading-relaxed">
                  Enter current Soil Water Content (SWC) and hourly lag observations on the left to compute 3-hour moisture forecasts.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
