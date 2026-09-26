import React, { useState, useRef } from 'react';
import { Send, Square, Image, Camera, Mic, Paperclip, X } from 'lucide-react';
import { useFarmAICopilot } from '../../context/FarmAICopilotContext';

export const AssistantComposer: React.FC = () => {
  const { sendMessage, isStreaming, stopGeneration } = useFarmAICopilot();

  const [text, setText] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [taskType, setTaskType] = useState<'disease' | 'pest'>('disease');
  const [showAttachMenu, setShowAttachMenu] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (isStreaming) {
      stopGeneration();
      return;
    }

    if ((!text || !text.trim()) && !selectedFile) return;

    sendMessage(text, selectedFile ? { file: selectedFile, taskType } : undefined);
    setText('');
    setSelectedFile(null);
    setShowAttachMenu(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  return (
    <div className="border-t border-emerald-500/15 bg-slate-950/90 backdrop-blur-md p-3">
      {/* Selected Image Attachment Preview Bar */}
      {selectedFile && (
        <div className="flex items-center justify-between gap-2 mb-2 px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-500/30 text-emerald-200 text-xs">
          <div className="flex items-center gap-2 overflow-hidden">
            <Camera className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="truncate font-medium">{selectedFile.name}</span>
            <span className="shrink-0 px-1.5 py-0.5 rounded bg-emerald-900/60 text-[10px] uppercase font-bold text-emerald-300">
              {taskType}
            </span>
          </div>
          <button
            onClick={() => setSelectedFile(null)}
            className="p-1 text-emerald-300/70 hover:text-emerald-100 hover:bg-emerald-900/50 rounded cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Attachment Task Selector Menu */}
      {showAttachMenu && !selectedFile && (
        <div className="flex items-center gap-2 mb-2 p-2 rounded-xl bg-emerald-950/90 border border-emerald-500/30 animate-fade-in text-xs">
          <span className="text-emerald-200/70 text-[11px] font-medium pl-1">Attach photo for:</span>
          <button
            onClick={() => {
              setTaskType('disease');
              fileInputRef.current?.click();
            }}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-900/60 hover:bg-emerald-800/80 border border-emerald-500/25 text-emerald-200 cursor-pointer"
          >
            <Image className="w-3.5 h-3.5 text-emerald-400" />
            <span>Leaf Disease</span>
          </button>

          <button
            onClick={() => {
              setTaskType('pest');
              fileInputRef.current?.click();
            }}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-900/60 hover:bg-emerald-800/80 border border-emerald-500/25 text-emerald-200 cursor-pointer"
          >
            <Camera className="w-3.5 h-3.5 text-amber-400" />
            <span>Pest Inspection</span>
          </button>
        </div>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Main Composer Bar */}
      <div className="flex items-end gap-2 bg-emerald-950/60 border border-emerald-500/25 rounded-2xl p-1.5 focus-within:border-emerald-400/50 transition-colors">
        {/* Attach Button */}
        <button
          type="button"
          onClick={() => setShowAttachMenu((prev) => !prev)}
          title="Attach plant or pest photo"
          aria-label="Attach photo"
          className="p-2 rounded-xl text-emerald-300/70 hover:text-emerald-100 hover:bg-emerald-900/40 transition-colors cursor-pointer shrink-0"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        {/* Text Area */}
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your crops, weather, soil or irrigation..."
          rows={1}
          aria-label="Ask AgriNexus AI"
          className="flex-1 bg-transparent text-emerald-100 text-xs placeholder:text-emerald-300/40 resize-none outline-none py-1.5 px-1 max-h-24 custom-scrollbar"
        />

        {/* Voice Microphone (Placeholder for future voice extension) */}
        <button
          type="button"
          title="Voice input (coming soon)"
          aria-label="Voice input"
          onClick={() => alert('Voice assistant input feature ready for audio stream integration!')}
          className="p-2 rounded-xl text-emerald-300/40 hover:text-emerald-300 hover:bg-emerald-900/30 transition-colors cursor-pointer shrink-0 hidden sm:flex"
        >
          <Mic className="w-4 h-4" />
        </button>

        {/* Send / Stop Action Button */}
        <button
          type="button"
          onClick={handleSend}
          disabled={!isStreaming && (!text.trim() && !selectedFile)}
          aria-label={isStreaming ? 'Stop response' : 'Send message'}
          className={`p-2 rounded-xl flex items-center justify-center transition-all cursor-pointer shrink-0 ${
            isStreaming
              ? 'bg-rose-600/80 hover:bg-rose-500 text-white'
              : text.trim() || selectedFile
              ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md'
              : 'bg-emerald-950/40 text-emerald-300/30 cursor-not-allowed'
          }`}
        >
          {isStreaming ? <Square className="w-4 h-4 fill-white" /> : <Send className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
};
