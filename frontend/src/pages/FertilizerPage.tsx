import React, { useState } from 'react';
import { FlaskConical, AlertTriangle, Sparkles, Layers } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ConfidenceBar } from '../components/intelligence/ConfidenceBar';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { api } from '../services/api';
import { FertilizerRecommendResponse } from '../types/api';

export const FertilizerPage: React.FC = () => {
  const [formData, setFormData] = useState({
    Nitrogen: 20.0,
    Phosphorus: 20.0,
    Potassium: 20.0,
    pH: 6.5,
    Rainfall: 800.0,
    Temperature: 26.0,
    District_Name: 'Pune',
    Soil_color: 'Black',
    Crop: 'Sugarcane',
    Link: 'https://example.com',
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<FertilizerRecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictFertilizer(formData);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate fertilizer formulation recommendation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold">
          <FlaskConical className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Fertilizer Recommendation</h1>
          <p className="text-xs text-slate-500">
            Commercial fertilizer product formulation classification using LightGBM preprocessed pipeline.
          </p>
        </div>
      </div>

      <ScopeWarning
        type="warning"
        message="Model trained primarily on Western Maharashtra agricultural data. Represents commercial product formulation classification, not universal NPK optimization."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Inputs */}
        <GlassCard variant="strong" className="p-6 lg:col-span-1 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-purple-600" /> Nutrient & Field Context
          </h3>

          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-3 gap-2">
              <Input
                label="Nitrogen"
                type="number"
                step="0.1"
                value={formData.Nitrogen}
                onChange={(e) => setFormData({ ...formData, Nitrogen: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Phosphorus"
                type="number"
                step="0.1"
                value={formData.Phosphorus}
                onChange={(e) => setFormData({ ...formData, Phosphorus: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Potassium"
                type="number"
                step="0.1"
                value={formData.Potassium}
                onChange={(e) => setFormData({ ...formData, Potassium: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <Input
                label="Soil pH"
                type="number"
                step="0.1"
                min="0"
                max="14"
                value={formData.pH}
                onChange={(e) => setFormData({ ...formData, pH: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Rainfall (mm)"
                type="number"
                step="0.1"
                value={formData.Rainfall}
                onChange={(e) => setFormData({ ...formData, Rainfall: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Temp (°C)"
                type="number"
                step="0.1"
                value={formData.Temperature}
                onChange={(e) => setFormData({ ...formData, Temperature: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <Select
              label="District Name"
              value={formData.District_Name}
              onChange={(e) => setFormData({ ...formData, District_Name: e.target.value })}
              options={[
                { value: 'Pune', label: 'Pune' },
                { value: 'Nashik', label: 'Nashik' },
                { value: 'Kolhapur', label: 'Kolhapur' },
                { value: 'Ahmednagar', label: 'Ahmednagar' },
                { value: 'Solapur', label: 'Solapur' },
              ]}
            />

            <Select
              label="Soil Color"
              value={formData.Soil_color}
              onChange={(e) => setFormData({ ...formData, Soil_color: e.target.value })}
              options={[
                { value: 'Black', label: 'Black Soil' },
                { value: 'Red', label: 'Red Soil' },
                { value: 'Brown', label: 'Brown Soil' },
                { value: 'Alluvial', label: 'Alluvial Soil' },
              ]}
            />

            <Select
              label="Target Crop"
              value={formData.Crop}
              onChange={(e) => setFormData({ ...formData, Crop: e.target.value })}
              options={[
                { value: 'Sugarcane', label: 'Sugarcane' },
                { value: 'Cotton', label: 'Cotton' },
                { value: 'Rice', label: 'Rice' },
                { value: 'Wheat', label: 'Wheat' },
                { value: 'Maize', label: 'Maize' },
              ]}
            />

            <Button type="submit" variant="secondary" size="md" className="w-full mt-2" isLoading={loading}>
              Recommend Formulation
            </Button>
          </form>
        </GlassCard>

        {/* Prediction Output */}
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
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">Recommended Product Formulation</span>
                  <h2 className="text-3xl font-black text-slate-900 capitalize mt-1">
                    Formulation Code: {result.predicted_formulation}
                  </h2>
                </div>
                <Badge variant="primary">LightGBM Classification</Badge>
              </div>

              {result.confidence !== null && (
                <ConfidenceBar confidence={result.confidence} label="Formulation Recommendation Confidence" />
              )}

              {result.top_k_predictions && result.top_k_predictions.length > 0 && (
                <div className="space-y-2 text-xs">
                  <span className="font-bold uppercase tracking-wider text-slate-500 block">Alternative Commercial Product Formulations</span>
                  {result.top_k_predictions.map((p, idx) => (
                    <div key={idx} className="flex justify-between p-2 rounded-lg bg-white/70 border border-slate-100">
                      <span className="font-semibold text-slate-800">Formulation {p.formulation}</span>
                      <span className="font-mono font-bold text-slate-700">{(p.probability * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>
          ) : (
            <GlassCard className="p-12 text-center space-y-3">
              <FlaskConical className="w-10 h-10 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">No Fertilizer Formulation Recommended</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Fill out soil NPK, pH, district, and crop parameters on the left to obtain fertilizer recommendations.
              </p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
