import { useCallback, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { useChatStore } from '../stores/chatStore';

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

export function useChat(wsUrl: string = 'ws://localhost:8000/api/v1/chat/stream') {
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

  const { isConnected, sendMessage, subscribe } = useWebSocket<StreamEvent>(wsUrl);

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