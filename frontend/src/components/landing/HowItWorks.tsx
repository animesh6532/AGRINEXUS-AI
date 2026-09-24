import React from 'react';
import { Camera, Cpu, Eye, CheckCircle2 } from 'lucide-react';

interface Step {
  num: string;
  title: string;
  desc: string;
  icon: React.ReactNode;
}

export const HowItWorks: React.FC = () => {
  const steps: Step[] = [
    {
      num: '01',
      title: 'Capture',
      desc: 'Input soil nutrients, upload leaf photos, or connect real-time browser camera stream.',
      icon: <Camera className="w-5 h-5 text-[#2F6B3C]" />
    },
    {
      num: '02',
      title: 'Analyze',
      desc: 'OpenCV inspects frame quality while 7 frozen ML models process agronomic feature contracts.',
      icon: <Cpu className="w-5 h-5 text-[#2F6B3C]" />
    },
    {
      num: '03',
      title: 'Understand',
      desc: 'Review Grad-CAM visual heatmaps, 95% confidence intervals, and persistence baselines.',
      icon: <Eye className="w-5 h-5 text-[#2F6B3C]" />
    },
    {
      num: '04',
      title: 'Act',
      desc: 'Execute field operations, apply fertilizer formulations, or schedule crop sales at peak prices.',
      icon: <CheckCircle2 className="w-5 h-5 text-[#2F6B3C]" />
    }
  ];

  return (
    <section className="py-24 lg:py-32 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto space-y-16 text-left">
        
        {/* Section Header */}
        <div className="space-y-3 max-w-xl">
          <span className="text-xs font-extrabold uppercase tracking-widest text-[#2F6B3C]">
            Four-Stage Pipeline
          </span>
          <h2 className="editorial-heading text-[#0B1C10]">
            How AgriNexus-AI Works
          </h2>
        </div>

        {/* 4 Connected Minimal Steps Grid */}
        <div className="relative pt-4">
          
          {/* Thin Horizontal Connecting Line (Desktop) */}
          <div className="hidden lg:block absolute top-16 left-8 right-8 h-0.5 bg-[#E2E7DA] -z-0" />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 relative z-10">
            {steps.map((s, idx) => (
              <div
                key={idx}
                className="agri-card p-8 space-y-6 hover:border-[#2F6B3C] transition-all group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-4xl font-black font-sans text-[#2F6B3C]">
                    {s.num}
                  </span>
                  <div className="w-10 h-10 rounded-xl bg-[#EEF3E8] border border-[#E2E7DA] flex items-center justify-center">
                    {s.icon}
                  </div>
                </div>

                <div className="space-y-2">
                  <h3 className="text-xl font-extrabold text-[#0B1C10] group-hover:text-[#2F6B3C] transition-colors">
                    {s.title}
                  </h3>
                  <p className="text-xs text-[#39463B] leading-relaxed font-normal">
                    {s.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>

        </div>

      </div>
    </section>
  );
};
