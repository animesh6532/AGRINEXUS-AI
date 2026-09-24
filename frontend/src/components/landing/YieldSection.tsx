import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, ArrowRight, AlertCircle } from 'lucide-react';

export const YieldSection: React.FC = () => {
  return (
    <section className="py-24 lg:py-32 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
        
        {/* Left Column: Harvester Image + Prediction Preview Box (6 Cols) */}
        <div className="lg:col-span-6 relative order-2 lg:order-1">
          <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-[#E2E7DA] group">
            <img
              src="/images/yield-intelligence.webp"
              alt="Combine Harvester Working Golden Wheat Field"
              className="w-full h-[450px] sm:h-[500px] object-cover transition-transform duration-700 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10]/90 via-[#0B1C10]/20 to-transparent" />

            {/* Top Badge */}
            <div className="absolute top-6 left-6 flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-[#0B1C10]/80 text-[#D4E768] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/10">
                XGBoost Regressor
              </span>
              <span className="px-3 py-1 rounded-full bg-white/90 text-[#0B1C10] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/80">
                PRODUCT PREVIEW
              </span>
            </div>

            {/* Prediction UI Overlay Card */}
            <div className="absolute bottom-6 left-6 right-6 p-5 rounded-2xl bg-white/95 backdrop-blur-md border border-white/90 shadow-2xl space-y-3 text-left">
              <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-2">
                <span className="text-[10px] font-extrabold uppercase text-[#2F6B3C]">
                  Harvest Yield Forecast
                </span>
                <span className="text-[10px] font-mono font-bold text-gray-600">
                  Target: Regional Production
                </span>
              </div>

              <div className="flex items-baseline justify-between">
                <div>
                  <span className="text-[10px] font-bold text-gray-500 uppercase block">Predicted Output</span>
                  <h4 className="text-2xl font-extrabold text-[#0B1C10]">18.4 Metric Tonnes</h4>
                </div>
                <span className="text-xs font-mono font-bold text-[#2F6B3C] bg-[#EEF3E8] px-2.5 py-1 rounded-full">
                  ~3.68 t/Ha
                </span>
              </div>

              {/* Explicit Uncertainty Bar */}
              <div className="space-y-1 pt-2 border-t border-[#E2E7DA]">
                <div className="flex justify-between text-[10px] font-mono font-bold text-gray-600">
                  <span>95% CI Lower: 16.1 t</span>
                  <span>95% CI Upper: 20.7 t</span>
                </div>
                <div className="w-full h-2 rounded-full bg-gray-100 relative overflow-hidden border border-[#E2E7DA]">
                  <div className="absolute left-[15%] right-[15%] top-0 bottom-0 bg-[#5E9F48]/40" />
                  <div className="absolute left-[50%] w-1 top-0 bottom-0 bg-[#2F6B3C]" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Editorial Copy (6 Cols) */}
        <div className="lg:col-span-6 space-y-8 text-left order-1 lg:order-2">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EEF3E8] border border-[#2F6B3C]/20 text-xs font-bold uppercase tracking-widest text-[#2F6B3C]">
            <TrendingUp className="w-3.5 h-3.5 text-[#5E9F48]" />
            <span>YIELD INTELLIGENCE</span>
          </div>

          <h2 className="editorial-heading text-[#0B1C10]">
            Turn field conditions <br />
            <span className="text-[#2F6B3C] font-serif italic font-normal">into yield insight.</span>
          </h2>

          <p className="text-lg text-[#39463B] leading-relaxed font-normal">
            Predicting crop production requires synthesizing historical weather patterns, soil inputs, pesticide volumes, and cultivated land area. AgriNexus-AI uses XGBoost regression with 95% uncertainty confidence bounds.
          </p>

          <div className="p-5 rounded-2xl bg-white border border-[#E2E7DA] shadow-md space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold uppercase text-[#0B1C10]">
              <AlertCircle className="w-4 h-4 text-[#2F6B3C]" />
              <span>Honest Uncertainty Bounds</span>
            </div>
            <p className="text-xs text-[#39463B] leading-relaxed">
              Every yield prediction displays residual uncertainty ranges so farmers and agricultural planners can evaluate worst-case and best-case harvest scenarios safely.
            </p>
          </div>

          <div className="pt-2">
            <Link
              to="/yield"
              className="btn-agri-dark text-sm hover:scale-105 shadow-lg"
            >
              <span>Calculate Yield Prediction</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

      </div>
    </section>
  );
};
