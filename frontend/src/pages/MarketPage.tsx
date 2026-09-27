import React, { useState, useEffect, useRef } from 'react';
import { TrendingUp, AlertCircle, MapPin, Globe, ArrowLeft } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Select } from '../components/ui/Select';
import { useLocationContext } from '../context/LocationContext';
import { LocationBadge } from '../components/location/LocationBadge';
import { api } from '../services/api';
import {
  MarketPriceRecord,
  MarketForecastResponse,
  MarketSignalsResponse,
  CommodityCatalogueItem,
} from '../types/api';

const MODEL_LABELS: Record<string, string> = {
  ets: 'Recommended (ETS Holt-Winters)',
  moving_average: 'Moving Average (7-Day Trend)',
  naive: 'Baseline / Naive (Last Observed)',
  arima: 'Statistical ARIMA (1, 1, 1)',
};

const DEFAULT_COMMODITY_OPTIONS = [
  { value: 'Paddy(Common)', label: 'Paddy (Common)' },
  { value: 'Masur Dal', label: 'Masur Dal (Lentil)' },
  { value: 'Wheat', label: 'Wheat' },
  { value: 'Maize', label: 'Maize' },
  { value: 'Cotton', label: 'Cotton' },
];

function getForecastPoints(forecast: MarketForecastResponse | null) {
  if (!forecast) return [];
  const raw = (forecast.forecast ?? forecast.forecasts ?? []) as Array<Record<string, any>>;
  return raw.map((f) => ({
    date: String(f.date ?? ''),
    predicted_price: Number(f.predicted_price ?? f.predicted_modal_price ?? 0),
    confidence_lower: f.confidence_lower ?? f.lower_ci ?? undefined,
    confidence_upper: f.confidence_upper ?? f.upper_ci ?? undefined,
  }));
}

function getModelLabel(value: string): string {
  return MODEL_LABELS[value] ?? value;
}

