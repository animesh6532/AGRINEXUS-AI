import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';

export const IntroSection: React.FC = () => {
  return (
    <section id="intro" className="py-24 lg:py-36 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA] relative overflow-hidden">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Asymmetric Editorial Composition */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          
          {/* Left Column: Heading + Copy + CTA (7 Cols) */}
          <div className="lg:col-span-7 space-y-8 text-left">
            <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-[#EEF3E8] border border-[#2F6B3C]/20 text-xs font-bold uppercase tracking-widest text-[#2F6B3C]">
              <Sparkles className="w-3.5 h-3.5 text-[#5E9F48]" />
              <span>Editorial Overview</span>
            </div>

            <h2 className="editorial-heading text-[#0B1C10] font-bold tracking-tight">
              Modern Intelligence <br />
              <span className="text-[#2F6B3C] italic font-serif font-normal">for Traditional Fields.</span>
            </h2>

            <p className="text-lg sm:text-xl text-[#39463B] leading-relaxed font-normal max-w-2xl">
              AgriNexus-AI connects crop, soil, plant health, water, yield, weather and market intelligence into one cohesive platform. Built specifically for complex agricultural environments where field conditions change continuously.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                to="/dashboard"
                className="btn-agri-dark text-sm hover:scale-105 shadow-md"
              >
                <span>Explore Platform Features</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* Quick Core Benefits */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-6 border-t border-[#E2E7DA]">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-[#2F6B3C] shrink-0 mt-0.5" />
                <span className="text-sm font-semibold text-[#162018]">
                  Integrated agronomic ML models with clear data contracts
                </span>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-[#2F6B3C] shrink-0 mt-0.5" />
                <span className="text-sm font-semibold text-[#162018]">
                  Quality-gated computer vision for real-time field diagnostics
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Large Agricultural Image Composition (5 Cols) */}
          <div className="lg:col-span-5 relative">
            <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-[#E2E7DA] group">
              <img
                src="/images/hero-farmland.webp"
                alt="VerdaAgro Inspired Agricultural Farmland"
                className="w-full h-[450px] lg:h-[540px] object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10]/80 via-transparent to-transparent" />
              
              {/* Overlay Badge */}
              <div className="absolute bottom-6 left-6 right-6 p-5 rounded-2xl bg-white/90 backdrop-blur-md border border-white/80 shadow-lg text-left">
                <div className="text-[10px] font-extrabold uppercase tracking-widest text-[#2F6B3C]">
                  Precision Field Telemetry
                </div>
                <div className="text-sm font-bold text-[#0B1C10] mt-1">
                  Connecting satellite, soil sensors & vision models
                </div>
              </div>
            </div>

            {/* Floating Organic Accent Ring */}
            <div className="absolute -top-6 -right-6 w-32 h-32 rounded-full border-2 border-dashed border-[#2F6B3C]/20 pointer-events-none -z-10" />
          </div>

        </div>

      </div>
    </section>
  );
};
