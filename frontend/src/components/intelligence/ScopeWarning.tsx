import React from 'react';
import { Info, AlertTriangle } from 'lucide-react';

interface ScopeWarningProps {
  message: string;
  type?: 'info' | 'warning';
}

export const ScopeWarning: React.FC<ScopeWarningProps> = ({ message, type = 'info' }) => {
  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-2xl text-xs border transition-all ${
        type === 'warning'
          ? 'bg-amber-500/10 border-amber-500/25 text-amber-900'
          : 'bg-[#EEF3E8] border-[#E2E7DA] text-[#162018]'
      }`}
    >
      {type === 'warning' ? (
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
      ) : (
        <Info className="w-4 h-4 text-[#2F6B3C] shrink-0 mt-0.5" />
      )}
      <div className="space-y-0.5 leading-relaxed">
        <span className="font-bold block uppercase tracking-widest text-[10px] text-[#536056]">
          Domain Scope & Model Context
        </span>
        <p className="font-sans text-xs text-[#162018]/90">{message}</p>
      </div>
    </div>
  );
};
