import React from 'react';
import { X, Sprout, Check, AlertTriangle, ExternalLink, ShieldCheck, Thermometer, Droplets, Layers, Calendar } from 'lucide-react';
import { SmartCropRecommendationItem } from '../../types/api';

interface CropDetailModalProps {
  item: SmartCropRecommendationItem | null;
  onClose: () => void;
}

export const CropDetailModal: React.FC<CropDetailModalProps> = ({ item, onClose }) => {
  if (!item) return null;

  const profile = item.profile_details;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-3xl bg-[#FAFBF7] border border-[#E2E7DA] rounded-3xl shadow-2xl overflow-hidden my-8 space-y-6 p-6 sm:p-8 max-h-[90vh] overflow-y-auto selection:bg-[#D4E768] selection:text-[#0B1C10]">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[#E2E7DA] pb-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center">
              <Sprout className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl sm:text-3xl font-black font-editorial text-[#0B1C10] capitalize">
                {item.display_name}
              </h2>
              <p className="text-xs italic font-editorial text-[#536056]">
                {item.scientific_name}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Score & Suitability Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-[#EEF3E8] p-4 rounded-2xl border border-[#E2E7DA]">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block">Suitability Level</span>
            <span className="text-sm font-extrabold text-[#2F6B3C] block mt-0.5">
              ● {item.suitability_level}
            </span>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block">Suitability Score</span>
            <span className="text-xl font-black font-mono text-[#0B1C10] block mt-0.5">
              {item.suitability_score} / 100
            </span>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block">ML Prediction</span>
            <span className="text-sm font-extrabold text-[#0B1C10] block mt-0.5 font-mono">
              {item.ml_prediction?.supported && item.ml_prediction.probability != null
                ? `${(item.ml_prediction.probability * 100).toFixed(0)}% Match`
                : 'Catalogue Crop'}
            </span>
          </div>
        </div>

        {/* Agronomic Parameter Comparison Grid */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#536056] flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#2F6B3C]" />
            Agronomic Requirements vs Field Conditions
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3.5 rounded-xl bg-white border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold text-[#536056] uppercase flex items-center gap-1">
                <Thermometer className="w-3.5 h-3.5 text-[#2F6B3C]" /> Temperature Range
              </span>
              <p className="font-semibold text-[#0B1C10]">
                Optimal: {profile.temp_optimal?.[0]}-{profile.temp_optimal?.[1]}°C
              </p>
              <p className="text-[11px] text-[#536056]">
                Acceptable: {profile.temp_acceptable?.[0]}-{profile.temp_acceptable?.[1]}°C
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-white border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold text-[#536056] uppercase flex items-center gap-1">
                <Droplets className="w-3.5 h-3.5 text-[#2F6B3C]" /> Seasonal Rainfall
              </span>
              <p className="font-semibold text-[#0B1C10]">
                Optimal: {profile.rainfall_optimal?.[0]}-{profile.rainfall_optimal?.[1]} mm
              </p>
              <p className="text-[11px] text-[#536056]">
                Water Requirement: <strong className="uppercase">{profile.water_requirement}</strong>
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-white border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold text-[#536056] uppercase flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-[#2F6B3C]" /> Soil pH & Texture
              </span>
              <p className="font-semibold text-[#0B1C10]">
                Optimal pH: {profile.ph_optimal?.[0]}-{profile.ph_optimal?.[1]}
              </p>
              <p className="text-[11px] text-[#536056]">
                Preferred Textures: {profile.soil_textures?.join(', ')}
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-white border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold text-[#536056] uppercase flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-[#2F6B3C]" /> Season & Duration
              </span>
              <p className="font-semibold text-[#0B1C10] capitalize">
                Optimal Seasons: {profile.seasons?.join(', ')}
              </p>
              <p className="text-[11px] text-[#536056]">
                Growth Duration: {profile.growth_duration_days?.[0]}-{profile.growth_duration_days?.[1]} Days
              </p>
            </div>
          </div>
        </div>

        {/* Reasons & Warnings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#2F6B3C]">
              Positive Field Alignments:
            </h4>
            <div className="space-y-1.5 text-xs">
              {item.reasons.map((r, i) => (
                <div key={i} className="flex items-start gap-1.5 bg-emerald-50/60 p-2.5 rounded-xl border border-emerald-100 text-emerald-950">
                  <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                  <span>{r.replace(/^✓\s*/, '')}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800">
              Cautions & Risk Factors:
            </h4>
            <div className="space-y-1.5 text-xs">
              {item.warnings.length > 0 ? (
                item.warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-1.5 bg-amber-50/60 p-2.5 rounded-xl border border-amber-200/60 text-amber-900">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
                    <span>{w.replace(/^⚠\s*/, '')}</span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-gray-500 italic p-2.5 bg-gray-50 rounded-xl border border-gray-100">
                  No critical agronomic warnings detected for this crop.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Data Provenance & Authoritative Sources */}
        <div className="p-4 rounded-2xl bg-white border border-[#E2E7DA] space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block">
            Authoritative Agronomic Data Source:
          </span>
          <p className="text-xs text-[#0B1C10] font-semibold">{profile.source}</p>
          {profile.source_url && (
            <a
              href={profile.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-xs text-[#2F6B3C] font-bold hover:underline"
            >
              <span>View Scientific Source Reference</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
          <p className="text-[10px] text-[#536056] italic pt-1 border-t border-[#E2E7DA]/50">
            {profile.notes}
          </p>
        </div>

        {/* Trust Disclaimer */}
        <p className="text-[10px] text-[#536056] text-center italic">
          Decision Support — not a farming guarantee. Environmental suitability does not guarantee yield or profitability.
        </p>
      </div>
    </div>
  );
};
