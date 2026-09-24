import React, { useState, useEffect } from 'react';
import {
  Sprout,
  AlertTriangle,
  Layers,
  Sparkles,
  CheckCircle2,
  RefreshCw,
  Scale
} from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { ConfidenceBar } from '../components/intelligence/ConfidenceBar';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';

import { useLocationContext } from '../context/LocationContext';
import { useSmartCropRecommendation, RecommendationMode } from '../hooks/useSmartCropRecommendation';
import { CropModeSwitcher } from '../components/crop/CropModeSwitcher';
import { FieldSnapshotPanel } from '../components/crop/FieldSnapshotPanel';
import { FeaturedCropCard } from '../components/crop/FeaturedCropCard';
import { AlternativeCropCard } from '../components/crop/AlternativeCropCard';
import { CropDetailModal } from '../components/crop/CropDetailModal';
import { CropCompareModal } from '../components/crop/CropCompareModal';
import { HybridOverrideDrawer } from '../components/crop/HybridOverrideDrawer';
import { LocationPicker } from '../components/location/LocationPicker';

import { api } from '../services/api';
import { CropRecommendationResponse, SmartCropRecommendationItem } from '../types/api';

export const CropPage: React.FC = () => {
  const { location, openPicker } = useLocationContext();

  const {
    mode,
    setMode,
    isAnalyzing,
    stages,
    result: smartResult,
    error: smartError,
    soilOverrides,
    setSoilOverrides,
    weatherOverrides,
    setWeatherOverrides,
    farmOverrides,
    setFarmOverrides,
    categoryFilter,
    setCategoryFilter,
    analyzeField,
  } = useSmartCropRecommendation();

  // Selected crop detail modal / drawer
  const [selectedCropDetail, setSelectedCropDetail] = useState<SmartCropRecommendationItem | null>(null);

  // Multi-Crop Comparison State
  const [comparedCrops, setComparedCrops] = useState<SmartCropRecommendationItem[]>([]);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState<boolean>(false);

  // Hybrid override drawer visibility
  const [isOverrideDrawerOpen, setIsOverrideDrawerOpen] = useState<boolean>(false);

  // Manual Mode State
  const [manualFormData, setManualFormData] = useState({
    N: 90.0,
    P: 42.0,
    K: 43.0,
    temperature: 20.87,
    humidity: 82.0,
    ph: 6.5,
    rainfall: 202.9,
  });

  const [manualLoading, setManualLoading] = useState<boolean>(false);
  const [manualResult, setManualResult] = useState<CropRecommendationResponse | null>(null);
  const [manualError, setManualError] = useState<string | null>(null);

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setManualLoading(true);
    setManualError(null);
    try {
      const res = await api.predictCrop(manualFormData);
      setManualResult(res);
    } catch (err: any) {
      setManualError(err.message || 'Failed to generate manual crop recommendation.');
    } finally {
      setManualLoading(false);
    }
  };

  const handleToggleCompare = (cropItem: SmartCropRecommendationItem) => {
    setComparedCrops((prev) => {
      const exists = prev.some((c) => c.crop === cropItem.crop);
      if (exists) {
        return prev.filter((c) => c.crop !== cropItem.crop);
      }
      if (prev.length >= 4) {
        alert('You can compare up to 4 crops simultaneously.');
        return prev;
      }
      return [...prev, cropItem];
    });
  };

  const handleRemoveCompare = (cropKey: string) => {
    setComparedCrops((prev) => prev.filter((c) => c.crop !== cropKey));
  };

  // Automatically trigger smart analysis when location is available on mount
  useEffect(() => {
    if (location && mode !== 'manual' && !smartResult && !isAnalyzing) {
      analyzeField(location);
    }
  }, [location, mode, smartResult, isAnalyzing, analyzeField]);

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Compact Editorial Hero Header */}
      <AgriculturalPageHero
        category="AGRICULTURAL SUITABILITY ADVISOR"
        title="Know What Your Field Can Grow."
        description="AgriNexus-AI combines field location, weather, soil and seasonal conditions to identify suitable crop options."
        imageSrc="/images/crop-intelligence.webp"
      />

      {/* Segmented Mode Control & Direct Analyze Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-6">
        <CropModeSwitcher mode={mode} onModeChange={setMode} />

        {location && mode !== 'manual' && (
          <Button
            type="button"
            variant="lime"
            size="md"
            className="shadow-sm hover:shadow-glow self-start sm:self-auto"
            isLoading={isAnalyzing}
            onClick={() => analyzeField(location)}
            icon={<Sparkles className="w-4 h-4 text-[#0B1C10]" />}
          >
            ANALYZE FIELD
          </Button>
        )}
      </div>

      {/* ============================================================ */}
      {/* 1. SMART AUTO / HYBRID MODES */}
      {/* ============================================================ */}
      {mode !== 'manual' && (
        <div className="space-y-8">
          {/* Unified Field Intelligence Snapshot Panel (Replaces 4 repetitive cards) */}
          <FieldSnapshotPanel
            location={location}
            smartResponse={smartResult}
            onOpenLocationPicker={openPicker}
            onOpenHybridEdit={() => setIsOverrideDrawerOpen(true)}
          />

          {/* Pipeline Stage Progress Bar During Analysis */}
          {isAnalyzing && (
            <GlassCard variant="solid" className="p-6 space-y-4 border-[#2F6B3C]/30 bg-white">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-widest text-[#2F6B3C] flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-[#2F6B3C]" />
                  Evaluating Field Agro-Ecological Suitability...
                </span>
                <span className="text-xs font-mono text-[#536056]">Smart Advisor Pipeline</span>
              </div>

              {/* Real Stages List */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                {stages.map((st) => (
                  <div
                    key={st.id}
                    className={`p-3 rounded-xl border flex items-center gap-2 transition-all ${
                      st.status === 'completed'
                        ? 'bg-[#EEF3E8] border-[#E2E7DA] text-[#2F6B3C] font-semibold'
                        : st.status === 'active'
                        ? 'bg-white border-[#2F6B3C] text-[#0B1C10] font-extrabold shadow-sm'
                        : st.status === 'failed'
                        ? 'bg-rose-50 border-rose-200 text-rose-800 font-semibold'
                        : 'bg-[#FAFBF7] border-gray-200 text-gray-400'
                    }`}
                  >
                    {st.status === 'completed' ? (
                      <CheckCircle2 className="w-4 h-4 text-[#2F6B3C] shrink-0" />
                    ) : st.status === 'active' ? (
                      <RefreshCw className="w-4 h-4 text-[#2F6B3C] animate-spin shrink-0" />
                    ) : (
                      <span className="w-4 h-4 rounded-full border border-gray-300 flex items-center justify-center text-[10px] text-gray-400 shrink-0">
                        •
                      </span>
                    )}
                    <span className="truncate">{st.label}</span>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}

          {/* Error State Banner */}
          {smartError && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
              <div className="flex-1">
                <span className="font-bold block">Field Analysis Error</span>
                <span>{smartError}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() => analyzeField(location)}
              >
                Retry Analysis
              </Button>
            </div>
          )}

          {/* RECOMMENDATION RESULTS */}
          {smartResult && (
            <div className="space-y-8 pt-2">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-4">
                <div>
                  <h2 className="text-2xl font-black font-editorial text-[#0B1C10] tracking-tight">
                    CROPS SUITED TO YOUR FIELD
                  </h2>
                  <p className="text-xs text-[#536056] mt-0.5">
                    Evaluated against field location ({smartResult.location.display_name}), weather, soil, and seasonal conditions ({smartResult.season.season}).
                  </p>
                </div>

                {/* Category Filter Pills */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
                  {['all', 'cereal', 'pulse', 'fruit', 'cash_crop', 'oilseed', 'vegetable'].map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => setCategoryFilter(cat)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold capitalize transition-all whitespace-nowrap ${
                        categoryFilter === cat
                          ? 'bg-[#2F6B3C] text-white shadow-sm'
                          : 'bg-[#EEF3E8] text-[#536056] hover:text-[#0B1C10] hover:bg-[#E2E7DA]'
                      }`}
                    >
                      {cat.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              {/* Multi-Crop Comparison Floating Action Bar */}
              {comparedCrops.length > 0 && (
                <div className="sticky top-4 z-40 p-4 rounded-2xl bg-[#0B1C10] text-white shadow-2xl flex items-center justify-between gap-4 border border-[#2F6B3C]/50 animate-fade-in">
                  <div className="flex items-center gap-3">
                    <Scale className="w-5 h-5 text-[#D4E768]" />
                    <div>
                      <span className="text-xs font-bold text-white block">
                        {comparedCrops.length} Crops Selected for Comparison
                      </span>
                      <span className="text-[10px] text-[#A2B5A5] truncate max-w-md block">
                        {comparedCrops.map((c) => c.display_name).join(', ')}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setComparedCrops([])}
                      className="px-3 py-1.5 text-xs text-[#A2B5A5] hover:text-white"
                    >
                      Clear
                    </button>
                    <Button
                      type="button"
                      variant="lime"
                      size="sm"
                      onClick={() => setIsCompareModalOpen(true)}
                    >
                      Compare Side-by-Side
                    </Button>
                  </div>
                </div>
              )}

              {/* Hierarchical Recommendation Presentation */}
              {smartResult.recommendations.length > 0 && (
                <div className="space-y-8">
                  {/* FEATURED TOP RECOMMENDATION (#1) */}
                  <div className="space-y-3">
                    <FeaturedCropCard
                      item={smartResult.recommendations[0]}
                      onOpenDetail={setSelectedCropDetail}
                      isCompared={comparedCrops.some((c) => c.crop === smartResult.recommendations[0].crop)}
                      onToggleCompare={handleToggleCompare}
                    />
                  </div>

                  {/* ALTERNATIVE CROP OPTIONS GRID (#2 to #N) */}
                  {smartResult.recommendations.length > 1 && (
                    <div className="space-y-4 pt-6 border-t border-[#E2E7DA]">
                      <div className="flex items-center justify-between">
                        <h3 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                          OTHER SUITABLE CROP OPTIONS ({smartResult.recommendations.length - 1})
                        </h3>
                        <span className="text-xs text-[#536056]">
                          Click "Compare" to analyze crops side-by-side
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {smartResult.recommendations.slice(1).map((item, idx) => (
                          <AlternativeCropCard
                            key={item.crop}
                            rank={idx + 2}
                            item={item}
                            onOpenDetail={setSelectedCropDetail}
                            isCompared={comparedCrops.some((c) => c.crop === item.crop)}
                            onToggleCompare={handleToggleCompare}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Data Provenance & Engine Sources */}
              <GlassCard variant="solid" className="p-6 space-y-4 text-xs bg-[#FAFBF7]">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#536056] border-b border-[#E2E7DA] pb-2">
                  TRANSPARENT DATA PROVENANCE & ENGINE SOURCES
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-white border border-[#E2E7DA]">
                    <span className="text-[10px] text-[#536056] font-bold block uppercase">Weather Telemetry</span>
                    <span className="font-extrabold text-[#0B1C10] block">{smartResult.weather.source}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-[#E2E7DA]">
                    <span className="text-[10px] text-[#536056] font-bold block uppercase">Soil Context</span>
                    <span className="font-extrabold text-[#0B1C10] block">{smartResult.soil.data_source}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-[#E2E7DA]">
                    <span className="text-[10px] text-[#536056] font-bold block uppercase">Crop Calendar</span>
                    <span className="font-extrabold text-[#0B1C10] block">{smartResult.season.source}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-[#E2E7DA]">
                    <span className="text-[10px] text-[#536056] font-bold block uppercase">Crop Profiles</span>
                    <span className="font-extrabold text-[#0B1C10] block">FAO ECOCROP & ICAR Guidelines</span>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-[#E2E7DA]">
                    <span className="text-[10px] text-[#536056] font-bold block uppercase">ML Artifact</span>
                    <span className="font-extrabold text-[#0B1C10] block">
                      {smartResult.ml_status.available ? 'ExtraTrees Classifier Active' : 'ML Incomplete Input'}
                    </span>
                  </div>
                </div>

                <div className="pt-2 text-[11px] text-[#536056] space-y-1 border-t border-[#E2E7DA]/60 leading-relaxed">
                  <p>• <strong>Decision Support:</strong> AgriNexus-AI suitability scores are decision support indicators, not farming guarantees.</p>
                  <p>• <strong>Soil Data:</strong> Geospatial soil information represents a 250m regional estimate. NPK and pH values should be verified with a lab soil test.</p>
                  <p>• <strong>ML Model:</strong> Machine learning recommendations are limited to the 22 supported model classes. Environmental suitability evaluates the full 26-crop catalogue.</p>
                </div>
              </GlassCard>
            </div>
          )}
        </div>
      )}

      {/* ============================================================ */}
      {/* 2. MANUAL MODE (Legacy ML Form) */}
      {/* ============================================================ */}
      {mode === 'manual' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-6">
            <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5 bg-white">
              <div className="flex items-center gap-2 border-b border-[#E2E7DA] pb-4">
                <Layers className="w-5 h-5 text-[#2F6B3C]" />
                <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                  Manual Agronomic Parameters
                </h3>
              </div>

              <form onSubmit={handleManualSubmit} className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  <Input
                    label="Nitrogen (N)"
                    type="number"
                    step="0.1"
                    value={manualFormData.N}
                    onChange={(e) => setManualFormData({ ...manualFormData, N: parseFloat(e.target.value) || 0 })}
                    required
                  />
                  <Input
                    label="Phosphorus (P)"
                    type="number"
                    step="0.1"
                    value={manualFormData.P}
                    onChange={(e) => setManualFormData({ ...manualFormData, P: parseFloat(e.target.value) || 0 })}
                    required
                  />
                  <Input
                    label="Potassium (K)"
                    type="number"
                    step="0.1"
                    value={manualFormData.K}
                    onChange={(e) => setManualFormData({ ...manualFormData, K: parseFloat(e.target.value) || 0 })}
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Temperature"
                    type="number"
                    step="0.01"
                    unit="°C"
                    value={manualFormData.temperature}
                    onChange={(e) => setManualFormData({ ...manualFormData, temperature: parseFloat(e.target.value) || 0 })}
                    required
                  />
                  <Input
                    label="Humidity"
                    type="number"
                    step="0.1"
                    unit="%"
                    value={manualFormData.humidity}
                    onChange={(e) => setManualFormData({ ...manualFormData, humidity: parseFloat(e.target.value) || 0 })}
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Soil pH"
                    type="number"
                    step="0.1"
                    min="0"
                    max="14"
                    value={manualFormData.ph}
                    onChange={(e) => setManualFormData({ ...manualFormData, ph: parseFloat(e.target.value) || 0 })}
                    required
                  />
                  <Input
                    label="Rainfall"
                    type="number"
                    step="0.1"
                    unit="mm"
                    value={manualFormData.rainfall}
                    onChange={(e) => setManualFormData({ ...manualFormData, rainfall: parseFloat(e.target.value) || 0 })}
                    required
                  />
                </div>

                <Button
                  type="submit"
                  variant="lime"
                  size="lg"
                  className="w-full mt-2 shadow-md hover:shadow-glow"
                  isLoading={manualLoading}
                  icon={<Sprout className="w-4 h-4 text-[#0B1C10]" />}
                >
                  RECOMMEND CROPS
                </Button>
              </form>
            </GlassCard>

            <ScopeWarning
              message="Manual mode evaluates ExtraTrees multi-class classification over soil NPK and climate features directly. Use Smart Auto or Hybrid mode for location, weather, and seasonal intelligence."
              type="info"
            />
          </div>

          <div className="lg:col-span-7 space-y-6">
            {manualError && (
              <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{manualError}</span>
              </div>
            )}

            {manualResult ? (
              <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6 bg-white">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-6">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                      RECOMMENDED CROP SPECIES
                    </span>
                    <h2 className="text-4xl font-black font-editorial text-[#0B1C10] capitalize mt-1 flex items-center gap-3">
                      <Sprout className="w-8 h-8 text-[#2F6B3C]" />
                      {manualResult.prediction}
                    </h2>
                  </div>

                  <div className="sm:text-right">
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
                      manualResult.is_plausible
                        ? 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                        : 'bg-amber-500/10 text-amber-800 border border-amber-500/20'
                    }`}>
                      {manualResult.is_plausible ? '● Plausible Profile' : '● Out of Distribution'}
                    </span>
                    <p className="text-[10px] text-[#536056] mt-1 font-mono">{manualResult.anomaly_status}</p>
                  </div>
                </div>

                <ConfidenceBar confidence={manualResult.confidence} label="ExtraTrees Model Confidence" />

                {manualResult.top_k_predictions && manualResult.top_k_predictions.length > 0 && (
                  <div className="space-y-3 pt-4">
                    <h4 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                      Top Alternative Crop Matches
                    </h4>
                    <div className="space-y-2">
                      {manualResult.top_k_predictions.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-3.5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-semibold text-[#162018]"
                        >
                          <span className="capitalize flex items-center gap-2.5">
                            <span className="w-6 h-6 rounded-full bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center text-xs font-extrabold">
                              {idx + 1}
                            </span>
                            {item.crop}
                          </span>
                          <span className="font-mono font-extrabold text-[#2F6B3C]">
                            {(item.probability * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </GlassCard>
            ) : (
              <div className="relative rounded-3xl overflow-hidden border border-[#E2E7DA] bg-[#FAFBF7] p-8 sm:p-12 text-center space-y-6 flex flex-col items-center justify-center min-h-[380px] group">
                <div className="w-full h-full absolute inset-0 z-0 opacity-15 overflow-hidden">
                  <img
                    src="/images/crop-intelligence.webp"
                    alt="Crop preview background"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                  />
                </div>

                <div className="relative z-10 w-14 h-14 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-extrabold text-xl shadow-sm">
                  <Sprout className="w-7 h-7" />
                </div>

                <div className="relative z-10 space-y-2 max-w-md">
                  <h3 className="text-xl font-extrabold font-editorial text-[#0B1C10]">
                    Ready for Manual ML Inference
                  </h3>
                  <p className="text-xs text-[#536056] leading-relaxed">
                    Enter your soil NPK nutrients, pH, and local weather telemetry on the left to evaluate crop suitability across 22 major crop species.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODALS & DRAWERS */}
      <LocationPicker />

      <CropDetailModal
        item={selectedCropDetail}
        onClose={() => setSelectedCropDetail(null)}
      />

      {isCompareModalOpen && (
        <CropCompareModal
          crops={comparedCrops}
          onClose={() => setIsCompareModalOpen(false)}
          onRemoveCrop={handleRemoveCompare}
        />
      )}

      <HybridOverrideDrawer
        isOpen={isOverrideDrawerOpen}
        onClose={() => setIsOverrideDrawerOpen(false)}
        soilOverrides={soilOverrides}
        onSoilChange={setSoilOverrides}
        weatherOverrides={weatherOverrides}
        onWeatherChange={setWeatherOverrides}
        farmOverrides={farmOverrides}
        onFarmChange={setFarmOverrides}
        onApplyAndAnalyze={() => {
          if (location) analyzeField(location);
        }}
      />
    </div>
  );
};
