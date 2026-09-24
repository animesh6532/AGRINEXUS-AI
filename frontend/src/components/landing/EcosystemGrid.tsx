import React from 'react';
import { Link } from 'react-router-dom';
import {
  Sprout,
  Stethoscope,
  Mountain,
  Droplets,
  Bug,
  TrendingUp,
  ArrowUpRight,
  Sparkles
} from 'lucide-react';

export const EcosystemGrid: React.FC = () => {
  return (
    <section id="intelligence" className="py-28 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 text-left">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-[#EEF3E8] border border-[#2F6B3C]/20 text-xs font-bold uppercase tracking-widest text-[#2F6B3C]">
              <Sparkles className="w-3.5 h-3.5 text-[#5E9F48]" />
              <span>Core Intelligence Architecture</span>
            </div>
            <h2 className="editorial-heading text-[#0B1C10]">
              One platform. <br />
              <span className="text-[#2F6B3C] font-serif italic font-normal">Many field decisions.</span>
            </h2>
          </div>
          <p className="text-base text-[#39463B] max-w-md leading-relaxed font-normal">
            AgriNexus-AI integrates specialized ML modules into a continuous analytical workflow — from seed selection to harvest economics.
          </p>
        </div>

        {/* Asymmetric Image + Typography Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-stretch">
          
          {/* FEATURE 01: Crop Recommendation (Large 7-Col Hero Feature Block) */}
          <Link
            to="/crop"
            className="md:col-span-7 group relative bg-[#0B1C10] text-white rounded-3xl overflow-hidden border border-white/10 shadow-2xl flex flex-col justify-between p-8 sm:p-12 hover:border-[#D4E768]/50 transition-all transform hover:-translate-y-1 min-h-[420px]"
          >
            <img
              src="/images/crop-intelligence.webp"
              alt="Crop Intelligence Field Canopy"
              className="absolute inset-0 w-full h-full object-cover opacity-35 transition-transform duration-700 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10] via-[#0B1C10]/60 to-transparent z-10" />

            <div className="relative z-20 flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-widest px-3 py-1 rounded-full bg-[#D4E768] text-[#0B1C10] font-bold">
                Feature 01
              </span>
              <span className="text-xs font-mono uppercase tracking-wider text-gray-300">
                ExtraTrees Engine
              </span>
            </div>

            <div className="relative z-20 space-y-4 text-left mt-24">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/10 text-[#D4E768] flex items-center justify-center">
                  <Sprout className="w-5 h-5" />
                </div>
                <h3 className="text-2xl sm:text-4xl font-extrabold text-white">
                  Crop Recommendation
                </h3>
              </div>
              <p className="text-sm sm:text-base text-gray-200/90 leading-relaxed max-w-xl">
                Evaluates Nitrogen, Phosphorus, Potassium, soil pH, ambient temperature, humidity, and rainfall signals to recommend optimal crop profiles.
              </p>
              <div className="pt-4 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#D4E768]">
                <span>Explore Crop Recommendation</span>
                <ArrowUpRight className="w-4 h-4" />
              </div>
            </div>
          </Link>

          {/* FEATURE 02: Plant Disease Detection (5-Col Feature Block) */}
          <Link
            to="/disease"
            className="md:col-span-5 group relative bg-white text-[#0B1C10] rounded-3xl overflow-hidden border border-[#E2E7DA] shadow-xl flex flex-col justify-between p-8 sm:p-10 hover:border-[#2F6B3C] transition-all transform hover:-translate-y-1 min-h-[420px]"
          >
            <div className="w-full h-44 rounded-2xl overflow-hidden mb-6 border border-[#E2E7DA] relative">
              <img
                src="/images/plant-health.webp"
                alt="Plant Leaf Macro Photography"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-[#0B1C10]/80 text-[#D4E768] text-[10px] font-mono font-bold uppercase backdrop-blur-md">
                Grad-CAM Enabled
              </div>
            </div>

            <div className="space-y-3 text-left">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold uppercase tracking-widest text-[#2F6B3C]">
                  Feature 02
                </span>
                <span className="text-xs font-semibold text-gray-500">ResNet18</span>
              </div>
              <h3 className="text-2xl font-extrabold text-[#0B1C10] group-hover:text-[#2F6B3C] transition-colors">
                Plant Disease Diagnostics
              </h3>
              <p className="text-xs text-[#39463B] leading-relaxed">
                Diagnoses 38 plant pathology classes with explainable Grad-CAM visual heatmaps highlighting infected leaf regions.
              </p>
              <div className="pt-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#2F6B3C]">
                <span>Analyze Leaf Health</span>
                <ArrowUpRight className="w-4 h-4" />
              </div>
            </div>
          </Link>

          {/* FEATURE 03: Pest Intelligence (4-Col Block) */}
          <Link
            to="/pest"
            className="md:col-span-4 group bg-white border border-[#E2E7DA] rounded-3xl overflow-hidden p-6 sm:p-8 flex flex-col justify-between space-y-6 hover:border-[#2F6B3C] shadow-lg transition-all transform hover:-translate-y-1"
          >
            <div className="w-full h-36 rounded-2xl overflow-hidden relative border border-[#E2E7DA]">
              <img
                src="/images/pest-intelligence.webp"
                alt="Macro Insect Photography"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
            </div>
            <div className="space-y-2 text-left">
              <div className="flex items-center justify-between text-xs font-mono font-bold text-[#2F6B3C]">
                <span>Feature 03</span>
                <span className="text-[10px] text-gray-500 uppercase">102 Species</span>
              </div>
              <h4 className="text-xl font-extrabold text-[#0B1C10]">Pest Intelligence</h4>
              <p className="text-xs text-[#39463B] leading-relaxed">
                Single-insect visual classification combined with environmental outbreak risk scoring.
              </p>
            </div>
            <div className="pt-2 flex items-center justify-between text-xs font-bold text-[#2F6B3C] border-t border-[#E2E7DA]">
              <span>Identify Pest</span>
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </Link>

          {/* FEATURE 04: Soil Intelligence (4-Col Block) */}
          <Link
            to="/soil"
            className="md:col-span-4 group bg-white border border-[#E2E7DA] rounded-3xl overflow-hidden p-6 sm:p-8 flex flex-col justify-between space-y-6 hover:border-[#2F6B3C] shadow-lg transition-all transform hover:-translate-y-1"
          >
            <div className="w-full h-36 rounded-2xl overflow-hidden relative border border-[#E2E7DA]">
              <img
                src="/images/soil-intelligence.webp"
                alt="Fertile Soil Texture"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
            </div>
            <div className="space-y-2 text-left">
              <div className="flex items-center justify-between text-xs font-mono font-bold text-[#2F6B3C]">
                <span>Feature 04</span>
                <span className="text-[10px] text-gray-500 uppercase">LUCAS Topsoil</span>
              </div>
              <h4 className="text-xl font-extrabold text-[#0B1C10]">Soil Organic Carbon</h4>
              <p className="text-xs text-[#39463B] leading-relaxed">
                Estimates topsoil organic carbon (g/kg) with 95% confidence intervals based on field composition.
              </p>
            </div>
            <div className="pt-2 flex items-center justify-between text-xs font-bold text-[#2F6B3C] border-t border-[#E2E7DA]">
              <span>Analyze Soil</span>
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </Link>

          {/* FEATURE 05: Irrigation Intelligence (4-Col Block) */}
          <Link
            to="/irrigation"
            className="md:col-span-4 group bg-white border border-[#E2E7DA] rounded-3xl overflow-hidden p-6 sm:p-8 flex flex-col justify-between space-y-6 hover:border-[#2F6B3C] shadow-lg transition-all transform hover:-translate-y-1"
          >
            <div className="w-full h-36 rounded-2xl overflow-hidden relative border border-[#E2E7DA]">
              <img
                src="/images/irrigation.webp"
                alt="Farm Irrigation Sprinkler"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
            </div>
            <div className="space-y-2 text-left">
              <div className="flex items-center justify-between text-xs font-mono font-bold text-[#2F6B3C]">
                <span>Feature 05</span>
                <span className="text-[10px] text-gray-500 uppercase">3h SWC Forecast</span>
              </div>
              <h4 className="text-xl font-extrabold text-[#0B1C10]">Irrigation Dynamics</h4>
              <p className="text-xs text-[#39463B] leading-relaxed">
                Soil water content forecast benchmarked against simple persistence baselines.
              </p>
            </div>
            <div className="pt-2 flex items-center justify-between text-xs font-bold text-[#2F6B3C] border-t border-[#E2E7DA]">
              <span>Water Forecast</span>
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </Link>

          {/* FEATURE 06: Yield Intelligence (12-Col Full Width Banner) */}
          <Link
            to="/yield"
            className="md:col-span-12 group relative bg-[#112316] text-white rounded-3xl overflow-hidden border border-white/10 shadow-2xl p-8 sm:p-12 flex flex-col md:flex-row items-center justify-between gap-8 hover:border-[#D4E768]/50 transition-all transform hover:-translate-y-1"
          >
            <div className="absolute inset-0 w-full h-full">
              <img
                src="/images/yield-intelligence.webp"
                alt="Combine Harvester Wheat Sunset"
                className="w-full h-full object-cover opacity-25 transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-[#112316] via-[#112316]/90 to-transparent z-10" />
            </div>

            <div className="relative z-20 space-y-3 text-left max-w-2xl">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono font-bold uppercase tracking-widest px-3 py-1 rounded-full bg-[#D4E768] text-[#0B1C10]">
                  Feature 06
                </span>
                <span className="text-xs font-mono text-gray-300 uppercase">XGBoost Regression</span>
              </div>
              <h3 className="text-2xl sm:text-4xl font-extrabold text-white">
                Yield Prediction & Uncertainty Bounds
              </h3>
              <p className="text-sm text-gray-200/90 leading-relaxed font-normal">
                Converts regional climate telemetry, soil inputs, and historical crop data into predicted yield estimates accompanied by uncertainty confidence intervals.
              </p>
            </div>

            <div className="relative z-20 shrink-0">
              <div className="btn-agri-lime text-sm hover:scale-105 shadow-xl">
                <span>Calculate Yield</span>
                <ArrowUpRight className="w-4 h-4" />
              </div>
            </div>
          </Link>

        </div>

      </div>
    </section>
  );
};
