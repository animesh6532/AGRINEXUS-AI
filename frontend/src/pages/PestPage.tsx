import React, { useState } from 'react';
import { Bug, Upload, Image as ImageIcon, AlertTriangle, CloudRain } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ConfidenceBar } from '../components/intelligence/ConfidenceBar';
import { QualityReport } from '../components/intelligence/QualityReport';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { api } from '../services/api';
import { VisualPestPredictResponse, PestRiskResponse } from '../types/api';

export const PestPage: React.FC = () => {
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
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
          <Bug className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Pest Intelligence & Outbreak Risk</h1>
          <p className="text-xs text-slate-500">
            Dual pest services: PyTorch MobileNetV3 visual insect species classification & RandomForest environmental risk assessment.
          </p>
        </div>
      </div>

      {/* Mode Switcher Tabs */}
      <div className="flex border-b border-slate-200/80 gap-2">
        <button
          onClick={() => setActiveTab('visual')}
          className={`px-4 py-2.5 text-xs font-bold transition-all border-b-2 ${
            activeTab === 'visual'
              ? 'border-amber-600 text-amber-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Visual Pest Insect Classification
        </button>
        <button
          onClick={() => setActiveTab('env')}
          className={`px-4 py-2.5 text-xs font-bold transition-all border-b-2 ${
            activeTab === 'env'
              ? 'border-amber-600 text-amber-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Environmental Outbreak Risk Model
        </button>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* TAB 1: VISUAL PEST CLASSIFICATION */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === 'visual' && (
        <div className="space-y-6">
          <ScopeWarning
            type="info"
            message="Uses MobileNetV3 Small (102 insect classes). Performs single-insect visual classification, NOT bounding-box object detection or multi-target tracking."
          />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <GlassCard variant="strong" className="p-6 space-y-4">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Upload className="w-4 h-4 text-amber-600" /> Upload Insect Photo
              </h3>

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
                  className="border-2 border-dashed border-slate-300 hover:border-amber-500 rounded-2xl p-6 text-center bg-white/40 cursor-pointer relative"
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
                    className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                  />

                  {previewUrl ? (
                    <div className="space-y-2">
                      <img src={previewUrl} alt="Insect Preview" className="h-48 max-w-full object-contain mx-auto rounded-xl" />
                      <p className="text-xs font-semibold text-slate-700">{selectedFile?.name}</p>
                    </div>
                  ) : (
                    <div className="space-y-2 py-6">
                      <ImageIcon className="w-10 h-10 text-slate-400 mx-auto" />
                      <p className="text-xs font-semibold text-slate-700">Drag & drop insect photo or click to browse</p>
                    </div>
                  )}
                </div>

                <Button type="submit" variant="secondary" size="md" className="w-full" disabled={!selectedFile} isLoading={visualLoading}>
                  Classify Insect Species
                </Button>
              </form>
            </GlassCard>

            <div className="space-y-6">
              {visualError && (
                <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>{visualError}</span>
                </div>
              )}

              {visualResult ? (
                <GlassCard variant="strong" className="p-6 space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-200/60 pb-4">
                    <div>
                      <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">Classified Insect Species</span>
                      <h2 className="text-2xl font-black text-slate-900 capitalize mt-1">
                        {visualResult.predicted_pest}
                      </h2>
                    </div>
                    <Badge variant="warning">
                      {(visualResult.confidence * 100).toFixed(1)}% Match
                    </Badge>
                  </div>

                  <ConfidenceBar confidence={visualResult.confidence} label="MobileNetV3 Species Classification Probability" />

                  <QualityReport report={visualResult.image_quality} />

                  {visualResult.top_k_predictions && (
                    <div className="space-y-2 text-xs">
                      <span className="font-bold uppercase tracking-wider text-slate-500 block">Top 3 Candidates</span>
                      {visualResult.top_k_predictions.map((p, idx) => (
                        <div key={idx} className="flex justify-between p-2 rounded-lg bg-white/70 border border-slate-100">
                          <span className="font-medium text-slate-800 capitalize">{p.pest_class}</span>
                          <span className="font-mono font-bold text-slate-700">{(p.probability * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                </GlassCard>
              ) : (
                <GlassCard className="p-12 text-center space-y-3">
                  <Bug className="w-10 h-10 text-slate-300 mx-auto" />
                  <h3 className="text-base font-bold text-slate-700">No Insect Image Analyzed</h3>
                  <p className="text-xs text-slate-500">Upload a single-insect image to run MobileNetV3 102-class classification.</p>
                </GlassCard>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* TAB 2: ENVIRONMENTAL PEST RISK */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === 'env' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <GlassCard variant="strong" className="p-6 lg:col-span-1 space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <CloudRain className="w-4 h-4 text-amber-600" /> Climate & Soil Outbreak Factors
            </h3>

            <form onSubmit={handleEnvSubmit} className="space-y-3">
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

              <Select
                label="Region"
                value={envForm.Region}
                onChange={(e) => setEnvForm({ ...envForm, Region: e.target.value })}
                options={[
                  { value: 'South', label: 'South Region' },
                  { value: 'North', label: 'North Region' },
                  { value: 'West', label: 'West Region' },
                  { value: 'East', label: 'East Region' },
                ]}
              />

              <Button type="submit" variant="secondary" size="md" className="w-full mt-2" isLoading={envLoading}>
                Assess Environmental Outbreak Risk
              </Button>
            </form>
          </GlassCard>

          <div className="lg:col-span-2 space-y-6">
            {envError && (
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{envError}</span>
              </div>
            )}

            {envResult ? (
              <GlassCard variant="strong" className="p-6 space-y-6">
                <div className="flex items-center justify-between border-b border-slate-200/60 pb-4">
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">Outbreak Severity Risk Level</span>
                    <h2 className="text-3xl font-black text-slate-900 mt-1">{envResult.pest_severity_risk}</h2>
                  </div>
                  <Badge
                    variant={
                      envResult.pest_severity_risk === 'Low'
                        ? 'success'
                        : envResult.pest_severity_risk === 'Medium'
                        ? 'warning'
                        : 'danger'
                    }
                  >
                    {envResult.pest_severity_risk} Risk
                  </Badge>
                </div>

                {envResult.confidence && <ConfidenceBar confidence={envResult.confidence} label="RandomForest Risk Severity Confidence" />}

                {envResult.top_k_predictions && (
                  <div className="space-y-2 text-xs">
                    <span className="font-bold uppercase tracking-wider text-slate-500 block">Risk Distribution</span>
                    {envResult.top_k_predictions.map((r, idx) => (
                      <div key={idx} className="flex justify-between p-2 rounded-lg bg-white/70 border border-slate-100">
                        <span className="font-semibold text-slate-800">{r.risk_level} Risk</span>
                        <span className="font-mono font-bold text-slate-700">{(r.probability * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </GlassCard>
            ) : (
              <GlassCard className="p-12 text-center space-y-3">
                <CloudRain className="w-10 h-10 text-slate-300 mx-auto" />
                <h3 className="text-base font-bold text-slate-700">No Environmental Risk Evaluation</h3>
                <p className="text-xs text-slate-500">Provide climate and soil parameters on the left to estimate outbreak risk.</p>
              </GlassCard>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
