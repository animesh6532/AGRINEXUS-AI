import React from 'react';
import { Link } from 'react-router-dom';
import { Mountain, Droplets, ArrowRight, ShieldCheck, BarChart2 } from 'lucide-react';

export const SoilWaterSection: React.FC = () => {
  return (
    <section id="insights" className="py-24 lg:py-32 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Section Header */}
        <div className="text-left space-y-3 max-w-3xl">
          <span className="text-xs font-extrabold uppercase tracking-widest text-[#2F6B3C]">
            Subsurface Physical Telemetry
          </span>
          <h2 className="editorial-heading text-[#0B1C10]">
            Soil Carbon & <br />
            <span className="text-[#2F6B3C] font-serif italic font-normal">Water Dynamics.</span>
          </h2>
        </div>

        {/* 2-Column Editorial Visual Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
          
          {/* Card 1: Soil Organic Carbon */}
          <div className="agri-card overflow-hidden flex flex-col justify-between p-8 sm:p-10 space-y-8 text-left group">
            <div className="space-y-6">
              
              <div className="w-full h-48 rounded-2xl overflow-hidden relative border border-[#E2E7DA]">
                <img
                  src="/images/soil-intelligence.webp"
                  alt="Fertile Soil Texture Close Up"
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute top-3 left-3 px-3 py-1 rounded-full bg-[#0B1C10]/80 text-[#D4E768] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/10">
                  LUCAS Topsoil Scope
                </div>
                <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-white/90 text-[#0B1C10] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/80">
                  PRODUCT PREVIEW
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-[#2F6B3C]">
                  <Mountain className="w-5 h-5" />
                  <span className="text-xs font-extrabold uppercase tracking-wider">SOIL INTELLIGENCE</span>
                </div>
                <h3 className="text-2xl font-extrabold text-[#0B1C10]">
                  Understand what's beneath the crop.
                </h3>
                <p className="text-sm text-[#39463B] leading-relaxed">
                  Estimates Soil Organic Carbon (SOC in g/kg) with 95% residual confidence intervals derived from European LUCAS topsoil calibration data.
                </p>
              </div>

              {/* Sample Prediction Preview */}
              <div className="p-4 rounded-xl bg-[#EEF3E8] border border-[#2F6B3C]/20 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#0B1C10]">Estimated SOC Content</span>
                  <span className="font-mono font-extrabold text-[#2F6B3C]">24.8 g/kg</span>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-[10px] text-gray-600 font-mono">
                    <span>95% CI Lower: 21.2 g/kg</span>
                    <span>95% CI Upper: 28.4 g/kg</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-white relative overflow-hidden border border-[#2F6B3C]/30">
                    <div className="absolute left-[20%] right-[25%] top-0 bottom-0 bg-[#5E9F48]/40" />
                    <div className="absolute left-[52%] w-1.5 top-0 bottom-0 bg-[#2F6B3C] rounded-full" />
                  </div>
                </div>
              </div>

            </div>

            <div className="pt-4 border-t border-[#E2E7DA]">
              <Link
                to="/soil"
                className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#2F6B3C] hover:underline"
              >
                <span>Analyze Soil Organic Carbon</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Card 2: 3-Hour Soil Water Forecast */}
          <div className="agri-card overflow-hidden flex flex-col justify-between p-8 sm:p-10 space-y-8 text-left group">
            <div className="space-y-6">
              
              <div className="w-full h-48 rounded-2xl overflow-hidden relative border border-[#E2E7DA]">
                <img
                  src="/images/irrigation.webp"
                  alt="Irrigation Water Spraying Crops"
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute top-3 left-3 px-3 py-1 rounded-full bg-[#0B1C10]/80 text-sky-400 text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/10">
                  3h SWC Forecast
                </div>
                <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-white/90 text-[#0B1C10] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/80">
                  PRODUCT PREVIEW
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sky-700">
                  <Droplets className="w-5 h-5" />
                  <span className="text-xs font-extrabold uppercase tracking-wider">WATER INTELLIGENCE</span>
                </div>
                <h3 className="text-2xl font-extrabold text-[#0B1C10]">
                  Know when water matters.
                </h3>
                <p className="text-sm text-[#39463B] leading-relaxed">
                  Evaluates 3-hour Soil Water Content (SWC) predictions side-by-side with a naïve persistence baseline benchmark.
                </p>
              </div>

              {/* Sample Prediction Preview */}
              <div className="p-4 rounded-xl bg-sky-50 border border-sky-200 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#0B1C10]">Current Soil Water Baseline</span>
                  <span className="font-mono font-extrabold text-sky-700">0.24 m³/m³</span>
                </div>
                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="p-2.5 bg-white rounded-lg border border-sky-100">
                    <span className="text-[9px] uppercase font-bold text-gray-500 block">ML 3h Forecast</span>
                    <span className="text-xs font-mono font-bold text-sky-700 block mt-0.5">0.22 m³/m³</span>
                  </div>
                  <div className="p-2.5 bg-white rounded-lg border border-sky-100">
                    <span className="text-[9px] uppercase font-bold text-gray-500 block">Persistence Benchmark</span>
                    <span className="text-xs font-mono font-bold text-gray-700 block mt-0.5">0.24 m³/m³</span>
                  </div>
                </div>
              </div>

            </div>

            <div className="pt-4 border-t border-[#E2E7DA]">
              <Link
                to="/irrigation"
                className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-sky-700 hover:underline"
              >
                <span>Explore Water Forecast</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
};
