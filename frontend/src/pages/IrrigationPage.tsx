import React, { useState, useEffect, useCallback } from 'react';
import {
  Droplets,
  AlertTriangle,
  Calendar,
  Sun,
  Sparkles,
  CheckCircle2,
  Clock,
  Gauge,
  PlusCircle,
  RefreshCw,
  Zap,
  Sliders,
  X,
  ChevronDown,
} from 'lucide-react';
import {
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Bar,
  ComposedChart,
} from 'recharts';

import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';

import { api } from '../services/api';
import { useFarmerProfile } from '../context/FarmerProfileContext';
import type {
  IrrigationIntelligenceResponse,
  WhatIfSimulationResponse,
  IrrigationPredictionResponse,
} from '../types/api';

export const IrrigationPage: React.FC = () => {
  const { fields, selectedField, selectField, farmer } = useFarmerProfile();

  // Active Selected Field ID (defaults to first available or selected field)
  const activeField = selectedField || (fields.length > 0 ? fields[0] : null);
  const activeFieldId = activeField?.id;

  // Intelligence State
  const [intel, setIntel] = useState<IrrigationIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Irrigation Log Modal State
  const [showLogModal, setShowLogModal] = useState<boolean>(false);
  const [logForm, setLogForm] = useState({
    water_amount_mm: 15.0,
    method: 'Drip',
    duration_minutes: 45,
    notes: '',
  });
  const [submittingLog, setSubmittingLog] = useState<boolean>(false);

  // What-If Simulator Interactive State
  const [simForm, setSimForm] = useState({
    custom_irrigation_mm: 15.0,
    delay_hours: 12,
    simulated_rain_mm: 10.0,
  });
  const [simResult, setSimResult] = useState<WhatIfSimulationResponse | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);

  // Manual Telemetry Override Drawer State
  const [showManualDrawer, setShowManualDrawer] = useState<boolean>(false);
  const [manualMlData, setManualMlData] = useState({
    SWC: 0.22,
    SWC_lag1h: 0.225,
    SWC_lag2h: 0.23,
    SWC_lag3h: 0.235,
    SWC_roll6h_mean: 0.23,
    Rainfall_mm: 0.0,
    Rain_roll6h_sum: 0.0,
  });
  const [manualMlResult, setManualMlResult] = useState<IrrigationPredictionResponse | null>(null);
  const [loadingManualMl, setLoadingManualMl] = useState<boolean>(false);

  // Load Irrigation Intelligence
  const fetchIntelligence = useCallback(
    async (isManualRefresh = false) => {
      if (isManualRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      try {
        const userId = farmer?.user_id || 'default_farmer';
        const data = await api.getIrrigationIntelligence(
          activeFieldId,
          activeField?.latitude || undefined,
          activeField?.longitude || undefined,
          userId
        );
        setIntel(data);
      } catch (err: any) {
        console.error('Error fetching irrigation intelligence:', err);
        setError(err.message || 'Failed to load digital irrigation intelligence.');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [activeFieldId, activeField, farmer?.user_id]
  );

  useEffect(() => {
    fetchIntelligence();
  }, [fetchIntelligence]);

  // Handle Field Selection Change
  const handleFieldSelect = (fieldIdStr: string) => {
    const id = parseInt(fieldIdStr, 10);
    const target = fields.find((f) => f.id === id);
    if (target) {
      selectField(target);
    }
  };

  // Handle Log Irrigation Form Submit
  const handleLogSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFieldId) return;

    setSubmittingLog(true);
    try {
      const userId = farmer?.user_id || 'default_farmer';
      await api.logIrrigationEvent(
        {
          field_id: activeFieldId,
          water_amount_mm: logForm.water_amount_mm,
          method: logForm.method,
          duration_minutes: logForm.duration_minutes || undefined,
          notes: logForm.notes || undefined,
        },
        userId
      );
      setShowLogModal(false);
      setLogForm({ water_amount_mm: 15.0, method: 'Drip', duration_minutes: 45, notes: '' });
      await fetchIntelligence(true);
    } catch (err: any) {
      alert(err.message || 'Failed to log irrigation event.');
    } finally {
      setSubmittingLog(false);
    }
  };

  // Handle What-If Simulation Run
  const handleRunSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFieldId) return;

    setSimulating(true);
    try {
      const userId = farmer?.user_id || 'default_farmer';
      const res = await api.simulateWhatIf(
        {
          field_id: activeFieldId,
          custom_irrigation_mm: simForm.custom_irrigation_mm,
          delay_hours: simForm.delay_hours,
          simulated_rain_mm: simForm.simulated_rain_mm,
        },
        userId
      );
      setSimResult(res);
    } catch (err: any) {
      console.error('Simulation error:', err);
    } finally {
      setSimulating(false);
    }
  };

  // Handle Manual ML Prediction Submit
  const handleManualMlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingManualMl(true);
    try {
      const res = await api.predictIrrigation(manualMlData);
      setManualMlResult(res);
    } catch (err: any) {
      alert(err.message || 'Failed to run ML prediction.');
    } finally {
      setLoadingManualMl(false);
    }
  };

  // Decision State Visual Helper
  const getDecisionBadge = (state: string) => {
    switch (state) {
      case 'IRRIGATE_NOW':
        return {
          bg: 'bg-rose-500/10 text-rose-900 border-rose-500/30',
          dot: 'bg-rose-500',
          title: 'IRRIGATE NOW',
        };
      case 'IRRIGATE_SOON':
        return {
          bg: 'bg-amber-500/10 text-amber-900 border-amber-500/30',
          dot: 'bg-amber-500',
          title: 'IRRIGATE SOON',
        };
      case 'WAIT_FOR_RAIN':
        return {
          bg: 'bg-sky-500/10 text-sky-900 border-sky-500/30',
          dot: 'bg-sky-500',
          title: 'WAIT FOR RAIN',
        };
      case 'MONITOR':
        return {
          bg: 'bg-[#EEF3E8] text-[#2F6B3C] border-[#E2E7DA]',
          dot: 'bg-[#2F6B3C]',
          title: 'MONITOR MOISTURE',
        };
      case 'NO_IRRIGATION_REQUIRED':
        return {
          bg: 'bg-emerald-500/10 text-emerald-900 border-emerald-500/30',
          dot: 'bg-emerald-500',
          title: 'NO IRRIGATION REQUIRED',
        };
      default:
        return {
          bg: 'bg-slate-100 text-slate-800 border-slate-300',
          dot: 'bg-slate-400',
          title: state,
        };
    }
  };

  return (
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="SMART WATER MANAGEMENT"
        title="Irrigation Intelligence"
        description="Digital Irrigation Advisor combining real-time weather, FAO-56 crop evapotranspiration water balance, rainfall forecasts, and frozen short-horizon ML predictions."
        imageSrc="/images/irrigation.webp"
      />

      <ScopeWarning
        type="info"
        message="Irrigation Intelligence integrates multi-signal water balance analysis (ET₀, Kc, forecast rain, field capacity) with the frozen 3-hour ML soil water content model as a supporting signal."
      />

      {/* Field Selector & Actions Header Bar */}
      <GlassCard variant="solid" className="p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="w-10 h-10 rounded-xl bg-[#EEF3E8] text-[#2F6B3C] flex items-center justify-center font-bold shrink-0">
              <Droplets className="w-5 h-5" />
            </div>

            <div className="flex-1 min-w-[200px]">
              <label className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                Target Field Selection
              </label>
              <div className="relative mt-0.5">
                <select
                  className="w-full appearance-none bg-[#FAFBF7] border border-[#E2E7DA] rounded-xl px-3 py-1.5 pr-8 text-sm font-extrabold text-[#0B1C10] focus:outline-none focus:ring-2 focus:ring-[#2F6B3C]/20"
                  value={activeFieldId || ''}
                  onChange={(e) => handleFieldSelect(e.target.value)}
                >
                  {fields.length > 0 ? (
                    fields.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.field_name} — {f.plantings?.find((p) => p.status === 'ACTIVE')?.crop_name || 'Crop'} (
                        {f.area_value || 2} acres)
                      </option>
                    ))
                  ) : (
                    <option value="">Field 01 — Rice — 2.0 acres</option>
                  )}
                </select>
                <ChevronDown className="w-4 h-4 text-[#536056] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Header Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchIntelligence(true)}
              isLoading={refreshing}
              icon={<RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />}
            >
              Refresh
            </Button>

            <Button
              variant="lime"
              size="sm"
              onClick={() => setShowLogModal(true)}
              icon={<PlusCircle className="w-3.5 h-3.5" />}
              className="shadow-sm"
            >
              + Log Irrigation
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowManualDrawer(!showManualDrawer)}
              icon={<Sliders className="w-3.5 h-3.5 text-[#536056]" />}
              className="text-xs text-[#536056]"
            >
              Manual Telemetry
            </Button>
          </div>
        </div>
      </GlassCard>

      {/* Main Loading & Error States */}
      {loading && (
        <GlassCard variant="solid" className="p-12 text-center space-y-4">
          <RefreshCw className="w-8 h-8 text-[#2F6B3C] animate-spin mx-auto" />
          <p className="text-sm font-medium text-[#536056]">
            Calculating FAO-56 root-zone water balance & forecast models...
          </p>
        </GlassCard>
      )}

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={() => fetchIntelligence()}>
            Retry
          </Button>
        </div>
      )}

      {!loading && intel && (
        <div className="space-y-8">
          {/* ============================================================ */}
          {/* 1. EXECUTIVE IRRIGATION DECISION HERO BANNER */}
          {/* ============================================================ */}
          <GlassCard
            variant="solid"
            className="p-6 sm:p-8 relative overflow-hidden border-t-4 border-t-[#2F6B3C]"
          >
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              {/* Decision & Key Action (7 Cols) */}
              <div className="lg:col-span-7 space-y-6">
                <div className="flex flex-wrap items-center gap-3">
                  <span
                    className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-black tracking-wider border ${
                      getDecisionBadge(intel.decision.state).bg
                    }`}
                  >
                    <span
                      className={`w-2 h-2 rounded-full ${getDecisionBadge(intel.decision.state).dot} animate-pulse`}
                    />
                    {intel.decision.state_title}
                  </span>

                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-[#536056] bg-[#FAFBF7] px-3 py-1.5 rounded-xl border border-[#E2E7DA]">
                    <Clock className="w-3.5 h-3.5 text-[#2F6B3C]" />
                    Window: <strong className="text-[#0B1C10]">{intel.decision.window}</strong>
                  </span>

                  <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#536056] bg-[#EEF3E8] px-2.5 py-1 rounded-lg">
                    Evidence Quality: <strong className="text-[#2F6B3C]">{intel.evidence_quality}</strong>
                  </span>
                </div>

                <div>
                  <h2 className="text-2xl sm:text-3xl font-black font-editorial text-[#0B1C10] leading-tight">
                    {intel.decision.reason}
                  </h2>
                  <p className="text-xs text-[#536056] mt-2 leading-relaxed">
                    Digital Irrigation Advisor assessment for{' '}
                    <strong>{intel.field_context.field_name}</strong> ({intel.field_context.crop_name} •{' '}
                    {intel.field_context.growth_stage} • {intel.field_context.area_value}{' '}
                    {intel.field_context.area_unit}).
                  </p>
                </div>

                {/* Net Irrigation Depth & Volume Metrics */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[#2F6B3C] block">
                      Estimated Net Need
                    </span>
                    <div className="text-2xl font-black font-editorial text-[#0B1C10]">
                      {intel.decision.net_depth_mm !== null && intel.decision.net_depth_mm !== undefined ? (
                        <>
                          {intel.decision.net_depth_mm}{' '}
                          <span className="text-xs font-sans font-medium text-[#536056]">mm</span>
                        </>
                      ) : (
                        <span className="text-xs font-sans font-normal text-slate-500">Uncalculated</span>
                      )}
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                      Gross Application
                    </span>
                    <div className="text-2xl font-black font-editorial text-[#0B1C10]">
                      {intel.decision.gross_depth_mm !== null && intel.decision.gross_depth_mm !== undefined ? (
                        <>
                          {intel.decision.gross_depth_mm}{' '}
                          <span className="text-xs font-sans font-medium text-[#536056]">mm</span>
                        </>
                      ) : (
                        <span className="text-xs font-sans font-normal text-slate-500">--</span>
                      )}
                    </div>
                    <span className="text-[9px] text-[#536056] block">
                      {intel.decision.efficiency_note || intel.field_context.irrigation_method}
                    </span>
                  </div>

                  <div className="col-span-2 sm:col-span-1 p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                      Field Water Volume
                    </span>
                    <div className="text-2xl font-black font-editorial text-[#0B1C10]">
                      {intel.decision.water_volume_liters !== null && intel.decision.water_volume_liters !== undefined ? (
                        <>
                          {(intel.decision.water_volume_liters / 1000).toFixed(1)}k{' '}
                          <span className="text-xs font-sans font-medium text-[#536056]">Liters</span>
                        </>
                      ) : (
                        <span className="text-xs font-sans font-normal text-slate-500">N/A</span>
                      )}
                    </div>
                    <span className="text-[9px] text-[#536056] block">
                      For {intel.field_context.area_value} {intel.field_context.area_unit}
                    </span>
                  </div>
                </div>
              </div>

              {/* Evidence Explainer Checklist (5 Cols) */}
              <div className="lg:col-span-5 p-5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-4">
                <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[#2F6B3C]" />
                    <h3 className="text-xs font-extrabold uppercase tracking-widest text-[#0B1C10]">
                      Why This Recommendation?
                    </h3>
                  </div>
                  <span className="text-[10px] font-bold text-[#536056]">Decision Evidence</span>
                </div>

                <ul className="space-y-2.5">
                  {intel.evidence_items.map((ev, idx) => (
                    <li key={idx} className="flex items-start gap-2.5 text-xs text-[#162018]">
                      <CheckCircle2 className="w-4 h-4 text-[#2F6B3C] shrink-0 mt-0.5" />
                      <span className="leading-snug">{ev}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </GlassCard>

          {/* ============================================================ */}
          {/* 2. SOIL WATER BALANCE TRAJECTORY TIMELINE CHART */}
          {/* ============================================================ */}
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                  AGRONOMIC WATER BALANCE TIMELINE
                </span>
                <h3 className="text-xl font-black font-editorial text-[#0B1C10] mt-0.5">
                  Soil Water Content Trajectory & Rainfall Forecast
                </h3>
              </div>

              <div className="flex items-center gap-4 text-xs font-semibold text-[#536056]">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-1 bg-[#2F6B3C] rounded-full inline-block" />
                  <span>SWC Forecast</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-1 bg-amber-500 rounded-full inline-block" />
                  <span>Critical Threshold</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 bg-sky-400/40 rounded inline-block" />
                  <span>Rainfall (mm)</span>
                </div>
              </div>
            </div>

            <div className="h-[280px] w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={intel.water_balance_trajectory}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="swcGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2F6B3C" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#2F6B3C" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E7DA" vertical={false} />
                  <XAxis
                    dataKey="label"
                    tickLine={false}
                    axisLine={{ stroke: '#E2E7DA' }}
                    tick={{ fill: '#536056', fontSize: 11, fontWeight: 600 }}
                  />
                  <YAxis
                    yAxisId="swc"
                    domain={[0.1, 0.35]}
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: '#536056', fontSize: 11 }}
                  />
                  <YAxis
                    yAxisId="rain"
                    orientation="right"
                    domain={[0, 40]}
                    tickLine={false}
                    axisLine={false}
                    hide
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="p-3 bg-[#0B1C10] text-white rounded-xl shadow-xl border border-white/10 text-xs space-y-1">
                            <p className="font-bold text-[#D4E768]">{data.label} ({data.timestamp})</p>
                            <p>
                              SWC: <strong className="text-white">{data.swc_projected} m³/m³</strong>
                            </p>
                            <p>
                              Rainfall: <strong className="text-sky-300">{data.rainfall_mm} mm</strong>
                            </p>
                            <p>
                              Crop ETc: <strong className="text-amber-300">{data.etc_mm} mm</strong>
                            </p>
                            <p className="text-[10px] text-slate-300 border-t border-white/10 pt-1">
                              Status: {data.status}
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <ReferenceLine
                    yAxisId="swc"
                    y={intel.water_status.critical_threshold}
                    stroke="#D97706"
                    strokeDasharray="4 4"
                    label={{
                      value: `Critical (${intel.water_status.critical_threshold})`,
                      fill: '#D97706',
                      fontSize: 10,
                      position: 'insideTopRight',
                    }}
                  />
                  <Bar yAxisId="rain" dataKey="rainfall_mm" fill="#38BDF8" opacity={0.6} radius={[4, 4, 0, 0]} />
                  <Area
                    yAxisId="swc"
                    type="monotone"
                    dataKey="swc_projected"
                    stroke="#2F6B3C"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#swcGrad)"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </GlassCard>

          {/* ============================================================ */}
          {/* 3. SOIL WATER BALANCE GAUGE & ET0 CROP DEMAND */}
          {/* ============================================================ */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Soil Water Balance Gauge (6 Cols) */}
            <div className="lg:col-span-6">
              <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6 h-full flex flex-col justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Gauge className="w-4 h-4 text-[#2F6B3C]" />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056]">
                      SOIL WATER BALANCE GAUGE
                    </span>
                  </div>
                  <h3 className="text-xl font-black font-editorial text-[#0B1C10]">
                    Current Water Reserve Status
                  </h3>
                </div>

                {/* Progress Bar / Zone Display */}
                <div className="space-y-3 my-4">
                  <div className="flex items-center justify-between text-xs font-bold text-[#0B1C10]">
                    <span>Current SWC: {intel.water_status.current_swc} m³/m³</span>
                    <span className="text-[#2F6B3C]">{intel.water_status.water_zone}</span>
                  </div>

                  <div className="w-full h-4 bg-slate-200 rounded-full overflow-hidden relative border border-[#E2E7DA]">
                    {/* Visual markers */}
                    <div
                      className="h-full bg-gradient-to-r from-rose-500 via-amber-500 to-[#2F6B3C] rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(
                          100,
                          Math.max(
                            5,
                            ((intel.water_status.current_swc - intel.water_status.wilting_point) /
                              (intel.water_status.field_capacity - intel.water_status.wilting_point)) *
                              100
                          )
                        )}%`,
                      }}
                    />
                  </div>

                  <div className="flex justify-between text-[10px] font-bold text-[#536056]">
                    <span>Wilting Pt ({intel.water_status.wilting_point})</span>
                    <span className="text-amber-700">Critical ({intel.water_status.critical_threshold})</span>
                    <span>Field Cap ({intel.water_status.field_capacity})</span>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs space-y-1">
                  <span className="font-extrabold text-[#0B1C10] block">{intel.water_status.status_title}</span>
                  <p className="text-[#536056] leading-relaxed">{intel.water_status.status_description}</p>
                </div>
              </GlassCard>
            </div>

            {/* FAO-56 Evapotranspiration & Kc Engine (6 Cols) */}
            <div className="lg:col-span-6">
              <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6 h-full flex flex-col justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Sun className="w-4 h-4 text-amber-600" />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056]">
                      FAO-56 EVAPOTRANSPIRATION ENGINE
                    </span>
                  </div>
                  <h3 className="text-xl font-black font-editorial text-[#0B1C10]">
                    Crop Water Requirement (ETc)
                  </h3>
                </div>

                <div className="grid grid-cols-3 gap-3 my-2">
                  <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] text-center space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                      Ref ET₀
                    </span>
                    <span className="text-2xl font-black font-editorial text-[#0B1C10] block">
                      {intel.et0.et0_today_mm}
                    </span>
                    <span className="text-[9px] text-[#536056] block">mm/day</span>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-center space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                      Crop Kc
                    </span>
                    <span className="text-2xl font-black font-editorial text-[#2F6B3C] block">
                      {intel.et0.kc_value !== null && intel.et0.kc_value !== undefined ? intel.et0.kc_value : 'N/A'}
                    </span>
                    <span className="text-[9px] text-[#536056] block">{intel.field_context.growth_stage}</span>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-center space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                      Crop ETc
                    </span>
                    <span className="text-2xl font-black font-editorial text-amber-800 block">
                      {intel.et0.etc_today_mm !== null && intel.et0.etc_today_mm !== undefined
                        ? intel.et0.etc_today_mm
                        : 'N/A'}
                    </span>
                    <span className="text-[9px] text-[#536056] block">mm/day</span>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-[#EEF3E8] text-xs text-[#162018] leading-relaxed border border-[#E2E7DA]">
                  <span className="font-bold text-[#0B1C10] block mb-0.5">Methodology Note:</span>
                  {intel.et0.kc_note}
                </div>
              </GlassCard>
            </div>
          </div>

          {/* ============================================================ */}
          {/* 4. 7-DAY WATER PLAN */}
          {/* ============================================================ */}
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
            <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                  AGRONOMIC SCHEDULING
                </span>
                <h3 className="text-xl font-black font-editorial text-[#0B1C10] mt-0.5">
                  7-Day Water Advisory Plan
                </h3>
              </div>
              <Calendar className="w-5 h-5 text-[#2F6B3C]" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
              {intel.seven_day_plan.map((item, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-2xl border space-y-2 flex flex-col justify-between transition-all ${
                    item.status === 'Irrigate'
                      ? 'bg-amber-500/10 border-amber-500/30 text-amber-950'
                      : item.status === 'Wait for Rain'
                      ? 'bg-sky-500/10 border-sky-500/30 text-sky-950'
                      : 'bg-[#FAFBF7] border-[#E2E7DA] text-[#0B1C10]'
                  }`}
                >
                  <div className="space-y-1">
                    <span className="text-xs font-black block">{item.day}</span>
                    <span className="text-[10px] text-[#536056] block">{item.date_str}</span>
                  </div>

                  <div className="space-y-1 my-2">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-extrabold ${
                        item.status === 'Irrigate'
                          ? 'bg-amber-600 text-white'
                          : item.status === 'Wait for Rain'
                          ? 'bg-sky-600 text-white'
                          : 'bg-[#EEF3E8] text-[#2F6B3C]'
                      }`}
                    >
                      {item.status}
                    </span>
                    <p className="text-[10px] font-medium leading-tight">{item.action}</p>
                  </div>

                  <div className="pt-2 border-t border-black/5 text-[9px] text-[#536056] space-y-0.5">
                    <p>Rain: {item.rain_expected_mm} mm</p>
                    <p>ETc: {item.etc_mm} mm</p>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* ============================================================ */}
          {/* 5. WATER BUDGET & RAIN DEFERRAL OPPORTUNITIES */}
          {/* ============================================================ */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Water Budget Card (6 Cols) */}
            <div className="lg:col-span-6">
              <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5 h-full">
                <div className="space-y-1 border-b border-[#E2E7DA] pb-4">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                    FIELD BALANCE SHEET
                  </span>
                  <h3 className="text-xl font-black font-editorial text-[#0B1C10]">
                    Weekly Field Water Budget
                  </h3>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-1">
                    <span className="text-[10px] font-bold text-[#536056] block uppercase">Rainfall Received</span>
                    <span className="text-xl font-black font-editorial text-sky-700 block">
                      {intel.water_budget.rainfall_received_mm} mm
                    </span>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-1">
                    <span className="text-[10px] font-bold text-[#536056] block uppercase">Irrigation Applied</span>
                    <span className="text-xl font-black font-editorial text-[#2F6B3C] block">
                      {intel.water_budget.irrigation_applied_mm} mm
                    </span>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-1">
                    <span className="text-[10px] font-bold text-[#536056] block uppercase">Crop Water Consumed</span>
                    <span className="text-xl font-black font-editorial text-amber-800 block">
                      {intel.water_budget.crop_consumed_mm} mm
                    </span>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1">
                    <span className="text-[10px] font-bold text-[#2F6B3C] block uppercase">Estimated Deficit</span>
                    <span className="text-xl font-black font-editorial text-[#0B1C10] block">
                      {intel.water_budget.estimated_deficit_mm} mm
                    </span>
                  </div>
                </div>
              </GlassCard>
            </div>

            {/* Rain Deferral & Water Saving Opportunities (6 Cols) */}
            <div className="lg:col-span-6">
              <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5 h-full flex flex-col justify-between">
                <div className="space-y-1 border-b border-[#E2E7DA] pb-4">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-[#2F6B3C]" />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056]">
                      EFFICIENCY OPPORTUNITIES
                    </span>
                  </div>
                  <h3 className="text-xl font-black font-editorial text-[#0B1C10]">
                    Water-Saving Insights & Rainfall Deferral
                  </h3>
                </div>

                <div className="space-y-3 my-2">
                  {intel.water_saving_opportunities.map((opp, idx) => (
                    <div key={idx} className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-black text-[#0B1C10]">{opp.title}</span>
                        {opp.potential_water_saved_liters && (
                          <span className="text-[10px] font-extrabold text-[#2F6B3C] bg-[#EEF3E8] px-2 py-0.5 rounded-full">
                            Save ~{(opp.potential_water_saved_liters / 1000).toFixed(0)}k L
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[#536056] leading-relaxed">{opp.description}</p>
                    </div>
                  ))}
                </div>

                <p className="text-[10px] text-[#536056] italic">
                  Note: Potential water savings are calculated based on deferred application depth over field area.
                </p>
              </GlassCard>
            </div>
          </div>

          {/* ============================================================ */}
          {/* 6. WHAT-IF SCENARIO SIMULATOR */}
          {/* ============================================================ */}
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E7DA] pb-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                  DECISION SIMULATION TOOL
                </span>
                <h3 className="text-xl font-black font-editorial text-[#0B1C10] mt-0.5">
                  "What-If?" Water Management Simulator
                </h3>
              </div>

              <span className="text-xs text-[#536056] bg-[#FAFBF7] px-3 py-1.5 rounded-xl border border-[#E2E7DA]">
                Simulate custom irrigation timing & forecast rainfall impact
              </span>
            </div>

            <form onSubmit={handleRunSimulation} className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
              <Input
                label="Custom Irrigation (mm)"
                type="number"
                step="1"
                min="0"
                value={simForm.custom_irrigation_mm}
                onChange={(e) => setSimForm({ ...simForm, custom_irrigation_mm: parseFloat(e.target.value) || 0 })}
              />

              <Input
                label="Irrigation Delay (Hours)"
                type="number"
                step="6"
                min="0"
                max="72"
                value={simForm.delay_hours}
                onChange={(e) => setSimForm({ ...simForm, delay_hours: parseInt(e.target.value, 10) || 0 })}
              />

              <Input
                label="Simulated Rain (mm)"
                type="number"
                step="1"
                min="0"
                value={simForm.simulated_rain_mm}
                onChange={(e) => setSimForm({ ...simForm, simulated_rain_mm: parseFloat(e.target.value) || 0 })}
              />

              <div className="sm:col-span-3">
                <Button
                  type="submit"
                  variant="lime"
                  size="md"
                  isLoading={simulating}
                  icon={<Sparkles className="w-4 h-4" />}
                >
                  Run What-If Simulation
                </Button>
              </div>
            </form>

            {/* Simulation Results Display */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
              {(simResult?.scenarios || intel.what_if_scenarios).map((sc, idx) => (
                <div key={idx} className="p-5 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-3">
                  <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-2">
                    <span className="text-xs font-black text-[#0B1C10]">{sc.scenario_name}</span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        sc.risk_level === 'Low' || sc.risk_level === 'Optimal'
                          ? 'bg-emerald-100 text-emerald-800'
                          : sc.risk_level === 'Moderate'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}
                    >
                      {sc.risk_level} Risk
                    </span>
                  </div>

                  <p className="text-xs text-[#536056] leading-relaxed">{sc.description}</p>

                  <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                    <div>
                      <span className="text-[10px] text-[#536056] block">Projected 48h SWC</span>
                      <strong className="text-[#0B1C10] text-sm">{sc.projected_swc_48h} m³/m³</strong>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#536056] block">Water Deficit</span>
                      <strong className="text-amber-800 text-sm">{sc.deficit_mm} mm</strong>
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-[#EEF3E8] text-[11px] font-medium text-[#2F6B3C]">
                    💡 {sc.recommendation}
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* ============================================================ */}
          {/* 7. FROZEN SHORT-HORIZON ML SIGNAL & PERSISTENCE BASELINE */}
          {/* ============================================================ */}
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E2E7DA] pb-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                  SUPPORTING SIGNAL LAYER
                </span>
                <h3 className="text-lg font-black font-editorial text-[#0B1C10]">
                  Frozen 3-Hour ML Soil Water Forecast
                </h3>
              </div>
              <span className="text-xs text-[#536056] bg-[#FAFBF7] px-3 py-1 rounded-xl border border-[#E2E7DA]">
                Model: <strong className="text-[#0B1C10]">irrigation_prediction.pkl</strong>
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#2F6B3C] block">
                  ML Model Forecast (t+3h)
                </span>
                <div className="text-3xl font-black font-editorial text-[#0B1C10]">
                  {intel.ml_forecast.ml_predicted_swc_3h}{' '}
                  <span className="text-xs font-sans font-medium text-[#536056]">m³/m³</span>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                  Persistence Benchmark (t+3h)
                </span>
                <div className="text-3xl font-black font-editorial text-[#0B1C10]">
                  {intel.ml_forecast.persistence_swc_3h}{' '}
                  <span className="text-xs font-sans font-medium text-[#536056]">m³/m³</span>
                </div>
              </div>
            </div>

            <p className="text-xs text-[#536056] leading-relaxed bg-[#FAFBF7] p-3.5 rounded-xl border border-[#E2E7DA]">
              {intel.ml_forecast.baseline_note}
            </p>
          </GlassCard>

          {/* ============================================================ */}
          {/* 8. HISTORICAL IRRIGATION LOG TABLE */}
          {/* ============================================================ */}
          <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5">
            <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#536056] block">
                  FIELD AUDIT LOG
                </span>
                <h3 className="text-xl font-black font-editorial text-[#0B1C10] mt-0.5">
                  Historical Irrigation Log
                </h3>
              </div>
              <Button
                variant="lime"
                size="sm"
                onClick={() => setShowLogModal(true)}
                icon={<PlusCircle className="w-3.5 h-3.5" />}
              >
                + Log Irrigation
              </Button>
            </div>

            {intel.irrigation_history.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-[#EEF3E8] text-[#2F6B3C] uppercase font-bold text-[10px]">
                    <tr>
                      <th className="px-4 py-3 rounded-l-xl">Date & Time</th>
                      <th className="px-4 py-3">Water Amount</th>
                      <th className="px-4 py-3">Volume (L)</th>
                      <th className="px-4 py-3">Method</th>
                      <th className="px-4 py-3">Duration</th>
                      <th className="px-4 py-3 rounded-r-xl">Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E7DA]">
                    {intel.irrigation_history.map((log) => (
                      <tr key={log.id} className="hover:bg-[#FAFBF7]">
                        <td className="px-4 py-3 font-semibold text-[#0B1C10]">{log.logged_at}</td>
                        <td className="px-4 py-3 font-bold text-[#2F6B3C]">{log.water_amount_mm} mm</td>
                        <td className="px-4 py-3 text-[#536056]">
                          {log.water_amount_liters ? `${log.water_amount_liters.toLocaleString()} L` : '--'}
                        </td>
                        <td className="px-4 py-3">{log.method}</td>
                        <td className="px-4 py-3 text-[#536056]">
                          {log.duration_minutes ? `${log.duration_minutes} mins` : '--'}
                        </td>
                        <td className="px-4 py-3 text-[#536056] italic">{log.notes || '--'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-xs text-[#536056] italic py-4 text-center">
                No recorded irrigation events for this field yet. Click "+ Log Irrigation" to record an application.
              </p>
            )}
          </GlassCard>
        </div>
      )}

      {/* ============================================================ */}
      {/* 9. MODAL: + LOG IRRIGATION EVENT */}
      {/* ============================================================ */}
      {showLogModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-8 space-y-5 shadow-2xl border border-[#E2E7DA]">
            <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
              <div className="flex items-center gap-2">
                <Droplets className="w-5 h-5 text-[#2F6B3C]" />
                <h3 className="text-lg font-black font-editorial text-[#0B1C10]">
                  Record Applied Irrigation
                </h3>
              </div>
              <button
                onClick={() => setShowLogModal(false)}
                className="p-1 rounded-lg text-[#536056] hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleLogSubmit} className="space-y-4">
              <Input
                label="Water Amount Applied (mm)"
                type="number"
                step="0.5"
                min="0.5"
                value={logForm.water_amount_mm}
                onChange={(e) => setLogForm({ ...logForm, water_amount_mm: parseFloat(e.target.value) || 0 })}
                required
              />

              <div className="space-y-1">
                <label className="text-xs font-bold text-[#0B1C10] block">Irrigation Method</label>
                <select
                  className="w-full bg-[#FAFBF7] border border-[#E2E7DA] rounded-xl px-3 py-2 text-xs font-medium text-[#0B1C10]"
                  value={logForm.method}
                  onChange={(e) => setLogForm({ ...logForm, method: e.target.value })}
                >
                  <option value="Drip">Drip Irrigation (85% Efficiency)</option>
                  <option value="Sprinkler">Sprinkler Irrigation (75% Efficiency)</option>
                  <option value="Surface">Surface Irrigation (60% Efficiency)</option>
                  <option value="Flood">Flood / Basin (50% Efficiency)</option>
                </select>
              </div>

              <Input
                label="Duration (Minutes)"
                type="number"
                step="5"
                min="0"
                value={logForm.duration_minutes}
                onChange={(e) => setLogForm({ ...logForm, duration_minutes: parseInt(e.target.value, 10) || 0 })}
              />

              <Input
                label="Notes / Observations"
                type="text"
                placeholder="e.g. Evening drip cycle after fertilizer application"
                value={logForm.notes}
                onChange={(e) => setLogForm({ ...logForm, notes: e.target.value })}
              />

              <div className="pt-2 flex justify-end gap-3">
                <Button variant="outline" type="button" onClick={() => setShowLogModal(false)}>
                  Cancel
                </Button>
                <Button variant="lime" type="submit" isLoading={submittingLog}>
                  Save Log Entry
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* 10. DRAWER: ADVANCED MANUAL TELEMETRY */}
      {/* ============================================================ */}
      {showManualDrawer && (
        <GlassCard variant="solid" className="p-6 sm:p-8 space-y-5 border-t-2 border-t-amber-500">
          <div className="flex items-center justify-between border-b border-[#E2E7DA] pb-4">
            <div className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-amber-600" />
              <h3 className="text-base font-black font-editorial text-[#0B1C10]">
                Advanced / Manual Soil Moisture Telemetry Input
              </h3>
            </div>
            <button onClick={() => setShowManualDrawer(false)} className="text-xs text-[#536056] underline">
              Close Drawer
            </button>
          </div>

          <form onSubmit={handleManualMlSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <Input
                label="Current SWC"
                type="number"
                step="0.001"
                value={manualMlData.SWC}
                onChange={(e) => setManualMlData({ ...manualMlData, SWC: parseFloat(e.target.value) || 0 })}
              />
              <Input
                label="Lag 1h"
                type="number"
                step="0.001"
                value={manualMlData.SWC_lag1h}
                onChange={(e) => setManualMlData({ ...manualMlData, SWC_lag1h: parseFloat(e.target.value) || 0 })}
              />
              <Input
                label="Lag 2h"
                type="number"
                step="0.001"
                value={manualMlData.SWC_lag2h}
                onChange={(e) => setManualMlData({ ...manualMlData, SWC_lag2h: parseFloat(e.target.value) || 0 })}
              />
              <Input
                label="Lag 3h"
                type="number"
                step="0.001"
                value={manualMlData.SWC_lag3h}
                onChange={(e) => setManualMlData({ ...manualMlData, SWC_lag3h: parseFloat(e.target.value) || 0 })}
              />
            </div>

            <Button type="submit" variant="outline" size="sm" isLoading={loadingManualMl}>
              Test Manual ML Inference
            </Button>
          </form>

          {manualMlResult && (
            <div className="p-4 rounded-2xl bg-[#FAFBF7] border border-[#E2E7DA] text-xs space-y-2">
              <p>
                <strong>ML Predicted 3h SWC:</strong> {manualMlResult.ml_predicted_swc_3h} m³/m³
              </p>
              <p>
                <strong>Persistence Benchmark:</strong> {manualMlResult.persistence_swc_3h} m³/m³
              </p>
              <p>
                <strong>Agronomic Status:</strong> {manualMlResult.agronomic_status.status_message}
              </p>
            </div>
          )}
        </GlassCard>
      )}
    </div>
  );
};
