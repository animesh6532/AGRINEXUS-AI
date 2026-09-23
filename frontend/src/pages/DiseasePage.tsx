import React, { useState } from 'react';
import { Stethoscope, Upload, Image as ImageIcon, AlertTriangle, Layers } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ConfidenceBar } from '../components/intelligence/ConfidenceBar';
import { QualityReport } from '../components/intelligence/QualityReport';
import { GradCAMViewer } from '../components/intelligence/GradCAMViewer';
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
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary-100 text-primary-700 flex items-center justify-center font-bold">
          <Stethoscope className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Plant Disease Detection</h1>
          <p className="text-xs text-slate-500">
            ResNet18 computer vision leaf diagnosis with OpenCV image quality inspection and Grad-CAM visual heatmaps.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Workspace */}
        <GlassCard variant="strong" className="p-6 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Upload className="w-4 h-4 text-primary-600" /> Upload Leaf Photo
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className="border-2 border-dashed border-slate-300 hover:border-primary-500 rounded-2xl p-6 text-center transition-all bg-white/40 cursor-pointer relative"
            >
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(e) => e.target.files && e.target.files[0] && handleFileChange(e.target.files[0])}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />

              {previewUrl ? (
                <div className="space-y-2">
                  <img src={previewUrl} alt="Preview" className="h-48 max-w-full object-contain mx-auto rounded-xl shadow-sm" />
                  <p className="text-xs font-semibold text-slate-700">{selectedFile?.name}</p>
                  <p className="text-[10px] text-slate-400">Click or drag to replace image</p>
                </div>
              ) : (
                <div className="space-y-2 py-6">
                  <ImageIcon className="w-10 h-10 text-slate-400 mx-auto" />
                  <p className="text-xs font-semibold text-slate-700">Drag & drop leaf photo or click to browse</p>
                  <p className="text-[10px] text-slate-400">Supports JPEG, PNG, WEBP (Max 10MB)</p>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between text-xs bg-white/60 p-3 rounded-xl border border-slate-200/60">
              <label className="flex items-center gap-2 text-slate-700 font-medium cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeGradcam}
                  onChange={(e) => setIncludeGradcam(e.target.checked)}
                  className="rounded text-primary-600 focus:ring-primary-500"
                />
                <span>Generate Grad-CAM Visual Heatmap</span>
              </label>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full"
              disabled={!selectedFile}
              isLoading={loading}
            >
              Analyze Plant Leaf
            </Button>
          </form>
        </GlassCard>

        {/* Diagnostic Results */}
        <div className="space-y-6">
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
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">Diagnosed Condition</span>
                  <h2 className="text-2xl font-black text-slate-900 capitalize mt-1">
                    {result.predicted_disease.replace(/___/g, ' - ').replace(/_/g, ' ')}
                  </h2>
                </div>
                <Badge variant={result.confidence > 0.6 ? 'success' : 'warning'}>
                  {(result.confidence * 100).toFixed(1)}% Match
                </Badge>
              </div>

              <ConfidenceBar confidence={result.confidence} label="ResNet18 Diagnostic Probability" />

              {/* OpenCV Quality Report */}
              <QualityReport report={result.image_quality} />

              {/* Top Predictions List */}
              {result.top_k_predictions && (
                <div className="space-y-2 text-xs">
                  <span className="font-bold uppercase tracking-wider text-slate-500 block">Top 3 Candidates</span>
                  {result.top_k_predictions.map((p, idx) => (
                    <div key={idx} className="flex justify-between p-2 rounded-lg bg-white/70 border border-slate-100">
                      <span className="font-medium text-slate-800">{p.disease.replace(/___/g, ' - ').replace(/_/g, ' ')}</span>
                      <span className="font-mono font-bold text-slate-700">{(p.probability * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Grad-CAM Heatmap Component */}
              <GradCAMViewer heatmapBase64={result.gradcam_heatmap} available={result.gradcam_available} />
            </GlassCard>
          ) : (
            <GlassCard className="p-12 text-center space-y-3">
              <Stethoscope className="w-10 h-10 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">No Leaf Image Analyzed</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Upload a clear leaf photo on the left to evaluate OpenCV quality metrics and ResNet18 disease diagnosis.
              </p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
