import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, ArrowUpRight } from 'lucide-react';
import { useHealth } from '../../context/HealthContext';

export const Footer: React.FC = () => {
  const { isModelSystemReady, isApiConnected } = useHealth();

  return (
    <footer className="w-full bg-[#0B1C10] text-[#FAFBF7] border-t border-white/10 pt-16 pb-12 px-6 sm:px-12 mt-20 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      <div className="max-w-7xl mx-auto space-y-12">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-10">
          {/* Brand Column */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-extrabold text-sm tracking-tight">
                AN
              </div>
              <span className="font-extrabold text-xl font-editorial tracking-tight text-white">
                AGRI NEXUS-AI
              </span>
            </div>

            <p className="text-xs text-white/70 leading-relaxed max-w-sm font-sans">
              "Intelligence rooted in the field." Unifying 7 machine learning models, OpenCV live vision, weather telemetry, and mandi market prices into one unified decision support platform.
            </p>

            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#112316] border border-[#D4E768]/30 text-xs text-[#D4E768]">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span className="font-bold">
                {isModelSystemReady && isApiConnected ? '● Systems Operational' : '● System Status Check'}
              </span>
            </div>
          </div>

          {/* Platform ML Services */}
          <div className="space-y-3">
            <h4 className="text-[11px] font-bold uppercase tracking-widest text-[#D4E768]">
              Platform Intelligence
            </h4>
            <ul className="space-y-2 text-xs text-white/70 font-sans">
              <li>
                <Link to="/crop" className="hover:text-[#D4E768] transition-colors flex items-center gap-1 group">
                  <span>Crop Recommendation</span>
                  <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              </li>
              <li>
                <Link to="/disease" className="hover:text-[#D4E768] transition-colors flex items-center gap-1 group">
                  <span>Plant Health Diagnostics</span>
                  <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              </li>
              <li>
                <Link to="/pest" className="hover:text-[#D4E768] transition-colors flex items-center gap-1 group">
                  <span>Pest Intelligence</span>
                  <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              </li>
              <li>
                <Link to="/fertilizer" className="hover:text-[#D4E768] transition-colors flex items-center gap-1 group">
                  <span>Fertilizer Advisor</span>
                  <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              </li>
              <li>
                <Link to="/irrigation" className="hover:text-[#D4E768] transition-colors flex items-center gap-1 group">
                  <span>Irrigation Predictor</span>
                  <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              </li>
              <li>
                <Link to="/soil" className="hover:text-[#D4E768] transition-colors flex items-center gap-1 group">
                  <span>Soil Analysis</span>
                  <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              </li>
              <li>
                <Link to="/yield" className="hover:text-[#D4E768] transition-colors flex items-center gap-1 group">
                  <span>Yield Forecasting</span>
                  <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              </li>
            </ul>
          </div>

          {/* Agronomic Signals */}
          <div className="space-y-3">
            <h4 className="text-[11px] font-bold uppercase tracking-widest text-[#D4E768]">
              Agronomic Signals
            </h4>
            <ul className="space-y-2 text-xs text-white/70 font-sans">
              <li>
                <Link to="/live" className="hover:text-[#D4E768] transition-colors">Camera Vision Studio</Link>
              </li>
              <li>
                <Link to="/weather" className="hover:text-[#D4E768] transition-colors">Weather Telemetry</Link>
              </li>
              <li>
                <Link to="/market" className="hover:text-[#D4E768] transition-colors">Mandi Market Prices</Link>
              </li>
              <li>
                <Link to="/crop-calendar" className="hover:text-[#D4E768] transition-colors">Crop Calendar Planner</Link>
              </li>
              <li>
                <Link to="/history" className="hover:text-[#D4E768] transition-colors">Analysis History</Link>
              </li>
            </ul>
          </div>

          {/* Account & Trust */}
          <div className="space-y-3">
            <h4 className="text-[11px] font-bold uppercase tracking-widest text-[#D4E768]">
              Account & System
            </h4>
            <ul className="space-y-2 text-xs text-white/70 font-sans">
              <li>
                <Link to="/dashboard" className="hover:text-[#D4E768] transition-colors">Command Dashboard</Link>
              </li>
              <li>
                <Link to="/profile" className="hover:text-[#D4E768] transition-colors">Farmer Profile</Link>
              </li>
              <li>
                <Link to="/settings" className="hover:text-[#D4E768] transition-colors">Platform Settings</Link>
              </li>
            </ul>
            <div className="pt-2 text-[10px] text-white/40 leading-relaxed font-sans">
              Models: ExtraTrees, ResNet18, LightGBM, MobileNetV3, XGBoost, OpenCV quality engine.
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between text-xs text-white/40 gap-4">
          <p>© 2026 AgriNexus-AI. All rights reserved. Precision Agricultural Intelligence.</p>
          <div className="flex items-center gap-6">
            <span>Model Scope & Limitations Enforced</span>
            <span>FastAPI ML Infrastructure</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
