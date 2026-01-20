import { Component, createSignal, onMount } from 'solid-js';

interface Domain {
  id: string;
  name: string;
  display_name: string;
  description: string;
  node_count: number;
  edge_count: number;
}

interface SchemaField {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

export const DomainSchema: Component = () => {
  const [domains, setDomains] = createSignal<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = createSignal<string | null>(null);
  const [schema, setSchema] = createSignal<SchemaField[]>([]);
  const [loading, setLoading] = createSignal(false);

  onMount(async () => {
    try {
      const response = await fetch('/api/domains');
      const data = await response.json();
      setDomains(Array.isArray(data) ? data : (data.domains || []));
    } catch (error) {
      console.error('Failed to load domains:', error);
    }
  });

  const handleDomainSelect = async (domainId: string) => {
    setSelectedDomain(domainId);
    setLoading(true);

    try {
      const response = await fetch(`/api/domains/${domainId}/schema`);
      const data = await response.json();
      setSchema(data.schema || []);
    } catch (error) {
      console.error('Failed to load schema:', error);
      setSchema([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div class="w-full">
      <h2 class="text-xl font-bold mb-4">Domain Schemas</h2>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h3 class="text-lg font-semibold mb-3">Domains</h3>
          <div class="space-y-2">
            {domains().map((domain) => (
              <button
                key={domain.id}
                class={`w-full text-left p-4 rounded-lg border transition-colors ${
                  selectedDomain() === domain.id
                    ? 'bg-blue-600 border-blue-500'
                    : 'bg-gray-800 border-gray-700 hover:border-blue-500'
                }`}
                onClick={() => handleDomainSelect(domain.id)}
              >
                <div class="font-semibold">{domain.name}</div>
                <div class="text-sm text-gray-400 mt-1">{domain.description}</div>
                <div class="flex gap-4 mt-2 text-xs text-gray-500">
                  <span>{domain.node_count} nodes</span>
                  <span>{domain.edge_count} edges</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3 class="text-lg font-semibold mb-3">Schema</h3>
          <Show
            when={selectedDomain()}
            fallback={
              <div class="text-center text-gray-400 py-8">
                Select a domain to view its schema
              </div>
            }
          >
            <Show
              when={!loading()}
              fallback={
                <div class="text-center text-gray-400 py-8">
                  Loading schema...
                </div>
              }
            >
              <div class="bg-gray-800 rounded-lg border border-gray-700">
                <table class="w-full">
                  <thead class="bg-gray-700">
                    <tr>
                      <th class="px-4 py-2 text-left">Field</th>
                      <th class="px-4 py-2 text-left">Type</th>
                      <th class="px-4 py-2 text-left">Required</th>
                      <th class="px-4 py-2 text-left">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {schema().map((field) => (
                      <tr key={field.name} class="border-t border-gray-700">
                        <td class="px-4 py-2 font-mono">{field.name}</td>
                        <td class="px-4 py-2">
                          <span class="px-2 py-1 bg-blue-600 rounded text-xs">
                            {field.type}
                          </span>
                        </td>
                        <td class="px-4 py-2">
                          {field.required ? '✓' : ''}
                        </td>
                        <td class="px-4 py-2 text-gray-400">{field.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Show>
          </Show>
        </div>
      </div>
    </div>
  );
};