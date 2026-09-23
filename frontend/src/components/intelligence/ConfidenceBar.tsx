import React from 'react';

interface ConfidenceBarProps {
  confidence: number; // 0 to 1 or 0 to 100
  label?: string;
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ confidence, label = 'Confidence' }) => {
  const percentage = confidence > 1 ? confidence : Math.round(confidence * 100);

  let barColor = 'bg-emerald-500';
  if (percentage < 50) barColor = 'bg-amber-500';
  if (percentage < 25) barColor = 'bg-rose-500';

  return (
    <div className="space-y-1.5 w-full">
      <div className="flex justify-between items-center text-xs font-medium text-slate-600">
        <span>{label}</span>
        <span className="font-bold text-slate-900">{percentage}%</span>
      </div>
      <div className="h-2 w-full bg-slate-200/60 rounded-full overflow-hidden p-0.5">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
