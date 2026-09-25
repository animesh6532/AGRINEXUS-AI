import React from 'react';
import { Check, AlertTriangle, ChevronRight, Sparkles, Layers, ShieldCheck, HelpCircle } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { SmartCropRecommendationItem } from '../../types/api';
import { getCropImageMetadata } from '../../utils/cropImageMap';
import { CropImage } from './CropImage';

interface FeaturedCropCardProps {
  item: SmartCropRecommendationItem;
  onOpenDetail: (item: SmartCropRecommendationItem) => void;
  isCompared?: boolean;
  onToggleCompare?: (item: SmartCropRecommendationItem) => void;
}

const getSowingBadge = (sowingStatus?: string) => {
  switch (sowingStatus) {
    case 'IDEAL_WINDOW':
      return { label: 'Ideal Sowing Window', color: 'bg-emerald-100 text-emerald-800 border-emerald-300' };
    case 'GOOD_WINDOW':
      return { label: 'Good Sowing Window', color: 'bg-green-50 text-green-700 border-green-200' };
    case 'LATE':
      return { label: 'Late Sowing Window', color: 'bg-amber-100 text-amber-800 border-amber-300' };
    case 'OUTSIDE_WINDOW':
      return { label: 'Outside Sowing Window', color: 'bg-rose-100 text-rose-800 border-rose-300' };
    default:
      return { label: 'Seasonal Window Active', color: 'bg-gray-100 text-gray-700 border-gray-300' };
  }
};

