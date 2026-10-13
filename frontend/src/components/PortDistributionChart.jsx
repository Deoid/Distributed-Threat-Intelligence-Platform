import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { Server } from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const PORT_SERVICE_NAMES = {
  21: 'FTP',
  22: 'SSH',
  23: 'Telnet',
  80: 'HTTP',
  443: 'HTTPS',
  445: 'SMB',
  3306: 'MySQL',
  3389: 'RDP',
  5432: 'PostgreSQL',
  6379: 'Redis',
  8080: 'HTTP-Alt',
  8443: 'HTTPS-Alt'
};

export default function PortDistributionChart({ ports, cached }) {
  const portList = (ports || []).slice(0, 8);
  const labels = portList.map(p => `${p.port} (${PORT_SERVICE_NAMES[p.port] || p.protocol})`);
  const counts = portList.map(p => p.count);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Inbound Probes',
        data: counts,
        backgroundColor: 'rgba(139, 92, 246, 0.75)',
        borderColor: '#8b5cf6',
        borderWidth: 1,
        borderRadius: 4
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        borderWidth: 1,
        titleColor: '#f8fafc',
        bodyColor: '#a78bfa',
        callbacks: {
          label: (context) => ` ${context.parsed.y} probes intercepted`
        }
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#cbd5e1', font: { size: 10, family: "'JetBrains Mono', monospace" } }
      },
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
        ticks: { color: '#94a3b8', font: { size: 10, family: "'JetBrains Mono', monospace" } }
      }
    }
  };

  return (
    <div className="glass-card p-5 flex flex-col h-[360px]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-purple-400" />
          <h3 className="text-sm font-semibold text-white tracking-wide uppercase">Targeted Ports & Services</h3>
        </div>
        {cached && (
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/50">
            Redis Cached
          </span>
        )}
      </div>

      <div className="flex-1 w-full relative">
        {counts.length > 0 ? (
          <Bar data={chartData} options={options} />
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500 text-sm">
            No targeted port telemetry recorded.
          </div>
        )}
      </div>
    </div>
  );
}
