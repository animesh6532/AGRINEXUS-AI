import React from 'react';

interface ConfidenceBarProps {
  confidence: number; // 0 to 1 or 0 to 100
  label?: string;
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ confidence, label = 'Confidence' }) => {
  const percentage = confidence > 1 ? confidence : Math.round(confidence * 100);

  let barColor = 'bg-gradient-to-r from-[#2F6B3C] to-[#D4E768]';
  if (percentage < 60) barColor = 'bg-gradient-to-r from-amber-600 to-amber-400';
  if (percentage < 30) barColor = 'bg-gradient-to-r from-rose-600 to-rose-400';

  return (
    <div className="space-y-2 w-full">
      <div className="flex justify-between items-center text-xs font-semibold text-[#162018]">
        <span className="uppercase tracking-wider text-[11px] text-[#536056]">{label}</span>
        <span className="font-mono font-bold text-sm text-[#0B1C10]">{percentage}%</span>
      </div>
      <div className="h-2.5 w-full bg-[#EEF3E8] rounded-full overflow-hidden p-0.5 border border-[#E2E7DA]">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
