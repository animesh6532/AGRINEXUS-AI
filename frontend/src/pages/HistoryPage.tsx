import React from 'react';
import { History, Sprout, Stethoscope, Bug, Mountain, TrendingUp } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Badge } from '../components/ui/Badge';

export const HistoryPage: React.FC = () => {
  const dummyHistory = [
    { type: 'Crop Recommendation', icon: <Sprout className="w-4 h-4 text-agri-600" />, result: 'rice', confidence: '68.7%', date: 'Today, 10:45 AM' },
    { type: 'Plant Disease Detection', icon: <Stethoscope className="w-4 h-4 text-primary-600" />, result: 'Corn___healthy', confidence: '55.1%', date: 'Today, 09:30 AM' },
    { type: 'Pest Risk Assessment', icon: <Bug className="w-4 h-4 text-amber-600" />, result: 'Medium Risk', confidence: '78.0%', date: 'Yesterday' },
    { type: 'Soil Analysis', icon: <Mountain className="w-4 h-4 text-emerald-600" />, result: '19.71 g/kg SOC', confidence: '95% CI', date: '2 days ago' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center font-bold">
          <History className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Analysis Session History</h1>
          <p className="text-xs text-slate-500">
            Local browser session history of generated crop, disease, soil, and yield analyses.
          </p>
        </div>
      </div>

      <GlassCard variant="strong" className="p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200/60 pb-3">
          <h3 className="text-sm font-bold text-slate-900">Recent Session Analyses</h3>
          <Badge variant="neutral">Local Storage Session</Badge>
        </div>

        <div className="space-y-3">
          {dummyHistory.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between p-3.5 rounded-xl bg-white/70 border border-slate-100 text-xs">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-slate-100">{item.icon}</div>
                <div>
                  <p className="font-bold text-slate-900">{item.type}</p>
                  <p className="text-[10px] text-slate-400">{item.date}</p>
                </div>
              </div>
              <div className="text-right">
                <span className="font-bold text-slate-800 block capitalize">{item.result}</span>
                <span className="text-[10px] text-slate-500">{item.confidence}</span>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
};
