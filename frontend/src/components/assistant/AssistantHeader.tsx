import React from 'react';
import { Bot, Sparkles, History, Plus, Minus, X, MapPin, Sprout } from 'lucide-react';
import { useFarmAICopilot } from '../../context/FarmAICopilotContext';

export const AssistantHeader: React.FC = () => {
  const {
    pageContext,
    startNewConversation,
    minimizeAssistant,
    closeAssistant,
    isHistoryOpen,
    setIsHistoryOpen,
  } = useFarmAICopilot();

  const fieldName = pageContext.selected_field_name;
  const cropName = pageContext.selected_crop_name;
  const locationName = pageContext.selected_location?.displayName;

  return (
    <div className="flex flex-col border-b border-emerald-500/15 bg-gradient-to-r from-emerald-950/90 via-slate-950/90 to-emerald-950/90 backdrop-blur-lg px-4 py-3 select-none">
      <div className="flex items-center justify-between gap-2">
        {/* Title & Status */}
        <div className="flex items-center gap-2.5">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-700/30 border border-emerald-500/30 text-emerald-300 shadow-inner">
            <Bot className="w-5 h-5" />
            <Sparkles className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 text-lime-400" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm text-emerald-50 tracking-wide">AgriNexus AI</h3>
              <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Copilot
              </span>
            </div>
            <p className="text-[11px] text-emerald-200/60 font-normal">Intelligent farming companion</p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsHistoryOpen(!isHistoryOpen)}
            title="Conversation History"
            aria-label="Toggle history"
            className={`p-1.5 rounded-lg text-emerald-200/70 hover:text-emerald-100 hover:bg-emerald-900/40 transition-colors ${
              isHistoryOpen ? 'bg-emerald-900/60 text-emerald-300' : ''
            }`}
          >
            <History className="w-4 h-4" />
          </button>

          <button
            onClick={startNewConversation}
            title="New Conversation"
            aria-label="Start new conversation"
            className="p-1.5 rounded-lg text-emerald-200/70 hover:text-emerald-100 hover:bg-emerald-900/40 transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>

          <button
            onClick={minimizeAssistant}
            title="Minimize"
            aria-label="Minimize assistant"
            className="p-1.5 rounded-lg text-emerald-200/70 hover:text-emerald-100 hover:bg-emerald-900/40 transition-colors"
          >
            <Minus className="w-4 h-4" />
          </button>

          <button
            onClick={closeAssistant}
            title="Close"
            aria-label="Close assistant"
            className="p-1.5 rounded-lg text-emerald-200/70 hover:text-emerald-100 hover:bg-emerald-900/40 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Context Pill (Field/Location Awareness) */}
      {(fieldName || locationName || pageContext.page_name) && (
        <div className="flex items-center gap-2 mt-2 pt-2 border-t border-emerald-500/10 text-[11px] text-emerald-300/80 overflow-x-auto no-scrollbar">
          <span className="shrink-0 font-medium px-2 py-0.5 rounded bg-emerald-900/50 text-emerald-200 border border-emerald-500/20">
            {pageContext.page_name}
          </span>

          {fieldName && (
            <span className="inline-flex items-center gap-1 shrink-0 px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/20">
              <Sprout className="w-3 h-3 text-emerald-400" />
              {fieldName} {cropName ? `· ${cropName}` : ''}
            </span>
          )}

          {locationName && (
            <span className="inline-flex items-center gap-1 shrink-0 px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/20 max-w-[160px] truncate">
              <MapPin className="w-3 h-3 text-emerald-400 shrink-0" />
              <span className="truncate">{locationName}</span>
            </span>
          )}
        </div>
      )}
    </div>
  );
};
