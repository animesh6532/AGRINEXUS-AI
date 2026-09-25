import React from 'react';
import { Link } from 'react-router-dom';
import { CloudSun, TrendingUp, ArrowRight } from 'lucide-react';

export const WeatherMarketSection: React.FC = () => {
  return (
    <section id="signals" className="py-24 lg:py-32 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Section Header */}
        <div className="text-left space-y-3 max-w-3xl">
          <span className="text-xs font-extrabold uppercase tracking-widest text-[#2F6B3C]">
            Agronomic Field & Market Telemetry
          </span>
          <h2 className="editorial-heading text-[#0B1C10]">
            Weather Signals & <br />
            <span className="text-[#2F6B3C] font-serif italic font-normal">Mandi Markets.</span>
          </h2>
        </div>

        {/* Dual Editorial Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
          
          {/* Card 1: Weather Telemetry */}
          <div className="agri-card overflow-hidden flex flex-col justify-between p-8 sm:p-10 space-y-8 text-left group">
            <div className="space-y-6">
              
              <div className="w-full h-48 rounded-2xl overflow-hidden relative border border-[#E2E7DA]">
                <img
                  src="/images/weather-intelligence.webp"
                  alt="Farmland Sky Weather"
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute top-3 left-3 px-3 py-1 rounded-full bg-[#0B1C10]/80 text-sky-400 text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/10">
                  Open-Meteo API
                </div>
                <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-white/90 text-[#0B1C10] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/80">
                  PRODUCT PREVIEW
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sky-700">
                  <CloudSun className="w-5 h-5" />
                  <span className="text-xs font-extrabold uppercase tracking-wider">WEATHER TELEMETRY</span>
                </div>
                <h3 className="text-2xl font-extrabold text-[#0B1C10]">
                  Field climate & operational windows.
                </h3>
                <p className="text-sm text-[#39463B] leading-relaxed">
                  Hourly climate forecasts with rule-based agronomic alerts for rain disruptions, spraying suitability windows, and crop temperature stress.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-sky-50 border border-sky-200 flex items-center justify-between text-xs">
                <div>
                  <span className="text-[10px] font-bold text-gray-500 uppercase block">7-Day Field Outlook</span>
                  <span className="font-bold text-[#0B1C10]">Optimal Spraying Window</span>
                </div>
                <span className="font-mono font-bold text-sky-700 bg-white px-2.5 py-1 rounded-full border border-sky-200">
                  Low Risk
                </span>
              </div>

            </div>

            <div className="pt-4 border-t border-[#E2E7DA]">
              <Link
                to="/weather"
                className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-sky-700 hover:underline"
              >
                <span>View Full Weather Telemetry</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Card 2: Mandi Market Signals */}
          <div className="agri-card overflow-hidden flex flex-col justify-between p-8 sm:p-10 space-y-8 text-left group">
            <div className="space-y-6">
              
              <div className="w-full h-48 rounded-2xl overflow-hidden relative border border-[#E2E7DA]">
                <img
                  src="/images/market-intelligence.webp"
                  alt="Agricultural Harvest Mandi Market"
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute top-3 left-3 px-3 py-1 rounded-full bg-[#0B1C10]/80 text-[#D4E768] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/10">
                  Government Mandi Series
                </div>
                <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-white/90 text-[#0B1C10] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/80">
                  PRODUCT PREVIEW
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-[#2F6B3C]">
                  <TrendingUp className="w-5 h-5" />
                  <span className="text-xs font-extrabold uppercase tracking-wider">MARKET INTELLIGENCE</span>
                </div>
                <h3 className="text-2xl font-extrabold text-[#0B1C10]">
                  Turn harvest timing into profit.
                </h3>
                <p className="text-sm text-[#39463B] leading-relaxed">
                  Tracks mandi commodity prices across Indian agricultural markets, generating time-series forecast trajectories to inform crop sales timing.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#EEF3E8] border border-[#2F6B3C]/20 flex items-center justify-between text-xs">
                <div>
                  <span className="text-[10px] font-bold text-gray-500 uppercase block">Paddy (Common) Forecast</span>
                  <span className="font-bold text-[#0B1C10]">Modal Price: ₹2,180 / Quintal</span>
                </div>
                <span className="font-mono font-bold text-[#2F6B3C] bg-white px-2.5 py-1 rounded-full border border-[#2F6B3C]/20">
                  +3.2% Trend
                </span>
              </div>

            </div>

            <div className="pt-4 border-t border-[#E2E7DA]">
              <Link
                to="/market"
                className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#2F6B3C] hover:underline"
              >
                <span>Explore Market Signals</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
};
