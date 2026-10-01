import { useEffect, useRef, useState, useCallback } from 'react';
import { apiClient } from '../services/apiClient';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  reconnectInterval?: number;
  maxRetries?: number;
  enabled?: boolean;
}

export function useWebSocket<T = any>(url: string, options: UseWebSocketOptions = {}) {
  const { reconnectInterval = 3000, maxRetries = 5, enabled = true } = options;

  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMounted = useRef(true);

  // Set is faster than Array for adding/removing handlers
  const messageHandlers = useRef<Set<(data: T) => void>>(new Set());
  const connectRef = useRef<() => void>(() => {});

  const connect = useCallback(async () => {
    if (!isMounted.current || !enabled || !url) return;

    setStatus('connecting');
    let finalUrl = url;
    const token = localStorage.getItem('helios_token');
    if (token) {
      try {
        const data = await apiClient.post<{ticket: string}>('/auth/ws-ticket', {});
        finalUrl += (finalUrl.includes('?') ? '&' : '?') + `ticket=${data.ticket}`;
      } catch (err) {
        console.error('[WS] Failed to authenticate WebSocket', err);
        setStatus('error');
        return;
      }
    }

    if (!isMounted.current) return;

    const socket = new WebSocket(finalUrl);
    ws.current = socket;

    socket.onopen = () => {
      if (!isMounted.current) return;
      setStatus('connected');
      reconnectAttempts.current = 0;
      console.log('[WS] Connected');
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as T;
        messageHandlers.current.forEach(handler => handler(data));
      } catch (error) {
        console.error('[WS] Failed to parse message', error);
      }
    };

    socket.onclose = () => {
      if (!isMounted.current) return;
      setStatus('disconnected');
      console.log('[WS] Disconnected');

      // Auto-reconnect with exponential backoff
      if (reconnectAttempts.current < maxRetries) {
        const delay = reconnectInterval * Math.pow(2, reconnectAttempts.current);
        console.log(`[WS] Reconnecting in ${delay}ms...`);
        reconnectTimeout.current = setTimeout(() => {
          reconnectAttempts.current += 1;
          connectRef.current();
        }, delay);
      }
    };

    socket.onerror = (error) => {
      if (!isMounted.current) return;
      setStatus('error');
      console.error('[WS] Error', error);
      socket.close(); // Trigger onclose to start reconnect logic
    };
  }, [url, reconnectInterval, maxRetries, enabled]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    isMounted.current = true;
    if (!enabled || !url) {
      setStatus('disconnected');
      return () => { isMounted.current = false; };
    }
    connect();

    return () => {
      isMounted.current = false;
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect, enabled, url]);

  const sendMessage = useCallback((message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('[WS] Cannot send message: Socket is not open');
    }
  }, []);

  const subscribe = useCallback((handler: (data: T) => void) => {
    messageHandlers.current.add(handler);
    return () => {
      messageHandlers.current.delete(handler);
    };
  }, []);

  return {
    status,
    isConnected: status === 'connected',
    sendMessage,
    subscribe
  };
}
