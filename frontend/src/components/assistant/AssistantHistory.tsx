import React, { useState } from 'react';
import { MessageSquare, Trash2, Edit2, Check, X, Plus } from 'lucide-react';
import { useFarmAICopilot } from '../../context/FarmAICopilotContext';

export const AssistantHistory: React.FC = () => {
  const {
    conversations,
    activeConversationId,
    loadConversation,
    deleteConversation,
    updateTitle,
    startNewConversation,
    setIsHistoryOpen,
  } = useFarmAICopilot();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState<string>('');

  const handleStartRename = (id: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(id);
    setEditTitle(currentTitle);
  };

  const handleSaveRename = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      await updateTitle(id, editTitle.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="absolute inset-0 z-30 flex flex-col bg-slate-950/95 backdrop-blur-xl animate-fade-in">
      {/* History Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-emerald-500/15">
        <h3 className="font-semibold text-sm text-emerald-100 flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-emerald-400" />
          Conversation History
        </h3>

        <button
          onClick={() => setIsHistoryOpen(false)}
          className="p-1 rounded-lg text-emerald-200/70 hover:text-emerald-100 hover:bg-emerald-900/40 transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* History Items Container */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
        <button
          onClick={startNewConversation}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/40 border border-emerald-500/30 text-emerald-100 font-medium text-xs transition-colors cursor-pointer mb-3"
        >
          <Plus className="w-4 h-4 text-emerald-400" />
          <span>New Conversation</span>
        </button>

        {conversations.length === 0 ? (
          <div className="text-center py-10 text-emerald-300/50 text-xs">
            No previous conversations saved yet.
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = activeConversationId === conv.id;
            const isEditing = editingId === conv.id;

            return (
              <div
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                className={`group flex items-center justify-between p-2.5 rounded-xl border text-xs transition-all cursor-pointer ${
                  isActive
                    ? 'bg-emerald-900/60 border-emerald-500/40 text-emerald-100 font-medium shadow-md'
                    : 'bg-emerald-950/40 border-emerald-500/15 text-emerald-200/80 hover:bg-emerald-900/30 hover:border-emerald-500/25'
                }`}
              >
                <div className="flex items-center gap-2 overflow-hidden flex-1 mr-2">
                  <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-emerald-400' : 'text-emerald-300/40'}`} />

                  {isEditing ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="bg-emerald-950 border border-emerald-500/40 text-emerald-100 text-xs rounded px-1.5 py-0.5 outline-none w-full"
                    />
                  ) : (
                    <span className="truncate">{conv.title || 'Untitled Conversation'}</span>
                  )}
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {isEditing ? (
                    <button
                      onClick={(e) => handleSaveRename(conv.id, e)}
                      className="p-1 rounded hover:bg-emerald-800/50 text-emerald-400"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  ) : (
                    <button
                      onClick={(e) => handleStartRename(conv.id, conv.title, e)}
                      className="p-1 rounded hover:bg-emerald-800/50 text-emerald-300/70 hover:text-emerald-100"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                  )}

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('Delete this conversation history?')) {
                        deleteConversation(conv.id);
                      }
                    }}
                    className="p-1 rounded hover:bg-rose-900/50 text-rose-300/70 hover:text-rose-200"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
