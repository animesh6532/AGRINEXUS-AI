import React from 'react';
import { Leaf, Activity, Camera } from 'lucide-react';

export const SmartFarmingSection: React.FC = () => {
  return (
    <section className="py-24 lg:py-32 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Asymmetric Header Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column: Heading (6 Cols) */}
          <div className="lg:col-span-6 space-y-6 text-left">
            <span className="text-xs font-extrabold uppercase tracking-widest text-[#2F6B3C]">
              Smart Agriculture Framework
            </span>
            <h2 className="editorial-heading text-[#0B1C10]">
              Smart Intelligence <br />
              <span className="text-[#2F6B3C] font-serif italic font-normal">for a Changing Field.</span>
            </h2>
            <p className="text-lg text-[#39463B] leading-relaxed">
              Precision farming requires more than simple threshold alerts. AgriNexus-AI processes real-time crop growth cycles, local climate anomalies, and field imagery to deliver high-confidence insights directly to growers.
            </p>
          </div>

          {/* Right Column: Agricultural Drone & Machinery Visual (6 Cols) */}
          <div className="lg:col-span-6">
            <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-[#E2E7DA] group">
              <img
                src="/images/smart-farming.webp"
                alt="Precision Agricultural Inspection Drone"
                className="w-full h-[380px] lg:h-[450px] object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10]/70 via-transparent to-transparent" />
              <div className="absolute bottom-6 left-6 right-6 p-4 rounded-xl bg-white/90 backdrop-blur-md border border-white/80 shadow-md text-left">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#2F6B3C]">
                  Drone & Vision Aerial Telemetry
                </span>
                <p className="text-xs font-bold text-[#0B1C10] mt-0.5">
                  High-resolution canopy inspection with non-destructive AI scanning
                </p>
              </div>
            </div>
          </div>

        </div>

        {/* Underneath: 3 Compact Value Blocks (NOT large cards) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-12 border-t border-[#E2E7DA] text-left">
          
          {/* Block 1 */}
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#EEF3E8] border border-[#2F6B3C]/20 text-[#2F6B3C] flex items-center justify-center">
              <Leaf className="w-5 h-5" />
            </div>
            <h4 className="text-lg font-bold text-[#0B1C10]">Crop Intelligence</h4>
            <p className="text-sm text-[#39463B] leading-relaxed">
              Match soil chemical profiles and climate conditions to optimal high-yield crop varieties.
            </p>
          </div>

          {/* Block 2 */}
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#EEF3E8] border border-[#2F6B3C]/20 text-[#2F6B3C] flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <h4 className="text-lg font-bold text-[#0B1C10]">Plant Health</h4>
            <p className="text-sm text-[#39463B] leading-relaxed">
              Detect early leaf pathology using Grad-CAM explainable heatmaps before visible damage spreads.
            </p>
          </div>

          {/* Block 3 */}
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#EEF3E8] border border-[#2F6B3C]/20 text-[#2F6B3C] flex items-center justify-center">
              <Camera className="w-5 h-5" />
            </div>
            <h4 className="text-lg font-bold text-[#0B1C10]">Field Intelligence</h4>
            <p className="text-sm text-[#39463B] leading-relaxed">
              Continuous live computer vision streaming with quality control and temporal smoothing.
            </p>
          </div>

        </div>

      </div>
    </section>
  );
};
