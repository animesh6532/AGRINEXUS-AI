import React, { useState } from 'react';
import { Sprout, AlertTriangle, Layers } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { ConfidenceBar } from '../components/intelligence/ConfidenceBar';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
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
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Editorial Page Hero */}
      <AgriculturalPageHero
        category="FIELD INTELLIGENCE"
        title="Crop Recommendation Studio"
        description="Match soil NPK nutrients, soil pH, ambient temperature, humidity, and rainfall against ExtraTrees machine learning inference to identify optimal crop species."
        imageSrc="/images/crop-intelligence.webp"
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Form Inputs Panel (5 Cols Desktop) */}
        <div className="lg:col-span-5 space-y-6">
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
            <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-4">
              <Layers className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                Agronomic Parameters
              </h3>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
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

              <Button
                type="submit"
                variant="lime"
                size="lg"
                className="w-full mt-2 shadow-md hover:shadow-glow"
                isLoading={loading}
                icon={<Sprout className="w-4 h-4" />}
              >
                Recommend Crop Species
              </Button>
            </form>
          </GlassCard>

          <ScopeWarning
            message="Crop recommendation evaluates ExtraTrees multi-class classification over soil NPK and climate features. Verify local seed availability and seasonal sowing windows."
            type="info"
          />
        </div>

        {/* Intelligence Visual & Result Area (7 Cols Desktop) */}
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
                    RECOMMENDED CROP SPECIES
                  </span>
                  <h2 className="text-4xl font-black font-editorial text-[#0B1C10] capitalize mt-1 flex items-center gap-3">
                    <Sprout className="w-8 h-8 text-[#2F6B3C]" />
                    {result.prediction}
                  </h2>
                </div>

                <div className="sm:text-right">
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
                    result.is_plausible
                      ? 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                      : 'bg-amber-500/10 text-amber-800 border border-amber-500/20'
                  }`}>
                    {result.is_plausible ? '● Plausible Profile' : '● Out of Distribution'}
                  </span>
                  <p className="text-[10px] text-[#536056] mt-1 font-mono">{result.anomaly_status}</p>
                </div>
              </div>

              <ConfidenceBar confidence={result.confidence} label="ExtraTrees Model Confidence" />

              {/* Top K Probabilities */}
              {result.top_k_predictions && result.top_k_predictions.length > 0 && (
                <div className="space-y-3 pt-4">
                  <h4 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                    Top Alternative Crop Matches
                  </h4>
                  <div className="space-y-2">
                    {result.top_k_predictions.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3.5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-semibold text-[#162018]"
                      >
                        <span className="capitalize flex items-center gap-2.5">
                          <span className="w-6 h-6 rounded-full bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center text-xs font-extrabold">
                            {idx + 1}
                          </span>
                          {item.crop}
                        </span>
                        <span className="font-mono font-extrabold text-[#2F6B3C]">
                          {(item.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </GlassCard>
          ) : (
            <div className="relative rounded-3xl overflow-hidden border border-[#E2E7DA] bg-[#FAFBF7] p-8 sm:p-12 text-center space-y-6 flex flex-col items-center justify-center min-h-[380px] group">
              <div className="w-full h-full absolute inset-0 z-0 opacity-15 overflow-hidden">
                <img
                  src="/images/crop-intelligence.webp"
                  alt="Crop preview background"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                />
              </div>

              <div className="relative z-10 w-14 h-14 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-extrabold text-xl shadow-sm">
                <Sprout className="w-7 h-7" />
              </div>

              <div className="relative z-10 space-y-2 max-w-md">
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                  Ready for Crop Analysis
                </h3>
                <p className="text-xs text-[#536056] leading-relaxed">
                  Enter your soil NPK nutrients, pH, and local weather telemetry on the left to evaluate crop suitability across 22 major crop species.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
