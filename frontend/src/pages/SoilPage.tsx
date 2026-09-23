import React, { useState } from 'react';
import { Mountain, AlertTriangle, Layers } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { api } from '../services/api';
import { SoilAnalysisResponse } from '../types/api';

export const SoilPage: React.FC = () => {
  const [formData, setFormData] = useState({
    'pH(CaCl2)': 6.2,
    'pH(H2O)': 6.8,
    Clay: 25.0,
    Silt: 40.0,
    Sand: 35.0,
    CaCO3: 12.0,
    P: 18.5,
    N: 2.1,
    K: 180.0,
    EC: 15.0,
    NUTS_0: 'DE',
    LC1: 'B11',
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SoilAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.analyzeSoil(formData);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to estimate Soil Organic Carbon.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
          <Mountain className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Soil Organic Carbon Analysis</h1>
          <p className="text-xs text-slate-500">
            Estimates Soil Organic Carbon (SOC in g/kg) with 95% residual confidence bounds using LUCAS preprocessor pipeline.
          </p>
        </div>
      </div>

      <ScopeWarning
        type="warning"
        message="Model trained using the LUCAS European Topsoil dataset. Not automatically validated for all non-European regional soil profiles."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Inputs */}
        <GlassCard variant="strong" className="p-6 lg:col-span-1 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-600" /> Physical & Chemical Soil Properties
          </h3>

          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <Input
                label="pH (CaCl2)"
                type="number"
                step="0.1"
                value={formData['pH(CaCl2)']}
                onChange={(e) => setFormData({ ...formData, 'pH(CaCl2)': parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="pH (H2O)"
                type="number"
                step="0.1"
                value={formData['pH(H2O)']}
                onChange={(e) => setFormData({ ...formData, 'pH(H2O)': parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <Input
                label="Clay %"
                type="number"
                step="0.1"
                value={formData.Clay}
                onChange={(e) => setFormData({ ...formData, Clay: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Silt %"
                type="number"
                step="0.1"
                value={formData.Silt}
                onChange={(e) => setFormData({ ...formData, Silt: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Sand %"
                type="number"
                step="0.1"
                value={formData.Sand}
                onChange={(e) => setFormData({ ...formData, Sand: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <Input
                label="CaCO3"
                type="number"
                step="0.1"
                value={formData.CaCO3}
                onChange={(e) => setFormData({ ...formData, CaCO3: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Phosphorus (P)"
                type="number"
                step="0.1"
                value={formData.P}
                onChange={(e) => setFormData({ ...formData, P: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <Input
                label="Nitrogen (N)"
                type="number"
                step="0.1"
                value={formData.N}
                onChange={(e) => setFormData({ ...formData, N: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Potassium (K)"
                type="number"
                step="0.1"
                value={formData.K}
                onChange={(e) => setFormData({ ...formData, K: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="EC"
                type="number"
                step="0.1"
                value={formData.EC}
                onChange={(e) => setFormData({ ...formData, EC: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <Input
                label="NUTS_0 Region"
                value={formData.NUTS_0}
                onChange={(e) => setFormData({ ...formData, NUTS_0: e.target.value })}
                required
              />
              <Input
                label="LC1 Land Cover"
                value={formData.LC1}
                onChange={(e) => setFormData({ ...formData, LC1: e.target.value })}
                required
              />
            </div>

            <Button type="submit" variant="secondary" size="md" className="w-full mt-2" isLoading={loading}>
              Estimate Soil Organic Carbon
            </Button>
          </form>
        </GlassCard>

        {/* Prediction Results & 95% Confidence Interval */}
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
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">Predicted Soil Organic Carbon (SOC)</span>
                  <h2 className="text-4xl font-black text-slate-900 mt-1">
                    {result.predicted_soc.toFixed(2)} <span className="text-sm font-normal text-slate-500">{result.unit}</span>
                  </h2>
                </div>
                <Badge variant="success">LUCAS Pipeline</Badge>
              </div>

              {/* 95% Confidence Interval Display */}
              <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200/60 space-y-3">
                <div className="flex justify-between items-center text-xs font-bold text-emerald-900">
                  <span>95% Residual Prediction Interval</span>
                  <span>± {result.prediction_interval.margin.toFixed(2)} g/kg</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div className="p-2.5 rounded-lg bg-white/80 border border-emerald-100">
                    <span className="text-slate-500 block text-[10px]">Lower Bound</span>
                    <span className="font-mono font-bold text-slate-800">{result.prediction_interval.lower.toFixed(2)} g/kg</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-white/80 border border-emerald-100">
                    <span className="text-slate-500 block text-[10px]">Upper Bound</span>
                    <span className="font-mono font-bold text-slate-800">{result.prediction_interval.upper.toFixed(2)} g/kg</span>
                  </div>
                </div>
              </div>
            </GlassCard>
          ) : (
            <GlassCard className="p-12 text-center space-y-3">
              <Mountain className="w-10 h-10 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">No Soil Organic Carbon Estimated</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Fill out soil chemical & physical parameters on the left to estimate SOC content with confidence bounds.
              </p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
