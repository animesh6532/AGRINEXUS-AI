import React from 'react';
import { MapPin, Plus, Check, X, Building2 } from 'lucide-react';
import { useFarmerProfile } from '../../context/FarmerProfileContext';
import { Button } from '../ui/Button';

interface FarmSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenAddFarm: () => void;
}

export const FarmSelectorModal: React.FC<FarmSelectorModalProps> = ({
  isOpen,
  onClose,
  onOpenAddFarm,
}) => {
  const { farms, selectedFarm, selectFarm } = useFarmerProfile();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg bg-[#FAFBF7] rounded-3xl border border-[#E2E7DA] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 bg-[#0B1C10] text-[#FAFBF7] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#D4E768]/20 text-[#D4E768] flex items-center justify-center font-bold">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-extrabold font-editorial text-white">Select Active Farm</h3>
              <p className="text-xs text-white/70">
                Choose which farm's location, soil, crops, and weather to monitor
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-white/10 text-white/70 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Farm List */}
        <div className="p-6 overflow-y-auto space-y-3 flex-1">
          {farms && farms.length > 0 ? (
            farms.map((farm) => {
              const isSelected = selectedFarm?.id === farm.id;
              return (
                <div
                  key={farm.id}
                  onClick={() => {
                    selectFarm(farm);
                    onClose();
                  }}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between group ${
                    isSelected
                      ? 'bg-[#EEF3E8] border-[#2F6B3C] shadow-sm'
                      : 'bg-white border-[#E2E7DA] hover:border-[#2F6B3C]/50 hover:bg-[#EEF3E8]/40'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0 pr-2">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 font-bold text-xs ${
                        isSelected
                          ? 'bg-[#2F6B3C] text-white'
                          : 'bg-[#0B1C10]/5 text-[#0B1C10] group-hover:bg-[#2F6B3C]/10'
                      }`}
                    >
                      <MapPin className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="font-extrabold text-[#0B1C10] font-editorial text-sm truncate">
                          {farm.farm_name}
                        </h4>
                        {isSelected && (
                          <span className="px-2 py-0.5 rounded-full bg-[#2F6B3C] text-white text-[10px] font-bold">
                            Active
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[#536056] truncate">
                        {farm.location_name || 'Location Unspecified'} • {farm.area_value} {farm.area_unit} ({farm.fields?.length || 0} fields)
                      </p>
                      <p className="text-[10px] text-[#536056]/80 font-mono">
                        GPS: {farm.latitude.toFixed(4)}° N, {farm.longitude.toFixed(4)}° E
                      </p>
                    </div>
                  </div>

                  <div
                    className={`w-6 h-6 rounded-full border flex items-center justify-center shrink-0 transition-colors ${
                      isSelected
                        ? 'bg-[#2F6B3C] border-[#2F6B3C] text-white'
                        : 'border-[#E2E7DA] text-transparent group-hover:border-[#2F6B3C]'
                    }`}
                  >
                    <Check className="w-3.5 h-3.5" />
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center py-8 space-y-3">
              <Building2 className="w-12 h-12 text-[#2F6B3C] mx-auto opacity-50" />
              <h4 className="text-base font-bold text-[#0B1C10]">No Farms Configured Yet</h4>
              <p className="text-xs text-[#536056] max-w-xs mx-auto">
                Add your first farm to unlock farm-specific weather, soil, crop, and market intelligence.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#EEF3E8] border-t border-[#E2E7DA] flex items-center justify-between">
          <Button
            onClick={() => {
              onClose();
              onOpenAddFarm();
            }}
            variant="lime"
            size="sm"
            icon={<Plus className="w-4 h-4" />}
          >
            Add New Farm
          </Button>

          <Button onClick={onClose} variant="secondary" size="sm">
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};
