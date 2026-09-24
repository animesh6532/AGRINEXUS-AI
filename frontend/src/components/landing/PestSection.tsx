import React from 'react';
import { Link } from 'react-router-dom';
import { Bug, ArrowRight, ShieldAlert, CheckCircle2 } from 'lucide-react';

export const PestSection: React.FC = () => {
  return (
    <section className="py-24 lg:py-32 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
        
        {/* Left Column: Macro Insect Image + Single-Insect Classification Preview Card (6 Cols) */}
        <div className="lg:col-span-6 relative order-2 lg:order-1">
          <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-[#E2E7DA] group">
            <img
              src="/images/pest-intelligence.webp"
              alt="Macro Insect Pest Photography"
              className="w-full h-[450px] sm:h-[500px] object-cover transition-transform duration-700 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10]/90 via-[#0B1C10]/20 to-transparent" />

            {/* Overlay Top Badge */}
            <div className="absolute top-6 left-6 flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-[#0B1C10]/80 text-amber-400 text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/10">
                MobileNetV3 • 102 Species
              </span>
              <span className="px-3 py-1 rounded-full bg-white/90 text-[#0B1C10] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/80">
                PRODUCT PREVIEW
              </span>
            </div>

            {/* Classification Preview Floating Card */}
            <div className="absolute bottom-6 left-6 right-6 p-5 rounded-2xl bg-white/95 backdrop-blur-md border border-white/90 shadow-2xl space-y-3 text-left">
              <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-800">
                  Single-Insect Visual Classification
                </span>
                <span className="text-[10px] font-mono font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Target #42
                </span>
              </div>

              <div className="flex items-baseline justify-between">
                <h4 className="text-xl font-extrabold text-[#0B1C10]">Spodoptera frugiperda</h4>
                <span className="text-xs font-mono font-bold text-amber-700">Fall Armyworm</span>
              </div>

              <div className="p-3 rounded-xl bg-[#FAFBF7] border border-[#E2E7DA] flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-600" />
                  <span className="font-semibold text-gray-700">Environmental Outbreak Risk</span>
                </div>
                <span className="font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded text-[10px] uppercase">
                  Moderate Risk
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Editorial Text (6 Cols) */}
        <div className="lg:col-span-6 space-y-8 text-left order-1 lg:order-2">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-50 border border-amber-200 text-xs font-bold uppercase tracking-widest text-amber-800">
            <Bug className="w-3.5 h-3.5 text-amber-600" />
            <span>PEST INTELLIGENCE</span>
          </div>

          <h2 className="editorial-heading text-[#0B1C10]">
            Understand the threats <br />
            <span className="text-[#2F6B3C] font-serif italic font-normal">before they spread.</span>
          </h2>

          <p className="text-lg text-[#39463B] leading-relaxed font-normal">
            Pest outbreaks destroy field crops rapidly if unchecked. AgriNexus-AI pairs transparent single-insect visual species classification with micro-climate environmental outbreak risk modeling.
          </p>

          <div className="space-y-3 pt-2 text-sm font-semibold text-[#0B1C10]">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-[#2F6B3C] shrink-0" />
              <span>MobileNetV3 architecture trained across 102 insect species</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-[#2F6B3C] shrink-0" />
              <span>Climate-based outbreak risk scoring from ambient humidity & temperature</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-[#2F6B3C] shrink-0" />
              <span>Single-insect focus scope (no misleading multi-box bounding claims)</span>
            </div>
          </div>

          <div className="pt-4">
            <Link
              to="/pest"
              className="btn-agri-dark text-sm hover:scale-105 shadow-lg"
            >
              <span>Explore Pest Intelligence</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

      </div>
    </section>
  );
};
