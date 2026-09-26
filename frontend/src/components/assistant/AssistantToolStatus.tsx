import React from 'react';
import { Loader2, Cpu } from 'lucide-react';

interface AssistantToolStatusProps {
  status: string;
}

export const AssistantToolStatus: React.FC<AssistantToolStatusProps> = ({ status }) => {
  return (
    <div className="flex items-center gap-2 py-1.5 px-3 rounded-lg bg-emerald-950/70 border border-emerald-500/20 text-emerald-300 text-xs font-medium my-1 animate-fade-in w-fit">
      <Loader2 className="w-3.5 h-3.5 text-emerald-400 animate-spin" />
      <span className="truncate">{status}</span>
    </div>
  );
};
