import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { Crosshair, ShieldAlert } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function TopIpsChart({ ips, cached, onBlockIp }) {
  const topIpsList = (ips || []).slice(0, 8);
  const labels = topIpsList.map(item => item.ip);
  const counts = topIpsList.map(item => item.total_events);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Total Attack Events',
        data: counts,
        backgroundColor: topIpsList.map(item => {
          const score = item.threat_score || 0;
          if (score >= 80) return 'rgba(239, 68, 68, 0.85)';
          if (score >= 50) return 'rgba(245, 158, 11, 0.85)';
          return 'rgba(59, 130, 246, 0.85)';
        }),
        borderRadius: 4,
        borderWidth: 0,
        barThickness: 16
      }
    ]
  };

  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        borderWidth: 1,
        titleColor: '#f8fafc',
        bodyColor: '#38bdf8',
        padding: 10,
        callbacks: {
          label: (context) => {
            const item = topIpsList[context.dataIndex];
            return `${context.parsed.x} attacks | Threat Score: ${item?.threat_score || 0} | Country: ${item?.country || 'Unknown'}`;
          }
        }
      }
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
        ticks: { color: '#94a3b8', font: { size: 10, family: "'JetBrains Mono', monospace" } }
      },
      y: {
        grid: { display: false },
        ticks: { color: '#e2e8f0', font: { size: 11, family: "'JetBrains Mono', monospace" } }
      }
    }
  };

  return (
    <div className="glass-card p-5 flex flex-col h-[360px]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Crosshair className="w-5 h-5 text-red-400" />
          <h3 className="text-sm font-semibold text-white tracking-wide uppercase">Top Offending Source IPs</h3>
        </div>
        {cached && (
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/50">
            Redis Cached
          </span>
        )}
      </div>

      <div className="flex-1 w-full relative">
        {labels.length > 0 ? (
          <Bar data={chartData} options={options} />
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500 text-sm">
            No malicious IPs logged yet.
          </div>
        )}
      </div>
    </div>
  );
}
