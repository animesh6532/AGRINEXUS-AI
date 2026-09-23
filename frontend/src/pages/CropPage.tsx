import React, { useState } from 'react';
import { Sprout, CheckCircle2, AlertTriangle, Sparkles, Layers } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ConfidenceBar } from '../components/intelligence/ConfidenceBar';
import { api } from '../services/api';
import { CropRecommendationResponse } from '../types/api';

export const CropPage: React.FC = () => {
  const [formData, setFormData] = useState({
    N: 90.0,
    P: 42.0,
    K: 43.0,
    temperature: 20.87,
    humidity: 82.0,
    ph: 6.5,
    rainfall: 202.9,
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<CropRecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictCrop(formData);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate crop recommendation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-agri-100 text-agri-700 flex items-center justify-center font-bold">
          <Sprout className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Crop Recommendation</h1>
          <p className="text-xs text-slate-500">
            ExtraTreesClassifier champion model trained on raw soil NPK and climate factors.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Inputs */}
        <GlassCard variant="strong" className="p-6 lg:col-span-1 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-primary-600" /> Input Agronomic Parameters
          </h3>

          <form onSubmit={handleSubmit} className="space-y-3">
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
                label="Phosphorus (P)"
                type="number"
                step="0.1"
                value={formData.P}
                onChange={(e) => setFormData({ ...formData, P: parseFloat(e.target.value) || 0 })}
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
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Temperature"
                type="number"
                step="0.01"
                unit="°C"
                value={formData.temperature}
                onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Humidity"
                type="number"
                step="0.1"
                unit="%"
                value={formData.humidity}
                onChange={(e) => setFormData({ ...formData, humidity: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Soil pH"
                type="number"
                step="0.1"
                min="0"
                max="14"
                value={formData.ph}
                onChange={(e) => setFormData({ ...formData, ph: parseFloat(e.target.value) || 0 })}
                required
              />
              <Input
                label="Rainfall"
                type="number"
                step="0.1"
                unit="mm"
                value={formData.rainfall}
                onChange={(e) => setFormData({ ...formData, rainfall: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>

            <Button type="submit" variant="secondary" size="md" className="w-full mt-2" isLoading={loading}>
              Recommend Crop Species
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
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">Recommended Crop</span>
                  <h2 className="text-3xl font-black text-slate-900 capitalize mt-1 flex items-center gap-2">
                    <Sprout className="w-7 h-7 text-agri-600" />
                    {result.prediction}
                  </h2>
                </div>
                <div className="text-right">
                  <Badge variant={result.is_plausible ? 'success' : 'warning'} dot>
                    {result.is_plausible ? 'Plausible Profile' : 'Out of Distribution'}
                  </Badge>
                  <p className="text-[10px] text-slate-400 mt-1">{result.anomaly_status}</p>
                </div>
              </div>

              <ConfidenceBar confidence={result.confidence} label="Prediction Confidence Score" />

              {/* Top K Probabilities */}
              {result.top_k_predictions && result.top_k_predictions.length > 0 && (
                <div className="space-y-3 pt-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Top Alternative Crop Recommendations</h4>
                  <div className="space-y-2">
                    {result.top_k_predictions.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-white/70 border border-slate-100 text-xs">
                        <span className="font-semibold text-slate-800 capitalize flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-agri-100 text-agri-700 flex items-center justify-center text-[10px] font-bold">
                            {idx + 1}
                          </span>
                          {item.crop}
                        </span>
                        <span className="font-mono font-bold text-slate-700">{(item.probability * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </GlassCard>
          ) : (
            <GlassCard className="p-12 text-center space-y-3">
              <Sparkles className="w-10 h-10 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">No Crop Recommendation Yet</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Fill out the soil NPK, pH, and climate parameters on the left and click "Recommend Crop Species" to run ExtraTrees evaluation.
              </p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
