import { createSignal, onCleanup } from 'solid-js';

export interface Log {
  log_type: string;
  message: string;
  timestamp: string;
}

interface WebSocketMessage {
  type: string;
  data: Log;
}

let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

export function useWebSocket(channelId: string) {
  const [connected, setConnected] = createSignal(false);
  const [logs, setLogs] = createSignal<Log[]>([]);

  let ws: WebSocket | null = null;
  let reconnectTimeout: number | null = null;

  const connect = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/${channelId}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      reconnectAttempts = 0;
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('WebSocket message received:', message);
        
        // Handle both wrapped and direct log formats
        let logData: Log;
        
        if (message.type === 'log' && message.data) {
          // Wrapped format: {type: "log", data: {message, log_type, timestamp}}
          logData = {
            log_type: message.data.log_type || 'info',
            message: message.data.message || '',
            timestamp: message.data.timestamp || new Date().toISOString(),
          };
        } else if (message.type === 'connection') {
          // Connection message
          logData = {
            log_type: 'info',
            message: `Connected to channel: ${message.channel || 'default'}`,
            timestamp: new Date().toISOString(),
          };
        } else if (message.log_type && message.message) {
          // Direct format: {log_type, message, timestamp}
          logData = {
            log_type: message.log_type,
            message: message.message,
            timestamp: message.timestamp || new Date().toISOString(),
          };
        } else {
          // Fallback: try to extract message from any format
          const msgText = message.message || message.data?.message || JSON.stringify(message);
          logData = {
            log_type: message.log_type || message.data?.log_type || 'info',
            message: msgText,
            timestamp: message.timestamp || message.data?.timestamp || new Date().toISOString(),
          };
        }
        
        setLogs((prev) => [...prev, logData]);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error, event.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('WebSocket disconnected');

      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        const delay = 1000 * Math.pow(2, reconnectAttempts - 1);
        reconnectTimeout = window.setTimeout(() => {
          connect();
        }, delay);
      }
    };
  };

  connect();

  onCleanup(() => {
    if (reconnectTimeout !== null) {
      clearTimeout(reconnectTimeout);
    }
    ws?.close();
  });

  return { connected, logs };
}