import React, { useState } from 'react';
import { TrendingUp, AlertTriangle, Layers } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { api } from '../services/api';
import { YieldPredictionResponse } from '../types/api';

export const YieldPage: React.FC = () => {
  const [formData, setFormData] = useState({
    Crop: 'Rice',
    Season: 'Kharif',
    State: 'Punjab',
    Area: 100.0,
    Annual_Rainfall: 1200.0,
    Fertilizer: 15000.0,
    Pesticide: 500.0,
    Fertilizer_Per_Area: 150.0,
    Pesticide_Per_Area: 5.0,
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<YieldPredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictYield(formData);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate crop yield prediction.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold">
          <TrendingUp className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Crop Yield Prediction</h1>
          <p className="text-xs text-slate-500">
            XGBoost regression yield prediction with 95% residual confidence bounds.
          </p>
        </div>
      </div>

      <ScopeWarning
        type="info"
        message="Yield dataset combines heterogeneous target conventions across states and crops. Predictions report uncertainty interval bounds."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Inputs */}
        <GlassCard variant="strong" className="p-6 lg:col-span-1 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-600" /> Agronomic & Input Parameters
          </h3>

          <form onSubmit={handleSubmit} className="space-y-3">
            <Select
              label="Crop"
              value={formData.Crop}
              onChange={(e) => setFormData({ ...formData, Crop: e.target.value })}
              options={[
                { value: 'Rice', label: 'Rice' },
                { value: 'Wheat', label: 'Wheat' },
                { value: 'Maize', label: 'Maize' },
                { value: 'Cotton', label: 'Cotton' },
              ]}
            />

            <div className="grid grid-cols-2 gap-2">
              <Select
                label="Season"
                value={formData.Season}
                onChange={(e) => setFormData({ ...formData, Season: e.target.value })}
                options={[
                  { value: 'Kharif', label: 'Kharif' },
                  { value: 'Rabi', label: 'Rabi' },
                  { value: 'Whole Year', label: 'Whole Year' },
                ]}
              />
              <Input
                label="State"
                value={formData.State}
                onChange={(e) => setFormData({ ...formData, State: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <Input
                label="Area (Hectares)"
                type="number"
                step="0.1"
                value={formData.Area}
                onChange={(e) => {
                  const area = parseFloat(e.target.value) || 1;
                  setFormData({
                    ...formData,
                    Area: area,
                    Fertilizer_Per_Area: formData.Fertilizer / area,
                    Pesticide_Per_Area: formData.Pesticide / area,
                  });
                }}
                required
              />
              <Input
                label="Rainfall (mm)"
                type="number"
                step="0.1"
                value={formData.Annual_Rainfall}
                onChange={(e) => setFormData({ ...formData, Annual_Rainfall: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <Input
                label="Total Fertilizer"
                type="number"
                step="1"
                value={formData.Fertilizer}
                onChange={(e) => setFormData({ ...formData, Fertilizer: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Total Pesticide"
                type="number"
                step="1"
                value={formData.Pesticide}
                onChange={(e) => setFormData({ ...formData, Pesticide: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <Button type="submit" variant="secondary" size="md" className="w-full mt-2" isLoading={loading}>
              Predict Crop Yield
            </Button>
          </form>
        </GlassCard>

        {/* Prediction Results */}
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
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">Predicted Crop Yield</span>
                  <h2 className="text-4xl font-black text-slate-900 mt-1">
                    {result.predicted_yield.toFixed(2)}
                  </h2>
                </div>
                <Badge variant="primary">XGBoost Regression</Badge>
              </div>

              {/* Uncertainty Interval Card */}
              <div className="p-4 rounded-xl bg-indigo-50/80 border border-indigo-200/60 space-y-3">
                <div className="flex justify-between items-center text-xs font-bold text-indigo-900">
                  <span>95% Residual Confidence Bounds</span>
                  <span>± {result.prediction_interval.margin.toFixed(2)}</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div className="p-2.5 rounded-lg bg-white/80 border border-indigo-100">
                    <span className="text-slate-500 block text-[10px]">Lower Bound</span>
                    <span className="font-mono font-bold text-slate-800">{result.prediction_interval.lower.toFixed(2)}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-white/80 border border-indigo-100">
                    <span className="text-slate-500 block text-[10px]">Upper Bound</span>
                    <span className="font-mono font-bold text-slate-800">{result.prediction_interval.upper.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </GlassCard>
          ) : (
            <GlassCard className="p-12 text-center space-y-3">
              <TrendingUp className="w-10 h-10 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">No Yield Prediction Calculated</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Specify crop area, rainfall, and inputs on the left to run XGBoost yield estimation.
              </p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
