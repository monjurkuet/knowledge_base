import { Component, createSignal } from 'solid-js';
import { useWebSocket } from '../../services/websocket';

export const LogViewer: Component = () => {
  const [logs, setLogs] = createSignal<Log[]>([]);
  const [filter, setFilter] = createSignal('all');

  const filteredLogs = () => {
    if (filter() === 'all') return logs();
    return logs().filter((log) => log.log_type === filter());
  };

  return (
    <div class="w-full">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold">Log Viewer</h3>
        <select
          class="bg-gray-800 text-white px-3 py-1 rounded border border-gray-700"
          value={filter()}
          onChange={(e) => setFilter(e.currentTarget.value)}
        >
          <option value="all">All</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
        </select>
      </div>

      <div class="h-96 overflow-y-auto bg-gray-800 rounded-lg border border-gray-700 p-4 font-mono text-sm">
        {filteredLogs().length === 0 ? (
          <div class="text-gray-500 text-center py-8">No logs available</div>
        ) : (
          filteredLogs().map((log, index) => (
            <div
              key={index}
              class={`py-1 ${
                log.log_type === 'error'
                  ? 'text-red-400'
                  : log.log_type === 'warning'
                  ? 'text-yellow-400'
                  : 'text-green-400'
              }`}
            >
              <span class="text-gray-500 mr-2">
                [{new Date(log.timestamp).toLocaleTimeString()}]
              </span>
              {log.message}
            </div>
          ))
        )}
      </div>
    </div>
  );
};