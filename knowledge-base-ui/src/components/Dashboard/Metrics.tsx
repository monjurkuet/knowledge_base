import { Component, createSignal } from 'solid-js';

interface Metrics {
  avg_degree: number;
  density: number;
  clustering: number;
  diameter: number;
}

export const Metrics: Component = () => {
  const [metrics, setMetrics] = createSignal<Metrics>({
    avg_degree: 0,
    density: 0,
    clustering: 0,
    diameter: 0,
  });

  return (
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
      <div class="bg-gray-800 p-4 rounded-lg">
        <div class="text-lg font-bold">{metrics().avg_degree.toFixed(2)}</div>
        <div class="text-xs text-gray-400">Avg Degree</div>
      </div>
      <div class="bg-gray-800 p-4 rounded-lg">
        <div class="text-lg font-bold">{metrics().density.toFixed(4)}</div>
        <div class="text-xs text-gray-400">Density</div>
      </div>
      <div class="bg-gray-800 p-4 rounded-lg">
        <div class="text-lg font-bold">{metrics().clustering.toFixed(3)}</div>
        <div class="text-xs text-gray-400">Clustering</div>
      </div>
      <div class="bg-gray-800 p-4 rounded-lg">
        <div class="text-lg font-bold">{metrics().diameter}</div>
        <div class="text-xs text-gray-400">Diameter</div>
      </div>
    </div>
  );
};