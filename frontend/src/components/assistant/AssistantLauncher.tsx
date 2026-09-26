import React, { useState, useEffect } from 'react';
import { Sparkles, Bot, MessageSquare } from 'lucide-react';
import { useFarmAICopilot } from '../../context/FarmAICopilotContext';

export const AssistantLauncher: React.FC = () => {
  const { isOpen, toggleAssistant } = useFarmAICopilot();
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  // Auto-collapse pill text after 6 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsExpanded(false);
    }, 6000);
    return () => clearTimeout(timer);
  }, []);

  if (isOpen) return null;

  return (
    <div
      className="fixed bottom-6 right-6 z-40 flex items-center gap-3 transition-all duration-300 ease-out"
      style={{
        paddingBottom: 'env(safe-area-inset-bottom, 0px)',
      }}
    >
      {/* Expanded Pill Label */}
      {isExpanded && (
        <button
          onClick={toggleAssistant}
          onMouseEnter={() => setIsExpanded(true)}
          className="hidden sm:flex items-center gap-2 px-4 py-2.5 rounded-full bg-emerald-950/80 backdrop-blur-md border border-emerald-500/30 text-emerald-100 text-sm font-medium shadow-xl hover:bg-emerald-900/90 hover:border-emerald-400/50 transition-all duration-200 cursor-pointer animate-fade-in"
        >
          <Sparkles className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span>Ask AgriNexus</span>
        </button>
      )}

      {/* Floating Circular Launcher Button */}
      <button
        onClick={toggleAssistant}
        onMouseEnter={() => setIsExpanded(true)}
        aria-label="Open AgriNexus AI assistant"
        className="group relative flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-gradient-to-br from-emerald-600 via-emerald-700 to-teal-900 text-white shadow-2xl shadow-emerald-950/60 border border-emerald-400/30 hover:scale-105 hover:border-emerald-300/60 active:scale-95 transition-all duration-200 cursor-pointer"
      >
        {/* Soft Ambient Glow Effect */}
        <span className="absolute -inset-1 rounded-full bg-emerald-500/20 blur-md group-hover:bg-emerald-400/30 transition-all duration-300" />
        
        {/* Sparkles / Bot Icon */}
        <div className="relative flex items-center justify-center">
          <Bot className="w-7 h-7 text-emerald-100 group-hover:rotate-12 transition-transform duration-300" />
          <Sparkles className="absolute -top-1 -right-1 w-3.5 h-3.5 text-lime-300 animate-pulse" />
        </div>

        {/* Unread Alert Dot indicator */}
        <span className="absolute top-0 right-0 w-3.5 h-3.5 rounded-full bg-lime-400 border-2 border-emerald-950 shadow-md" />
      </button>
    </div>
  );
};
