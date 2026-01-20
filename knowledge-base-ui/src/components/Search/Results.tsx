import { Component, createSignal, Show } from 'solid-js';

interface SearchResult {
  id: string;
  name: string;
  type: string;
  description?: string;
  score: number;
}

export const Results: Component = () => {
  const [query, setQuery] = createSignal('');
  const [results, setResults] = createSignal<SearchResult[]>([]);
  const [loading, setLoading] = createSignal(false);
  const [hasSearched, setHasSearched] = createSignal(false);

  const handleSearch = async () => {
    if (!query().trim()) return;

    setLoading(true);
    setHasSearched(true);

    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query() }),
      });
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div class="w-full">
      <h2 class="text-xl font-bold mb-4">Search Knowledge Base</h2>
      <div class="flex gap-4 mb-6">
        <input
          type="text"
          class="flex-1 bg-gray-800 text-white px-4 py-2 rounded border border-gray-700 focus:outline-none focus:border-blue-500"
          placeholder="Search for entities, concepts, events..."
          value={query()}
          onInput={(e) => setQuery(e.currentTarget.value)}
          onKeyPress={handleKeyPress}
        />
        <button
          class="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded font-medium"
          onClick={handleSearch}
          disabled={loading()}
        >
          {loading() ? 'Searching...' : '🔍 Search'}
        </button>
      </div>

      <Show when={hasSearched()}>
        <div class="space-y-4">
          <Show
            when={!loading() && results().length === 0}
          >
            <div class="text-center text-gray-400 py-8">
              No results found for "{query()}"
            </div>
          </Show>

          {results().map((result) => (
            <div
              key={result.id}
              class="bg-gray-800 p-4 rounded-lg border border-gray-700 hover:border-blue-500 transition-colors"
            >
              <div class="flex justify-between items-start">
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class={`px-2 py-1 text-xs rounded ${
                      result.type === 'entity' ? 'bg-blue-600' :
                      result.type === 'concept' ? 'bg-green-600' :
                      result.type === 'event' ? 'bg-orange-600' :
                      'bg-purple-600'
                    }`}>
                      {result.type}
                    </span>
                    <h3 class="text-lg font-semibold">{result.name}</h3>
                  </div>
                  <Show when={result.description}>
                    <p class="text-gray-400 mt-2">{result.description}</p>
                  </Show>
                </div>
                <div class="text-sm text-gray-500">
                  Score: {(result.score * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </Show>
    </div>
  );
};