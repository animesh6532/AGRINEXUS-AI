import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Sun, Droplets, TrendingUp, ShieldAlert, ArrowRight, Calendar, AlertTriangle } from 'lucide-react';
import type { AssistantAction, AssistantCard } from '../../types/assistant';

interface AssistantActionCardProps {
  card?: AssistantCard;
  actions?: AssistantAction[];
  onClosePanel?: () => void;
}

export const AssistantActionCard: React.FC<AssistantActionCardProps> = ({ card, actions, onClosePanel }) => {
  const navigate = useNavigate();

  const handleNavigate = (route: string) => {
    if (onClosePanel) onClosePanel();
    navigate(route);
  };

  return (
    <div className="flex flex-col gap-2 mt-2">
      {/* Visual Structured Card if present */}
      {card && (
        <div className="rounded-xl bg-gradient-to-br from-emerald-950/80 via-slate-900/90 to-emerald-900/50 border border-emerald-500/25 p-3.5 shadow-lg backdrop-blur-sm">
          {/* Card Header */}
          <div className="flex items-center justify-between border-b border-emerald-500/15 pb-2 mb-2">
            <div className="flex items-center gap-2">
              {card.type === 'weather' && <Sun className="w-4 h-4 text-amber-400" />}
              {card.type === 'irrigation' && <Droplets className="w-4 h-4 text-cyan-400" />}
              {card.type === 'market' && <TrendingUp className="w-4 h-4 text-emerald-400" />}
              {card.type === 'disease' && <ShieldAlert className="w-4 h-4 text-rose-400" />}
              {card.type === 'brief' && <Calendar className="w-4 h-4 text-lime-400" />}
              
              <span className="font-semibold text-xs text-emerald-100 tracking-wide">{card.title}</span>
            </div>

            {card.metric && (
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                {card.metric}
              </span>
            )}
          </div>

          {/* Subtitle / Details */}
          {card.subtitle && (
            <p className="text-xs font-medium text-emerald-200 mb-1">{card.subtitle}</p>
          )}
          {card.description && (
            <p className="text-xs text-emerald-200/80 mb-2 leading-relaxed">{card.description}</p>
          )}

          {/* Key Data Points */}
          {card.data_points && card.data_points.length > 0 && (
            <div className="grid grid-cols-2 gap-1.5 mb-3 bg-emerald-950/50 p-2 rounded-lg border border-emerald-500/10">
              {card.data_points.map((dp, idx) => (
                <div key={idx} className="flex flex-col">
                  <span className="text-[10px] text-emerald-200/60 uppercase">{dp.label}</span>
                  <span className="text-xs font-semibold text-emerald-100">{dp.value}</span>
                </div>
              ))}
            </div>
          )}

          {/* Card Action Button */}
          {card.action_route && (
            <button
              onClick={() => handleNavigate(card.action_route!)}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/40 text-emerald-100 font-medium text-xs transition-colors cursor-pointer"
            >
              <span>{card.action_label || 'View Details'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {/* Direct Navigation Action Buttons list */}
      {actions && actions.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-1">
          {actions.map((act, index) => (
            <button
              key={index}
              onClick={() => handleNavigate(act.route)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-900/60 hover:bg-emerald-800/80 border border-emerald-500/30 text-emerald-200 text-xs font-medium transition-all cursor-pointer shadow-sm"
            >
              <span>{act.label}</span>
              <ArrowRight className="w-3 h-3 text-emerald-400" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
