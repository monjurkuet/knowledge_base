import { Component, createSignal, Show } from 'solid-js';

interface SearchResultsProps {
  query: string;
  results: SearchResult[];
}

interface SearchResult {
  id: string;
  name: string;
  type: string;
  description?: string;
  score: number;
}

export const GraphView: Component = () => {
  return (
    <>
      <GraphControls
        onLayoutChange={(layout) => console.log('Layout:', layout)}
        onFilterChange={(filter) => console.log('Filter:', filter)}
        onExport={() => console.log('Export')}
      />
      <KnowledgeGraph />
    </>
  );
};

import { KnowledgeGraph } from './KnowledgeGraph';
import { GraphControls } from './GraphControls';