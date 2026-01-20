const API_BASE = '/api';

export interface Node {
  id: string;
  name: string;
  type: string;
}

export interface Edge {
  source: string;
  target: string;
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

export interface Stats {
  nodes_count: number;
  edges_count: number;
  communities_count: number;
  events_count: number;
}

export interface SearchResult {
  id: string;
  name: string;
  type: string;
  description?: string;
  score: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
}

export interface Domain {
  id: string;
  name: string;
  description: string;
  node_count: number;
  edge_count: number;
}

export interface SchemaField {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

export const api = {
  async getStats(): Promise<Stats> {
    const response = await fetch(`${API_BASE}/stats`);
    return response.json();
  },

  async getGraph(limit = 10000): Promise<GraphData> {
    const response = await fetch(`${API_BASE}/graph?limit=${limit}`);
    return response.json();
  },

  async search(query: string): Promise<SearchResponse> {
    const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
    return response.json();
  },

  async getDomains(): Promise<{ domains: Domain[] }> {
    const response = await fetch(`${API_BASE}/domains`);
    return response.json();
  },

  async getDomainSchema(domainId: string): Promise<{ schema: SchemaField[] }> {
    const response = await fetch(`${API_BASE}/domains/${domainId}/schema`);
    return response.json();
  },

  async ingestText(data: {
    text: string;
    filename: string;
    channel_id: string;
  }): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/ingest/text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async ingestFile(file: File, channelId: string): Promise<{ success: boolean; message: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('channel_id', channelId);

    const response = await fetch(`${API_BASE}/ingest/file`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  },
};