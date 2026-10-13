import React, { useState } from 'react';
import { Shield, ShieldAlert, Cpu, Terminal, RefreshCw, Zap, Download } from 'lucide-react';

export default function Navbar({ onSimulate, onSeed, onOpenBlocklist, loading }) {
  const [simulating, setSimulating] = useState(false);

  const handleSimulate = async () => {
    setSimulating(true);
    await onSimulate();
    setSimulating(false);
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Logo and Brand */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 shadow-lg shadow-cyan-500/20 text-white">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">
                Distributed Threat Intelligence Platform
              </h1>
              <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider bg-cyan-950 text-cyan-400 border border-cyan-800/60 rounded-full flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                SOC Active
              </span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-2">
              <span>Flask Microservices</span>
              <span>•</span>
              <span className="text-emerald-400">PostgreSQL</span>
              <span>•</span>
              <span className="text-red-400">Redis In-Memory Cache</span>
              <span>•</span>
              <span className="text-purple-400">K-Means AI</span>
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center flex-wrap gap-2.5">
          <button
            onClick={handleSimulate}
            disabled={simulating || loading}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            title="Simulate realistic honeypot attack traffic burst"
          >
            <Zap className={`w-4 h-4 ${simulating ? 'animate-spin' : 'text-red-400'}`} />
            <span>{simulating ? 'Injecting Attack...' : 'Simulate Honeypot Burst'}</span>
          </button>

          <button
            onClick={onSeed}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all hover:scale-[1.02] active:scale-[0.98]"
            title="Seed fresh telemetry dataset"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Seed Telemetry</span>
          </button>

          <button
            onClick={onOpenBlocklist}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-md shadow-blue-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Download className="w-4 h-4" />
            <span>Firewall Block-List</span>
          </button>
        </div>
      </div>
    </header>
  );
}
