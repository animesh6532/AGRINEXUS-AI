import React from 'react';
import { Database, CheckCircle2 } from 'lucide-react';

interface AssistantSourcesProps {
  sources?: string[];
}

export const AssistantSources: React.FC<AssistantSourcesProps> = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-2 pt-2 border-t border-emerald-500/10 flex flex-wrap items-center gap-1.5 text-[11px] text-emerald-200/70">
      <span className="inline-flex items-center gap-1 font-medium text-emerald-300/80">
        <Database className="w-3 h-3 text-emerald-400" />
        Data used:
      </span>
      {sources.map((src, index) => (
        <span
          key={index}
          className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-500/15 text-emerald-200/90 text-[10.5px]"
        >
          <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
          {src}
        </span>
      ))}
    </div>
  );
};
