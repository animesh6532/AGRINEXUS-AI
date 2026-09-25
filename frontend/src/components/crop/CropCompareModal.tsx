import React from 'react';
import { X, Check, AlertTriangle, Sparkles, Scale } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { SmartCropRecommendationItem } from '../../types/api';

interface CropCompareModalProps {
  crops: SmartCropRecommendationItem[];
  onClose: () => void;
  onRemoveCrop: (cropId: string) => void;
}

const safeFormatScore = (value: number | undefined | null, decimals = 0): string => {
  if (value == null || typeof value !== 'number' || isNaN(value)) {
    return '—';
  }
  return value.toFixed(decimals);
};

export const CropCompareModal: React.FC<CropCompareModalProps> = ({ crops, onClose, onRemoveCrop }) => {
  if (!crops || crops.length === 0) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="relative w-full max-w-6xl max-h-[90vh] bg-white border border-[#E2E7DA] rounded-3xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 bg-[#FAFBF7] border-b border-[#E2E7DA] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-black font-editorial text-[#0B1C10]">
                AGRONOMIC CROP COMPARISON MATRIX
              </h2>
              <p className="text-xs text-[#536056]">
                Comparing {crops.length} candidate crops across land, climate, soil, seasonal, and sowing factors.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-700 rounded-full hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Comparison Content Table */}
        <div className="p-6 overflow-x-auto flex-1 space-y-6">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#E2E7DA]">
                <th className="p-3 font-extrabold uppercase text-[#536056] bg-[#FAFBF7] w-44 sticky left-0 z-10 border-r border-[#E2E7DA]">
                  Agronomic Dimension
                </th>
                {crops.map((c) => (
                  <th key={c.crop} className="p-4 min-w-[220px] bg-white border-r border-[#E2E7DA] last:border-r-0">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <h4 className="font-extrabold text-base text-[#0B1C10] capitalize">{c.display_name}</h4>
                        <span className="text-[10px] text-[#536056] italic font-editorial block">{c.scientific_name}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => onRemoveCrop(c.crop)}
                        className="text-gray-300 hover:text-rose-600 p-1"
                        title="Remove from comparison"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7DA]">
              {/* Suitability Score */}
              <tr>
                <td className="p-3 font-bold text-[#0B1C10] bg-[#FAFBF7] sticky left-0 border-r border-[#E2E7DA]">
                  Suitability Score
                </td>
                {crops.map((c) => (
                  <td key={c.crop} className="p-4 border-r border-[#E2E7DA] last:border-r-0 font-mono text-base font-black text-[#2F6B3C]">
                    {c.suitability_score ?? '—'} / 100
                    <span className="block text-[10px] font-sans font-bold text-[#536056]">{c.suitability_level}</span>
                  </td>
                ))}
              </tr>

              {/* Sowing Feasibility */}
              <tr>
                <td className="p-3 font-bold text-[#0B1C10] bg-[#FAFBF7] sticky left-0 border-r border-[#E2E7DA]">
                  Sowing Window
                </td>
                {crops.map((c) => (
                  <td key={c.crop} className="p-4 border-r border-[#E2E7DA] last:border-r-0 font-semibold text-[#0B1C10]">
                    {(c as any).sowing_feasibility || 'GOOD_WINDOW'}
                  </td>
                ))}
              </tr>

              {/* Optimal Temperature */}
              <tr>
                <td className="p-3 font-bold text-[#0B1C10] bg-[#FAFBF7] sticky left-0 border-r border-[#E2E7DA]">
                  Optimal Temperature
                </td>
                {crops.map((c) => (
                  <td key={c.crop} className="p-4 border-r border-[#E2E7DA] last:border-r-0 text-[#0B1C10]">
                    {c.profile_details?.temp_optimal?.[0]}–{c.profile_details?.temp_optimal?.[1]}°C
                    <span className="block text-[10px] text-[#536056]">Score: {safeFormatScore(c.factor_scores?.temperature)}%</span>
                  </td>
                ))}
              </tr>

              {/* Optimal Rainfall */}
              <tr>
                <td className="p-3 font-bold text-[#0B1C10] bg-[#FAFBF7] sticky left-0 border-r border-[#E2E7DA]">
                  Optimal Rainfall
                </td>
                {crops.map((c) => (
                  <td key={c.crop} className="p-4 border-r border-[#E2E7DA] last:border-r-0 text-[#0B1C10]">
                    {c.profile_details?.rainfall_optimal?.[0]}–{c.profile_details?.rainfall_optimal?.[1]} mm
                    <span className="block text-[10px] text-[#536056]">Score: {safeFormatScore(c.factor_scores?.rainfall ?? c.factor_scores?.water)}%</span>
                  </td>
                ))}
              </tr>

              {/* Soil pH Range */}
              <tr>
                <td className="p-3 font-bold text-[#0B1C10] bg-[#FAFBF7] sticky left-0 border-r border-[#E2E7DA]">
                  Soil pH Range
                </td>
                {crops.map((c) => (
                  <td key={c.crop} className="p-4 border-r border-[#E2E7DA] last:border-r-0 text-[#0B1C10]">
                    {c.profile_details?.ph_optimal?.[0]}–{c.profile_details?.ph_optimal?.[1]}
                    <span className="block text-[10px] text-[#536056]">Score: {safeFormatScore(c.factor_scores?.ph)}%</span>
                  </td>
                ))}
              </tr>

              {/* Preferred Soil Textures */}
              <tr>
                <td className="p-3 font-bold text-[#0B1C10] bg-[#FAFBF7] sticky left-0 border-r border-[#E2E7DA]">
                  Preferred Soil
                </td>
                {crops.map((c) => (
                  <td key={c.crop} className="p-4 border-r border-[#E2E7DA] last:border-r-0 text-[#0B1C10]">
                    {c.profile_details?.soil_textures?.join(', ')}
                  </td>
                ))}
              </tr>

              {/* Water Requirement */}
              <tr>
                <td className="p-3 font-bold text-[#0B1C10] bg-[#FAFBF7] sticky left-0 border-r border-[#E2E7DA]">
                  Water Requirement
                </td>
                {crops.map((c) => (
                  <td key={c.crop} className="p-4 border-r border-[#E2E7DA] last:border-r-0 capitalize text-[#0B1C10]">
                    {c.profile_details?.water_requirement}
                  </td>
                ))}
              </tr>

              {/* ML Evidence */}
              <tr>
                <td className="p-3 font-bold text-[#0B1C10] bg-[#FAFBF7] sticky left-0 border-r border-[#E2E7DA]">
                  ML Evidence
                </td>
                {crops.map((c) => (
                  <td key={c.crop} className="p-4 border-r border-[#E2E7DA] last:border-r-0 text-[#0B1C10]">
                    {c.ml_prediction?.supported && c.ml_prediction.probability != null ? (
                      <span className="inline-flex items-center gap-1 font-mono font-bold text-[#2F6B3C]">
                        <Sparkles className="w-3.5 h-3.5" />
                        {safeFormatScore(c.ml_prediction.probability * 100)}%
                      </span>
                    ) : (
                      <span className="text-gray-400 italic">Not Trained in ML</span>
                    )}
                  </td>
                ))}
              </tr>

              {/* Growth Duration */}
              <tr>
                <td className="p-3 font-bold text-[#0B1C10] bg-[#FAFBF7] sticky left-0 border-r border-[#E2E7DA]">
                  Growth Duration
                </td>
                {crops.map((c) => (
                  <td key={c.crop} className="p-4 border-r border-[#E2E7DA] last:border-r-0 text-[#0B1C10]">
                    {c.profile_details?.growth_duration_days?.[0]}–{c.profile_details?.growth_duration_days?.[1]} Days
                  </td>
                ))}
              </tr>

              {/* Limiting Factors & Warnings */}
              <tr>
                <td className="p-3 font-bold text-[#0B1C10] bg-[#FAFBF7] sticky left-0 border-r border-[#E2E7DA]">
                  Limiting Cautions
                </td>
                {crops.map((c) => (
                  <td key={c.crop} className="p-4 border-r border-[#E2E7DA] last:border-r-0 text-amber-900">
                    {c.warnings && c.warnings.length > 0 ? (
                      <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                        {c.warnings.map((w, idx) => (
                          <li key={idx}>{w.replace(/^⚠\s*/, '')}</li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-emerald-700 font-semibold flex items-center gap-1">
                        <Check className="w-3.5 h-3.5" /> None severe
                      </span>
                    )}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#FAFBF7] border-t border-[#E2E7DA] flex justify-end shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-[#2F6B3C] text-white font-extrabold text-xs shadow-sm hover:bg-[#255730] transition-colors"
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
};
