import React from 'react';

export default function StatCard({ title, value, subtitle, icon: Icon, badge, color = 'blue' }) {
  const colorMap = {
    blue: {
      bg: 'from-blue-500/10 to-blue-600/5',
      border: 'border-blue-500/20',
      text: 'text-blue-400',
      badge: 'bg-blue-950 text-blue-300 border-blue-800/40',
      glow: 'shadow-blue-500/5'
    },
    cyan: {
      bg: 'from-cyan-500/10 to-cyan-600/5',
      border: 'border-cyan-500/20',
      text: 'text-cyan-400',
      badge: 'bg-cyan-950 text-cyan-300 border-cyan-800/40',
      glow: 'shadow-cyan-500/5'
    },
    red: {
      bg: 'from-red-500/10 to-red-600/5',
      border: 'border-red-500/20',
      text: 'text-red-400',
      badge: 'bg-red-950 text-red-300 border-red-800/40',
      glow: 'shadow-red-500/5'
    },
    amber: {
      bg: 'from-amber-500/10 to-amber-600/5',
      border: 'border-amber-500/20',
      text: 'text-amber-400',
      badge: 'bg-amber-950 text-amber-300 border-amber-800/40',
      glow: 'shadow-amber-500/5'
    },
    purple: {
      bg: 'from-purple-500/10 to-purple-600/5',
      border: 'border-purple-500/20',
      text: 'text-purple-400',
      badge: 'bg-purple-950 text-purple-300 border-purple-800/40',
      glow: 'shadow-purple-500/5'
    }
  };

  const c = colorMap[color] || colorMap.blue;

  return (
    <div className={`p-5 rounded-xl bg-gradient-to-br ${c.bg} border ${c.border} shadow-lg ${c.glow} relative overflow-hidden backdrop-blur-sm transition-all hover:translate-y-[-2px]`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold tracking-wider text-slate-400 uppercase">{title}</p>
          <h3 className="text-2xl font-bold tracking-tight text-white mt-1.5 font-mono">
            {value !== undefined && value !== null ? value.toLocaleString() : '—'}
          </h3>
          {subtitle && (
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
              {subtitle}
            </p>
          )}
        </div>
        <div className={`p-2.5 rounded-lg bg-slate-900/60 border ${c.border} ${c.text}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {badge && (
        <div className="mt-3">
          <span className={`inline-block px-2 py-0.5 text-[11px] font-medium rounded border ${c.badge}`}>
            {badge}
          </span>
        </div>
      )}
    </div>
  );
}
