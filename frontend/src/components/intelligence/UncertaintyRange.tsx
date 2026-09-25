import React from 'react';

interface UncertaintyRangeProps {
  lowerBound: number;
  prediction: number;
  upperBound: number;
  unit?: string;
  label?: string;
  confidenceIntervalLabel?: string;
}

export const UncertaintyRange: React.FC<UncertaintyRangeProps> = ({
  lowerBound,
  prediction,
  upperBound,
  unit = '',
  label = 'Uncertainty Interval',
  confidenceIntervalLabel = '95% Confidence Interval Bounds',
}) => {
  const range = upperBound - lowerBound;
  const positionPercentage = range > 0 ? Math.min(100, Math.max(0, ((prediction - lowerBound) / range) * 100)) : 50;

  return (
    <div className="p-5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">{label}</span>
          <span className="text-xs text-[#162018] font-medium">{confidenceIntervalLabel}</span>
        </div>
        <div className="text-right">
          <span className="text-xs text-[#536056] block">Point Estimate</span>
          <span className="font-mono font-bold text-base text-[#2F6B3C]">
            {prediction.toFixed(2)} {unit}
          </span>
        </div>
      </div>

      {/* Interval Bar Visualization */}
      <div className="relative pt-6 pb-2">
        {/* Track Line */}
        <div className="h-3 w-full bg-[#EEF3E8] rounded-full relative overflow-visible border border-[#E2E7DA]">
          {/* Active Interval Fill */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#2F6B3C]/30 via-[#2F6B3C]/60 to-[#D4E768]/50 rounded-full" />

          {/* Point Prediction Indicator Marker */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-[#D4E768] border-2 border-[#0B1C10] shadow-md transition-all duration-500 z-10"
            style={{ left: `calc(${positionPercentage}% - 8px)` }}
          >
            <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-[10px] font-mono font-extrabold bg-[#0B1C10] text-[#D4E768] px-1.5 py-0.5 rounded shadow whitespace-nowrap">
              {prediction.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Bound Labels */}
        <div className="flex justify-between items-center text-xs font-mono text-[#536056] mt-3">
          <div>
            <span className="block text-[10px] font-sans text-[#536056] uppercase">Lower Bound</span>
            <span className="font-bold text-[#162018]">{lowerBound.toFixed(2)} {unit}</span>
          </div>
          <div className="text-right">
            <span className="block text-[10px] font-sans text-[#536056] uppercase">Upper Bound</span>
            <span className="font-bold text-[#162018]">{upperBound.toFixed(2)} {unit}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
