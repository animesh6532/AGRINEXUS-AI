import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, AlertCircle, MapPin } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Select } from '../components/ui/Select';
import { useLocationContext } from '../context/LocationContext';
import { LocationBadge } from '../components/location/LocationBadge';
import { api } from '../services/api';
import { MarketPriceRecord, MarketForecastResponse, MarketSignalsResponse } from '../types/api';

export const MarketPage: React.FC = () => {
  const { location } = useLocationContext();
  const [commodity, setCommodity] = useState<string>('Paddy(Common)');
  const [model, setModel] = useState<string>('ets');

  const [current, setCurrent] = useState<MarketPriceRecord | null>(null);
  const [history, setHistory] = useState<MarketPriceRecord[]>([]);
  const [forecast, setForecast] = useState<MarketForecastResponse | null>(null);
  const [signals, setSignals] = useState<MarketSignalsResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMarketData = async () => {
    setLoading(true);
    setError(null);
    try {
      const stateParam = location?.state;
      const [cData, hData, fData, sData] = await Promise.allSettled([
        api.getMarketCurrent(commodity, stateParam),
        api.getMarketHistory(commodity),
        api.getMarketForecast(commodity, 7, model),
        api.getMarketSignals(commodity),
      ]);

      if (cData.status === 'fulfilled') setCurrent(cData.value);
      if (hData.status === 'fulfilled') setHistory(hData.value);
      if (fData.status === 'fulfilled') setForecast(fData.value);
      if (sData.status === 'fulfilled') setSignals(sData.value);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch market data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketData();
  }, [commodity, model, location?.state]);

  const forecastChartData =
    forecast?.forecasts.map((f) => ({
      date: f.date.split('-').slice(1).join('/'),
      ForecastPrice: f.predicted_modal_price,
    })) || [];

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
            value={commodity}
            onChange={(e) => setCommodity(e.target.value)}
            options={[
              { value: 'Paddy(Common)', label: 'Paddy (Common)' },
              { value: 'Wheat', label: 'Wheat' },
              { value: 'Maize', label: 'Maize' },
              { value: 'Cotton', label: 'Cotton' },
            ]}
          />
          <Select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            options={[
              { value: 'ets', label: 'ETS Holt-Winters Model' },
              { value: 'arima', label: 'ARIMA Model' },
              { value: 'ma', label: 'Moving Average Model' },
            ]}
          />
        </div>
      </AgriculturalPageHero>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Current Mandi Observation Card */}
      {current && (
        <GlassCard variant="solid" className="p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                OBSERVED MANDI MARKET PRICE ({current.market}, {current.state})
              </span>
              <h2 className="text-4xl font-black font-editorial text-[#0B1C10] mt-1">
                ₹{current.modal_price}{' '}
                <span className="text-sm font-sans font-medium text-[#536056]">/ quintal</span>
              </h2>
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

      {/* Forecast Chart */}
      {forecastChartData.length > 0 && (
        <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E2E7DA] pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                7-DAY MODAL PRICE FORECAST
              </span>
              <h3 className="text-2xl font-extrabold font-editorial text-[#0B1C10]">
                Predictive Price Horizon ({forecast?.model_used.toUpperCase()})
              </h3>
            </div>
            <span className="text-xs text-[#536056] font-mono">
              Historical Baseline: {forecast?.last_historical_date}
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
      {signals && signals.actionable_signals && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-widest text-[#536056]">
              Actionable Mandi Signals
            </h3>
            <span className="text-xs text-[#2F6B3C] font-semibold">
              {signals.actionable_signals.length} Active Market Signals
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {signals.actionable_signals.map((sig, idx) => (
              <GlassCard
                key={idx}
                variant="solid"
                className="p-6 space-y-3 border-l-4 border-l-[#2F6B3C]"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#0B1C10]">
                    {sig.type}
                  </span>
                  <span className="px-3 py-0.5 rounded-full bg-[#EEF3E8] text-[#2F6B3C] text-[10px] font-extrabold uppercase border border-[#E2E7DA]">
                    Signal Strength: {(sig.signal_strength * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-[#536056] leading-relaxed font-sans">{sig.description}</p>
                <p className="text-xs font-bold text-[#2F6B3C] bg-[#EEF3E8] p-3 rounded-2xl border border-[#E2E7DA]">
                  {sig.recommendation}
                </p>
              </GlassCard>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
