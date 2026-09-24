import React, { useState } from 'react';
import { Stethoscope, Upload, Image as ImageIcon, AlertTriangle, Layers } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { ConfidenceBar } from '../components/intelligence/ConfidenceBar';
import { QualityReport } from '../components/intelligence/QualityReport';
import { GradCAMViewer } from '../components/intelligence/GradCAMViewer';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
import { api } from '../services/api';
import { DiseasePredictResponse } from '../types/api';

export const DiseasePage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [includeGradcam, setIncludeGradcam] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<DiseasePredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    try {
      const res = await api.predictDisease(selectedFile, includeGradcam);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to process plant disease diagnosis.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero Banner */}
      <AgriculturalPageHero
        category="FIELD INTELLIGENCE"
        title="Plant Health Diagnostics Studio"
        description="ResNet18 computer vision leaf diagnosis with OpenCV image quality inspection gates and Grad-CAM visual feature heatmaps."
        imageSrc="/images/plant-health.webp"
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Upload Workspace (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
            <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-4">
              <Upload className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                Leaf Image Diagnostics Studio
              </h3>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className="border-2 border-dashed border-[#E2E7DA] hover:border-[#2F6B3C] rounded-3xl p-6 text-center transition-all bg-[#FAFBF7] cursor-pointer relative group"
              >
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(e) => e.target.files && e.target.files[0] && handleFileChange(e.target.files[0])}
                  className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-20"
                />

                {previewUrl ? (
                  <div className="space-y-3 relative z-10">
                    <img
                      src={previewUrl}
                      alt="Preview"
                      className="h-52 max-w-full object-contain mx-auto rounded-2xl shadow-md border border-[#E2E7DA]"
                    />
                    <p className="text-xs font-bold text-[#0B1C10]">{selectedFile?.name}</p>
                    <p className="text-[10px] text-[#536056]">Click or drag to replace leaf photo</p>
                  </div>
                ) : (
                  <div className="space-y-3 py-8 relative z-10">
                    <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                      <ImageIcon className="w-6 h-6" />
                    </div>
                    <p className="text-xs font-extrabold font-editorial text-[#0B1C10]">
                      Drag & drop leaf photo or click to browse
                    </p>
                    <p className="text-[10px] text-[#536056]">Supports JPEG, PNG, WEBP (Max 10MB)</p>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between text-xs bg-[#EEF3E8] p-3.5 rounded-2xl border border-[#E2E7DA]">
                <label className="flex items-center gap-2.5 text-[#162018] font-semibold cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeGradcam}
                    onChange={(e) => setIncludeGradcam(e.target.checked)}
                    className="rounded text-[#2F6B3C] focus:ring-[#2F6B3C] accent-[#2F6B3C]"
                  />
                  <span>Generate Grad-CAM Visual Heatmap</span>
                </label>
              </div>

              <Button
                type="submit"
                variant="lime"
                size="lg"
                className="w-full shadow-md hover:shadow-glow"
                disabled={!selectedFile}
                isLoading={loading}
              >
                Analyze Plant Health
              </Button>
            </form>
          </GlassCard>

          <ScopeWarning
            message="ResNet18 trained on PlantVillage benchmark dataset. Controlled test set accuracy does not equal field accuracy under complex natural lighting, multi-leaf clutter, or variable angles."
            type="warning"
          />
        </div>

        {/* Right Column: Diagnostic Results & Grad-CAM (7 Cols) */}
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
                    DIAGNOSED CONDITION
                  </span>
                  <h2 className="text-3xl font-black font-editorial text-[#0B1C10] capitalize mt-1">
                    {result.predicted_disease.replace(/___/g, ' — ').replace(/_/g, ' ')}
                  </h2>
                </div>
                <span className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold ${
                  result.confidence > 0.6
                    ? 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                    : 'bg-amber-500/10 text-amber-800 border border-amber-500/20'
                }`}>
                  {(result.confidence * 100).toFixed(1)}% Match Probability
                </span>
              </div>

              <ConfidenceBar confidence={result.confidence} label="ResNet18 Diagnostic Confidence" />

              {/* OpenCV Quality Report */}
              <QualityReport report={result.image_quality} />

              {/* Top Predictions List */}
              {result.top_k_predictions && (
                <div className="space-y-3 pt-2">
                  <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                    Top Candidate Match Breakdown
                  </span>
                  <div className="space-y-2">
                    {result.top_k_predictions.map((p, idx) => (
                      <div
                        key={idx}
                        className="flex justify-between p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-semibold"
                      >
                        <span className="text-[#0B1C10]">
                          {p.disease.replace(/___/g, ' — ').replace(/_/g, ' ')}
                        </span>
                        <span className="font-mono font-extrabold text-[#2F6B3C]">
                          {(p.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Grad-CAM Heatmap */}
              <GradCAMViewer heatmapBase64={result.gradcam_heatmap} available={result.gradcam_available} />
            </GlassCard>
          ) : (
            <div className="relative rounded-3xl overflow-hidden border border-[#E2E7DA] bg-[#FAFBF7] p-8 sm:p-12 text-center space-y-6 flex flex-col items-center justify-center min-h-[380px] group">
              <div className="w-full h-full absolute inset-0 z-0 opacity-15 overflow-hidden">
                <img
                  src="/images/plant-health.webp"
                  alt="Plant health background preview"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                />
              </div>

              <div className="relative z-10 w-14 h-14 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-extrabold text-xl shadow-sm">
                <Stethoscope className="w-7 h-7" />
              </div>

              <div className="relative z-10 space-y-2 max-w-md">
                <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                  Ready for Plant Leaf Diagnosis
                </h3>
                <p className="text-xs text-[#536056] leading-relaxed">
                  Upload a leaf photo on the left to evaluate OpenCV sharpness/brightness quality metrics, run ResNet18 diagnosis, and generate visual Grad-CAM feature heatmaps.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
