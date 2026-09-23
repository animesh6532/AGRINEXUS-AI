import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, RefreshCw, AlertCircle, Calendar } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { GlassCard } from '../components/ui/GlassCard';
import { Select } from '../components/ui/Select';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { api } from '../services/api';
import { MarketPriceRecord, MarketForecastResponse, MarketSignalsResponse } from '../types/api';

export const MarketPage: React.FC = () => {
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
      const [cData, hData, fData, sData] = await Promise.allSettled([
        api.getMarketCurrent(commodity),
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
  }, [commodity, model]);

  const historyChartData = history.map((h) => ({
    date: h.arrival_date,
    ModalPrice: h.modal_price,
    MinPrice: h.min_price,
    MaxPrice: h.max_price,
  }));

  const forecastChartData = forecast?.forecasts.map((f) => ({
    date: f.date.split('-').slice(1).join('/'),
    ForecastPrice: f.predicted_modal_price,
  })) || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Market Intelligence & Mandi Forecast</h1>
            <p className="text-xs text-slate-500">
              Government of India mandi observations, ETS/ARIMA price forecasting, and actionable trend signals.
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
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
              { value: 'ets', label: 'ETS Holt-Winters' },
              { value: 'arima', label: 'ARIMA Model' },
              { value: 'ma', label: 'Moving Average' },
            ]}
          />
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Current Mandi Observation Card */}
      {current && (
        <GlassCard variant="strong" className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
                Latest Mandi Observation ({current.market}, {current.state})
              </span>
              <h2 className="text-3xl font-black text-slate-900 mt-1">
                ₹{current.modal_price} <span className="text-xs font-normal text-slate-500">/ quintal</span>
              </h2>
            </div>
            <div className="flex items-center gap-4 text-xs font-medium text-slate-600">
              <span className="p-2 rounded-lg bg-white/70 border border-slate-100">Min: ₹{current.min_price}</span>
              <span className="p-2 rounded-lg bg-white/70 border border-slate-100">Max: ₹{current.max_price}</span>
              <Badge variant="success">Observed {current.arrival_date}</Badge>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Forecast Chart */}
      {forecastChartData.length > 0 && (
        <GlassCard variant="strong" className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-600" /> 7-Day Modal Price Forecast ({forecast?.model_used.toUpperCase()})
            </h3>
            <span className="text-xs text-slate-400 font-medium">As of {forecast?.last_historical_date}</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecastChartData}>
                <XAxis dataKey="date" stroke="#94A3B8" fontSize={11} />
                <YAxis stroke="#94A3B8" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '12px', borderColor: '#E2E8F0' }}
                />
                <Line type="monotone" dataKey="ForecastPrice" stroke="#10B981" strokeWidth={3} dot={{ r: 4 }} name="Predicted Price (₹)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      )}

      {/* Market Signals */}
      {signals && signals.actionable_signals && (
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Actionable Market Signals</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {signals.actionable_signals.map((sig, idx) => (
              <GlassCard key={idx} className="p-4 space-y-2 border-l-4 border-l-emerald-500">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">{sig.type}</span>
                  <Badge variant="success">Strength: {(sig.signal_strength * 100).toFixed(0)}%</Badge>
                </div>
                <p className="text-xs text-slate-600">{sig.description}</p>
                <p className="text-xs font-semibold text-emerald-700 bg-emerald-50 p-2 rounded-lg">{sig.recommendation}</p>
              </GlassCard>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
