import { Component, createSignal, onMount } from 'solid-js';

interface Stats {
  nodes_count: number;
  edges_count: number;
  communities_count: number;
  events_count: number;
}

export const Dashboard: Component = () => {
  const [stats, setStats] = createSignal<Stats>({
    nodes_count: 0,
    edges_count: 0,
    communities_count: 0,
    events_count: 0,
  });

  onMount(async () => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    };

    await fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  });

  return (
    <header class="bg-gray-900 border-b border-gray-800 p-6">
      <div class="max-w-7xl mx-auto">
        <h1 class="text-3xl font-bold mb-6">🧠 Knowledge Base Dashboard</h1>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="bg-gradient-to-br from-blue-600 to-blue-800 p-4 rounded-lg shadow-lg">
            <div class="text-3xl font-bold">{stats().nodes_count.toLocaleString()}</div>
            <div class="text-sm text-blue-100 mt-1">Nodes</div>
          </div>
          <div class="bg-gradient-to-br from-green-600 to-green-800 p-4 rounded-lg shadow-lg">
            <div class="text-3xl font-bold">{stats().edges_count.toLocaleString()}</div>
            <div class="text-sm text-green-100 mt-1">Edges</div>
          </div>
          <div class="bg-gradient-to-br from-purple-600 to-purple-800 p-4 rounded-lg shadow-lg">
            <div class="text-3xl font-bold">{stats().communities_count.toLocaleString()}</div>
            <div class="text-sm text-purple-100 mt-1">Communities</div>
          </div>
          <div class="bg-gradient-to-br from-orange-600 to-orange-800 p-4 rounded-lg shadow-lg">
            <div class="text-3xl font-bold">{stats().events_count.toLocaleString()}</div>
            <div class="text-sm text-orange-100 mt-1">Events</div>
          </div>
        </div>
      </div>
    </header>
  );
};