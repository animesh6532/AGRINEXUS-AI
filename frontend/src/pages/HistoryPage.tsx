import React from 'react';
import { History, Sprout, Stethoscope, Bug, Mountain, TrendingUp, CheckCircle2 } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';

export const HistoryPage: React.FC = () => {
  const historyItems = [
    {
      type: 'Crop Recommendation',
      icon: <Sprout className="w-5 h-5 text-[#2F6B3C]" />,
      result: 'Rice (Paddy)',
      confidence: '68.7% Confidence',
      date: 'Today, 10:45 AM',
      details: 'Evaluated against NPK soil ratios & climate precipitation signals.',
    },
    {
      type: 'Plant Disease Diagnostics',
      icon: <Stethoscope className="w-5 h-5 text-[#2F6B3C]" />,
      result: 'Corn — Healthy',
      confidence: '95.1% Match Probability',
      date: 'Today, 09:30 AM',
      details: 'ResNet18 leaf inspection with Grad-CAM heatmap generated.',
    },
    {
      type: 'Pest Risk Assessment',
      icon: <Bug className="w-5 h-5 text-amber-700" />,
      result: 'Medium Outbreak Risk',
      confidence: '78.0% Severity Score',
      date: 'Yesterday, 04:15 PM',
      details: 'Evaluated microclimate humidity & regional rainfall vectors.',
    },
    {
      type: 'Soil Carbon Analysis',
      icon: <Mountain className="w-5 h-5 text-emerald-800" />,
      result: '19.71 g/kg Soil Organic Carbon',
      confidence: '95% Confidence Bounds',
      date: '2 Days Ago',
      details: 'LUCAS European topsoil regression pipeline.',
    },
    {
      type: 'Harvest Yield Forecast',
      icon: <TrendingUp className="w-5 h-5 text-indigo-700" />,
      result: '2.45 Tons / Hectare Forecast',
      confidence: 'XGBoost Model',
      date: '3 Days Ago',
      details: 'Predicted using area, rainfall, and fertilizer application rate.',
    },
  ];

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="ACTIVITY"
        title="Your Field Intelligence Timeline"
        description="Chronological record of generated crop recommendations, plant leaf diagnoses, pest risk assessments, and soil analysis inferences."
        imageSrc="/images/hero-farmland.webp"
      />

      <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
              LOCAL SESSION RECORD
            </span>
            <h2 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">
              Recent Field Inferences & Diagnoses
            </h2>
          </div>
          <span className="px-3 py-1 rounded-full bg-[#EEF3E8] text-[#2F6B3C] text-xs font-bold border border-[#E2E7DA]">
            ● Active Browser Session
          </span>
        </div>

        {/* Vertical Timeline */}
        <div className="relative border-l-2 border-[#2F6B3C]/30 ml-4 pl-6 space-y-8 py-2">
          {historyItems.map((item, idx) => (
            <div key={idx} className="relative group">
              {/* Timeline Dot */}
              <div className="absolute -left-[31px] top-2 w-4 h-4 rounded-full bg-[#D4E768] border-2 border-[#0B1C10] shadow-sm group-hover:scale-125 transition-transform" />

              <div className="p-6 rounded-3xl bg-white border border-[#E2E7DA] hover:border-[#D4E768] hover:shadow-card-hover transition-all duration-300 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E2E7DA]/60 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-2xl bg-[#EEF3E8]">
                      {item.icon}
                    </div>
                    <div>
                      <h4 className="font-extrabold font-editorial text-base text-[#0B1C10]">{item.type}</h4>
                      <span className="text-[10px] text-[#536056] font-mono">{item.date}</span>
                    </div>
                  </div>

                  <div className="sm:text-right">
                    <span className="font-bold text-[#2F6B3C] text-sm block capitalize">{item.result}</span>
                    <span className="text-[10px] font-semibold text-[#536056]">{item.confidence}</span>
                  </div>
                </div>

                <p className="text-xs text-[#536056] leading-relaxed font-sans">{item.details}</p>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
};
