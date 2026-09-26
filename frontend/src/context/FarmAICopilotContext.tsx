import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import { useAuth } from './AuthContext';
import { usePageContext } from '../hooks/usePageContext';
import type { AssistantMessage, ConversationSummary, PageContext } from '../types/assistant';

interface FarmAICopilotContextType {
  isOpen: boolean;
  isMinimized: boolean;
  isHistoryOpen: boolean;
  activeConversationId: string | null;
  conversations: ConversationSummary[];
  messages: AssistantMessage[];
  isStreaming: boolean;
  currentToolStatus: string | null;
  error: string | null;
  pageContext: PageContext;

  openAssistant: () => void;
  closeAssistant: () => void;
  toggleAssistant: () => void;
  minimizeAssistant: () => void;
  setIsHistoryOpen: (open: boolean) => void;
  sendMessage: (content: string, attachment?: { file: File; taskType?: 'disease' | 'pest' }) => Promise<void>;
  stopGeneration: () => void;
  startNewConversation: () => void;
  loadConversation: (id: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  updateTitle: (id: string, title: string) => Promise<void>;
  fetchConversations: () => Promise<void>;
}

const FarmAICopilotContext = createContext<FarmAICopilotContextType | undefined>(undefined);

const GREETING_MESSAGE: AssistantMessage = {
  id: 'greeting_msg',
  conversation_id: 'default',
  role: 'assistant',
  content: `Hello 👋\nI'm your **AgriNexus AI** farming copilot.\n\nI can help you understand your crops, weather impact, soil signals, irrigation timing, pest risks, plant disease warnings, fertilizer schedules, market trends and daily farm tasks.`,
  created_at: new Date().toISOString(),
};

export const FarmAICopilotProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const userId = user?.email || 'default_farmer';
  const pageContext = usePageContext();

  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);

  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [messages, setMessages] = useState<AssistantMessage[]>([GREETING_MESSAGE]);

  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [currentToolStatus, setCurrentToolStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Fetch conversations history
  const fetchConversations = useCallback(async () => {
    try {
      const data = await api.getCopilotConversations(userId);
      if (Array.isArray(data)) {
        setConversations(data);
      }
    } catch (err) {
      console.warn('Failed to load copilot conversation history:', err);
    }
  }, [userId]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // Open/Close handlers
  const openAssistant = useCallback(() => {
    setIsOpen(true);
    setIsMinimized(false);
  }, []);

  const closeAssistant = useCallback(() => {
    setIsOpen(false);
    setIsHistoryOpen(false);
  }, []);

  const toggleAssistant = useCallback(() => {
    setIsOpen((prev) => !prev);
    setIsMinimized(false);
  }, []);

  const minimizeAssistant = useCallback(() => {
    setIsMinimized(true);
  }, []);

  // Abort streaming
  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setCurrentToolStatus(null);
  }, []);

  // Load a conversation
  const loadConversation = useCallback(async (conversationId: string) => {
    try {
      setError(null);
      const data = await api.getCopilotConversation(conversationId, userId);
      setActiveConversationId(data.id);
      if (Array.isArray(data.messages) && data.messages.length > 0) {
        setMessages(data.messages);
      } else {
        setMessages([GREETING_MESSAGE]);
      }
      setIsHistoryOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to load conversation history');
    }
  }, [userId]);

  // Start new conversation
  const startNewConversation = useCallback(() => {
    stopGeneration();
    setActiveConversationId(null);
    setMessages([GREETING_MESSAGE]);
    setError(null);
    setIsHistoryOpen(false);
  }, [stopGeneration]);

  // Delete conversation
  const deleteConversation = useCallback(async (conversationId: string) => {
    try {
      await api.deleteCopilotConversation(conversationId, userId);
      setConversations((prev) => prev.filter((c) => c.id !== conversationId));
      if (activeConversationId === conversationId) {
        startNewConversation();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete conversation');
    }
  }, [activeConversationId, userId, startNewConversation]);

  // Update title
  const updateTitle = useCallback(async (conversationId: string, title: string) => {
    try {
      await api.updateCopilotConversationTitle(conversationId, title, userId);
      setConversations((prev) =>
        prev.map((c) => (c.id === conversationId ? { ...c, title } : c))
      );
    } catch (err: any) {
      console.warn('Failed to update title:', err);
    }
  }, [userId]);

  // Send message handler (streaming)
  const sendMessage = useCallback(
    async (content: string, attachment?: { file: File; taskType?: 'disease' | 'pest' }) => {
      if ((!content || !content.trim()) && !attachment) return;

      stopGeneration();
      setError(null);

      const userMsgId = `user_${Date.now()}`;
      const userMsg: AssistantMessage = {
        id: userMsgId,
        conversation_id: activeConversationId || 'pending',
        role: 'user',
        content: content.trim(),
        created_at: new Date().toISOString(),
      };

      // Append user message immediately
      setMessages((prev) => [...prev, userMsg]);

      setIsStreaming(true);
      setCurrentToolStatus(attachment ? `Analyzing ${attachment.taskType || 'plant'} image...` : 'Thinking...');

      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        let actualConvId = activeConversationId;
        let imageAnalysisContext = '';

        // Handle image attachment first if provided
        if (attachment?.file) {
          try {
            const imgRes = await api.analyzeCopilotImage(
              attachment.file,
              attachment.taskType || 'disease',
              activeConversationId || undefined,
              userId
            );
            if (imgRes.conversation_id) {
              actualConvId = imgRes.conversation_id;
              setActiveConversationId(imgRes.conversation_id);
            }
            if (imgRes.explanation) {
              imageAnalysisContext = `\n[Uploaded Image Analysis: ${imgRes.task_type.toUpperCase()} Prediction: ${imgRes.prediction} (Confidence: ${imgRes.confidence})]\n`;
            }
          } catch (imgErr: any) {
            console.error('Image analysis error:', imgErr);
            setCurrentToolStatus(null);
          }
        }

        const combinedMessage = (userMsg.content + imageAnalysisContext).trim();

        const assistantMsgId = `asst_${Date.now()}`;
        const placeholderAssistantMsg: AssistantMessage = {
          id: assistantMsgId,
          conversation_id: actualConvId || 'pending',
          role: 'assistant',
          content: '',
          created_at: new Date().toISOString(),
          tool_calls: [],
          actions: [],
          sources: [],
        };

        // Add placeholder assistant message
        setMessages((prev) => [...prev, placeholderAssistantMsg]);

        await api.streamCopilotChat(
          {
            message: combinedMessage,
            conversation_id: actualConvId || undefined,
            page_context: pageContext,
          },
          (evt) => {
            const { event, data } = evt;

            if (event === 'message_start') {
              if (data.conversation_id) {
                actualConvId = data.conversation_id;
                setActiveConversationId(data.conversation_id);
              }
            } else if (event === 'tool_start') {
              const toolName = data.tool_name || 'backend tool';
              const cleanTool = toolName.replace(/^get_/, '').replace(/_/g, ' ');
              setCurrentToolStatus(`Checking ${cleanTool}...`);

              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? {
                        ...msg,
                        tool_calls: [
                          ...(msg.tool_calls || []),
                          { tool_name: toolName, arguments: data.arguments, status: 'running' },
                        ],
                      }
                    : msg
                )
              );
            } else if (event === 'tool_result') {
              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.id !== assistantMsgId) return msg;
                  const updatedCalls = (msg.tool_calls || []).map((call) =>
                    call.tool_name === data.tool_name
                      ? { ...call, result: data.result, status: data.status || 'success' }
                      : call
                  );
                  return { ...msg, tool_calls: updatedCalls };
                })
              );
            } else if (event === 'message_delta') {
              setCurrentToolStatus(null);
              const deltaText = typeof data === 'string' ? data : data?.content || '';
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? { ...msg, content: msg.content + deltaText }
                    : msg
                )
              );
            } else if (event === 'message_complete') {
              setCurrentToolStatus(null);
              setIsStreaming(false);

              if (data) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? {
                          ...msg,
                          content: data.content || msg.content,
                          actions: data.actions || msg.actions || [],
                          sources: data.sources || msg.sources || [],
                          tool_summary: data.tool_summary || msg.tool_summary || [],
                          card: data.card || msg.card,
                        }
                      : msg
                  )
                );
              }
              fetchConversations();
            } else if (event === 'error') {
              setCurrentToolStatus(null);
              setIsStreaming(false);
              const errMessage = typeof data === 'string' ? data : data?.message || 'Error executing assistant response';
              setError(errMessage);
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? {
                        ...msg,
                        content: msg.content
                          ? `${msg.content}\n\n⚠️ *${errMessage}*`
                          : `⚠️ ${errMessage}. You can use direct navigation below or try again.`,
                        actions: [
                          { type: 'navigate', route: '/dashboard', label: 'Open Farm Command Center' },
                          { type: 'navigate', route: '/weather', label: 'Open Weather Intelligence' },
                        ],
                      }
                    : msg
                )
              );
            }
          },
          userId,
          controller.signal
        );
      } catch (err: any) {
        if (err.name === 'AbortError') {
          console.log('Copilot streaming cancelled by user');
        } else {
          console.error('Copilot streaming error:', err);
          setError(err.message || 'AI assistant is temporarily unavailable.');
        }
      } finally {
        setIsStreaming(false);
        setCurrentToolStatus(null);
        abortControllerRef.current = null;
      }
    },
    [activeConversationId, userId, pageContext, stopGeneration, fetchConversations]
  );

  return (
    <FarmAICopilotContext.Provider
      value={{
        isOpen,
        isMinimized,
        isHistoryOpen,
        activeConversationId,
        conversations,
        messages,
        isStreaming,
        currentToolStatus,
        error,
        pageContext,
        openAssistant,
        closeAssistant,
        toggleAssistant,
        minimizeAssistant,
        setIsHistoryOpen,
        sendMessage,
        stopGeneration,
        startNewConversation,
        loadConversation,
        deleteConversation,
        updateTitle,
        fetchConversations,
      }}
    >
      {children}
    </FarmAICopilotContext.Provider>
  );
};

export const useFarmAICopilot = () => {
  const context = useContext(FarmAICopilotContext);
  if (!context) {
    throw new Error('useFarmAICopilot must be used within a FarmAICopilotProvider');
  }
  return context;
};
