import React from 'react';
import { Sprout, Check, AlertTriangle, ChevronRight, Sparkles } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { SmartCropRecommendationItem } from '../../types/api';

interface AlternativeCropCardProps {
  rank: number;
  item: SmartCropRecommendationItem;
  onOpenDetail: (item: SmartCropRecommendationItem) => void;
  isCompared?: boolean;
  onToggleCompare?: (item: SmartCropRecommendationItem) => void;
}

const safeFormatScore = (value: number | undefined | null, decimals = 0): string => {
  if (value == null || typeof value !== 'number' || isNaN(value)) {
    return '—';
  }
  return value.toFixed(decimals);
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

export const AlternativeCropCard: React.FC<AlternativeCropCardProps> = ({
  rank,
  item,
  onOpenDetail,
  isCompared = false,
  onToggleCompare,
}) => {
  const cropImagePath = `/images/crops/${item.crop.toLowerCase()}.webp`;

  return (
    <GlassCard
      variant="solid"
      className="p-5 rounded-2xl border border-[#E2E7DA] bg-white shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between space-y-4 group"
    >
      <div className="space-y-3">
        {/* Top Header Row: Rank, Checkbox, Image & Category */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            {onToggleCompare && (
              <input
                type="checkbox"
                checked={isCompared}
                onChange={() => onToggleCompare(item)}
                className="w-4 h-4 rounded border-gray-300 text-[#2F6B3C] focus:ring-[#2F6B3C] cursor-pointer"
                title="Select crop for comparison"
              />
            )}

            <div className="w-8 h-8 rounded-xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA] flex items-center justify-center text-xs font-black shrink-0">
              #{rank}
            </div>

            <div>
              <h4 className="text-lg font-extrabold font-editorial text-[#0B1C10] capitalize line-clamp-1">
                {item.display_name}
              </h4>
              <p className="text-[11px] italic text-[#536056] font-editorial line-clamp-1">
                {item.scientific_name}
              </p>
            </div>
          </div>

          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold border uppercase tracking-wider bg-gray-50 text-gray-700 border-gray-200 shrink-0">
            {(item.category || 'cereal').replace('_', ' ')}
          </span>
        </div>

        {/* Suitability Score & Level Row */}
        <div className="flex items-center justify-between bg-[#FAFBF7] p-3 rounded-xl border border-[#E2E7DA]/70">
          <div>
            <span className="text-[9px] uppercase font-bold text-[#536056] block tracking-wider">Suitability</span>
            <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border inline-block mt-0.5 ${getLevelBadgeColor(item.suitability_level)}`}>
              {item.suitability_level}
            </span>
          </div>

          <div className="text-right">
            <span className="text-xl font-black font-mono text-[#0B1C10]">
              {item.suitability_score ?? '—'}
            </span>
            <span className="text-[10px] font-normal text-[#536056]"> / 100</span>
          </div>
        </div>

        {/* Primary Why Alignment Reason */}
        {item.reasons && item.reasons.length > 0 && (
          <div className="text-xs text-[#0B1C10] bg-emerald-50/50 p-2.5 rounded-xl border border-emerald-100 flex items-start gap-1.5">
            <Check className="w-3.5 h-3.5 text-[#2F6B3C] shrink-0 mt-0.5" />
            <span className="line-clamp-2 leading-snug text-[11px]">{item.reasons[0].replace(/^✓\s*/, '')}</span>
          </div>
        )}

        {/* Warning if present */}
        {item.warnings && item.warnings.length > 0 && (
          <div className="text-[11px] text-amber-900 bg-amber-50 p-2 rounded-xl border border-amber-200 flex items-start gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
            <span className="line-clamp-1">{item.warnings[0].replace(/^⚠\s*/, '')}</span>
          </div>
        )}
      </div>

      {/* Card Footer CTA */}
      <div className="pt-2 border-t border-[#E2E7DA]/60 flex items-center justify-between">
        <span className="text-[10px] text-[#536056] font-mono">
          {item.ml_prediction?.supported && item.ml_prediction.probability != null
            ? `ML ${(item.ml_prediction.probability * 100).toFixed(0)}%`
            : 'Catalogue'}
        </span>

        <button
          type="button"
          onClick={() => onOpenDetail(item)}
          className="inline-flex items-center gap-1 text-xs font-bold text-[#2F6B3C] hover:text-[#0B1C10] hover:underline"
        >
          <span>View Analysis</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </GlassCard>
  );
};
