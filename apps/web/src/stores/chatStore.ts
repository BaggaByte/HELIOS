import { create } from 'zustand';
import { type ChatMessage } from '../hooks/useChat';

interface ChatState {
  messages: ChatMessage[];
  isConnected: boolean;
  activeAssistantMsgId: string | null;
  
  // Actions
  addMessage: (message: ChatMessage) => void;
  updateMessageContent: (id: string, contentChunk: string) => void;
  updateMessageStatus: (id: string, status: ChatMessage['status']) => void;
  updateMessageAgentStatus: (id: string, agentStatus: string) => void;
  setConnectionStatus: (status: boolean) => void;
  setActiveAssistantMsgId: (id: string | null) => void;
  appendErrorToMessage: (id: string, error: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isConnected: false,
  activeAssistantMsgId: null,

  addMessage: (message) => 
    set((state) => ({ messages: [...state.messages, message] })),

  updateMessageContent: (id, contentChunk) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, content: msg.content + contentChunk } : msg
      )
    })),

  updateMessageStatus: (id, status) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, status } : msg
      )
    })),

  updateMessageAgentStatus: (id, agentStatus) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, agentStatus } : msg
      )
    })),

  appendErrorToMessage: (id, error) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, content: msg.content + `\n\n[Error: ${error}]`, status: 'error' } : msg
      )
    })),

  setConnectionStatus: (isConnected) => 
    set({ isConnected }),

  setActiveAssistantMsgId: (activeAssistantMsgId) => 
    set({ activeAssistantMsgId }),
}));
