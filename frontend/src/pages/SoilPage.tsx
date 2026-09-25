import React, { useState } from 'react';
import { Mountain, AlertTriangle, Layers } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { UncertaintyRange } from '../components/intelligence/UncertaintyRange';
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
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="FIELD INTELLIGENCE"
        title="Soil Organic Carbon Analysis"
        description="Soil-science-inspired evaluation estimating Soil Organic Carbon (SOC in g/kg) with 95% residual confidence intervals using the LUCAS topsoil pipeline."
        imageSrc="/images/soil-intelligence.webp"
      />

      <ScopeWarning
        type="warning"
        message="Model trained using the LUCAS European Topsoil dataset. Not automatically validated for all non-European regional soil profiles or unique tropical soils."
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Form Inputs (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
            <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-4">
              <Layers className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                Physical & Chemical Soil Properties
              </h3>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
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

              <div className="grid grid-cols-3 gap-3">
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

              <div className="grid grid-cols-2 gap-3">
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

              <div className="grid grid-cols-2 gap-3">
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

              <Button
                type="submit"
                variant="lime"
                size="lg"
                className="w-full mt-2 shadow-md hover:shadow-glow"
                isLoading={loading}
                icon={<Mountain className="w-4 h-4" />}
              >
                Estimate Soil Organic Carbon
              </Button>
            </form>
          </GlassCard>
        </div>

        {/* Prediction Results & 95% Confidence Bounds (7 Cols) */}
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
                    PREDICTED SOIL ORGANIC CARBON (SOC)
                  </span>
                  <h2 className="text-4xl font-black font-editorial text-[#0B1C10] mt-1">
                    {result.predicted_soc.toFixed(2)}{' '}
                    <span className="text-sm font-sans font-medium text-[#536056]">{result.unit}</span>
                  </h2>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
                  ● LUCAS Pipeline Active
                </span>
              </div>

              {/* 95% Confidence Interval Display */}
              <UncertaintyRange
                lowerBound={result.prediction_interval.lower}
                prediction={result.predicted_soc}
                upperBound={result.prediction_interval.upper}
                unit={result.unit}
                label="SOC Prediction Uncertainty Range"
                confidenceIntervalLabel={`95% Confidence Interval (±${result.prediction_interval.margin.toFixed(2)} g/kg)`}
              />
            </GlassCard>
          ) : (
            <div className="relative rounded-3xl overflow-hidden border border-[#E2E7DA] bg-[#FAFBF7] p-8 sm:p-12 text-center space-y-6 flex flex-col items-center justify-center min-h-[380px] group">
              <div className="w-14 h-14 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-extrabold text-xl shadow-sm">
                <Mountain className="w-7 h-7" />
              </div>

              <div className="space-y-2 max-w-md">
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                  Ready for Soil Organic Carbon Analysis
                </h3>
                <p className="text-xs text-[#536056] leading-relaxed">
                  Provide soil pH, clay/silt/sand proportions, NPK, and region features on the left to estimate SOC content with uncertainty bounds.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
