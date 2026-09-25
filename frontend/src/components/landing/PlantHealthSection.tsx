import React from 'react';
import { Link } from 'react-router-dom';
import { Stethoscope, ArrowRight, Eye, Layers } from 'lucide-react';

export const PlantHealthSection: React.FC = () => {
  return (
    <section className="py-24 lg:py-32 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
        
        {/* Left Column: Content (6 Cols) */}
        <div className="lg:col-span-6 space-y-8 text-left">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EEF3E8] border border-[#2F6B3C]/20 text-xs font-bold uppercase tracking-widest text-[#2F6B3C]">
            <Stethoscope className="w-3.5 h-3.5 text-[#5E9F48]" />
            <span>PLANT HEALTH INTELLIGENCE</span>
          </div>

          <h2 className="editorial-heading text-[#0B1C10]">
            See what your crops <br />
            <span className="text-[#2F6B3C] font-serif italic font-normal">are telling you.</span>
          </h2>

          <p className="text-lg text-[#39463B] leading-relaxed font-normal">
            Early detection of leaf pathology prevents catastrophic crop damage. AgriNexus-AI utilizes a PyTorch ResNet18 convolutional neural network trained across 38 plant disease categories, complete with Grad-CAM explainability heatmaps.
          </p>

          <div className="p-6 rounded-2xl bg-white border border-[#E2E7DA] shadow-md space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center">
                <Eye className="w-5 h-5" />
              </div>
              <h4 className="text-base font-bold text-[#0B1C10]">Grad-CAM Visual Heatmaps</h4>
            </div>
            <p className="text-xs text-[#39463B] leading-relaxed">
              Grad-CAM visual overlays highlight exact lesion boundaries, chlorosis spots, and fungal rust vectors triggering the neural network classification.
            </p>
          </div>

          <div className="pt-2">
            <Link
              to="/disease"
              className="btn-agri-dark text-sm hover:scale-105 shadow-lg"
            >
              <span>Analyze a Plant</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Right Column: Visual Leaf Image with Grad-CAM Heatmap Overlay (6 Cols) */}
        <div className="lg:col-span-6 relative">
          <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-[#E2E7DA] group">
            <img
              src="/images/plant-health.webp"
              alt="Plant Leaf Disease Inspection"
              className="w-full h-[450px] sm:h-[500px] object-cover transition-transform duration-700 group-hover:scale-105"
            />
            
            {/* Grad-CAM Heatmap Overlay Effect */}
            <div className="absolute inset-0 bg-gradient-to-tr from-amber-500/30 via-emerald-500/20 to-transparent pointer-events-none mix-blend-color-dodge" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0B1C10]/80 via-transparent to-transparent" />

            {/* Top Badge */}
            <div className="absolute top-6 left-6 flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-[#0B1C10]/80 text-[#D4E768] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/10">
                ResNet18 • 38 Plant Classes
              </span>
              <span className="px-3 py-1 rounded-full bg-white/90 text-[#0B1C10] text-[10px] font-mono font-bold uppercase backdrop-blur-md border border-white/80">
                Product Preview
              </span>
            </div>

            {/* Grad-CAM Overlay Bottom Panel */}
            <div className="absolute bottom-6 left-6 right-6 p-5 rounded-2xl bg-[#0B1C10]/85 backdrop-blur-md border border-white/15 text-white flex items-center justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping" />
                  <span className="text-sm font-bold text-white">Tomato___Bacterial_spot</span>
                </div>
                <p className="text-[11px] text-gray-300">Grad-CAM Heatmap Analysis Active</p>
              </div>
              <div className="text-right">
                <span className="text-base font-mono font-extrabold text-[#D4E768]">96.8%</span>
                <span className="block text-[9px] uppercase font-mono text-gray-400">Confidence</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
};
