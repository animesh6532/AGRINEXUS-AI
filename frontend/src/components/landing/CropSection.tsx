import React from 'react';
import { Link } from 'react-router-dom';
import { Sprout, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';

export const CropSection: React.FC = () => {
  return (
    <section className="py-24 lg:py-32 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
        
        {/* Left Column: Large Image + Floating Product Preview Card (6 Cols) */}
        <div className="lg:col-span-6 relative order-2 lg:order-1">
          
          <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-[#E2E7DA] group">
            <img
              src="/images/crop-intelligence.webp"
              alt="Lush Crop Field Canopy"
              className="w-full h-[450px] sm:h-[520px] object-cover transition-transform duration-700 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10]/90 via-[#0B1C10]/30 to-transparent" />
            
            {/* Floating Product Preview Card */}
            <div className="absolute bottom-6 left-6 right-6 p-6 rounded-2xl bg-white/95 backdrop-blur-md border border-white/90 shadow-2xl space-y-4 text-left">
              <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
                <div className="flex items-center gap-2">
                  <Sprout className="w-4 h-4 text-[#2F6B3C]" />
                  <span className="text-xs font-bold text-[#0B1C10]">Crop Suitability Engine</span>
                </div>
                <span className="text-[10px] font-mono font-extrabold uppercase px-2.5 py-0.5 rounded bg-[#EEF3E8] text-[#2F6B3C] border border-[#2F6B3C]/20">
                  Product Preview
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-[11px]">
                <div className="p-2.5 rounded-xl bg-[#FAFBF7] border border-[#E2E7DA]">
                  <span className="text-[9px] font-bold text-gray-500 block uppercase">N-P-K Vector</span>
                  <span className="font-mono font-bold text-[#0B1C10] block mt-0.5">90 • 42 • 43</span>
                </div>
                <div className="p-2.5 rounded-xl bg-[#FAFBF7] border border-[#E2E7DA]">
                  <span className="text-[9px] font-bold text-gray-500 block uppercase">Soil pH</span>
                  <span className="font-mono font-bold text-[#0B1C10] block mt-0.5">6.5 (Optimal)</span>
                </div>
                <div className="p-2.5 rounded-xl bg-[#FAFBF7] border border-[#E2E7DA]">
                  <span className="text-[9px] font-bold text-gray-500 block uppercase">Rainfall</span>
                  <span className="font-mono font-bold text-[#0B1C10] block mt-0.5">202 mm</span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-[#EEF3E8] border border-[#2F6B3C]/30 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-extrabold uppercase text-[#2F6B3C] block">Top Match Profile</span>
                  <span className="text-base font-extrabold text-[#0B1C10]">Rice (Oryza sativa)</span>
                </div>
                <span className="text-xs font-mono font-bold text-[#2F6B3C] bg-white px-2.5 py-1 rounded-full border border-[#2F6B3C]/20">
                  Rank #1
                </span>
              </div>

              <div className="flex items-center gap-2 text-[10px] text-gray-600">
                <ShieldCheck className="w-3.5 h-3.5 text-[#5E9F48] shrink-0" />
                <span>IsolationForest verify: Soil feature vector within standard distribution.</span>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Editorial Text Content (6 Cols) */}
        <div className="lg:col-span-6 space-y-8 text-left order-1 lg:order-2">
          
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EEF3E8] border border-[#2F6B3C]/20 text-xs font-bold uppercase tracking-widest text-[#2F6B3C]">
            <Sprout className="w-3.5 h-3.5 text-[#5E9F48]" />
            <span>CROP INTELLIGENCE</span>
          </div>

          <h2 className="editorial-heading text-[#0B1C10]">
            Know what to grow.
          </h2>

          <p className="text-lg text-[#39463B] leading-relaxed font-normal">
            AgriNexus-AI evaluates Nitrogen (N), Phosphorus (P), Potassium (K), ambient temperature, relative humidity, soil pH, and regional rainfall to generate high-confidence crop recommendations.
          </p>

          <div className="space-y-3 pt-2 text-sm font-semibold text-[#0B1C10]">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-[#2F6B3C] shrink-0" />
              <span>7-variable soil nutrient & agro-climatic feature evaluation</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-[#2F6B3C] shrink-0" />
              <span>Integrated IsolationForest anomaly detection for out-of-distribution inputs</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-[#2F6B3C] shrink-0" />
              <span>Multi-crop probability ranking backed by ExtraTrees ensemble</span>
            </div>
          </div>

          <div className="pt-4">
            <Link
              to="/crop"
              className="btn-agri-dark text-sm hover:scale-105 shadow-lg"
            >
              <span>Explore Crop Recommendation</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

        </div>

      </div>
    </section>
  );
};