export const MarketPage: React.FC = () => {
  const { location } = useLocationContext();
  const [commodity, setCommodity] = useState<string>('Paddy(Common)');
  const [model, setModel] = useState<string>('ets');

  // Supported commodity catalogue from backend
  const [catalogue, setCatalogue] = useState<CommodityCatalogueItem[]>([]);

  // Explicit user-driven nationwide view toggle (Phase 17)
  const [viewNationwide, setViewNationwide] = useState<boolean>(false);

  const [current, setCurrent] = useState<MarketPriceRecord | null>(null);
  const [history, setHistory] = useState<MarketPriceRecord[]>([]);
  const [forecast, setForecast] = useState<MarketForecastResponse | null>(null);
  const [signals, setSignals] = useState<MarketSignalsResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [currentError, setCurrentError] = useState<string | null>(null);
  const [forecastError, setForecastError] = useState<string | null>(null);
  const [signalsError, setSignalsError] = useState<string | null>(null);

  // Monotonic request id: only the latest selection may write state.
  // Prevents Paddy -> Maize -> Wheat races where an older response wins.
  const requestIdRef = useRef(0);

  const stateParam = location?.state ? location.state : undefined;
  const effectiveState = viewNationwide ? undefined : stateParam;

  // Load supported commodity catalogue from backend whenever location state changes
  useEffect(() => {
    let cancelled = false;
    const fetchCatalogue = async () => {
      try {
        const res = await api.getMarketCommodities(stateParam);
        if (!cancelled && res?.commodities?.length > 0) {
          setCatalogue(res.commodities);
        }
      } catch {
        // Fallback to default options if catalogue endpoint fails
      }
    };
    fetchCatalogue();
    return () => {
      cancelled = true;
    };
  }, [stateParam]);

  // Reset nationwide view whenever user changes commodity or location state
  useEffect(() => {
    setViewNationwide(false);
  }, [commodity, stateParam]);

  useEffect(() => {
    const requestId = ++requestIdRef.current;
    let cancelled = false;

    const fetchMarketData = async () => {
      // Clear stale results immediately so the UI can never show
      // the previous commodity as if it were the new selection.
      setLoading(true);
      setCurrent(null);
      setHistory([]);
      setForecast(null);
      setSignals(null);
      setCurrentError(null);
      setForecastError(null);
      setSignalsError(null);

      try {
        const [cData, hData, fData, sData] = await Promise.allSettled([
          api.getMarketCurrent(commodity, effectiveState),
          api.getMarketHistory(commodity, effectiveState),
          api.getMarketForecast(commodity, 7, model, effectiveState),
          api.getMarketSignals(commodity, effectiveState, model),
        ]);

        // Ignore out-of-order responses from an older selection.
        if (cancelled || requestIdRef.current !== requestId) return;

        if (cData.status === 'fulfilled') {
          setCurrent(cData.value);
        } else {
          setCurrent(null);
          setCurrentError(cData.reason?.message || 'No market data available for this selection.');
        }
        if (hData.status === 'fulfilled') {
          setHistory(hData.value);
        } else {
          setHistory([]);
        }
        if (fData.status === 'fulfilled') {
          setForecast(fData.value);
        } else {
          setForecast(null);
          setForecastError(fData.reason?.message || 'Forecast unavailable for this selection.');
        }
        if (sData.status === 'fulfilled') {
          setSignals(sData.value);
        } else {
          setSignals(null);
          setSignalsError(sData.reason?.message || 'Market signals unavailable for this selection.');
        }
      } catch (err: any) {
        if (cancelled || requestIdRef.current !== requestId) return;
        setCurrentError(err?.message || 'Failed to fetch market data.');
      } finally {
        if (!cancelled && requestIdRef.current === requestId) {
          setLoading(false);
        }
      }
    };

    fetchMarketData();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [commodity, model, effectiveState]);

  const forecastPoints = getForecastPoints(forecast);
  const forecastChartData = forecastPoints.map((f) => ({
    date: f.date.split('-').slice(1).join('/') || f.date,
    ForecastPrice: f.predicted_price,
  }));
  const forecastModelName = forecast?.model ?? forecast?.model_used ?? model;

  // Build commodity options from catalogue if available, else defaults
  const commodityOptions = catalogue.length > 0
    ? catalogue.map((item) => {
        let label = item.display_name;
        if (stateParam && !item.is_available) {
          label = `${item.display_name} (No ${stateParam} data)`;
        }
        return {
          value: item.canonical_name,
          label,
        };
      })
    : DEFAULT_COMMODITY_OPTIONS;

  // Selected commodity display name
  const currentCommodityItem = catalogue.find((c) => c.canonical_name === commodity);
  const selectedCommodityDisplay = currentCommodityItem?.display_name || commodity.replace(/(\w)\(/, '$1 (');

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="FIELD SIGNALS"
        title="Mandi Market Intelligence"
        description="Government of India Mandi arrival observations, ETS/ARIMA price forecasting models, and actionable market signals tailored to your state/region."
        imageSrc="/images/market-intelligence.webp"
      >
        <div className="flex items-center gap-3 bg-black/40 backdrop-blur-md p-2 rounded-2xl border border-white/10 flex-wrap">
          <LocationBadge variant="pill" />
          <Select
            id="commodity-select"
            aria-label="Select Commodity"
            value={commodity}
            onChange={(e) => setCommodity(e.target.value)}
            options={commodityOptions}
          />
          <Select
            id="forecast-model-select"
            aria-label="Select Forecast Model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            options={[
              { value: 'ets', label: 'Recommended (ETS Holt-Winters)' },
              { value: 'moving_average', label: 'Moving Average (7-Day Trend)' },
              { value: 'naive', label: 'Baseline / Naive (Last Observed)' },
              { value: 'arima', label: 'Statistical ARIMA (1, 1, 1)' },
            ]}
          />
        </div>
      </AgriculturalPageHero>

      {/* Explicit Nationwide Active Banner (Phase 17) */}
      {viewNationwide && (
        <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 text-blue-900 text-xs flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-blue-700 shrink-0" />
            <span>
              <strong>All-India Market View Active:</strong> Showing latest available nationwide mandi observation for <strong>{selectedCommodityDisplay}</strong> (regional state filter cleared).
            </span>
          </div>
          {stateParam && (
            <button
              onClick={() => setViewNationwide(false)}
              className="px-3 py-1 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Return to {stateParam} Filter
            </button>
          )}
        </div>
      )}

      {loading && (
        <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] text-[#2F6B3C] text-xs font-semibold flex items-center gap-2">
          <TrendingUp className="w-4 h-4 shrink-0" />
          <span>Loading market intelligence for {selectedCommodityDisplay}{effectiveState ? ` in ${effectiveState}` : ' (All-India)'} using {getModelLabel(model)}…</span>
        </div>
      )}

      {!loading && !current && currentError && (
        <div className="p-5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-2 flex-1">
            <p className="font-extrabold uppercase tracking-wider">No market data available</p>
            <p className="leading-relaxed">
              No genuine <strong>{selectedCommodityDisplay}</strong> market data was found{stateParam && !viewNationwide ? ` for the selected region (${stateParam})` : ''}.
              Previous results were cleared rather than shown as stale.
            </p>
            {/* Phase 17 Explicit User Action */}
            {stateParam && !viewNationwide && (
              <div className="pt-2">
                <button
                  onClick={() => setViewNationwide(true)}
                  className="px-3.5 py-1.5 rounded-xl bg-[#2F6B3C] hover:bg-[#23532D] text-white font-bold text-xs flex items-center gap-1.5 transition-colors shadow-sm"
                >
                  <Globe className="w-3.5 h-3.5" /> View latest available India-wide {selectedCommodityDisplay} data
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Current Mandi Observation Card */}
      {current && (
        <GlassCard variant="solid" className="p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-6">
            <div>
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="text-xs font-bold uppercase tracking-widest text-[#536056]">
                  OBSERVED MANDI MARKET PRICE ({current.commodity} · {current.market}, {current.state})
                </span>
                {viewNationwide && (
                  <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 text-[10px] font-black uppercase tracking-wider border border-blue-200">
                    All-India View
                  </span>
                )}
              </div>
              <h2 className="text-4xl font-black font-editorial text-[#0B1C10] mt-1">
                ₹{current.modal_price}{' '}
                <span className="text-sm font-sans font-medium text-[#536056]">/ quintal</span>
              </h2>
              <p className="text-xs text-[#536056] mt-2 flex items-center gap-1">
                <MapPin className="w-3 h-3 text-[#2F6B3C]" /> {current.district}, {current.state} · Observation Date: {current.observation_date || current.arrival_date} · Source: data.gov.in
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs font-bold text-[#162018] flex-wrap">
              <span className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                Min: ₹{current.min_price}
              </span>
              <span className="p-3 rounded-2xl bg-[#EEF3E8] text-[#2F6B3C] border border-[#E2E7DA]">
                Modal: ₹{current.modal_price}
              </span>
              <span className="p-3 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA]">
                Max: ₹{current.max_price}
              </span>
            </div>
          </div>
        </GlassCard>
      )}

      {!loading && !forecast && forecastError && (
        <div className="p-5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-extrabold uppercase tracking-wider">Forecast unavailable: insufficient historical data</p>
            <p className="leading-relaxed">
              No {getModelLabel(model)} forecast could be generated for <strong>{selectedCommodityDisplay}</strong>
              {effectiveState ? ` in ${effectiveState}` : ''}. {forecastError}
            </p>
          </div>
        </div>
      )}

      {/* Forecast Chart */}
      {forecastChartData.length > 0 && forecast && (
        <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E2E7DA] pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                {forecast.forecast_horizon_days}-DAY MODAL PRICE FORECAST · {forecast.commodity}
              </span>
              <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">
                Predictive Price Horizon ({getModelLabel(forecastModelName)} · {String(forecastModelName).toUpperCase()})
              </h3>
            </div>
            <span className="text-xs text-[#536056] font-mono">
              {forecast.last_historical_date ? `Historical Baseline: ${forecast.last_historical_date}` : `Current: ₹${forecast.current_price}`}
            </span>
          </div>

          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecastChartData}>
                <XAxis dataKey="date" stroke="#536056" fontSize={11} tickLine={false} />
                <YAxis stroke="#536056" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B1C10',
                    color: '#FAFBF7',
                    borderRadius: '16px',
                    borderColor: '#D4E768',
                    fontSize: '12px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="ForecastPrice"
                  stroke="#2F6B3C"
                  strokeWidth={3}
                  dot={{ r: 5, fill: '#D4E768', stroke: '#0B1C10' }}
                  name="Predicted Price (₹)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      )}

      {/* Market Signals */}
      {!loading && !signals && signalsError && (
        <div className="p-5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-extrabold uppercase tracking-wider">Market signals unavailable</p>
            <p className="leading-relaxed">{signalsError}</p>
          </div>
        </div>
      )}
      {signals && signals.actionable_signals && signals.actionable_signals.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
              Actionable Mandi Signals · {selectedCommodityDisplay}
            </h3>
            <span className="text-xs text-[#2F6B3C] font-semibold">
              {signals.actionable_signals.length} Active Market Signals
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {signals.actionable_signals.map((sig, idx) => {
              const strength = typeof sig.signal_strength === 'number'
                ? sig.signal_strength
                : typeof (sig as Record<string, any>).strength === 'string'
                  ? undefined
                  : 0;
              return (
              <GlassCard
                key={idx}
                variant="solid"
                className="p-6 space-y-3 border-l-4 border-l-[#2F6B3C]"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#0B1C10]">
                    {sig.type}
                  </span>
                  <span className="px-3 py-0.5 rounded-full bg-[#EEF3E8] text-[#2F6B3C] text-[10px] font-extrabold uppercase border border-[#E2E7DA]">
                    {typeof strength === 'number'
                      ? `Signal Strength: ${(strength * 100).toFixed(0)}%`
                      : `Strength: ${sig.strength ?? sig.severity ?? sig.confidence ?? 'n/a'}`}
                  </span>
                </div>
                <p className="text-xs text-[#536056] leading-relaxed font-sans">{sig.description}</p>
                <p className="text-xs font-bold text-[#2F6B3C] bg-[#EEF3E8] p-3 rounded-2xl border border-[#E2E7DA]">
                  {sig.recommendation}
                </p>
              </GlassCard>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
