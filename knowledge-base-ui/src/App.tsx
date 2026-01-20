import { Component, createSignal } from 'solid-js';
import { Dashboard } from './components/Dashboard';
import { GraphView } from './components/Graph';
import { SearchView } from './components/Search';
import { DomainsView } from './components/Domains';
import { IngestView } from './components/Ingest';

const App: Component = () => {
  const [activeTab, setActiveTab] = createSignal('graph');

  const tabs = [
    { id: 'graph', label: '📊 Graph', component: GraphView },
    { id: 'search', label: '🔍 Search', component: SearchView },
    { id: 'domains', label: '📁 Domains', component: DomainsView },
    { id: 'ingest', label: '📥 Ingest', component: IngestView },
  ];

  return (
    <div class="min-h-screen bg-gray-950 text-white">
      <Dashboard />
      <main class="p-6">
        <div class="mb-6">
          <div class="flex gap-2 border-b border-gray-800 pb-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                class={`px-4 py-2 rounded-t-lg transition-colors ${
                  activeTab() === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
        <div class="bg-gray-900 rounded-lg p-6 min-h-[600px]">
          {tabs.find((t) => t.id === activeTab())?.component && (
            <>{tabs.find((t) => t.id === activeTab())?.component()}</>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;