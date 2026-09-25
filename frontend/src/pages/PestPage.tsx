import React, { useState, useEffect } from 'react';
import { Bug, Upload, Image as ImageIcon, AlertTriangle, CloudRain, MapPin } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { ConfidenceBar } from '../components/intelligence/ConfidenceBar';
import { QualityReport } from '../components/intelligence/QualityReport';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { useLocationContext } from '../context/LocationContext';
import { api } from '../services/api';
import { VisualPestPredictResponse, PestRiskResponse } from '../types/api';

export const PestPage: React.FC = () => {
  const { location } = useLocationContext();
  const [activeTab, setActiveTab] = useState<'visual' | 'env'>('visual');

  // Visual State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [visualLoading, setVisualLoading] = useState<boolean>(false);
  const [visualResult, setVisualResult] = useState<VisualPestPredictResponse | null>(null);
  const [visualError, setVisualError] = useState<string | null>(null);

  // Environmental Risk Form State
  const [envForm, setEnvForm] = useState({
    Temperature: 28.5,
    Humidity: 75.0,
    Rainfall: 120.0,
    Crop_Type: 'Rice',
    Soil_Type: 'Clay',
    Region: 'South',
  });

  // Pre-populate region from location context state when available
  useEffect(() => {
    if (location?.state) {
      setEnvForm((prev) => ({ ...prev, Region: location.state || prev.Region }));
    }
  }, [location?.state]);

  const [envLoading, setEnvLoading] = useState<boolean>(false);
  const [envResult, setEnvResult] = useState<PestRiskResponse | null>(null);
  const [envError, setEnvError] = useState<string | null>(null);

  const handleVisualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setVisualLoading(true);
    setVisualError(null);
    try {
      const res = await api.predictPestVisual(selectedFile);
      setVisualResult(res);
    } catch (err: any) {
      setVisualError(err.message || 'Failed to classify insect pest species.');
    } finally {
      setVisualLoading(false);
    }
  };

  const handleEnvSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEnvLoading(true);
    setEnvError(null);
    try {
      const res = await api.predictPestRisk(envForm);
      setEnvResult(res);
    } catch (err: any) {
      setEnvError(err.message || 'Failed to predict environmental pest outbreak risk.');
    } finally {
      setEnvLoading(false);
    }
  };

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="FIELD INTELLIGENCE"
        title="Pest Intelligence & Risk Studio"
        description="Dual pest inference capabilities: MobileNetV3 visual insect species classification and RandomForest microclimate outbreak risk assessment."
        imageSrc="/images/pest-intelligence.webp"
      />

      {/* Mode Switcher Tabs */}
      <div className="flex border-b border-[#E2E7DA] gap-3">
        <button
          onClick={() => setActiveTab('visual')}
          className={`px-5 py-3 text-xs font-bold transition-all border-b-2 ${
            activeTab === 'visual'
              ? 'border-[#2F6B3C] text-[#2F6B3C]'
              : 'border-transparent text-[#536056] hover:text-[#162018]'
          }`}
        >
          1. Visual Insect Classification
        </button>
        <button
          onClick={() => setActiveTab('env')}
          className={`px-5 py-3 text-xs font-bold transition-all border-b-2 ${
            activeTab === 'env'
              ? 'border-[#2F6B3C] text-[#2F6B3C]'
              : 'border-transparent text-[#536056] hover:text-[#162018]'
          }`}
        >
          2. Environmental Outbreak Risk Model
        </button>
      </div>

      {/* TAB 1: VISUAL PEST CLASSIFICATION */}
      {activeTab === 'visual' && (
        <div className="space-y-6">
          <ScopeWarning
            type="info"
            message="Uses MobileNetV3 Small (102 insect classes). Performs single-insect visual classification, NOT bounding-box object detection or multi-target tracking."
          />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Form */}
            <div className="lg:col-span-5 space-y-6">
              <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
                <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-4">
                  <Upload className="w-5 h-5 text-[#2F6B3C]" />
                  <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                    Upload Insect Photo
                  </h3>
                </div>

                <form onSubmit={handleVisualSubmit} className="space-y-4">
                  <div
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                        setSelectedFile(e.dataTransfer.files[0]);
                        setPreviewUrl(URL.createObjectURL(e.dataTransfer.files[0]));
                      }
                    }}
                    className="border-2 border-dashed border-[#E2E7DA] hover:border-[#2F6B3C] rounded-3xl p-6 text-center bg-[#FAFBF7] cursor-pointer relative group"
                  >
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          setSelectedFile(e.target.files[0]);
                          setPreviewUrl(URL.createObjectURL(e.target.files[0]));
                        }
                      }}
                      className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-20"
                    />

                    {previewUrl ? (
                      <div className="space-y-3 relative z-10">
                        <img
                          src={previewUrl}
                          alt="Insect Preview"
                          className="h-52 max-w-full object-contain mx-auto rounded-2xl shadow-md border border-[#E2E7DA]"
                        />
                        <p className="text-xs font-bold text-[#0B1C10]">{selectedFile?.name}</p>
                      </div>
                    ) : (
                      <div className="space-y-3 py-8 relative z-10">
                        <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                          <ImageIcon className="w-6 h-6" />
                        </div>
                        <p className="text-xs font-extrabold font-editorial text-[#0B1C10]">
                          Drag & drop single insect photo or click to browse
                        </p>
                      </div>
                    )}
                  </div>

                  <Button
                    type="submit"
                    variant="lime"
                    size="lg"
                    className="w-full shadow-md hover:shadow-glow"
                    disabled={!selectedFile}
                    isLoading={visualLoading}
                  >
                    Classify Insect Species
                  </Button>
                </form>
              </GlassCard>
            </div>

            {/* Results */}
            <div className="lg:col-span-7 space-y-6">
              {visualError && (
                <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>{visualError}</span>
                </div>
              )}

              {visualResult ? (
                <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-6">
                    <div>
                      <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                        CLASSIFIED INSECT SPECIES
                      </span>
                      <h2 className="text-3xl font-black font-editorial text-[#0B1C10] capitalize mt-1">
                        {visualResult.predicted_pest}
                      </h2>
                    </div>
                    <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
                      {(visualResult.confidence * 100).toFixed(1)}% Match Probability
                    </span>
                  </div>

                  <ConfidenceBar confidence={visualResult.confidence} label="MobileNetV3 Species Classification" />

                  <QualityReport report={visualResult.image_quality} />

                  {visualResult.top_k_predictions && (
                    <div className="space-y-3 pt-2">
                      <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                        Top Candidate Species Breakdown
                      </span>
                      <div className="space-y-2">
                        {visualResult.top_k_predictions.map((p, idx) => (
                          <div
                            key={idx}
                            className="flex justify-between p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-semibold"
                          >
                            <span className="text-[#0B1C10] capitalize">{p.pest_class}</span>
                            <span className="font-mono font-extrabold text-[#2F6B3C]">
                              {(p.probability * 100).toFixed(1)}%
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
                      src="/images/pest-intelligence.webp"
                      alt="Pest preview"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    />
                  </div>

                  <div className="relative z-10 w-14 h-14 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-extrabold text-xl shadow-sm">
                    <Bug className="w-7 h-7" />
                  </div>

                  <div className="relative z-10 space-y-2 max-w-md">
                    <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                      Ready for Insect Species Classification
                    </h3>
                    <p className="text-xs text-[#536056] leading-relaxed">
                      Upload a single-insect macro photo on the left to evaluate MobileNetV3 102-class visual classification.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ENVIRONMENTAL PEST RISK */}
      {activeTab === 'env' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-6">
            <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
              <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
                <div className="flex items-center gap-2">
                  <CloudRain className="w-5 h-5 text-[#2F6B3C]" />
                  <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                    Microclimate Outbreak Parameters
                  </h3>
                </div>
                {location && (
                  <span className="text-[10px] text-[#2F6B3C] font-semibold flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {location.state || location.city}
                  </span>
                )}
              </div>

              <form onSubmit={handleEnvSubmit} className="space-y-4">
                <Input
                  label="Temperature"
                  type="number"
                  step="0.1"
                  unit="°C"
                  value={envForm.Temperature}
                  onChange={(e) => setEnvForm({ ...envForm, Temperature: parseFloat(e.target.value) || 0 })}
                  required
                />
                <Input
                  label="Humidity"
                  type="number"
                  step="0.1"
                  unit="%"
                  value={envForm.Humidity}
                  onChange={(e) => setEnvForm({ ...envForm, Humidity: parseFloat(e.target.value) || 0 })}
                  required
                />
                <Input
                  label="Rainfall"
                  type="number"
                  step="0.1"
                  unit="mm"
                  value={envForm.Rainfall}
                  onChange={(e) => setEnvForm({ ...envForm, Rainfall: parseFloat(e.target.value) || 0 })}
                  required
                />

                <Select
                  label="Crop Type"
                  value={envForm.Crop_Type}
                  onChange={(e) => setEnvForm({ ...envForm, Crop_Type: e.target.value })}
                  options={[
                    { value: 'Rice', label: 'Rice' },
                    { value: 'Wheat', label: 'Wheat' },
                    { value: 'Maize', label: 'Maize' },
                    { value: 'Cotton', label: 'Cotton' },
                  ]}
                />

                <Select
                  label="Soil Type"
                  value={envForm.Soil_Type}
                  onChange={(e) => setEnvForm({ ...envForm, Soil_Type: e.target.value })}
                  options={[
                    { value: 'Clay', label: 'Clay' },
                    { value: 'Sandy', label: 'Sandy' },
                    { value: 'Loam', label: 'Loam' },
                    { value: 'Black', label: 'Black' },
                  ]}
                />

                <Input
                  label="Region (Location-aware)"
                  value={envForm.Region}
                  onChange={(e) => setEnvForm({ ...envForm, Region: e.target.value })}
                  required
                />

                <Button
                  type="submit"
                  variant="lime"
                  size="lg"
                  className="w-full mt-2 shadow-md hover:shadow-glow"
                  isLoading={envLoading}
                >
                  Assess Outbreak Risk
                </Button>
              </form>
            </GlassCard>
          </div>

          <div className="lg:col-span-7 space-y-6">
            {envError && (
              <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{envError}</span>
              </div>
            )}

            {envResult ? (
              <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-6">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                      OUTBREAK SEVERITY RISK LEVEL
                    </span>
                    <h2 className="text-4xl font-black font-editorial text-[#0B1C10] mt-1">
                      {envResult.pest_severity_risk} Severity
                    </h2>
                  </div>
                  <span className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold ${
                    envResult.pest_severity_risk === 'Low'
                      ? 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                      : envResult.pest_severity_risk === 'Medium'
                      ? 'bg-amber-500/10 text-amber-800 border border-amber-500/20'
                      : 'bg-rose-500/10 text-rose-800 border border-rose-500/20'
                  }`}>
                    {envResult.pest_severity_risk} Outbreak Risk
                  </span>
                </div>

                {envResult.confidence && (
                  <ConfidenceBar confidence={envResult.confidence} label="RandomForest Risk Severity Confidence" />
                )}

                {envResult.top_k_predictions && (
                  <div className="space-y-3 pt-2">
                    <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                      Risk Severity Probability Distribution
                    </span>
                    <div className="space-y-2">
                      {envResult.top_k_predictions.map((r, idx) => (
                        <div
                          key={idx}
                          className="flex justify-between p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-semibold"
                        >
                          <span className="text-[#0B1C10]">{r.risk_level} Risk Level</span>
                          <span className="font-mono font-extrabold text-[#2F6B3C]">
                            {(r.probability * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </GlassCard>
            ) : (
              <div className="relative rounded-3xl overflow-hidden border border-[#E2E7DA] bg-[#FAFBF7] p-8 sm:p-12 text-center space-y-6 flex flex-col items-center justify-center min-h-[380px]">
                <div className="w-14 h-14 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-extrabold text-xl shadow-sm">
                  <CloudRain className="w-7 h-7" />
                </div>

                <div className="space-y-2 max-w-md">
                  <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                    Ready for Outbreak Risk Assessment
                  </h3>
                  <p className="text-xs text-[#536056] leading-relaxed">
                    Provide microclimate temperature, humidity, rainfall, crop type, and soil parameters to evaluate outbreak severity risk.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
