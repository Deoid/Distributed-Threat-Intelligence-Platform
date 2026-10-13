import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { Globe2 } from 'lucide-react';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function CountryChart({ countries, cached }) {
  const topCountries = (countries || []).slice(0, 6);
  const labels = topCountries.map(c => `${c.country} (${c.country_code})`);
  const counts = topCountries.map(c => c.event_count);

  const colors = [
    '#ef4444', // Red
    '#f59e0b', // Amber
    '#06b6d4', // Cyan
    '#8b5cf6', // Purple
    '#3b82f6', // Blue
    '#10b981'  // Emerald
  ];

  const chartData = {
    labels,
    datasets: [
      {
        data: counts,
        backgroundColor: colors.slice(0, counts.length),
        borderColor: '#0f172a',
        borderWidth: 2,
        hoverOffset: 6
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '65%',
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: '#cbd5e1',
          font: { size: 11, family: "'Plus Jakarta Sans', sans-serif" },
          padding: 12,
          usePointStyle: true,
          pointStyle: 'circle'
        }
      },
      tooltip: {
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        borderWidth: 1,
        titleColor: '#f8fafc',
        bodyColor: '#38bdf8',
        callbacks: {
          label: (context) => ` ${context.parsed} attack events`
        }
      }
    }
  };

  return (
    <div className="glass-card p-5 flex flex-col h-[360px]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Globe2 className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white tracking-wide uppercase">Attacking Countries</h3>
        </div>
        {cached && (
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/50">
            Redis Cached
          </span>
        )}
      </div>

      <div className="flex-1 w-full relative flex items-center justify-center">
        {counts.length > 0 ? (
          <Doughnut data={chartData} options={options} />
        ) : (
          <div className="text-slate-500 text-sm">No geographic telemetry recorded.</div>
        )}
      </div>
    </div>
  );
}
