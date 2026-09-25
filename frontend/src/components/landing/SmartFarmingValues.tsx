import React from 'react';
import { Database, Sprout, Eye } from 'lucide-react';

export const SmartFarmingValues: React.FC = () => {
  return (
    <section className="py-28 lg:py-36 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto px-6 sm:px-12 space-y-20 text-left">
        
        <div className="space-y-4 max-w-2xl">
          <span className="text-xs font-extrabold uppercase tracking-widest text-[#2F6B3C]">
            Core Agricultural Philosophy
          </span>
          <h2 className="editorial-heading text-[#0B1C10]">
            Built for the reality <br />
            <span className="text-[#2F6B3C] font-serif italic font-normal">of modern farming.</span>
          </h2>
        </div>

        {/* 3 Large Value Columns Inspired by VerdaAgro Reference */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 lg:gap-16 pt-6 border-t border-[#E2E7DA]">
          
          {/* Value 01 */}
          <div className="space-y-6 group">
            <div className="flex items-center justify-between">
              <span className="text-5xl font-black text-[#D6E4CC] group-hover:text-[#2F6B3C] transition-colors font-sans">
                01
              </span>
              <div className="w-10 h-10 rounded-xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center">
                <Database className="w-5 h-5" />
              </div>
            </div>
            <h3 className="text-2xl font-extrabold text-[#0B1C10]">
              Data-Driven
            </h3>
            <p className="text-sm text-[#39463B] leading-relaxed">
              Grounding agronomic recommendations in physical soil parameters, regional rainfall history, and verified ML model weights rather than uncalibrated guesswork.
            </p>
          </div>

          {/* Value 02 */}
          <div className="space-y-6 group">
            <div className="flex items-center justify-between">
              <span className="text-5xl font-black text-[#D6E4CC] group-hover:text-[#2F6B3C] transition-colors font-sans">
                02
              </span>
              <div className="w-10 h-10 rounded-xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center">
                <Sprout className="w-5 h-5" />
              </div>
            </div>
            <h3 className="text-2xl font-extrabold text-[#0B1C10]">
              Field-Aware
            </h3>
            <p className="text-sm text-[#39463B] leading-relaxed">
              Designed specifically for ambient outdoor lighting, camera shake, and seasonal micro-climates — ensuring robust real-world field utility.
            </p>
          </div>

          {/* Value 03 */}
          <div className="space-y-6 group">
            <div className="flex items-center justify-between">
              <span className="text-5xl font-black text-[#D6E4CC] group-hover:text-[#2F6B3C] transition-colors font-sans">
                03
              </span>
              <div className="w-10 h-10 rounded-xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center">
                <Eye className="w-5 h-5" />
              </div>
            </div>
            <h3 className="text-2xl font-extrabold text-[#0B1C10]">
              Transparent
            </h3>
            <p className="text-sm text-[#39463B] leading-relaxed">
              Full transparency on dataset origin, model scope, out-of-distribution anomaly detection, and explicit uncertainty confidence bounds.
            </p>
          </div>

        </div>

      </div>
    </section>
  );
};
