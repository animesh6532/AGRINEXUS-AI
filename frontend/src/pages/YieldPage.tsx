import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertTriangle, Layers, MapPin } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { UncertaintyRange } from '../components/intelligence/UncertaintyRange';
import { useLocationContext } from '../context/LocationContext';
import { api } from '../services/api';
import { YieldPredictionResponse } from '../types/api';

export const YieldPage: React.FC = () => {
  const { location } = useLocationContext();

  const [formData, setFormData] = useState({
    Crop: 'Rice',
    Season: 'Kharif',
    State: 'West Bengal',
    Area: 100.0,
    Annual_Rainfall: 1200.0,
    Fertilizer: 15000.0,
    Pesticide: 500.0,
    Fertilizer_Per_Area: 150.0,
    Pesticide_Per_Area: 5.0,
  });

  // Pre-populate State from location context
  useEffect(() => {
    if (location?.state) {
      setFormData((prev) => ({ ...prev, State: location.state || prev.State }));
    }
  }, [location?.state]);

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
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="FIELD INTELLIGENCE"
        title="Harvest Yield Forecasting"
        description="From field conditions to harvest outlook. XGBoost regression model predicting crop yield with 95% uncertainty interval bounds based on area, rainfall, and input intensity."
        imageSrc="/images/yield-intelligence.webp"
      />

      <ScopeWarning
        type="info"
        message="Yield dataset combines heterogeneous target conventions across states and crops. Predictions report uncertainty interval bounds."
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Form Inputs (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
            <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-4">
              <Layers className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                Harvest & Input Parameters
              </h3>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
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

              <div className="grid grid-cols-2 gap-3">
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

              <div className="grid grid-cols-2 gap-3">
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

              <div className="grid grid-cols-2 gap-3">
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

              <Button
                type="submit"
                variant="lime"
                size="lg"
                className="w-full mt-2 shadow-md hover:shadow-glow"
                isLoading={loading}
                icon={<TrendingUp className="w-4 h-4" />}
              >
                Predict Crop Yield
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
                    PREDICTED HARVEST YIELD
                  </span>
                  <h2 className="text-4xl font-black font-editorial text-[#0B1C10] mt-1">
                    {result.predicted_yield.toFixed(2)}
                  </h2>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
                  ● XGBoost Regression
                </span>
              </div>

              {/* Uncertainty Range */}
              <UncertaintyRange
                lowerBound={result.prediction_interval.lower}
                prediction={result.predicted_yield}
                upperBound={result.prediction_interval.upper}
                unit=""
                label="Yield Uncertainty Range"
                confidenceIntervalLabel={`95% Confidence Interval (±${result.prediction_interval.margin.toFixed(2)})`}
              />
            </GlassCard>
          ) : (
            <div className="relative rounded-3xl overflow-hidden border border-[#E2E7DA] bg-[#FAFBF7] p-8 sm:p-12 text-center space-y-6 flex flex-col items-center justify-center min-h-[380px] group">
              <div className="w-14 h-14 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-extrabold text-xl shadow-sm">
                <TrendingUp className="w-7 h-7" />
              </div>

              <div className="space-y-2 max-w-md">
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                  Ready for Harvest Yield Forecasting
                </h3>
                <p className="text-xs text-[#536056] leading-relaxed">
                  Specify crop area, rainfall, and total input intensities on the left to run XGBoost yield estimation.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
