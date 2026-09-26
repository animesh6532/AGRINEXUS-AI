import React from 'react';
import { Bot, User, Sparkles } from 'lucide-react';
import type { AssistantMessage as AssistantMessageType } from '../../types/assistant';
import { AssistantSources } from './AssistantSources';
import { AssistantActionCard } from './AssistantActionCard';

interface AssistantMessageProps {
  message: AssistantMessageType;
  onClosePanel?: () => void;
}

// Simple safe markdown renderer
function renderFormattedContent(content: string) {
  if (!content) return null;

  const lines = content.split('\n');

  return (
    <div className="space-y-1.5 text-xs leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-1" />;

        // Header line (e.g. ### or TODAY'S FARM BRIEF)
        if (trimmed.startsWith('# ') || trimmed.startsWith('## ') || trimmed.startsWith('### ')) {
          const headerText = trimmed.replace(/^#+\s*/, '');
          return (
            <h4 key={idx} className="font-semibold text-emerald-200 text-xs mt-2 mb-1 tracking-wide">
              {headerText}
            </h4>
          );
        }

        // Bullet point line
        if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('* ')) {
          const bulletText = trimmed.replace(/^[•\-\*]\s*/, '');
          return (
            <div key={idx} className="flex items-start gap-1.5 pl-1 my-0.5">
              <span className="text-emerald-400 font-bold text-[11px] leading-tight">•</span>
              <span className="flex-1 text-emerald-100/90">{parseInlineFormatting(bulletText)}</span>
            </div>
          );
        }

        // Regular paragraph
        return (
          <p key={idx} className="text-emerald-100/90">
            {parseInlineFormatting(line)}
          </p>
        );
      })}
    </div>
  );
}

function parseInlineFormatting(text: string) {
  // Split bold **text**
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-emerald-100">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

export const AssistantMessage: React.FC<AssistantMessageProps> = ({ message, onClosePanel }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start gap-2.5 my-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar Icon */}
      <div
        className={`shrink-0 flex items-center justify-center w-7 h-7 rounded-xl border text-xs ${
          isUser
            ? 'bg-emerald-700/40 border-emerald-500/40 text-emerald-100'
            : 'bg-gradient-to-br from-emerald-600/30 to-teal-800/40 border-emerald-500/30 text-emerald-300'
        }`}
      >
        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
      </div>

      {/* Message Content Bubble */}
      <div
        className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 shadow-md ${
          isUser
            ? 'bg-emerald-800/60 border border-emerald-500/30 text-emerald-50 rounded-tr-xs'
            : 'bg-slate-900/90 border border-emerald-500/20 text-emerald-100 rounded-tl-xs backdrop-blur-sm'
        }`}
      >
        {/* Render Formatted Content */}
        {renderFormattedContent(message.content)}

        {/* Render Structured Card & Action Buttons if present */}
        {(message.card || (message.actions && message.actions.length > 0)) && (
          <AssistantActionCard card={message.card} actions={message.actions} onClosePanel={onClosePanel} />
        )}

        {/* Render Sources / Data Used */}
        {message.sources && message.sources.length > 0 && (
          <AssistantSources sources={message.sources} />
        )}
      </div>
    </div>
  );
};
