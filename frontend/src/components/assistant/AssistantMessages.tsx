import React, { useRef, useEffect } from 'react';
import { useFarmAICopilot } from '../../context/FarmAICopilotContext';
import { AssistantMessage } from './AssistantMessage';
import { AssistantToolStatus } from './AssistantToolStatus';

interface AssistantMessagesProps {
  onClosePanel?: () => void;
}

export const AssistantMessages: React.FC<AssistantMessagesProps> = ({ onClosePanel }) => {
  const { messages, isStreaming, currentToolStatus } = useFarmAICopilot();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on message update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentToolStatus]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1 custom-scrollbar">
      {messages.map((msg, idx) => (
        <AssistantMessage key={msg.id || idx} message={msg} onClosePanel={onClosePanel} />
      ))}

      {/* Tool Execution Indicator */}
      {isStreaming && currentToolStatus && (
        <AssistantToolStatus status={currentToolStatus} />
      )}

      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
};
