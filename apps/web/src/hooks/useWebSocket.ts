import { useEffect, useRef, useState, useCallback } from 'react';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  reconnectInterval?: number;
  maxRetries?: number;
}

export function useWebSocket<T = any>(url: string, options: UseWebSocketOptions = {}) {
  const { reconnectInterval = 3000, maxRetries = 5 } = options;

  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMounted = useRef(true);

  // Set is faster than Array for adding/removing handlers
  const messageHandlers = useRef<Set<(data: T) => void>>(new Set());

  const connect = useCallback(() => {
    if (!isMounted.current) return;

    setStatus('connecting');
    const socket = new WebSocket(url);
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
          connect();
        }, delay);
      }
    };

    socket.onerror = (error) => {
      if (!isMounted.current) return;
      setStatus('error');
      console.error('[WS] Error', error);
      socket.close(); // Trigger onclose to start reconnect logic
    };
  }, [url, reconnectInterval, maxRetries]);

  useEffect(() => {
    isMounted.current = true;
    connect();

    return () => {
      isMounted.current = false;
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

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