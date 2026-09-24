import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Camera, Sparkles } from 'lucide-react';

export const FinalCTA: React.FC = () => {
  return (
    <section className="relative py-28 lg:py-36 px-6 sm:px-12 bg-[#0B1C10] text-white overflow-hidden">
      {/* Background Visual Farmland Image */}
      <img
        src="/images/hero-farmland.webp"
        alt="Cinematic Farmland Background"
        className="absolute inset-0 w-full h-full object-cover opacity-30"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10] via-[#0B1C10]/80 to-[#0B1C10]/60 z-10" />

      <div className="max-w-5xl mx-auto text-center relative z-20 space-y-8">
        
        <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-white/10 border border-[#D4E768]/30 backdrop-blur-md text-xs font-bold uppercase tracking-widest text-[#D4E768]">
          <Sparkles className="w-4 h-4 text-[#D4E768] animate-pulse" />
          <span>TRANSFORM YOUR FIELD OPERATIONS</span>
        </div>

        <h2 className="hero-heading text-white tracking-tight leading-[0.98]">
          Your field has data. <br />
          <span className="text-[#D4E768] font-serif italic font-normal">Turn it into intelligence.</span>
        </h2>

        <p className="text-lg sm:text-xl text-gray-200 max-w-2xl mx-auto leading-relaxed font-normal">
          Access crop suitability, plant diagnostics, soil organic carbon, 3-hour irrigation forecasting, OpenCV camera vision, weather signals, and mandi price series in one platform.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-5 pt-4">
          <Link
            to="/dashboard"
            className="btn-agri-lime text-base shadow-2xl hover:scale-105"
          >
            <span>Explore AgriNexus-AI</span>
            <ArrowRight className="w-5 h-5" />
          </Link>

          <Link
            to="/live"
            className="btn-agri-ghost text-base backdrop-blur-md hover:scale-105"
          >
            <Camera className="w-5 h-5 text-[#D4E768]" />
            <span>Launch Live AI</span>
          </Link>
        </div>

      </div>
    </section>
  );
};
