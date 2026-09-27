import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Sprout,
  Calendar,
  Clock,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Info
} from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Select } from '../components/ui/Select';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import { api } from '../services/api';
import { CropScheduleResponse, CropCatalogEntry, CropCatalogResponse } from '../types/api';

// Verified reference crops bundled in AGRINEXUS backend with agronomic calendars
interface VerifiedCropMetadata {
  id: string;
  label: string;
  seasons: string[];
  typicalDuration: string;
  defaultSowingDate: string;
  sowingWindowDisplay: string;
  recommendedDate: string;
  recommendedAction: string;
  description: string;
}

const VERIFIED_REFERENCE_CROPS: VerifiedCropMetadata[] = [
  {
    id: 'rice',
    label: 'Rice / Paddy',
    seasons: ['Kharif', 'Rabi'],
    typicalDuration: '130 - 135 Days',
    defaultSowingDate: '2026-06-15',
    sowingWindowDisplay: 'June 1 – July 15 (Kharif) / November 15 – January 15 (Rabi)',
    recommendedDate: '2026-06-15',
    recommendedAction: 'Rice requires standing water during early vegetative stages. Align your sowing date with either the Kharif monsoon onset (June–July) or assured winter irrigation for Rabi (Nov–Jan).',
    description: 'Transplanted Kharif/Rabi paddy with 6 defined growth stages from nursery sowing to maturity.',
  },
  {
    id: 'wheat',
    label: 'Wheat',
    seasons: ['Rabi'],
    typicalDuration: '130 Days',
    defaultSowingDate: '2026-11-15',
    sowingWindowDisplay: 'November 1 – December 15 (Rabi)',
    recommendedDate: '2026-11-15',
    recommendedAction: 'Wheat requires cool weather during crown-root initiation and tillering. Sowing outside winter months leads to terminal heat stress. Shift sowing date to mid-November.',
    description: 'Rabi cereal with crown-root initiation, tillering, jointing, flowering, and grain filling stages.',
  },
  {
    id: 'maize',
    label: 'Maize',
    seasons: ['Kharif'],
    typicalDuration: '100 Days',
    defaultSowingDate: '2026-06-20',
    sowingWindowDisplay: 'June 15 – July 15 (Kharif)',
    recommendedDate: '2026-06-20',
    recommendedAction: 'Maize requires adequate soil moisture during vegetative and tasseling phases. Align sowing date with Kharif rainfall onset in late June or early July.',
    description: 'Medium-duration Kharif crop structured across emergence, vegetative, tasseling, silking, and maturity.',
  },
  {
    id: 'cotton',
    label: 'Cotton',
    seasons: ['Kharif'],
    typicalDuration: '170 Days',
    defaultSowingDate: '2026-05-25',
    sowingWindowDisplay: 'May 15 – June 30 (Kharif)',
    recommendedDate: '2026-05-25',
    recommendedAction: 'Cotton in northern and western India requires early sowing in mid-May to June to establish strong roots before peak monsoon and ensure adequate boll opening before winter.',
    description: 'Commercial fiber crop covering emergence, squaring, boll formation, and multi-flush harvesting.',
  },
];

type ErrorCategory = 'unsupported_crop' | 'season_mismatch' | 'validation_error' | 'provider_error' | 'generic_error';

