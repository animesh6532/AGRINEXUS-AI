import React from 'react';
import { Sprout, Check, AlertTriangle, ChevronRight, Sparkles, Droplets, Thermometer, Calendar } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { SmartCropRecommendationItem } from '../../types/api';

interface CropResultCardProps {
  rank: number;
  item: SmartCropRecommendationItem;
  onOpenDetail: (item: SmartCropRecommendationItem) => void;
}

const getCategoryBadgeColor = (category: string) => {
  switch (category.toLowerCase()) {
    case 'cereal':
      return 'bg-amber-500/10 text-amber-800 border-amber-500/20';
    case 'pulse':
      return 'bg-emerald-500/10 text-emerald-800 border-emerald-500/20';
    case 'cash_crop':
      return 'bg-purple-500/10 text-purple-800 border-purple-500/20';
    case 'fruit':
      return 'bg-rose-500/10 text-rose-800 border-rose-500/20';
    case 'oilseed':
      return 'bg-yellow-500/10 text-yellow-800 border-yellow-500/20';
    case 'vegetable':
      return 'bg-lime-500/10 text-lime-800 border-lime-500/20';
    default:
      return 'bg-gray-500/10 text-gray-800 border-gray-500/20';
  }
};

const getLevelBadgeColor = (level: string) => {
  switch (level) {
    case 'Highly Suitable':
      return 'bg-[#EEF3E8] text-[#2F6B3C] border-[#E2E7DA]';
    case 'Suitable':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    case 'Conditionally Suitable':
      return 'bg-amber-50 text-amber-800 border-amber-200';
    case 'Low Suitability':
      return 'bg-rose-50 text-rose-800 border-rose-200';
    default:
      return 'bg-gray-50 text-gray-700 border-gray-200';
  }
};

export const CropResultCard: React.FC<CropResultCardProps> = ({ rank, item, onOpenDetail }) => {
  const isTopRank = rank === 1;

  return (
    <GlassCard
      variant="solid"
      className={`p-6 sm:p-7 space-y-5 transition-all duration-300 hover:shadow-lg ${
        isTopRank ? 'ring-2 ring-[#2F6B3C]/30 bg-gradient-to-br from-[#FAFBF7] to-[#F3F7ED]' : ''
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-5">
        <div className="flex items-start gap-3.5">
          <div
            className={`w-10 h-10 rounded-2xl flex items-center justify-center text-sm font-black shrink-0 ${
              isTopRank
                ? 'bg-[#2F6B3C] text-white shadow-sm'
                : 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
            }`}
          >
            #{rank}
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-2xl font-black font-editorial text-[#0B1C10] capitalize">
                {item.display_name}
              </h3>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider ${getCategoryBadgeColor(item.category)}`}>
                {item.category.replace('_', ' ')}
              </span>
            </div>
            <p className="text-xs italic text-[#536056] font-editorial mt-0.5">
              {item.scientific_name}
            </p>
          </div>
        </div>

        {/* Suitability Score Pill & Level */}
        <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getLevelBadgeColor(item.suitability_level)}`}>
            ● {item.suitability_level}
          </span>

          <div className="text-right">
            <span className="text-xs text-[#536056] block">Suitability Score</span>
            <span className="text-2xl font-black font-mono text-[#0B1C10]">
              {item.suitability_score}
              <span className="text-xs font-normal text-[#536056]"> / 100</span>
            </span>
          </div>
        </div>
      </div>

      {/* ML Confidence & Factor Badges */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {item.ml_prediction?.supported && item.ml_prediction.probability != null ? (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-[#2F6B3C]/10 text-[#2F6B3C] font-extrabold font-mono border border-[#2F6B3C]/20">
            <Sparkles className="w-3.5 h-3.5 text-[#2F6B3C]" />
            ML Model Ranks: {(item.ml_prediction.probability * 100).toFixed(0)}%
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-gray-100 text-gray-600 text-[11px] font-mono border border-gray-200">
            ML: Catalogue Crop
          </span>
        )}

        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-[#FAFBF7] border border-[#E2E7DA] text-[11px] font-semibold text-[#536056]">
          <Calendar className="w-3 h-3 text-[#2F6B3C]" />
          Season: {item.factor_scores.season.toFixed(0)}%
        </span>
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-[#FAFBF7] border border-[#E2E7DA] text-[11px] font-semibold text-[#536056]">
          <Thermometer className="w-3 h-3 text-[#2F6B3C]" />
          Temp: {item.factor_scores.temperature.toFixed(0)}%
        </span>
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-[#FAFBF7] border border-[#E2E7DA] text-[11px] font-semibold text-[#536056]">
          <Droplets className="w-3 h-3 text-[#2F6B3C]" />
          Rain: {item.factor_scores.rainfall.toFixed(0)}%
        </span>
      </div>

      {/* Reasons Why Recommended */}
      {item.reasons && item.reasons.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[11px] font-bold uppercase tracking-wider text-[#536056]">
            Why Recommended:
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5 text-xs text-[#0B1C10]">
            {item.reasons.slice(0, 4).map((reason, idx) => (
              <div key={idx} className="flex items-start gap-1.5 bg-[#FAFBF7] p-2 rounded-xl border border-[#E2E7DA]/70">
                <Check className="w-3.5 h-3.5 text-[#2F6B3C] shrink-0 mt-0.5" />
                <span className="leading-snug">{reason.replace(/^✓\s*/, '')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warnings & Risk Alerts */}
      {item.warnings && item.warnings.length > 0 && (
        <div className="space-y-1 text-xs text-amber-900 bg-amber-500/10 p-3 rounded-xl border border-amber-500/20">
          <div className="flex items-center gap-1.5 font-bold">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-700 shrink-0" />
            <span>Field Risk Cautions:</span>
          </div>
          <ul className="list-disc list-inside text-[11px] space-y-0.5 text-amber-900/90 pl-1">
            {item.warnings.slice(0, 2).map((warn, idx) => (
              <li key={idx}>{warn.replace(/^⚠\s*/, '')}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer CTA */}
      <div className="pt-2 flex items-center justify-between border-t border-[#E2E7DA]/60">
        <span className="text-[11px] text-[#536056] font-mono">
          Growth Duration: {item.profile_details.growth_duration_days?.[0] || 90}-{item.profile_details.growth_duration_days?.[1] || 120} Days
        </span>

        <button
          type="button"
          onClick={() => onOpenDetail(item)}
          className="inline-flex items-center gap-1 text-xs font-extrabold text-[#2F6B3C] hover:text-[#0B1C10] hover:underline"
        >
          <span>View Crop Profile</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </GlassCard>
  );
};
