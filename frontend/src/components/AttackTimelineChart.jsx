import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { Activity } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function AttackTimelineChart({ data, cached }) {
  const labels = data?.labels?.length ? data.labels : ['12:00', '14:00', '16:00', '18:00', '20:00', '22:00'];
  const series = data?.series?.length ? data.series : [12, 19, 8, 27, 43, 31];

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Attacks Detected / Hour',
        data: series,
        fill: true,
        borderColor: '#06b6d4',
        backgroundColor: (context) => {
          const ctx = context.chart.ctx;
          const gradient = ctx.createLinearGradient(0, 0, 0, 300);
          gradient.addColorStop(0, 'rgba(6, 182, 212, 0.45)');
          gradient.addColorStop(1, 'rgba(6, 182, 212, 0.0)');
          return gradient;
        },
        borderWidth: 2.5,
        tension: 0.35,
        pointBackgroundColor: '#06b6d4',
        pointBorderColor: '#090d16',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        borderWidth: 1,
        titleColor: '#f8fafc',
        bodyColor: '#38bdf8',
        padding: 10,
        displayColors: false,
        callbacks: {
          label: (context) => `${context.parsed.y} attack events detected`
        }
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
          drawBorder: false
        },
        ticks: {
          color: '#94a3b8',
          font: { size: 11, family: "'JetBrains Mono', monospace" },
          maxRotation: 45
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
          drawBorder: false
        },
        ticks: {
          color: '#94a3b8',
          font: { size: 11, family: "'JetBrains Mono', monospace" }
        }
      }
    }
  };

  return (
    <div className="glass-card p-5 flex flex-col h-[360px]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white tracking-wide uppercase">Attack Volume Over Time</h3>
        </div>
        <div className="flex items-center gap-2">
          {cached && (
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/50">
              Redis Cached
            </span>
          )}
          <span className="text-xs text-slate-400">Past 24 Hours</span>
        </div>
      </div>
      <div className="flex-1 w-full relative">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
