import { Component, createSignal } from 'solid-js';

interface GraphControlsProps {
  onLayoutChange: (layout: string) => void;
  onFilterChange: (filter: string) => void;
  onExport: () => void;
}

export const GraphControls: Component<GraphControlsProps> = (props) => {
  const [selectedLayout, setSelectedLayout] = createSignal('circular');
  const [selectedFilter, setSelectedFilter] = createSignal('all');

  const handleLayoutChange = (layout: string) => {
    setSelectedLayout(layout);
    props.onLayoutChange(layout);
  };

  const handleFilterChange = (filter: string) => {
    setSelectedFilter(filter);
    props.onFilterChange(filter);
  };

  return (
    <div class="flex gap-4 mb-4">
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-400">Layout:</label>
        <select
          class="bg-gray-800 text-white px-3 py-1 rounded border border-gray-700"
          value={selectedLayout()}
          onChange={(e) => handleLayoutChange(e.currentTarget.value)}
        >
          <option value="circular">Circular</option>
          <option value="random">Random</option>
          <option value="force">Force Atlas</option>
        </select>
      </div>
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-400">Filter:</label>
        <select
          class="bg-gray-800 text-white px-3 py-1 rounded border border-gray-700"
          value={selectedFilter()}
          onChange={(e) => handleFilterChange(e.currentTarget.value)}
        >
          <option value="all">All</option>
          <option value="entity">Entities</option>
          <option value="concept">Concepts</option>
          <option value="event">Events</option>
          <option value="relation">Relations</option>
        </select>
      </div>
      <button
        class="px-4 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
        onClick={props.onExport}
      >
        📥 Export
      </button>
    </div>
  );
};