export const CropCalendarPageContent: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // URL query params synchronization
  const paramCrop = (searchParams.get('crop') || 'rice').toLowerCase().trim();
  const paramDate = searchParams.get('sowing_date') || '2026-06-15';

  const [crop, setCrop] = useState<string>(paramCrop);
  const [sowingDate, setSowingDate] = useState<string>(paramDate);
  const [schedule, setSchedule] = useState<CropScheduleResponse | null>(null);
  const [catalog, setCatalog] = useState<CropCatalogEntry[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [errorCategory, setErrorCategory] = useState<ErrorCategory | null>(null);

  // Sync state if URL search parameters change externally
  useEffect(() => {
    if (paramCrop && paramCrop !== crop) {
      setCrop(paramCrop);
    }
    if (paramDate && paramDate !== sowingDate) {
      setSowingDate(paramDate);
    }
  }, [paramCrop, paramDate]);

  // Load backend crop catalogue on mount to know active supported crops dynamically
  useEffect(() => {
    let isMounted = true;
    async function loadCatalogue() {
      try {
        const res: CropCatalogResponse = await api.getCropCalendarCatalogue();
        if (isMounted && res && Array.isArray(res.crops)) {
          setCatalog(res.crops);
        }
      } catch (err) {
        // Fall back gracefully to verified reference crops constant
        console.warn('Could not load dynamic crop catalogue, using verified reference list.', err);
      }
    }
    loadCatalogue();
    return () => {
      isMounted = false;
    };
  }, []);

  // Update URL search parameters when crop or date changes
  const updateUrlParams = useCallback((newCrop: string, newDate: string) => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set('crop', newCrop);
        next.set('sowing_date', newDate);
        return next;
      },
      { replace: true }
    );
  }, [setSearchParams]);

  // Fetch derived crop schedule
  const fetchSchedule = useCallback(async () => {
    if (!crop || !sowingDate) {
      setError('Crop name and a valid sowing date are required.');
      setErrorCategory('validation_error');
      setSchedule(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    setErrorCategory(null);

    try {
      const res = await api.getCropSchedule(crop, sowingDate);
      setSchedule(res);
    } catch (err: any) {
      setSchedule(null);
      const rawMessage = err?.message || 'Failed to fetch crop schedule.';
      const status = err?.statusCode || 0;
      const lowerMsg = rawMessage.toLowerCase();

      // Categorize error for tailored friendly UI
      if (status === 404 || lowerMsg.includes('unsupported crop') || lowerMsg.includes('not available') || lowerMsg.includes('not found')) {
        setErrorCategory('unsupported_crop');
        setError(rawMessage);
      } else if (
        status === 400 ||
        lowerMsg.includes('does not have a') ||
        lowerMsg.includes('calendar for a sowing date') ||
        lowerMsg.includes('available seasons')
      ) {
        // Agronomic seasonal constraint validation preserved
        setErrorCategory('season_mismatch');
        setError(rawMessage);
      } else if (status === 422 || lowerMsg.includes('valid date') || lowerMsg.includes('field required')) {
        setErrorCategory('validation_error');
        setError(rawMessage);
      } else if (status === 502 || status === 503 || lowerMsg.includes('provider') || lowerMsg.includes('gateway')) {
        setErrorCategory('provider_error');
        setError('The crop calendar data provider is currently unavailable. Please try again shortly.');
      } else {
        setErrorCategory('generic_error');
        setError(rawMessage);
      }
    } finally {
      setIsLoading(false);
    }
  }, [crop, sowingDate]);

  useEffect(() => {
    fetchSchedule();
  }, [fetchSchedule]);

  // Handle crop change from dropdown
  const handleCropChange = (selectedCrop: string) => {
    setCrop(selectedCrop);
    updateUrlParams(selectedCrop, sowingDate);
  };

  // Handle date change
  const handleDateChange = (newDate: string) => {
    setSowingDate(newDate);
    updateUrlParams(crop, newDate);
  };

  // Switch to supported crop handler
  const handleSwitchToCrop = (newCropId: string, defaultDate?: string) => {
    const nextDate = defaultDate || sowingDate;
    setCrop(newCropId);
    if (defaultDate) {
      setSowingDate(defaultDate);
    }
    updateUrlParams(newCropId, nextDate);
  };

  // Active crop metadata from reference database
  const activeCropMeta = useMemo(() => {
    return VERIFIED_REFERENCE_CROPS.find((c) => c.id === crop.toLowerCase()) || null;
  }, [crop]);

  // Build Select options list
  const selectOptions = useMemo(() => {
    const knownCrops = new Set(VERIFIED_REFERENCE_CROPS.map((c) => c.id));
    const options = VERIFIED_REFERENCE_CROPS.map((c) => ({
      value: c.id,
      label: c.label,
    }));

    // If active crop in state is not in verified list, include it as an explicitly marked option
    if (!knownCrops.has(crop.toLowerCase())) {
      const display = crop.charAt(0).toUpperCase() + crop.slice(1);
      options.push({
        value: crop,
        label: `${display} (Calendar Unavailable)`,
      });
    }

    return options;
  }, [crop]);

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* 1. Page Hero */}
      <AgriculturalPageHero
        category="FIELD SIGNALS"
        title="Field Season Calendar & Growth Planner"
        description="Calculate growth stages, sowing window compliance, field tasks, and estimated harvest dates dynamically from sowing date."
        imageSrc="/images/crop-calendar.webp"
      >
        <div className="space-y-3">
          <div className="flex items-center gap-3 bg-black/40 backdrop-blur-md p-2.5 rounded-2xl border border-white/10 flex-wrap">
            <div className="min-w-[180px]">
              <Select
                value={crop}
                onChange={(e) => handleCropChange(e.target.value)}
                options={selectOptions}
                className="text-xs bg-white text-[#0B1C10] font-semibold"
              />
            </div>
            <Input
              type="date"
              value={sowingDate}
              onChange={(e) => handleDateChange(e.target.value)}
              className="w-44 text-xs bg-[#0B1C10] text-[#FAFBF7] border-white/20 font-mono"
              aria-label="Sowing Date"
            />
            <Button
              variant="secondary"
              size="sm"
              onClick={fetchSchedule}
              disabled={isLoading}
              icon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
            >
              {isLoading ? 'Recalculating...' : 'Update Plan'}
            </Button>
          </div>

          {/* Quick interactive test chips */}
          <div className="flex items-center gap-2 text-xs text-white/80 pt-0.5 flex-wrap">
            <span className="text-[11px] font-medium text-white/60">Quick test:</span>
            <button
              type="button"
              onClick={() => {
                setCrop('rice');
                setSowingDate('2026-06-15');
                updateUrlParams('rice', '2026-06-15');
              }}
              className={`px-2.5 py-0.5 rounded-lg text-[11px] font-semibold transition-all ${
                crop === 'rice' && sowingDate === '2026-06-15'
                  ? 'bg-[#D4E768] text-[#0B1C10] font-bold shadow-sm'
                  : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
            >
              Rice (June 15 • Valid)
            </button>
            <button
              type="button"
              onClick={() => {
                setCrop('cotton');
                setSowingDate('2026-05-25');
                updateUrlParams('cotton', '2026-05-25');
              }}
              className={`px-2.5 py-0.5 rounded-lg text-[11px] font-semibold transition-all ${
                crop === 'cotton' && sowingDate === '2026-05-25'
                  ? 'bg-[#D4E768] text-[#0B1C10] font-bold shadow-sm'
                  : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
            >
              Cotton (May 25 • Valid)
            </button>
            <button
              type="button"
              onClick={() => {
                setCrop('cotton');
                setSowingDate('2027-04-05');
                updateUrlParams('cotton', '2027-04-05');
              }}
              className={`px-2.5 py-0.5 rounded-lg text-[11px] font-semibold transition-all ${
                crop === 'cotton' && sowingDate === '2027-04-05'
                  ? 'bg-amber-400 text-[#0B1C10] font-bold shadow-sm'
                  : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
            >
              Cotton (Apr 5 • Seasonal Constraint)
            </button>
            <button
              type="button"
              onClick={() => {
                setCrop('wheat');
                setSowingDate('2026-06-15');
                updateUrlParams('wheat', '2026-06-15');
              }}
              className={`px-2.5 py-0.5 rounded-lg text-[11px] font-semibold transition-all ${
                crop === 'wheat' && sowingDate === '2026-06-15'
                  ? 'bg-amber-400 text-[#0B1C10] font-bold shadow-sm'
                  : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
            >
              Wheat (June 15 • Seasonal Constraint)
            </button>
            <button
              type="button"
              onClick={() => {
                setCrop('potato');
                updateUrlParams('potato', sowingDate);
              }}
              className={`px-2.5 py-0.5 rounded-lg text-[11px] font-semibold transition-all ${
                crop === 'potato'
                  ? 'bg-amber-400 text-[#0B1C10] font-bold shadow-sm'
                  : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
            >
              Potato (Unsupported)
            </button>
          </div>
        </div>
      </AgriculturalPageHero>

      {/* 2. Loading State Indicator */}
      {isLoading && (
        <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] text-[#2F6B3C] text-xs font-semibold flex items-center gap-2.5 animate-pulse">
          <RefreshCw className="w-4 h-4 animate-spin text-[#2F6B3C]" />
          <span>Computing stage dates, harvest windows, and field tasks for {crop.toUpperCase()}...</span>
        </div>
      )}

      {/* 3. Dedicated State: CROP CALENDAR UNAVAILABLE (Unsupported Crop) */}
      {!isLoading && errorCategory === 'unsupported_crop' && (
        <GlassCard variant="cream" className="p-6 sm:p-8 space-y-6 border-amber-300 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-[#E2E7DA] pb-6">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300 text-xs font-bold uppercase tracking-wider">
                <AlertTriangle className="w-4 h-4 text-amber-700" />
                <span>CROP CALENDAR UNAVAILABLE</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black font-editorial text-[#0B1C10]">
                This crop does not currently have calendar data in AGRINEXUS.
              </h2>
              <p className="text-xs sm:text-sm text-[#536056] leading-relaxed">
                Calendar data for "{crop}" is currently unavailable. To maintain strict scientific accuracy, AGRINEXUS does not synthesize fake growth stages or fabricated durations.
              </p>
            </div>
            <div className="sm:text-right shrink-0">
              <span className="text-[11px] font-mono font-bold text-[#536056] block">STATUS: HTTP 404 NOT FOUND</span>
              <span className="text-[10px] text-[#536056] italic">Verified agricultural reference active</span>
            </div>
          </div>

          {/* Supported Reference Crops Section */}
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-widest text-[#2F6B3C] flex items-center gap-2">
                <Sprout className="w-4 h-4 text-[#2F6B3C]" />
                Supported Reference Crops Available in AGRINEXUS
              </h3>
              <p className="text-xs text-[#536056] mt-0.5">
                Select any of the four verified reference crops below to view complete stage timelines and field schedules:
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {VERIFIED_REFERENCE_CROPS.map((refCrop) => (
                <div
                  key={refCrop.id}
                  className="p-5 rounded-2xl bg-white border border-[#E2E7DA] hover:border-[#2F6B3C] hover:shadow-md transition-all space-y-3 flex flex-col justify-between group"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold font-editorial text-lg text-[#0B1C10] capitalize">
                        {refCrop.label}
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-[#EEF3E8] text-[#2F6B3C] text-[10px] font-bold uppercase">
                        {refCrop.seasons.join(', ')}
                      </span>
                    </div>
                    <p className="text-xs text-[#536056] leading-relaxed">
                      {refCrop.description}
                    </p>
                    <div className="text-[11px] font-mono text-[#2F6B3C] font-semibold">
                      Typical Cycle: {refCrop.typicalDuration}
                    </div>
                  </div>

                  <Button
                    variant="lime"
                    size="sm"
                    className="w-full text-xs font-bold mt-2"
                    onClick={() => handleSwitchToCrop(refCrop.id, refCrop.defaultSowingDate)}
                    icon={<ArrowRight className="w-3.5 h-3.5" />}
                  >
                    View {refCrop.id.toUpperCase()} Calendar
                  </Button>
                </div>
              ))}
            </div>
          </div>

          {/* Data Provenance & Spora Architecture Note */}
          <div className="p-4 rounded-2xl bg-[#EEF3E8]/80 border border-[#E2E7DA] space-y-1.5 text-xs text-[#0B1C10]">
            <div className="font-bold flex items-center gap-1.5 text-[#2F6B3C]">
              <Info className="w-4 h-4 text-[#2F6B3C] shrink-0" />
              <span>Agronomic Data Provenance & Provider Coverage</span>
            </div>
            <p className="text-[11px] text-[#536056] leading-relaxed">
              AGRINEXUS serves bundled, generalised Indian reference datasets for demonstration and testing. When a verified external provider is configured via <code>SPORA_API_KEY</code>, international and national planting and harvest calendars from the Spora Harvest API are queried automatically.
            </p>
          </div>
        </GlassCard>
      )}

      {/* 4. Dedicated State: Season Sowing Window Mismatch (HTTP 400 Constraint Preserved) */}
      {!isLoading && errorCategory === 'season_mismatch' && (
        <GlassCard variant="cream" className="p-6 sm:p-8 space-y-6 border-amber-300 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-[#E2E7DA] pb-5">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300 text-xs font-bold uppercase tracking-wider">
                <AlertTriangle className="w-4 h-4 text-amber-700" />
                <span>SEASONAL SOWING CONSTRAINT</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black font-editorial text-[#0B1C10]">
                {activeCropMeta ? activeCropMeta.label : crop.toUpperCase()} is outside its recommended sowing window.
              </h2>
              <p className="text-xs sm:text-sm text-[#536056] leading-relaxed">
                The selected sowing date does not align with the agronomic calendar configured for this crop. Operating outside the window can lead to severe moisture deficit, poor germination, or terminal heat stress.
              </p>
            </div>
            <div className="sm:text-right shrink-0">
              <span className="text-[11px] font-mono font-bold text-[#536056] block">STATUS: HTTP 400 CONSTRAINT</span>
              <span className="text-[10px] text-amber-800 font-semibold">Agronomic Validation Preserved</span>
            </div>
          </div>

          {/* Structured Guidance Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-white border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-[#536056]" />
                Selected Sowing Date
              </span>
              <p className="font-extrabold text-base text-[#0B1C10] font-mono">
                {sowingDate}
              </p>
              <p className="text-[11px] text-rose-700 font-semibold">
                ● Outside Sowing Window
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#2F6B3C]" />
                Supported Season(s)
              </span>
              <p className="font-extrabold text-base text-[#0B1C10] capitalize">
                {activeCropMeta?.seasons?.join(', ') || 'Kharif'}
              </p>
              <p className="text-[11px] text-[#536056]">
                Validated crop cycle
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#536056] block flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#2F6B3C]" />
                Recommended Sowing Window
              </span>
              <p className="font-extrabold text-base text-[#2F6B3C]">
                {activeCropMeta?.sowingWindowDisplay || 'Season specific'}
              </p>
              <p className="text-[11px] text-[#536056]">
                Optimal agronomic period
              </p>
            </div>
          </div>

          {/* Suggested Action Box */}
          <div className="p-5 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-3">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#2F6B3C] block">
                SUGGESTED AGRONOMIC ACTION:
              </span>
              <p className="text-xs text-[#0B1C10] mt-1 leading-relaxed font-medium">
                {activeCropMeta?.recommendedAction ||
                  'Adjust your sowing date to align with the recommended seasonal window to ensure viable vegetative growth.'}
              </p>
            </div>

            <div className="flex items-center gap-3 pt-1 flex-wrap">
              {activeCropMeta?.recommendedDate && (
                <Button
                  variant="lime"
                  size="sm"
                  onClick={() => handleDateChange(activeCropMeta.recommendedDate)}
                  icon={<Calendar className="w-3.5 h-3.5" />}
                >
                  Set Recommended Sowing Date ({activeCropMeta.recommendedDate})
                </Button>
              )}
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleSwitchToCrop('rice', '2026-06-15')}
              >
                Switch to Kharif Rice
              </Button>
            </div>
          </div>
        </GlassCard>
      )}

      {/* 5. Dedicated State: Provider Error or Generic Failure (500 / 502 / Network) */}
      {!isLoading && (errorCategory === 'provider_error' || errorCategory === 'validation_error' || errorCategory === 'generic_error') && (
        <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 space-y-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <h3 className="text-sm font-bold uppercase tracking-wider">
              {errorCategory === 'provider_error' ? 'Crop Calendar Data Provider Unavailable' : 'Request Validation Issue'}
            </h3>
          </div>
          <p className="text-xs text-rose-800 leading-relaxed">
            {error || 'Unable to retrieve crop schedule at this time.'}
          </p>
          <div className="flex items-center gap-3 pt-1">
            <Button
              variant="secondary"
              size="sm"
              onClick={fetchSchedule}
              icon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Retry Request
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleSwitchToCrop('rice', '2026-06-15')}
            >
              Reset to Default (Rice, June 15)
            </Button>
          </div>
        </div>
      )}

      {/* 6. Derived Schedule Display (When Valid Schedule Available) */}
      {!isLoading && schedule && (
        <GlassCard variant="solid" className="p-6 sm:p-8 space-y-8 shadow-xl">
          {/* Header Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                AGRONOMIC SCHEDULE ({(schedule.crop || crop).toUpperCase()} • {(schedule.season || 'ANNUAL').toUpperCase()} SEASON)
              </span>
              <h2 className="text-3xl font-black font-editorial text-[#0B1C10] mt-1 flex items-center gap-3 capitalize">
                <Sprout className="w-8 h-8 text-[#2F6B3C]" />
                Current Stage: {schedule.current_stage ? schedule.current_stage.replace(/_/g, ' ') : 'Off-Season / Pre-Sowing or Completed'}
              </h2>
            </div>
            <div className="sm:text-right">
              <span className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold ${
                schedule.sowing_window_compliant
                  ? 'bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]'
                  : 'bg-amber-500/10 text-amber-900 border border-amber-500/25'
              }`}>
                {schedule.sowing_window_compliant ? '● Optimal Sowing Window' : '● Off-Window Warning'}
              </span>
              <p className="text-xs font-medium text-[#536056] mt-1 font-mono">
                Duration: {schedule.crop_duration_days ?? 'N/A'} Days
              </p>
            </div>
          </div>

          {/* Sowing Window Warnings Callout if applicable */}
          {Array.isArray(schedule.warnings) && schedule.warnings.length > 0 && (
            <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-1">
              <span className="font-bold flex items-center gap-1.5 text-amber-800">
                <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
                Agronomic Schedule Advisory:
              </span>
              {schedule.warnings.map((w, idx) => (
                <p key={idx} className="text-[11px] leading-relaxed">
                  {w}
                </p>
              ))}
            </div>
          )}

          {/* Harvest Window & Next Stage Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-5 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-widest text-[#2F6B3C] block">
                ESTIMATED HARVEST WINDOW
              </span>
              <p className="font-extrabold text-[#0B1C10] text-base font-editorial">
                {schedule.harvest_window
                  ? `${schedule.harvest_window.start_date} → ${schedule.harvest_window.end_date}`
                  : 'Derived window unavailable'}
              </p>
              {schedule.days_to_harvest_estimate != null && (
                <span className="text-[11px] font-mono text-[#2F6B3C] font-semibold block">
                  ~{schedule.days_to_harvest_estimate} days to completion
                </span>
              )}
            </div>

            <div className="p-5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                NEXT UPCOMING GROWTH STAGE
              </span>
              <p className="font-extrabold text-[#0B1C10] text-base font-editorial capitalize">
                {schedule.next_stage ? schedule.next_stage.replace(/_/g, ' ') : 'Final Stage / Harvest Window Reached'}
              </p>
              {schedule.current_stage_progress_percent != null && (
                <span className="text-[11px] text-[#536056] font-medium block">
                  Current stage progress: {schedule.current_stage_progress_percent}%
                </span>
              )}
            </div>
          </div>

          {/* Organic Growth Stage Timeline */}
          {Array.isArray(schedule.scheduled_growth_stages) && schedule.scheduled_growth_stages.length > 0 && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                  Seasonal Growth Stages & Task Timeline
                </h3>
                <span className="text-[11px] font-mono text-[#536056]">
                  {schedule.scheduled_growth_stages.length} Scheduled Phases
                </span>
              </div>

              <div className="relative border-l-2 border-[#2F6B3C]/30 ml-4 pl-6 space-y-8">
                {schedule.scheduled_growth_stages.map((stg, idx) => (
                  <div key={idx} className="relative group">
                    {/* Timeline Dot */}
                    <div
                      className={`absolute -left-[31px] top-1.5 w-4 h-4 rounded-full border-2 border-[#0B1C10] transition-all ${
                        stg.is_current ? 'bg-[#D4E768] scale-125 shadow-md' : 'bg-[#EEF3E8]'
                      }`}
                    />

                    <div className={`p-6 rounded-3xl border transition-all ${
                      stg.is_current
                        ? 'bg-[#EEF3E8] border-[#2F6B3C] shadow-md'
                        : 'bg-white border-[#E2E7DA]'
                    }`}>
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E2E7DA]/60 pb-3">
                        <span className="font-extrabold font-editorial text-lg text-[#0B1C10] capitalize flex items-center gap-2">
                          {stg.is_current && <CheckCircle2 className="w-5 h-5 text-[#2F6B3C]" />}
                          {stg.stage ? stg.stage.replace(/_/g, ' ') : `Phase ${idx + 1}`}
                        </span>
                        <span className="text-xs font-mono font-bold text-[#2F6B3C]">
                          {stg.start_date || 'Start'} → {stg.end_date || 'End'} ({stg.duration_days ?? 'N/A'} days)
                        </span>
                      </div>

                      {stg.activities && stg.activities.length > 0 && (
                        <div className="mt-3 space-y-2 pt-2">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                            Recommended Agronomic Tasks:
                          </span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {stg.activities.map((act, i) => (
                              <div key={i} className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs font-semibold text-[#162018] flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-[#2F6B3C] shrink-0" />
                                <span>{act}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer Provenance Info */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-4 border-t border-[#E2E7DA] text-[11px] text-[#536056]">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-[#2F6B3C]" />
              Data Provenance: {schedule.is_reference_data ? 'Bundled Reference Dataset (India Generic)' : schedule.data_source}
            </span>
            <span className="font-mono">
              Serving Timestamp: {schedule.as_of_date || new Date().toISOString().split('T')[0]}
            </span>
          </div>
        </GlassCard>
      )}
    </div>
  );
};

export const CropCalendarPage: React.FC = () => {
  return (
    <ErrorBoundary
      fallbackTitle="Crop Calendar Planner Error"
      fallbackMessage="An unexpected rendering issue occurred in the Crop Calendar. Please refresh or return to Dashboard."
    >
      <CropCalendarPageContent />
    </ErrorBoundary>
  );
};

export default CropCalendarPage;
