import { apiClient } from './apiClient';

export interface ChatMessagePayload {
  content: string;
  projectId?: string;
}

export interface ChatResponse {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  status: 'sent' | 'streaming' | 'error';
}

export const chatService = {
  /**
   * Send a message to the backend via REST API.
   * Note: For full streaming support, a WebSocket connection is preferred,
   * but this works for basic REST req/res flows.
   */
  async sendMessage(payload: ChatMessagePayload): Promise<ChatResponse> {
    // Calling the endpoint defined in services/helios/api/v1/chat.py
    return await apiClient.post<ChatResponse>('/chat/message', payload);
  },

  /**
   * Get chat history for a project.
   */
  async getHistory(projectId: string): Promise<ChatResponse[]> {
    return await apiClient.get<ChatResponse[]>(`/chat/history/${projectId}`);
  },
  
  /**
   * Clear chat history for a project.
   */
  async clearHistory(projectId: string): Promise<void> {
    return await apiClient.delete<void>(`/chat/history/${projectId}`);
  }
};
