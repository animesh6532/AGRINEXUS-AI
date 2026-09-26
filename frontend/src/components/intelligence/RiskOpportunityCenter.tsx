import React, { useState } from 'react';
import {
  ShieldAlert,
  Sparkles,
  AlertTriangle,
  Clock,
  TrendingUp,
  CloudSun,
  Droplets,
  Sprout,
  CheckCircle2,
  Filter,
  Layers,
  ArrowRight,
  Info,
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import type { RiskItem, OpportunityItem, ImpactMatrixRow } from '../../types/farmer';

interface RiskOpportunityCenterProps {
  risks?: RiskItem[];
  opportunities?: OpportunityItem[];
  impactMatrix?: ImpactMatrixRow[];
  onNavigateToActionPlan?: () => void;
}

export const RiskOpportunityCenter: React.FC<RiskOpportunityCenterProps> = ({
  risks = [],
  opportunities = [],
  impactMatrix = [],
  onNavigateToActionPlan,
}) => {
  const [activeTab, setActiveTab] = useState<'all' | 'risks' | 'opportunities' | 'matrix'>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  // Count summaries
  const criticalCount = risks.filter((r) => r.severity === 'critical' || r.severity === 'high').length;
  const watchCount = risks.filter((r) => r.severity === 'medium' || r.severity === 'low').length;
  const oppCount = opportunities.length;

  const filteredRisks = risks.filter((r) => {
    if (severityFilter === 'ALL') return true;
    return r.severity.toUpperCase() === severityFilter;
  });

  return (
    <div className="space-y-6">
      {/* Top Header & Summary Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-[#0B1C10] text-[#FAFBF7] border border-white/10 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-[#D4E768]" />
            <h3 className="text-xl font-extrabold font-editorial text-white">
              RISK & OPPORTUNITY CENTER
            </h3>
          </div>
          <p className="text-xs text-white/60">
            Evidence-based decision-intelligence engine scanning weather, soil, water, market, and crop growth signals
          </p>
        </div>

        {/* Counter Pills */}
        <div className="flex items-center gap-2">
          <span className="px-3.5 py-1.5 rounded-full bg-rose-500/20 border border-rose-500/30 text-rose-300 font-bold text-xs flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> {criticalCount} Critical / High Risks
          </span>
          <span className="px-3.5 py-1.5 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-300 font-bold text-xs flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" /> {watchCount} Watch Items
          </span>
          <span className="px-3.5 py-1.5 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 font-bold text-xs flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" /> {oppCount} Opportunities
          </span>
        </div>
      </div>

      {/* Navigation Tabs & Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E2E7DA] pb-2">
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-none">
          {[
            { id: 'all', label: 'All Items' },
            { id: 'risks', label: `Risks (${risks.length})` },
            { id: 'opportunities', label: `Opportunities (${opportunities.length})` },
            { id: 'matrix', label: 'Field Risk Matrix' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-[#0B1C10] text-[#D4E768] shadow-md'
                  : 'bg-white/80 text-[#536056] hover:bg-[#EEF3E8] hover:text-[#0B1C10]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab !== 'matrix' && (
          <div className="flex items-center gap-2 text-xs">
            <Filter className="w-3.5 h-3.5 text-[#536056]" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-white border border-[#E2E7DA] rounded-xl px-3 py-1.5 text-xs font-bold text-[#0B1C10] focus:outline-none"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        )}
      </div>

      {/* TAB CONTENT */}

      {/* TAB: RISKS & OPPORTUNITIES (ALL / RISKS / OPPORTUNITIES) */}
      {activeTab !== 'matrix' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* RISKS LIST */}
          {(activeTab === 'all' || activeTab === 'risks') && (
            <div className="space-y-4">
              <h4 className="text-sm font-extrabold text-[#0B1C10] font-editorial flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600" /> FARM RISKS IDENTIFIED
              </h4>

              {filteredRisks.length > 0 ? (
                filteredRisks.map((risk) => (
                  <GlassCard
                    key={risk.id}
                    variant="solid"
                    className={`p-5 space-y-3 border-l-4 ${
                      risk.severity === 'critical' || risk.severity === 'high'
                        ? 'border-l-rose-500 bg-rose-50/20'
                        : 'border-l-amber-500 bg-amber-50/20'
                    } border-[#E2E7DA]`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={
                              risk.severity === 'critical' || risk.severity === 'high'
                                ? 'danger'
                                : 'warning'
                            }
                          >
                            {risk.severity.toUpperCase()} RISK
                          </Badge>
                          <span className="text-[11px] font-mono text-[#536056] font-bold">
                            Category: {risk.category}
                          </span>
                        </div>
                        <h5 className="text-base font-extrabold text-[#0B1C10] font-editorial mt-1">
                          {risk.title}
                        </h5>
                      </div>

                      <span className="text-[10px] font-bold px-2 py-1 bg-white rounded-lg border border-[#E2E7DA] text-[#536056]">
                        Time: Next 24-48h
                      </span>
                    </div>

                    <p className="text-xs text-[#0B1C10] font-medium">{risk.description}</p>

                    {risk.reasoning && (
                      <div className="p-3 rounded-2xl bg-white/70 border border-[#E2E7DA] text-[11px] space-y-1">
                        <strong className="text-[#2F6B3C] block font-sans">Evidence & Trigger:</strong>
                        <p className="text-[#536056]">{risk.reasoning}</p>
                      </div>
                    )}

                    {risk.recommended_follow_up && (
                      <div className="p-3 rounded-2xl bg-[#0B1C10] text-[#FAFBF7] text-xs flex items-center justify-between">
                        <div>
                          <strong className="text-[#D4E768] block text-[10px]">RECOMMENDED ACTION</strong>
                          <span>{risk.recommended_follow_up}</span>
                        </div>
                        {onNavigateToActionPlan && (
                          <button
                            onClick={onNavigateToActionPlan}
                            className="p-1.5 rounded-xl bg-[#D4E768] text-[#0B1C10] hover:bg-[#c3d853] transition-colors shrink-0"
                            title="Open Action Plan"
                          >
                            <ArrowRight className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    )}
                  </GlassCard>
                ))
              ) : (
                <GlassCard variant="solid" className="p-6 text-center text-xs text-[#536056]">
                  No active risks recorded for the selected filter.
                </GlassCard>
              )}
            </div>
          )}

          {/* OPPORTUNITIES LIST */}
          {(activeTab === 'all' || activeTab === 'opportunities') && (
            <div className="space-y-4">
              <h4 className="text-sm font-extrabold text-[#0B1C10] font-editorial flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-600" /> FARM OPPORTUNITIES IDENTIFIED
              </h4>

              {opportunities.length > 0 ? (
                opportunities.map((opp) => (
                  <GlassCard
                    key={opp.id}
                    variant="solid"
                    className="p-5 space-y-3 border-l-4 border-l-emerald-500 bg-emerald-50/20 border-[#E2E7DA]"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant="success">OPPORTUNITY</Badge>
                          <span className="text-[11px] font-mono text-[#536056] font-bold">
                            Category: {opp.category}
                          </span>
                        </div>
                        <h5 className="text-base font-extrabold text-[#0B1C10] font-editorial mt-1">
                          {opp.title}
                        </h5>
                      </div>

                      {opp.time_window && (
                        <span className="text-[10px] font-bold px-2 py-1 bg-white rounded-lg border border-[#E2E7DA] text-[#536056]">
                          {opp.time_window}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-[#0B1C10] font-medium">{opp.description}</p>

                    {opp.suggested_action && (
                      <div className="p-3 rounded-2xl bg-[#EEF3E8] border border-[#E2E7DA] text-xs text-[#2F6B3C] font-semibold flex items-center justify-between">
                        <span>💡 {opp.suggested_action}</span>
                      </div>
                    )}
                  </GlassCard>
                ))
              ) : (
                <GlassCard variant="solid" className="p-6 text-center text-xs text-[#536056]">
                  No active opportunity signals detected.
                </GlassCard>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB: FIELD RISK MATRIX */}
      {activeTab === 'matrix' && (
        <GlassCard variant="solid" className="p-6 space-y-4 overflow-x-auto">
          <div className="border-b border-[#E2E7DA] pb-3">
            <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
              FIELD × RISK MATRIX
            </h3>
            <p className="text-xs text-[#536056]">
              Operational field status matrix across Weather, Water, Soil, Pest, Disease, Market, and Calendar
            </p>
          </div>

          {impactMatrix.length > 0 ? (
            <table className="w-full text-left text-xs font-sans border-collapse">
              <thead>
                <tr className="border-b border-[#E2E7DA] text-[#536056] font-bold uppercase text-[10px]">
                  <th className="py-3 px-3">Field / Crop</th>
                  <th className="py-3 px-3">Area</th>
                  <th className="py-3 px-3">Weather</th>
                  <th className="py-3 px-3">Soil</th>
                  <th className="py-3 px-3">Water</th>
                  <th className="py-3 px-3">Pest Risk</th>
                  <th className="py-3 px-3">Market</th>
                  <th className="py-3 px-3">Attention Level</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E7DA]">
                {impactMatrix.map((row, idx) => (
                  <tr key={idx} className="hover:bg-[#EEF3E8]/50 transition-colors font-medium">
                    <td className="py-3 px-3 font-extrabold text-[#0B1C10]">
                      {row.field_name} • {row.crop_name}
                    </td>
                    <td className="py-3 px-3 font-mono">{row.area_display}</td>
                    <td className="py-3 px-3">{row.weather}</td>
                    <td className="py-3 px-3">{row.soil}</td>
                    <td className="py-3 px-3">{row.water}</td>
                    <td className="py-3 px-3">{row.pest}</td>
                    <td className="py-3 px-3 text-emerald-700 font-bold">{row.market}</td>
                    <td className="py-3 px-3">
                      <Badge
                        variant={
                          row.attention_level === 'High'
                            ? 'danger'
                            : row.attention_level === 'Medium'
                            ? 'warning'
                            : 'success'
                        }
                      >
                        {row.attention_level}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-xs text-[#536056] italic">No active field records for risk matrix.</p>
          )}
        </GlassCard>
      )}
    </div>
  );
};
