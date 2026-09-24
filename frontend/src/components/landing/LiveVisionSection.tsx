import React from 'react';
import { Link } from 'react-router-dom';
import { Camera, CheckCircle2, ShieldCheck, Zap, Activity, ArrowRight } from 'lucide-react';

export const LiveVisionSection: React.FC = () => {
  return (
    <section id="live-vision" className="py-28 px-6 sm:px-12 bg-[#0B1C10] text-white relative overflow-hidden">
      {/* Background Atmosphere */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-[#D4E768]/10 rounded-full blur-[150px] pointer-events-none" />

      <div className="max-w-7xl mx-auto space-y-16 relative z-10">
        
        {/* Section Header */}
        <div className="text-left space-y-4 max-w-3xl">
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-white/10 border border-[#D4E768]/30 text-xs font-bold uppercase tracking-widest text-[#D4E768]">
            <Camera className="w-4 h-4 text-[#D4E768]" />
            <span>REAL-TIME FIELD COMPUTER VISION</span>
          </div>

          <h2 className="editorial-heading text-white">
            AI That Can See <br />
            <span className="text-[#D4E768] font-serif italic font-normal">the Field.</span>
          </h2>

          <p className="text-lg text-gray-300 leading-relaxed font-normal">
            Stream live video directly from your mobile camera or field device. AgriNexus-AI inspects frame clarity with OpenCV, eliminates motion blur, and calculates temporal classification smoothing over live WebSockets.
          </p>
        </div>

        {/* Central Camera UI Interface & Pipeline Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          {/* Technical Pipeline Features (4 Cols) */}
          <div className="lg:col-span-4 space-y-5 text-left">
            
            <div className="p-6 rounded-2xl bg-[#112316] border border-white/10 space-y-2">
              <div className="flex items-center gap-2.5 text-[#D4E768] font-bold text-sm">
                <Zap className="w-4 h-4" />
                <span>OpenCV Quality Gates</span>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">
                Laplacian variance filters automatically discard out-of-focus or poorly lit frames before inference.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-[#112316] border border-white/10 space-y-2">
              <div className="flex items-center gap-2.5 text-[#D4E768] font-bold text-sm">
                <Activity className="w-4 h-4" />
                <span>Temporal Rolling Smoother</span>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">
                Prediction buffers stabilize frame output across minor lighting shifts or camera movement.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-[#112316] border border-white/10 space-y-2">
              <div className="flex items-center gap-2.5 text-[#D4E768] font-bold text-sm">
                <ShieldCheck className="w-4 h-4" />
                <span>Dual Neural Backends</span>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">
                Switch dynamically between 38-class plant pathology ResNet18 and 102-class insect classification MobileNetV3.
              </p>
            </div>

            <div className="pt-2">
              <Link
                to="/live"
                className="btn-agri-lime text-sm w-full justify-center shadow-xl"
              >
                <Camera className="w-4 h-4" />
                <span>Launch Live Camera</span>
              </Link>
            </div>

          </div>

          {/* Camera Viewport Mockup Box (8 Cols) */}
          <div className="lg:col-span-8 relative">
            <div className="bg-[#112316] border border-[#D4E768]/30 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-4">
              
              {/* Header Status Bar */}
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div className="flex items-center gap-3">
                  <span className="w-3 h-3 rounded-full bg-emerald-400 animate-ping" />
                  <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                    Vision Feed • Active Camera Stream
                  </span>
                </div>
                <span className="text-[10px] font-mono font-bold uppercase px-3 py-1 rounded bg-[#D4E768] text-[#0B1C10]">
                  PRODUCT PREVIEW
                </span>
              </div>

              {/* Viewport Frame */}
              <div className="aspect-video rounded-2xl bg-black relative overflow-hidden flex items-center justify-center border border-white/10">
                <img
                  src="/images/smart-farming.webp"
                  alt="Live Camera Vision Telemetry"
                  className="w-full h-full object-cover opacity-80"
                />

                {/* HUD Overlay Top Left */}
                <div className="absolute top-4 left-4 bg-[#0B1C10]/90 backdrop-blur-md px-3.5 py-1.5 rounded-xl text-[11px] font-mono text-[#D4E768] border border-white/10 flex items-center gap-3">
                  <span>FPS: 24.0</span>
                  <span>•</span>
                  <span>Laplacian Var: 210.4 (Passed)</span>
                  <span>•</span>
                  <span>Exposure: Nominal</span>
                </div>

                {/* Focus Reticle Overlay */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-52 h-52 border-2 border-dashed border-[#D4E768] rounded-2xl flex items-center justify-center relative">
                    <span className="text-[10px] font-mono font-bold text-[#D4E768] uppercase bg-[#0B1C10]/80 px-2 py-0.5 rounded border border-[#D4E768]/40">
                      Vision Focus Zone
                    </span>
                    <div className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-[#D4E768]" />
                    <div className="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-[#D4E768]" />
                    <div className="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-[#D4E768]" />
                    <div className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-[#D4E768]" />
                  </div>
                </div>

                {/* Bottom Prediction HUD */}
                <div className="absolute bottom-4 left-4 right-4 bg-[#0B1C10]/90 backdrop-blur-md p-4 rounded-2xl text-white border border-white/15 flex items-center justify-between">
                  <div className="space-y-0.5 text-left">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span className="text-sm font-bold text-white">Corn___healthy</span>
                    </div>
                    <p className="text-[10px] text-gray-300 font-mono">
                      Temporal Smoother: 5/5 Matching Frames
                    </p>
                  </div>

                  <div className="text-right">
                    <span className="text-lg font-mono font-extrabold text-[#D4E768]">98.4%</span>
                    <span className="block text-[9px] text-gray-400 uppercase font-mono">Confidence</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-gray-300 pt-2">
                <span>Direct browser video stream with zero plug-in requirements</span>
                <span className="text-[#D4E768] font-mono font-bold">OpenCV + PyTorch</span>
              </div>

            </div>
          </div>

        </div>

      </div>
    </section>
  );
};
