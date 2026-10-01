import { useCallback, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { useChatStore } from '../stores/chatStore';
import { useProjectStore } from '../stores/projectStore';
import { API_BASE_URL } from '../services/apiClient';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  status: 'pending' | 'streaming' | 'complete' | 'error';
  agentStatus?: string;
}

export interface StreamEvent {
  type: 'start' | 'token' | 'done' | 'error' | 'agent_status';
  content?: string;
  message_id?: string;
  error?: string;
}

export function useChat() {
  const projectId = useProjectStore(state => state.activeProjectId);
  const wsBase = API_BASE_URL.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:');
  const wsUrl = projectId ? `${wsBase}/chat/stream/${encodeURIComponent(projectId)}` : '';
  const { 
    messages, 
    activeAssistantMsgId,
    addMessage, 
    updateMessageContent, 
    updateMessageStatus,
    appendErrorToMessage,
    setActiveAssistantMsgId,
    setConnectionStatus
  } = useChatStore();

  const { isConnected, sendMessage, subscribe } = useWebSocket<StreamEvent>(wsUrl, { enabled: Boolean(projectId) });

  useEffect(() => {
    useChatStore.setState({ messages: [], activeAssistantMsgId: null });
  }, [projectId]);

  // Sync connection status to global store
  useEffect(() => {
    setConnectionStatus(isConnected);
  }, [isConnected, setConnectionStatus]);

  useEffect(() => {
    const unsubscribe = subscribe((event: StreamEvent) => {
      if (event.type === 'start') {
        const id = event.message_id || crypto.randomUUID();
        setActiveAssistantMsgId(id);

        addMessage({
          id,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          status: 'streaming'
        });
      }
      else if (event.type === 'token' && activeAssistantMsgId) {
        updateMessageContent(activeAssistantMsgId, event.content || '');
      }
      else if (event.type === 'done' && activeAssistantMsgId) {
        updateMessageStatus(activeAssistantMsgId, 'complete');
        setActiveAssistantMsgId(null);
      }
      else if (event.type === 'error') {
        const id = activeAssistantMsgId || crypto.randomUUID();
        appendErrorToMessage(id, event.error || 'Stream failed');
        setActiveAssistantMsgId(null);
      }
      else if (event.type === 'agent_status' && activeAssistantMsgId) {
        useChatStore.getState().updateMessageAgentStatus(activeAssistantMsgId, event.content || '');
      }
    });

    return unsubscribe;
  }, [subscribe, activeAssistantMsgId, addMessage, updateMessageContent, updateMessageStatus, appendErrorToMessage, setActiveAssistantMsgId]);

  const sendUserMessage = useCallback((content: string) => {
    if (!content.trim()) return;

    const userMsgId = crypto.randomUUID();
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content,
      timestamp: Date.now(),
      status: 'complete'
    };

    addMessage(userMsg);

    if (isConnected) {
      sendMessage({
        type: 'message',
        content,
        message_id: userMsgId
      });
    } else {
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'System is currently offline. Please try again later.',
        timestamp: Date.now(),
        status: 'error'
      });
    }
  }, [isConnected, sendMessage, addMessage]);

  return {
    messages,
    isConnected,
    sendUserMessage
  };
}
