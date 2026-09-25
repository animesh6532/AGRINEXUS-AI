import React from 'react';
import { Sparkles, Sliders, Calculator } from 'lucide-react';
import { RecommendationMode } from '../../hooks/useSmartCropRecommendation';

interface CropModeSwitcherProps {
  mode: RecommendationMode;
  onModeChange: (mode: RecommendationMode) => void;
}

export const CropModeSwitcher: React.FC<CropModeSwitcherProps> = ({ mode, onModeChange }) => {
  return (
    <div className="space-y-3">
      <div className="inline-flex p-1.5 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] shadow-inner gap-1.5 w-full sm:w-auto">
        <button
          type="button"
          onClick={() => onModeChange('auto')}
          className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-extrabold transition-all duration-200 ${
            mode === 'auto'
              ? 'bg-[#2F6B3C] text-white shadow-md'
              : 'text-[#536056] hover:text-[#0B1C10] hover:bg-white/50'
          }`}
        >
          <Sparkles className="w-4 h-4 text-[#D4E768]" />
          <span>SMART AUTO</span>
        </button>

        <button
          type="button"
          onClick={() => onModeChange('hybrid')}
          className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-extrabold transition-all duration-200 ${
            mode === 'hybrid'
              ? 'bg-[#2F6B3C] text-white shadow-md'
              : 'text-[#536056] hover:text-[#0B1C10] hover:bg-white/50'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>HYBRID</span>
          <span className="px-1.5 py-0.5 rounded-md text-[10px] bg-emerald-500/20 text-emerald-200 border border-emerald-400/30">
            Recommended
          </span>
        </button>

        <button
          type="button"
          onClick={() => onModeChange('manual')}
          className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-extrabold transition-all duration-200 ${
            mode === 'manual'
              ? 'bg-[#2F6B3C] text-white shadow-md'
              : 'text-[#536056] hover:text-[#0B1C10] hover:bg-white/50'
          }`}
        >
          <Calculator className="w-4 h-4" />
          <span>MANUAL</span>
        </button>
      </div>

      <div className="text-xs text-[#536056] bg-[#FAFBF7] p-3 rounded-xl border border-[#E2E7DA]/60">
        {mode === 'auto' && (
          <p>
            <strong>Smart Auto Mode:</strong> Automatically evaluates field coordinates, Open-Meteo weather telemetry, SoilGrids 250m geospatial soil estimates, and regional season engine.
          </p>
        )}
        {mode === 'hybrid' && (
          <p>
            <strong>Hybrid Mode:</strong> Automatically detects location, weather, and soil context while allowing you to edit or enter lab-measured soil test values (NPK, pH, water availability).
          </p>
        )}
        {mode === 'manual' && (
          <p>
            <strong>Manual Mode:</strong> Legacy ML inference workflow. Enter exact N, P, K, temperature, humidity, pH, and rainfall directly into the frozen ExtraTrees classifier.
          </p>
        )}
      </div>
    </div>
  );
};
