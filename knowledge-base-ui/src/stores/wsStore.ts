import { createSignal } from 'solid-js';

export interface WebSocketState {
  connected: boolean;
  channelId: string | null;
  logs: Array<any>;
  reconnectAttempts: number;
}

const initialState: WebSocketState = {
  connected: false,
  channelId: null,
  logs: [],
  reconnectAttempts: 0,
};

export function createWebSocketStore() {
  const [state, setState] = createSignal(initialState);

  return {
    get state() {
      return state();
    },
    setConnected(connected: boolean) {
      setState((prev) => ({ ...prev, connected }));
    },
    setChannelId(channelId: string) {
      setState((prev) => ({ ...prev, channelId }));
    },
    addLog(log: any) {
      setState((prev) => ({ ...prev, logs: [...prev.logs, log] }));
    },
    clearLogs() {
      setState((prev) => ({ ...prev, logs: [] }));
    },
    setReconnectAttempts(attempts: number) {
      setState((prev) => ({ ...prev, reconnectAttempts: attempts }));
    },
    reset() {
      setState(initialState);
    },
  };
}

export const wsStore = createWebSocketStore();