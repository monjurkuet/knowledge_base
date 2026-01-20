import { Component, onMount, onCleanup, createSignal } from 'solid-js';
import Graph from 'graphology';
import Sigma from 'sigma';
import { circular, random } from 'graphology-layout';

interface Node {
  id: string;
  name: string;
  type: string;
}

interface Edge {
  source: string;
  target: string;
}

const getNodeColor = (type: string): string => {
  const colors: Record<string, string> = {
    entity: '#3b82f6',
    concept: '#10b981',
    event: '#f59e0b',
    relation: '#8b5cf6',
    default: '#6b7280',
  };
  return colors[type] || colors.default;
};

export const KnowledgeGraph: Component = () => {
  let container!: HTMLDivElement;
  let renderer: Sigma | null = null;
  const [loading, setLoading] = createSignal(true);
  const [nodeCount, setNodeCount] = createSignal(0);
  const [edgeCount, setEdgeCount] = createSignal(0);

  onMount(async () => {
    const graph = new Graph({ multi: true });

    try {
      const response = await fetch('/api/graph?limit=10000');
      const data = await response.json();

      data.nodes.forEach((node: Node) => {
        graph.addNode(node.id, {
          label: node.name,
          x: Math.random() * 100,
          y: Math.random() * 100,
          size: 10,
          color: getNodeColor(node.type),
        });
      });

      data.edges.forEach((edge: Edge) => {
        if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
          try {
            graph.addEdge(edge.source, edge.target, {
              color: '#4b5563',
              size: 1,
            });
          } catch (e) {
            // Edge already exists, skip
          }
        }
      });

      setNodeCount(graph.order);
      setEdgeCount(graph.size);

      random.assign(graph, { scale: 100 });
      circular.assign(graph, { scale: 100 });

      const checkContainer = setInterval(() => {
        if (container) {
          clearInterval(checkContainer);
          try {
            renderer = new Sigma(graph, container, {
              labelRenderedSizeThreshold: 6,
              labelFont: 'Arial',
              labelSize: 14,
              labelColor: { color: '#ffffff' },
              defaultNodeColor: '#6b7280',
              defaultEdgeColor: '#4b5563',
              defaultEdgeType: 'arrow',
              minCameraRatio: 0.1,
              maxCameraRatio: 10,
            });

            if (renderer) {
              renderer.on('clickNode', ({ node }) => {
                const attrs = graph.getNodeAttributes(node);
                console.log('Clicked node:', attrs);
              });
            }
          } catch (e) {
            console.error('Failed to initialize Sigma:', e);
          }
        }
      }, 100);
    } catch (error) {
      console.error('Failed to load graph:', error);
    } finally {
      setLoading(false);
    }
  });

  onCleanup(() => {
    renderer?.kill();
  });

  return (
    <div class="w-full">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-bold">Knowledge Graph</h2>
        <div class="flex gap-4 text-sm text-gray-400">
          <span>Nodes: {nodeCount()}</span>
          <span>Edges: {edgeCount()}</span>
        </div>
      </div>
      {loading() ? (
        <div class="flex items-center justify-center h-[600px]">
          <div class="text-gray-400">Loading graph...</div>
        </div>
      ) : (
        <div
          ref={container}
          class="w-full h-[600px] bg-gray-850 rounded-lg border border-gray-800"
        />
      )}
    </div>
  );
};