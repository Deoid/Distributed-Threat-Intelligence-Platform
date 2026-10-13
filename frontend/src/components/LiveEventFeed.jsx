import React, { useState } from 'react';
import { Search, Radio, Eye, Shield, Terminal, Globe, Filter } from 'lucide-react';

export default function LiveEventFeed({ events, totalEvents, search, onSearchChange, onSelectEvent }) {
  return (
    <div className="glass-card flex flex-col h-[520px]">
      {/* Table Header and Search Bar */}
      <div className="p-5 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Radio className="w-5 h-5 text-cyan-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Live Honeypot Telemetry Stream
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800/60 rounded">
                {totalEvents} Total Logged
              </span>
            </div>
            <p className="text-xs text-slate-400">Real-time raw & enriched ingress events from deployed sensors</p>
          </div>
        </div>

        {/* Search */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search IP, country, user, port..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900 border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono transition-colors"
          />
        </div>
      </div>

      {/* Events Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/60 sticky top-0 z-10 backdrop-blur-sm">
            <tr className="border-b border-slate-800 text-slate-400 font-mono uppercase text-[11px]">
              <th className="py-3 px-4 font-semibold">Timestamp</th>
              <th className="py-3 px-4 font-semibold">Source IP</th>
              <th className="py-3 px-4 font-semibold">Origin & ASN</th>
              <th className="py-3 px-4 font-semibold">Target Service</th>
              <th className="py-3 px-4 font-semibold">Auth Probe</th>
              <th className="py-3 px-4 font-semibold">Threat Score</th>
              <th className="py-3 px-4 font-semibold text-right">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 font-mono">
            {(events || []).map((ev) => {
              const score = ev.threat_score || 0;
              const isHigh = score >= 80;
              const isMed = score >= 50 && score < 80;

              return (
                <tr key={ev.id} className="hover:bg-slate-800/40 transition-colors group">
                  <td className="py-3 px-4 text-slate-400 text-[11px]">
                    {ev.timestamp ? ev.timestamp.replace('T', ' ').slice(0, 19) : 'Just now'}
                  </td>
                  <td className="py-3 px-4 font-bold text-white group-hover:text-cyan-400 transition-colors">
                    {ev.source_ip}
                  </td>
                  <td className="py-3 px-4 font-sans text-slate-300">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-slate-200">
                        {ev.country || 'Unknown'}
                      </span>
                      {ev.country_code && ev.country_code !== 'XX' && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                          {ev.country_code}
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono truncate max-w-[130px]">
                      {ev.asn || 'AS Unknown'}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-purple-300 font-semibold text-[11px]">
                      {ev.honeypot_type || 'SSH'} :{ev.destination_port}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {ev.username ? (
                      <span className="text-amber-300 bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-900/40">
                        user:{ev.username}
                      </span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-12 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            isHigh ? 'bg-red-500' : isMed ? 'bg-amber-400' : 'bg-blue-400'
                          }`}
                          style={{ width: `${score}%` }}
                        />
                      </div>
                      <span
                        className={`font-bold ${
                          isHigh ? 'text-red-400' : isMed ? 'text-amber-400' : 'text-blue-400'
                        }`}
                      >
                        {score}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onSelectEvent(ev)}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                      title="Inspect Raw Event Details"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
            {(!events || events.length === 0) && (
              <tr>
                <td colSpan="7" className="py-12 text-center text-slate-500 font-sans">
                  No honeypot events matched current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
