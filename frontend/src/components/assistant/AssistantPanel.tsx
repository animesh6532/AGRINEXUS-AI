import React, { useEffect } from 'react';
import { Bot, Sparkles, Maximize2 } from 'lucide-react';
import { useFarmAICopilot } from '../../context/FarmAICopilotContext';
import { AssistantHeader } from './AssistantHeader';
import { AssistantQuickActions } from './AssistantQuickActions';
import { AssistantMessages } from './AssistantMessages';
import { AssistantComposer } from './AssistantComposer';
import { AssistantHistory } from './AssistantHistory';

export const AssistantPanel: React.FC = () => {
  const { isOpen, isMinimized, isHistoryOpen, openAssistant, closeAssistant } = useFarmAICopilot();

  // Handle body scroll locking on mobile screens when panel is fully open
  useEffect(() => {
    if (isOpen && !isMinimized && window.innerWidth < 640) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen, isMinimized]);

  // Handle Escape key to minimize/close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        closeAssistant();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, closeAssistant]);

  if (!isOpen) return null;

  // Render Minimized Pill if minimized
  if (isMinimized) {
    return (
      <div
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-full bg-emerald-950/90 backdrop-blur-xl border border-emerald-500/40 text-emerald-100 text-xs font-semibold shadow-2xl hover:bg-emerald-900 cursor-pointer transition-all duration-200 animate-fade-in"
        onClick={openAssistant}
      >
        <div className="relative flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400">
          <Bot className="w-3.5 h-3.5" />
          <Sparkles className="absolute -top-1 -right-1 w-2 h-2 text-lime-300 animate-pulse" />
        </div>
        <span>AgriNexus AI</span>
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-1" />
        <Maximize2 className="w-3.5 h-3.5 text-emerald-300/60 ml-2" />
      </div>
    );
  }

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      <div
        className="sm:hidden fixed inset-0 bg-slate-950/60 backdrop-blur-xs z-40 animate-fade-in"
        onClick={closeAssistant}
      />

      {/* Main Glass Panel */}
      <div
        className={`fixed z-50 flex flex-col bg-slate-950/90 backdrop-blur-2xl border border-emerald-500/25 shadow-2xl shadow-emerald-950/80 overflow-hidden transition-all duration-300 ease-out
          /* Mobile full-width bottom sheet */
          bottom-0 inset-x-0 h-[88vh] max-h-[760px] rounded-t-3xl
          /* Desktop right floating drawer */
          sm:bottom-6 sm:right-6 sm:left-auto sm:w-[420px] sm:h-[min(680px,calc(100vh-48px))] sm:rounded-3xl
        `}
        style={{
          paddingBottom: 'env(safe-area-inset-bottom, 0px)',
        }}
      >
        {/* Header Bar */}
        <AssistantHeader />

        {/* Dynamic Contextual Suggestions */}
        <AssistantQuickActions />

        {/* Scrollable Messages Thread */}
        <div className="relative flex-1 flex flex-col overflow-hidden">
          <AssistantMessages onClosePanel={closeAssistant} />

          {/* Sliding History Drawer */}
          {isHistoryOpen && <AssistantHistory />}
        </div>

        {/* Input Composer Bar */}
        <AssistantComposer />
      </div>
    </>
  );
};
