import { Component, createSignal } from 'solid-js';
import { useWebSocket } from '../../services/websocket';

export const TextIngest: Component = () => {
  const [text, setText] = createSignal('');
  const [filename, setFilename] = createSignal('manual_ingest.txt');
  const [ingesting, setIngesting] = createSignal(false);
  const [channelId] = createSignal(crypto.randomUUID());
  const { connected, logs } = useWebSocket(channelId());

  const handleIngest = async () => {
    if (!text().trim()) return;

    setIngesting(true);

    try {
      const response = await fetch('/api/ingest/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text(),
          filename: filename(),
          channel_id: channelId(),
        }),
      });

      if (!response.ok) {
        throw new Error('Ingestion failed');
      }
    } catch (error) {
      console.error('Ingestion error:', error);
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div class="w-full">
      <h2 class="text-xl font-bold mb-4">Text Ingestion</h2>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div class="mb-4">
            <label class="block text-sm text-gray-400 mb-2">Filename:</label>
            <input
              type="text"
              class="w-full bg-gray-800 text-white px-4 py-2 rounded border border-gray-700 focus:outline-none focus:border-blue-500"
              value={filename()}
              onInput={(e) => setFilename(e.currentTarget.value)}
              placeholder="document.txt"
            />
          </div>

          <div class="mb-4">
            <label class="block text-sm text-gray-400 mb-2">Content:</label>
            <textarea
              class="w-full h-64 bg-gray-800 text-white px-4 py-2 rounded border border-gray-700 focus:outline-none focus:border-blue-500 font-mono text-sm"
              value={text()}
              onInput={(e) => setText(e.currentTarget.value)}
              placeholder="Paste your text here..."
            />
          </div>

          <button
            class={`w-full px-6 py-3 rounded font-medium ${
              connected() && !ingesting()
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-700 cursor-not-allowed'
            }`}
            onClick={handleIngest}
            disabled={!connected() || ingesting()}
          >
            {ingesting()
              ? '⏳ Ingesting...'
              : connected()
              ? '🚀 Ingest Text'
              : '🔌 Connecting...'}
          </button>
        </div>

        <div>
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-lg font-semibold">Processing Log</h3>
            <div class={`flex items-center gap-2 text-sm ${
              connected() ? 'text-green-400' : 'text-red-400'
            }`}>
              <span class={`w-2 h-2 rounded-full ${
                connected() ? 'bg-green-400' : 'bg-red-400'
              }`} />
              {connected() ? 'Connected' : 'Disconnected'}
            </div>
          </div>

          <div class="h-96 overflow-y-auto bg-gray-800 rounded-lg border border-gray-700 p-4 font-mono text-sm">
            {logs().length === 0 ? (
              <div class="text-gray-500 text-center py-8">
                Waiting for logs...
              </div>
            ) : (
              logs().map((log, index) => (
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
      </div>
    </div>
  );
};