import React from 'react';
import { Link } from 'react-router-dom';
import { Leaf } from 'lucide-react';
import { useHealth } from '../../context/HealthContext';

export const LandingFooter: React.FC = () => {
  const { isApiConnected, isModelSystemReady, modelStatus } = useHealth();

  const totalServices = modelStatus?.models ? Object.keys(modelStatus.models).length : 8;
  const readyServices = modelStatus?.models 
    ? Object.values(modelStatus.models).filter((m: any) => m.status === 'loaded' || m.status === 'healthy' || m === 'ready').length
    : (isModelSystemReady ? 8 : 0);

  return (
    <footer className="w-full bg-[#07120A] text-gray-300 border-t border-white/10 pt-20 pb-12 px-6 sm:px-12 text-left">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Main Footer Columns */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12">
          
          {/* Brand & Tagline Column (2 Cols) */}
          <div className="lg:col-span-2 space-y-5">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#D4E768] text-[#0B1C10] flex items-center justify-center font-bold shadow-lg">
                <Leaf className="w-5 h-5 fill-current" />
              </div>
              <div className="flex flex-col">
                <span className="font-extrabold text-xl text-white tracking-tight font-sans">
                  AgriNexus<span className="text-[#D4E768]">-AI</span>
                </span>
                <span className="text-[10px] font-semibold text-[#D4E768] uppercase tracking-widest">
                  Agricultural Intelligence
                </span>
              </div>
            </Link>

            <p className="text-xs text-gray-400 leading-relaxed max-w-sm font-normal">
              An integrated agricultural decision-support platform connecting 7 frozen machine learning artifacts, OpenCV quality-gated camera inspection, soil carbon analytics, weather telemetry, and mandi price series.
            </p>

            <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 pt-2">
              <span className={`w-2.5 h-2.5 rounded-full ${isApiConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span>{isApiConnected ? `${readyServices}/${totalServices} Services Online` : 'System Standby'}</span>
            </div>
          </div>

          {/* Column: Platform */}
          <div className="space-y-4">
            <h4 className="text-xs font-extrabold uppercase tracking-widest text-[#D4E768]">Platform</h4>
            <ul className="space-y-2.5 text-xs text-gray-300">
              <li>
                <Link to="/dashboard" className="hover:text-[#D4E768] transition-colors">
                  Overview Dashboard
                </Link>
              </li>
              <li>
                <Link to="/crop" className="hover:text-[#D4E768] transition-colors">
                  Crop Intelligence
                </Link>
              </li>
              <li>
                <Link to="/disease" className="hover:text-[#D4E768] transition-colors">
                  Plant Disease Diagnostics
                </Link>
              </li>
              <li>
                <Link to="/pest" className="hover:text-[#D4E768] transition-colors">
                  Pest Species & Risk
                </Link>
              </li>
              <li>
                <Link to="/fertilizer" className="hover:text-[#D4E768] transition-colors">
                  Fertilizer Formulations
                </Link>
              </li>
            </ul>
          </div>

          {/* Column: AI Intelligence */}
          <div className="space-y-4">
            <h4 className="text-xs font-extrabold uppercase tracking-widest text-[#D4E768]">AI Intelligence</h4>
            <ul className="space-y-2.5 text-xs text-gray-300">
              <li>
                <Link to="/live" className="hover:text-[#D4E768] transition-colors">
                  Live Camera Vision
                </Link>
              </li>
              <li>
                <Link to="/soil" className="hover:text-[#D4E768] transition-colors">
                  Soil Organic Carbon
                </Link>
              </li>
              <li>
                <Link to="/irrigation" className="hover:text-[#D4E768] transition-colors">
                  Irrigation Predictor
                </Link>
              </li>
              <li>
                <Link to="/yield" className="hover:text-[#D4E768] transition-colors">
                  Yield Uncertainty Bounds
                </Link>
              </li>
            </ul>
          </div>

          {/* Column: Field Tools & Resources */}
          <div className="space-y-4">
            <h4 className="text-xs font-extrabold uppercase tracking-widest text-[#D4E768]">Field Tools</h4>
            <ul className="space-y-2.5 text-xs text-gray-300">
              <li>
                <Link to="/weather" className="hover:text-[#D4E768] transition-colors">
                  Weather Telemetry
                </Link>
              </li>
              <li>
                <Link to="/market" className="hover:text-[#D4E768] transition-colors">
                  Mandi Market Trends
                </Link>
              </li>
              <li>
                <Link to="/crop-calendar" className="hover:text-[#D4E768] transition-colors">
                  Crop Calendar Schedule
                </Link>
              </li>
              <li>
                <a href="#transparency" className="hover:text-[#D4E768] transition-colors">
                  Model Transparency
                </a>
              </li>
              <li>
                <Link to="/login" className="hover:text-[#D4E768] transition-colors">
                  Sign In
                </Link>
              </li>
            </ul>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between text-xs text-gray-500 gap-4">
          <p>© {new Date().getFullYear()} AgriNexus-AI. All rights reserved.</p>
          <div className="flex items-center gap-6 font-mono text-[11px] text-gray-400">
            <span>VerdaAgro-Level Art Direction</span>
            <span>•</span>
            <span>AgriNexus-AI Technology</span>
          </div>
        </div>

      </div>
    </footer>
  );
};