export const FeaturedCropCard: React.FC<FeaturedCropCardProps> = ({
  item,
  onOpenDetail,
  isCompared = false,
  onToggleCompare,
}) => {
  const sowingBadge = getSowingBadge(item.sowing_feasibility);
  const imageMeta = getCropImageMetadata(item.crop);

  // Terminology Fix: Decouple ML Evidence from Catalogue status
  const getMlSupportLabel = () => {
    if (item.ml_prediction?.supported) {
      if (item.ml_prediction.probability != null) {
        return `ML SUPPORT: Available (${(item.ml_prediction.probability * 100).toFixed(0)}%)`;
      }
      return 'ML SUPPORT: Unavailable (Incomplete Soil NPK)';
    }
    return 'ML SUPPORT: Catalogue-only assessment';
  };

  return (
    <GlassCard
      variant="solid"
      className="p-0 rounded-3xl overflow-hidden border-2 border-[#2F6B3C]/30 bg-gradient-to-br from-[#FAFBF7] via-white to-[#F2F7EB] shadow-xl hover:shadow-2xl transition-all duration-300 group"
    >
      <div className="grid grid-cols-1 lg:grid-cols-12">
        {/* Left Column: Crop Image & Visual Hero (40% desktop) */}
        <div className="lg:col-span-5 relative min-h-[260px] lg:min-h-[380px] overflow-hidden bg-[#0B1C10]">
          <CropImage crop={item} className="w-full h-full" showAttribution={true} />

          {/* Rank #1 Badge Overlay */}
          <div className="absolute top-4 left-4 z-10 flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-[#2F6B3C] text-white font-extrabold text-xs tracking-wider uppercase shadow-md flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#D4E768]" />
              #1 TOP SUITED CROP
            </span>
          </div>

          {/* Comparison Checkbox Overlay */}
          {onToggleCompare && (
            <div className="absolute top-4 right-4 z-10 bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/20 flex items-center gap-2 text-xs text-white">
              <input
                type="checkbox"
                checked={isCompared}
                onChange={() => onToggleCompare(item)}
                className="w-4 h-4 rounded border-gray-300 text-[#2F6B3C] focus:ring-[#2F6B3C] cursor-pointer"
                id="compare-top-crop"
              />
              <label htmlFor="compare-top-crop" className="cursor-pointer font-semibold text-[11px]">
                Compare
              </label>
            </div>
          )}

          {/* Quick Scientific Overlay */}
          <div className="absolute bottom-4 left-4 right-4 z-10 text-white">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-white/20 backdrop-blur-md border border-white/20 text-[#D4E768]">
              {(item.category || 'cereal').replace('_', ' ')}
            </span>
            <h3 className="text-3xl font-black font-editorial text-white capitalize mt-1 drop-shadow-md">
              {item.display_name}
            </h3>
            <p className="text-xs italic text-slate-200 font-editorial">
              {item.scientific_name}
            </p>
          </div>
        </div>

        {/* Right Column: Detailed Suitability Information (60% desktop) */}
        <div className="lg:col-span-7 p-6 sm:p-8 flex flex-col justify-between space-y-6">
          {/* Header Row: Score & Badges */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-5">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
                  ● {item.suitability_level}
                </span>
                <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold border ${sowingBadge.color}`}>
                  {sowingBadge.label}
                </span>
              </div>
              <p className="text-xs text-[#536056] pt-1">
                Highest overall agronomic alignment with field coordinates & seasonal climate.
              </p>
            </div>

            <div className="text-left sm:text-right shrink-0">
              <span className="text-[10px] uppercase font-bold text-[#536056] block tracking-wider">
                Suitability Index
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-black font-mono text-[#0B1C10]">
                  {item.suitability_score ?? '—'}
                </span>
                <span className="text-sm font-semibold text-[#536056]">/ 100</span>
              </div>
            </div>
          </div>

          {/* Key Alignment Points (Why Suitable) */}
          {item.reasons && item.reasons.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#536056]">
                Key Agronomic Alignments:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-[#0B1C10]">
                {item.reasons.slice(0, 4).map((reason, idx) => (
                  <div key={idx} className="flex items-start gap-2 bg-white p-2.5 rounded-xl border border-[#E2E7DA] shadow-2xs">
                    <Check className="w-4 h-4 text-[#2F6B3C] shrink-0 mt-0.5" />
                    <span className="font-medium leading-snug">{reason.replace(/^✓\s*/, '')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Telemetry Indicator Pills with Explicit Terminology */}
          <div className="grid grid-cols-3 gap-3 text-xs pt-1">
            <div className="p-3 rounded-2xl bg-white border border-[#E2E7DA] text-center">
              <span className="text-[10px] text-[#536056] font-bold uppercase block">ML Support</span>
              <span className="font-extrabold text-[#2F6B3C] text-[11px] block mt-0.5">
                {getMlSupportLabel()}
              </span>
            </div>

            <div className="p-3 rounded-2xl bg-white border border-[#E2E7DA] text-center">
              <span className="text-[10px] text-[#536056] font-bold uppercase block">Water Need</span>
              <span className="font-extrabold text-[#0B1C10] capitalize block mt-0.5">
                {item.profile_details?.water_requirement || 'Medium'}
              </span>
            </div>

            <div className="p-3 rounded-2xl bg-white border border-[#E2E7DA] text-center">
              <span className="text-[10px] text-[#536056] font-bold uppercase block">Growth Duration</span>
              <span className="font-extrabold text-[#0B1C10] font-mono block mt-0.5">
                {item.profile_details?.growth_duration_days?.[0] || 90}-{item.profile_details?.growth_duration_days?.[1] || 120} Days
              </span>
            </div>
          </div>

          {/* Warnings & Risk Alerts */}
          {item.warnings && item.warnings.length > 0 && (
            <div className="text-xs text-amber-900 bg-amber-500/10 p-3 rounded-xl border border-amber-500/20 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block">Verification Notice:</span>
                <span className="text-[11px] text-amber-900/90">{item.warnings[0].replace(/^⚠\s*/, '')}</span>
              </div>
            </div>
          )}

          {/* Primary Action Button */}
          <div className="pt-2 flex items-center justify-end border-t border-[#E2E7DA]">
            <button
              type="button"
              onClick={() => onOpenDetail(item)}
              className="px-6 py-2.5 rounded-xl bg-[#2F6B3C] hover:bg-[#23522d] text-white text-xs font-bold transition-all shadow-md flex items-center gap-2 group/btn"
            >
              <span>View Full Analysis</span>
              <ChevronRight className="w-4 h-4 text-[#D4E768] group-hover/btn:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};
