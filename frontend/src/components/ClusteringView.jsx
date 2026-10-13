import React, { useState } from 'react';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
} from 'chart.js';
import { Scatter } from 'react-chartjs-2';
import { BrainCircuit, RefreshCw, ShieldAlert, Cpu, Fingerprint, Layers } from 'lucide-react';

ChartJS.register(LinearScale, PointElement, Tooltip, Legend);

const CLUSTER_COLORS = [
  '#ef4444', // Cluster 0: Red
  '#06b6d4', // Cluster 1: Cyan
  '#8b5cf6', // Cluster 2: Purple
  '#f59e0b', // Cluster 3: Amber
  '#10b981'  // Cluster 4: Emerald
];

export default function ClusteringView({ clusterData, onRunClustering, loading }) {
  const [selectedK, setSelectedK] = useState(4);

  const clusters = clusterData?.clusters || [];
  const scatterPoints = clusterData?.scatter_points || [];

  // Group scatter points by cluster_id
  const datasets = clusters.map((c, idx) => {
    const points = scatterPoints.filter(p => p.cluster_id === c.cluster_id);
    return {
      label: c.profile_name,
      data: points.map(p => ({
        x: p.x, // Request Rate
        y: p.y, // Ports targeted
        size: p.size,
        ip: p.ip,
        country: p.country,
        score: p.threat_score
      })),
      backgroundColor: CLUSTER_COLORS[idx % CLUSTER_COLORS.length],
      borderColor: '#0f172a',
      borderWidth: 1.5,
      pointRadius: (ctx) => {
        const raw = ctx.raw;
        return raw?.size ? Math.max(5, Math.min(14, raw.size)) : 6;
      },
      pointHoverRadius: 9
    };
  });

  const scatterOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#cbd5e1',
          font: { size: 11, family: "'Plus Jakarta Sans', sans-serif" },
          padding: 12,
          usePointStyle: true
        }
      },
      tooltip: {
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        borderWidth: 1,
        titleColor: '#f8fafc',
        bodyColor: '#38bdf8',
        callbacks: {
          title: (items) => {
            const raw = items[0]?.raw;
            return `IP: ${raw?.ip} (${raw?.country || 'Unknown'})`;
          },
          label: (context) => {
            const raw = context.raw;
            return [
              `Profile: ${context.dataset.label}`,
              `Request Rate: ${raw?.x} req/min`,
              `Targeted Ports: ${raw?.y}`,
              `Threat Score: ${raw?.score}/100`
            ];
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Request Rate (Events / Min)',
          color: '#94a3b8',
          font: { size: 12, family: "'Plus Jakarta Sans', sans-serif" }
        },
        grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
        ticks: { color: '#94a3b8', font: { size: 10, family: "'JetBrains Mono', monospace" } }
      },
      y: {
        title: {
          display: true,
          text: 'Targeted Ports Count',
          color: '#94a3b8',
          font: { size: 12, family: "'Plus Jakarta Sans', sans-serif" }
        },
        beginAtZero: true,
        grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
        ticks: { color: '#94a3b8', font: { size: 10, family: "'JetBrains Mono', monospace" } }
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="glass-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">
                K-Means Behavioral Threat Profiling
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Clustering per-IP features: Targeted Ports, Usernames Tried, Request Rate, and Threat Severity
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700/80 rounded-lg p-1 text-xs">
            <span className="text-slate-400 px-2 font-medium">Clusters (k):</span>
            {[3, 4, 5].map((k) => (
              <button
                key={k}
                onClick={() => setSelectedK(k)}
                className={`px-2.5 py-1 rounded font-mono font-semibold transition-colors ${
                  selectedK === k
                    ? 'bg-purple-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {k}
              </button>
            ))}
          </div>

          <button
            onClick={() => onRunClustering(selectedK)}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-purple-600 hover:bg-purple-500 text-white shadow-md shadow-purple-500/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Re-Cluster with scikit-learn</span>
          </button>
        </div>
      </div>

      {/* Cluster Behavioral Profiles Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {clusters.map((c, idx) => {
          const color = CLUSTER_COLORS[idx % CLUSTER_COLORS.length];
          return (
            <div
              key={c.cluster_id}
              className="glass-card p-4 relative overflow-hidden flex flex-col justify-between"
              style={{ borderTop: `3px solid ${color}` }}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                    Cluster #{c.cluster_id}
                  </span>
                  <span
                    className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                      c.risk_level === 'Critical'
                        ? 'bg-red-950 text-red-400 border border-red-800/40'
                        : c.risk_level === 'High'
                        ? 'bg-amber-950 text-amber-400 border border-amber-800/40'
                        : 'bg-blue-950 text-blue-400 border border-blue-800/40'
                    }`}
                  >
                    {c.risk_level} Risk
                  </span>
                </div>

                <h4 className="text-sm font-bold text-white mt-2.5">{c.profile_name}</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{c.description}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] space-y-1 font-mono text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-500">Avg Ports:</span>
                  <span>{c.center?.avg_targeted_ports}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Avg Usernames:</span>
                  <span>{c.center?.avg_usernames_tried}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Avg Request Rate:</span>
                  <span>{c.center?.avg_request_rate} /min</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Identified IPs:</span>
                  <span className="text-cyan-400 font-bold">{c.member_count} IPs</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Interactive 2D Feature Scatter Plot */}
      <div className="glass-card p-6 h-[460px] flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Fingerprint className="w-5 h-5 text-purple-400" />
            <h3 className="text-sm font-semibold text-white tracking-wide uppercase">
              Attacker Behavioral Cluster Projections (Request Rate vs. Targeted Ports)
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Bubble Diameter ∝ Authentication Attempts
          </span>
        </div>

        <div className="flex-1 w-full relative">
          {scatterPoints.length > 0 ? (
            <Scatter data={{ datasets }} options={scatterOptions} />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 text-sm gap-2">
              <Layers className="w-8 h-8 text-slate-600 animate-pulse" />
              <span>No cluster projections available. Ingest or seed events to train model.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
