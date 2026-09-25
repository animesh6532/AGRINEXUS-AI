import React from 'react';
import { X, Sliders, Check } from 'lucide-react';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { SoilOverrides, WeatherOverrides, FarmOverrides } from '../../hooks/useSmartCropRecommendation';

interface HybridOverrideDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  soilOverrides: SoilOverrides;
  onSoilChange: (soil: SoilOverrides) => void;
  weatherOverrides: WeatherOverrides;
  onWeatherChange: (weather: WeatherOverrides) => void;
  farmOverrides: FarmOverrides;
  onFarmChange: (farm: FarmOverrides) => void;
  onApplyAndAnalyze: () => void;
}

export const HybridOverrideDrawer: React.FC<HybridOverrideDrawerProps> = ({
  isOpen,
  onClose,
  soilOverrides,
  onSoilChange,
  weatherOverrides,
  onWeatherChange,
  farmOverrides,
  onFarmChange,
  onApplyAndAnalyze,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-[#FAFBF7] h-full border-l border-[#E2E7DA] p-6 sm:p-8 space-y-6 overflow-y-auto flex flex-col justify-between shadow-2xl selection:bg-[#D4E768] selection:text-[#0B1C10]">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
            <div className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-[#2F6B3C]" />
              <h3 className="text-lg font-extrabold font-editorial text-[#0B1C10]">
                Field Parameter Adjustments
              </h3>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <p className="text-xs text-[#536056] leading-relaxed">
            Override estimated values with your lab soil test results or field measurements. User-provided values take immediate priority.
          </p>

          {/* 1. Measured Soil Nutrients & pH */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-[#E2E7DA]/60 pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0B1C10]">
                Soil Test Values (Lab / Measured)
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-800 border border-amber-500/20">
                User Measured
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Nitrogen (N)"
                type="number"
                step="1"
                placeholder="e.g. 90"
                unit="mg/kg"
                value={soilOverrides.nitrogen ?? ''}
                onChange={(e) =>
                  onSoilChange({
                    ...soilOverrides,
                    nitrogen: e.target.value ? parseFloat(e.target.value) : null,
                  })
                }
              />
              <Input
                label="Soil pH"
                type="number"
                step="0.1"
                placeholder="e.g. 6.5"
                value={soilOverrides.ph ?? ''}
                onChange={(e) =>
                  onSoilChange({
                    ...soilOverrides,
                    ph: e.target.value ? parseFloat(e.target.value) : null,
                  })
                }
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Phosphorus (P)"
                type="number"
                step="1"
                placeholder="e.g. 42"
                unit="mg/kg"
                value={soilOverrides.phosphorus ?? ''}
                onChange={(e) =>
                  onSoilChange({
                    ...soilOverrides,
                    phosphorus: e.target.value ? parseFloat(e.target.value) : null,
                  })
                }
              />
              <Input
                label="Potassium (K)"
                type="number"
                step="1"
                placeholder="e.g. 43"
                unit="mg/kg"
                value={soilOverrides.potassium ?? ''}
                onChange={(e) =>
                  onSoilChange({
                    ...soilOverrides,
                    potassium: e.target.value ? parseFloat(e.target.value) : null,
                  })
                }
              />
            </div>
          </div>

          {/* 2. Water Availability & Farm Size */}
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-[#E2E7DA]/60 pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0B1C10]">
                Farm Water & Area
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-800 border border-emerald-500/20">
                Management
              </span>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[#0B1C10] block">Water Availability</label>
              <select
                value={farmOverrides.water_availability}
                onChange={(e) => onFarmChange({ ...farmOverrides, water_availability: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E2E7DA] text-xs font-semibold text-[#0B1C10] focus:ring-2 focus:ring-[#2F6B3C] focus:outline-none"
              >
                <option value="unknown">Unknown / Not Specified</option>
                <option value="Rainfed">Rainfed (Dependent on Monsoon)</option>
                <option value="Limited Irrigation">Limited Irrigation (Canal / Tube-well)</option>
                <option value="Irrigated">Fully Irrigated (Drip / Sprinkler)</option>
              </select>
            </div>

            <Input
              label="Farm Area (Optional)"
              type="number"
              step="0.5"
              placeholder="e.g. 2.5"
              unit="acres"
              value={farmOverrides.area_acres ?? ''}
              onChange={(e) =>
                onFarmChange({
                  ...farmOverrides,
                  area_acres: e.target.value ? parseFloat(e.target.value) : null,
                })
              }
            />
          </div>

          {/* 3. Weather Overrides */}
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-[#E2E7DA]/60 pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0B1C10]">
                Weather Overrides
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-800 border border-blue-500/20">
                Optional
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Temperature"
                type="number"
                step="0.1"
                placeholder="Auto"
                unit="°C"
                value={weatherOverrides.temperature ?? ''}
                onChange={(e) =>
                  onWeatherChange({
                    ...weatherOverrides,
                    temperature: e.target.value ? parseFloat(e.target.value) : null,
                  })
                }
              />
              <Input
                label="Humidity"
                type="number"
                step="1"
                placeholder="Auto"
                unit="%"
                value={weatherOverrides.humidity ?? ''}
                onChange={(e) =>
                  onWeatherChange({
                    ...weatherOverrides,
                    humidity: e.target.value ? parseFloat(e.target.value) : null,
                  })
                }
              />
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-[#E2E7DA] space-y-2">
          <Button
            type="button"
            variant="lime"
            size="lg"
            className="w-full shadow-md"
            icon={<Check className="w-4 h-4" />}
            onClick={() => {
              onApplyAndAnalyze();
              onClose();
            }}
          >
            Apply Overrides & Analyze
          </Button>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="w-full text-xs text-[#536056]"
            onClick={() => {
              onSoilChange({ nitrogen: null, phosphorus: null, potassium: null, ph: null });
              onWeatherChange({ temperature: null, humidity: null, rainfall: null });
              onFarmChange({ area_acres: null, water_availability: 'unknown' });
            }}
          >
            Reset All Overrides
          </Button>
        </div>
      </div>
    </div>
  );
};
