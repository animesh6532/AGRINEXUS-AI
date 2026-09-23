import React from 'react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full glass-panel border-t border-slate-200/60 py-12 px-6 mt-16">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-agri-500 to-primary-600 flex items-center justify-center text-white text-sm font-bold">
              🌱
            </div>
            <span className="font-bold text-slate-900 tracking-tight text-base">AgriNexus-AI</span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            Smart agriculture decision-support platform integrating 7 frozen ML model artifacts, OpenCV live computer vision, weather, market, and crop calendar intelligence.
          </p>
        </div>

        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-3">ML Intelligence</h4>
          <ul className="space-y-2 text-xs text-slate-600">
            <li><Link to="/crop" className="hover:text-primary-600 transition-colors">Crop Recommendation</Link></li>
            <li><Link to="/disease" className="hover:text-primary-600 transition-colors">Plant Disease Detection</Link></li>
            <li><Link to="/pest" className="hover:text-primary-600 transition-colors">Pest Classification & Risk</Link></li>
            <li><Link to="/fertilizer" className="hover:text-primary-600 transition-colors">Fertilizer Advisor</Link></li>
            <li><Link to="/irrigation" className="hover:text-primary-600 transition-colors">Irrigation Predictor</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-3">Agronomic Signals</h4>
          <ul className="space-y-2 text-xs text-slate-600">
            <li><Link to="/weather" className="hover:text-primary-600 transition-colors">Weather Intelligence</Link></li>
            <li><Link to="/market" className="hover:text-primary-600 transition-colors">Market Mandi Prices</Link></li>
            <li><Link to="/crop-calendar" className="hover:text-primary-600 transition-colors">Crop Calendar</Link></li>
            <li><Link to="/live" className="hover:text-primary-600 transition-colors">Live Camera Vision</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-3">System & Security</h4>
          <p className="text-xs text-slate-500 mb-3 leading-relaxed">
            Powered by FastAPI backend running ExtraTrees, ResNet18, LightGBM, MobileNetV3, XGBoost, and OpenCV frame processors.
          </p>
          <div className="text-[10px] text-slate-400">
            University Final Project Scope • AgriNexus-AI © 2026
          </div>
        </div>
      </div>
    </footer>
  );
};
