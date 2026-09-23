import React from 'react';
import { Info, AlertTriangle } from 'lucide-react';

interface ScopeWarningProps {
  message: string;
  type?: 'info' | 'warning';
}

export const ScopeWarning: React.FC<ScopeWarningProps> = ({ message, type = 'info' }) => {
  return (
    <div
      className={`flex items-start gap-3 p-3.5 rounded-xl text-xs backdrop-blur-md border ${
        type === 'warning'
          ? 'bg-amber-500/10 border-amber-500/20 text-amber-800'
          : 'bg-sky-500/10 border-sky-500/20 text-sky-900'
      }`}
    >
      {type === 'warning' ? (
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
      ) : (
        <Info className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
      )}
      <div className="space-y-0.5 leading-relaxed">
        <span className="font-semibold block uppercase tracking-wider text-[10px] text-slate-500">
          Domain Scope & Model Context
        </span>
        <p>{message}</p>
      </div>
    </div>
  );
};
