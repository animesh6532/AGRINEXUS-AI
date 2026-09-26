import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  Calendar,
  Check,
  ChevronRight,
  Filter,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import type { ActionPlanItem } from '../../types/farmer';

interface PersonalizedActionPlanProps {
  actions?: ActionPlanItem[];
  onCompleteAction?: (actionId: string, status: string) => Promise<void>;
  onNavigateToModule?: (route: string) => void;
}

export const PersonalizedActionPlan: React.FC<PersonalizedActionPlanProps> = ({
  actions = [],
  onCompleteAction,
  onNavigateToModule,
}) => {
  const [selectedTimeWindow, setSelectedTimeWindow] = useState<string>('ALL');
  const [completingId, setCompletingId] = useState<string | null>(null);

  const handleStatusChange = async (id: string, status: string) => {
    if (!onCompleteAction) return;
    setCompletingId(id);
    try {
      await onCompleteAction(id, status);
    } finally {
      setCompletingId(null);
    }
  };

  const filteredActions = actions.filter((action) => {
    if (selectedTimeWindow === 'ALL') return true;
    const window = (action.time_window || action.recommended_time || 'TODAY').toUpperCase();
    return window.includes(selectedTimeWindow);
  });

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-[#0B1C10] text-[#FAFBF7] border border-white/10 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-[#D4E768]" />
            <h3 className="text-xl font-extrabold font-editorial text-white">MY ACTION PLAN</h3>
          </div>
          <p className="text-xs text-white/60">
            Prioritized agronomic action items generated from live weather, crop stage, soil, and market risk signals
          </p>
        </div>

        {/* Time Window Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none bg-white/10 p-1.5 rounded-2xl border border-white/10">
          {['ALL', 'TODAY', 'TOMORROW', 'THIS_WEEK', 'UPCOMING'].map((tw) => (
            <button
              key={tw}
              onClick={() => setSelectedTimeWindow(tw)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                selectedTimeWindow === tw
                  ? 'bg-[#D4E768] text-[#0B1C10] shadow-sm'
                  : 'text-white/70 hover:text-white'
              }`}
            >
              {tw.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Action Items List */}
      {filteredActions.length > 0 ? (
        <div className="space-y-4">
          {filteredActions.map((item, index) => {
            const isCritical = item.priority === 'critical' || item.priority === 'high';
            const isDone = item.status === 'DONE';

            return (
              <GlassCard
                key={item.id || index}
                variant="solid"
                className={`p-5 space-y-4 border-l-4 transition-all ${
                  isDone
                    ? 'opacity-60 bg-gray-50 border-l-gray-400'
                    : isCritical
                    ? 'border-l-rose-500 bg-rose-50/10'
                    : 'border-l-amber-500 bg-amber-50/10'
                } border-[#E2E7DA]`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E2E7DA] pb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-9 h-9 rounded-2xl flex items-center justify-center font-bold text-xs ${
                        isDone
                          ? 'bg-gray-200 text-gray-700'
                          : isCritical
                          ? 'bg-rose-100 text-rose-700'
                          : 'bg-amber-100 text-amber-700'
                      }`}
                    >
                      #{index + 1}
                    </div>
                    <div>
                      <h4 className="text-base font-extrabold text-[#0B1C10] font-editorial">
                        {item.title}
                      </h4>
                      <p className="text-xs text-[#536056] font-medium">
                        {item.affected_crop ? `Crop: ${item.affected_crop}` : 'Farm Operation'} • Priority:{' '}
                        <strong className="text-[#0B1C10] uppercase">{item.priority}</strong>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant={isCritical ? 'danger' : 'warning'}>
                      {item.time_window || item.recommended_time || 'TODAY'}
                    </Badge>
                  </div>
                </div>

                {/* Actionable Explanation */}
                <div className="space-y-2 text-xs">
                  <p className="text-[#0B1C10] font-semibold text-sm leading-relaxed">
                    {item.action}
                  </p>
                  <p className="text-[#536056]">
                    <strong>Reason / Signal:</strong> {item.reason}
                  </p>
                </div>

                {/* Action Status Controls */}
                <div className="flex items-center justify-between pt-2 border-t border-[#E2E7DA]">
                  <div className="flex items-center gap-2">
                    {!isDone ? (
                      <Button
                        onClick={() => handleStatusChange(item.id, 'DONE')}
                        variant="lime"
                        size="sm"
                        disabled={completingId === item.id}
                        icon={<Check className="w-4 h-4" />}
                      >
                        Mark Done
                      </Button>
                    ) : (
                      <Badge variant="success">✓ Completed</Badge>
                    )}

                    {!isDone && (
                      <button
                        type="button"
                        onClick={() => handleStatusChange(item.id, 'DISMISSED')}
                        className="px-3 py-1.5 rounded-xl text-xs font-semibold text-gray-500 hover:text-gray-800 transition-colors"
                      >
                        Dismiss
                      </button>
                    )}
                  </div>

                  {onNavigateToModule && (
                    <button
                      type="button"
                      onClick={() => onNavigateToModule('/irrigation')}
                      className="text-xs text-[#2F6B3C] font-bold hover:underline flex items-center gap-1"
                    >
                      Open Module <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </GlassCard>
            );
          })}
        </div>
      ) : (
        <GlassCard variant="solid" className="p-8 text-center space-y-3">
          <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
          <h4 className="text-base font-bold text-[#0B1C10]">All Action Items Complete</h4>
          <p className="text-xs text-[#536056]">
            No outstanding action items for the selected time window. Your farm operations are up to date!
          </p>
        </GlassCard>
      )}
    </div>
  );
};
