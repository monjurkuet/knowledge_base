import { createSignal, writable } from 'solid-js/store';

export interface GraphState {
  nodes: Map<string, any>;
  edges: Array<any>;
  selectedNode: string | null;
  layout: string;
  filter: string;
}

const initialState: GraphState = {
  nodes: new Map(),
  edges: [],
  selectedNode: null,
  layout: 'circular',
  filter: 'all',
};

export function createGraphStore() {
  const [state, setState] = createSignal(initialState);

  return {
    get state() {
      return state();
    },
    setNodes(nodes: Map<string, any>) {
      setState((prev) => ({ ...prev, nodes }));
    },
    addNode(id: string, data: any) {
      setState((prev) => {
        const newNodes = new Map(prev.nodes);
        newNodes.set(id, data);
        return { ...prev, nodes: newNodes };
      });
    },
    setEdges(edges: Array<any>) {
      setState((prev) => ({ ...prev, edges }));
    },
    setSelectedNode(nodeId: string | null) {
      setState((prev) => ({ ...prev, selectedNode: nodeId }));
    },
    setLayout(layout: string) {
      setState((prev) => ({ ...prev, layout }));
    },
    setFilter(filter: string) {
      setState((prev) => ({ ...prev, filter }));
    },
    reset() {
      setState(initialState);
    },
  };
}

export const graphStore = createGraphStore();