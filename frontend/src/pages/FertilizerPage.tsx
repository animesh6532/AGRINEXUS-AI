import React, { useState, useEffect } from 'react';
import { FlaskConical, AlertTriangle, Layers, MapPin } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { ConfidenceBar } from '../components/intelligence/ConfidenceBar';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { useLocationContext } from '../context/LocationContext';
import { api } from '../services/api';
import { FertilizerRecommendResponse } from '../types/api';

export const FertilizerPage: React.FC = () => {
  const { location } = useLocationContext();

  const [formData, setFormData] = useState({
    Nitrogen: 37.0,
    Phosphorus: 20.0,
    Potassium: 20.0,
    pH: 6.5,
    Rainfall: 120.0,
    Temperature: 26.0,
    District_Name: 'Pune',
    Soil_color: 'Black',
    Crop: 'Paddy',
  });

  // Pre-populate District_Name from selected field location
  useEffect(() => {
    if (location) {
      const dist = location.district || location.city;
      if (dist) {
        setFormData((prev) => ({ ...prev, District_Name: dist }));
      }
    }
  }, [location?.district, location?.city]);

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
      setError(err.message || 'Failed to generate fertilizer recommendation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="FIELD INTELLIGENCE"
        title="Fertilizer Formulation Advisor"
        description="Soil → Crop → Nutrient → Formulation recommendation using machine learning inference over target crop requirements and nutrient deficit levels."
        imageSrc="/images/smart-farming.webp"
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Form Inputs (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
            <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-[#2F6B3C]" />
                <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                  Soil & Crop Parameters
                </h3>
              </div>
              {location && (
                <span className="text-[10px] text-[#2F6B3C] font-semibold flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {location.city || location.district}
                </span>
              )}
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <Select
                  label="Soil Color"
                  value={formData.Soil_color}
                  onChange={(e) => setFormData({ ...formData, Soil_color: e.target.value })}
                  options={[
                    { value: 'Black', label: 'Black Soil' },
                    { value: 'Red', label: 'Red Soil' },
                    { value: 'Medium Brown', label: 'Medium Brown' },
                    { value: 'Dark Brown', label: 'Dark Brown' },
                    { value: 'Reddish', label: 'Reddish Soil' },
                  ]}
                />

                <Select
                  label="Crop Type"
                  value={formData.Crop}
                  onChange={(e) => setFormData({ ...formData, Crop: e.target.value })}
                  options={[
                    { value: 'Paddy', label: 'Paddy / Rice' },
                    { value: 'Maize', label: 'Maize' },
                    { value: 'Sugarcane', label: 'Sugarcane' },
                    { value: 'Cotton', label: 'Cotton' },
                    { value: 'Wheat', label: 'Wheat' },
                  ]}
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <Input
                  label="Nitrogen (N)"
                  type="number"
                  step="0.1"
                  value={formData.Nitrogen}
                  onChange={(e) => setFormData({ ...formData, Nitrogen: parseFloat(e.target.value) || 0 })}
                  required
                />
                <Input
                  label="Phosphorus (P)"
                  type="number"
                  step="0.1"
                  value={formData.Phosphorus}
                  onChange={(e) => setFormData({ ...formData, Phosphorus: parseFloat(e.target.value) || 0 })}
                  required
                />
                <Input
                  label="Potassium (K)"
                  type="number"
                  step="0.1"
                  value={formData.Potassium}
                  onChange={(e) => setFormData({ ...formData, Potassium: parseFloat(e.target.value) || 0 })}
                  required
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <Input
                  label="Soil pH"
                  type="number"
                  step="0.1"
                  value={formData.pH}
                  onChange={(e) => setFormData({ ...formData, pH: parseFloat(e.target.value) || 0 })}
                  required
                />
                <Input
                  label="Temperature (°C)"
                  type="number"
                  step="0.1"
                  value={formData.Temperature}
                  onChange={(e) => setFormData({ ...formData, Temperature: parseFloat(e.target.value) || 0 })}
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
              </div>

              <Input
                label="District Name (Location-aware)"
                value={formData.District_Name}
                onChange={(e) => setFormData({ ...formData, District_Name: e.target.value })}
                required
              />

              <Button
                type="submit"
                variant="lime"
                size="lg"
                className="w-full mt-2 shadow-md hover:shadow-glow"
                isLoading={loading}
                icon={<FlaskConical className="w-4 h-4" />}
              >
                Recommend Fertilizer Formulation
              </Button>
            </form>
          </GlassCard>

          <ScopeWarning
            message="Fertilizer recommendation model trained primarily on Western Maharashtra soil/crop agronomic surveys. Validate agronomic dose before field application."
            type="warning"
          />
        </div>

        {/* Recommendation Panel (7 Cols) */}
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
                    RECOMMENDED FERTILIZER FORMULATION
                  </span>
                  <h2 className="text-4xl font-black font-editorial text-[#0B1C10] mt-1 flex items-center gap-3">
                    <FlaskConical className="w-8 h-8 text-[#2F6B3C]" />
                    {result.predicted_formulation}
                  </h2>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
                  {((result.confidence ?? 0.85) * 100).toFixed(1)}% Formulation Match
                </span>
              </div>

              <ConfidenceBar confidence={result.confidence ?? 0.85} label="Model Formulation Match Probability" />

              {/* Alternative Formulations */}
              {result.top_k_predictions && result.top_k_predictions.length > 0 && (
                <div className="space-y-3 pt-4">
                  <h4 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                    Alternative Commercial Formulations
                  </h4>
                  <div className="space-y-2">
                    {result.top_k_predictions.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3.5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-semibold"
                      >
                        <span className="text-[#0B1C10] flex items-center gap-2.5">
                          <span className="w-6 h-6 rounded-full bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center text-xs font-extrabold">
                            {idx + 1}
                          </span>
                          {item.formulation}
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
              <div className="w-14 h-14 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-extrabold text-xl shadow-sm">
                <FlaskConical className="w-7 h-7" />
              </div>

              <div className="space-y-2 max-w-md">
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                  Ready for Fertilizer Recommendation
                </h3>
                <p className="text-xs text-[#536056] leading-relaxed">
                  Provide soil color, district, target crop, and NPK nutrient levels on the left to evaluate targeted fertilizer product formulations.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
