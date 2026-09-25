import React from 'react';
import { ShieldCheck, Info } from 'lucide-react';

interface ScopeItem {
  title: string;
  scope: string;
  desc: string;
}

export const TransparencySection: React.FC = () => {
  const limitations: ScopeItem[] = [
    {
      title: 'Fertilizer Formulation',
      scope: 'Western Maharashtra scope',
      desc: 'Recommendations reflect specific regional soil profiles. Always calibrate with local agricultural extension guidelines.'
    },
    {
      title: 'Soil Organic Carbon',
      scope: 'LUCAS European Topsoil scope',
      desc: 'Models output explicit 95% residual confidence bounds. Calibrated against European topsoil spectral samples.'
    },
    {
      title: 'Irrigation Predictor',
      scope: 'ML + persistence benchmark',
      desc: 'ML forecasts are benchmarked side-by-side against naïve persistence baselines to verify genuine predictive lift.'
    },
    {
      title: 'Plant Disease Model',
      scope: 'Controlled benchmark vs field domain',
      desc: '38-class ResNet18 trained on benchmark leaves. Controlled lab accuracy should not be blindly assumed in occluded field conditions.'
    },
    {
      title: 'Pest Intelligence',
      scope: 'Single-insect classification',
      desc: 'MobileNetV3 designed for macro single-insect photos. Does not perform multi-object bounding-box detection.'
    },
    {
      title: 'Yield Forecasting',
      scope: 'Heterogeneous target conventions',
      desc: 'Yield reporting conventions vary across regional databases. Projections include explicit 95% uncertainty ranges.'
    }
  ];

  return (
    <section id="transparency" className="py-28 px-6 sm:px-12 bg-[#0B1C10] text-white relative overflow-hidden">
      
      {/* Ambient Backlight */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#D4E768]/5 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-7xl mx-auto space-y-16 relative z-10 text-left">
        
        {/* Section Header */}
        <div className="space-y-4 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-white/10 border border-[#D4E768]/30 text-xs font-bold uppercase tracking-widest text-[#D4E768]">
            <ShieldCheck className="w-4 h-4 text-[#D4E768]" />
            <span>MODEL TRANSPARENCY & DATASET SCOPE</span>
          </div>

          <h2 className="editorial-heading text-white">
            Intelligence you can <br />
            <span className="text-[#D4E768] font-serif italic font-normal">understand.</span>
          </h2>

          <p className="text-lg text-gray-300 leading-relaxed font-normal">
            Machine learning in agriculture is only useful when dataset boundaries and model scopes are stated honestly. AgriNexus-AI makes every constraint transparent.
          </p>
        </div>

        {/* Technical Platform Facts Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-8 rounded-3xl bg-[#112316] border border-white/10 text-center">
          <div>
            <span className="block text-4xl sm:text-5xl font-black text-[#D4E768] font-sans">7</span>
            <span className="text-[11px] font-bold text-gray-300 uppercase tracking-widest mt-1 block">
              Frozen ML Artifacts
            </span>
          </div>
          <div>
            <span className="block text-4xl sm:text-5xl font-black text-[#D4E768] font-sans">8</span>
            <span className="text-[11px] font-bold text-gray-300 uppercase tracking-widest mt-1 block">
              Inference Services
            </span>
          </div>
          <div>
            <span className="block text-2xl sm:text-3xl font-extrabold text-white font-mono mt-2">OpenCV</span>
            <span className="text-[11px] font-bold text-gray-300 uppercase tracking-widest mt-1 block">
              Quality Inspection
            </span>
          </div>
          <div>
            <span className="block text-2xl sm:text-3xl font-extrabold text-white font-mono mt-2">95% CI</span>
            <span className="text-[11px] font-bold text-gray-300 uppercase tracking-widest mt-1 block">
              Prediction Uncertainty
            </span>
          </div>
        </div>

        {/* Dataset Scope & Limitations Breakdown Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {limitations.map((item, idx) => (
            <div
              key={idx}
              className="p-6 rounded-2xl bg-[#112316] border border-white/10 space-y-3 hover:border-[#D4E768]/40 transition-all text-left group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase px-2.5 py-0.5 rounded bg-[#D4E768]/20 text-[#D4E768]">
                  {item.scope}
                </span>
                <Info className="w-3.5 h-3.5 text-gray-400" />
              </div>
              <h4 className="font-extrabold text-white text-lg group-hover:text-[#D4E768] transition-colors">{item.title}</h4>
              <p className="text-xs text-gray-300 leading-relaxed font-normal">{item.desc}</p>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
};
