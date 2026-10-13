import React, { useState } from 'react';
import { X, ShieldAlert, Download, Copy, Check, Trash2, Plus, Terminal } from 'lucide-react';
import { getBlocklistExportUrl, addToBlocklist, removeFromBlocklist } from '../services/api';

export default function BlocklistModal({ isOpen, onClose, blocklist, onRefresh }) {
  const [format, setFormat] = useState('iptables');
  const [minScore, setMinScore] = useState(0);
  const [copied, setCopied] = useState(false);
  const [newIp, setNewIp] = useState('');
  const [newReason, setNewReason] = useState('');
  const [adding, setAdding] = useState(false);

  if (!isOpen) return null;

  const handleDownload = () => {
    const url = getBlocklistExportUrl(format, minScore);
    window.open(url, '_blank');
  };

  const handleCopyRules = () => {
    let text = '';
    const filtered = (blocklist || []).filter(b => b.threat_score >= minScore);

    if (format === 'iptables') {
      text = filtered.map(b => `iptables -A INPUT -s ${b.ip} -j DROP -m comment --comment "ThreatScore:${b.threat_score}"`).join('\n');
    } else if (format === 'ufw') {
      text = filtered.map(b => `ufw deny from ${b.ip} comment "ThreatScore ${b.threat_score}"`).join('\n');
    } else {
      text = filtered.map(b => b.ip).join('\n');
    }

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleAddIp = async (e) => {
    e.preventDefault();
    if (!newIp.trim()) return;
    setAdding(true);
    try {
      await addToBlocklist(newIp.trim(), newReason.trim() || 'Manual Security Operator Block', 95, 'Manual Override');
      setNewIp('');
      setNewReason('');
      onRefresh();
    } catch (err) {
      alert('Error adding IP: ' + err.message);
    } finally {
      setAdding(false);
    }
  };

  const handleRemoveIp = async (ip) => {
    try {
      await removeFromBlocklist(ip);
      onRefresh();
    } catch (err) {
      alert('Error removing IP: ' + err.message);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="glass-card w-full max-w-4xl max-h-[90vh] flex flex-col border border-slate-700 bg-slate-900 shadow-2xl rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Firewall Block-List Generator</h3>
              <p className="text-xs text-slate-400">Export active threat actor feeds to perimeter edge firewalls</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Export Configuration Controls */}
        <div className="p-6 border-b border-slate-800/80 bg-slate-950/40 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Firewall Syntax
            </label>
            <div className="grid grid-cols-3 gap-1.5 bg-slate-900 p-1 rounded-lg border border-slate-800">
              {['iptables', 'ufw', 'plain'].map((f) => (
                <button
                  key={f}
                  onClick={() => setFormat(f)}
                  className={`py-1.5 text-xs font-mono font-semibold rounded uppercase transition-colors ${
                    format === f ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Min Threat Score ({minScore})
            </label>
            <input
              type="range"
              min="0"
              max="95"
              step="5"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500 mt-2"
            />
          </div>

          <div className="flex items-end gap-2">
            <button
              onClick={handleCopyRules}
              className="flex-1 flex items-center justify-center gap-2 py-2 px-3 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              <span>{copied ? 'Copied!' : 'Copy Rules'}</span>
            </button>
            <button
              onClick={handleDownload}
              className="flex-1 flex items-center justify-center gap-2 py-2 px-3 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-500/20 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
          </div>
        </div>

        {/* Quick Add Custom IP Form */}
        <form onSubmit={handleAddIp} className="px-6 py-3 border-b border-slate-800 bg-slate-900 flex gap-3">
          <input
            type="text"
            placeholder="Manual IP (e.g. 198.51.100.44)"
            value={newIp}
            onChange={(e) => setNewIp(e.target.value)}
            className="flex-1 px-3 py-1.5 text-xs font-mono bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-blue-500"
          />
          <input
            type="text"
            placeholder="Block Reason"
            value={newReason}
            onChange={(e) => setNewReason(e.target.value)}
            className="flex-1 px-3 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={adding || !newIp.trim()}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-red-600/30 hover:bg-red-600/50 text-red-300 border border-red-500/30 disabled:opacity-50"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Block IP</span>
          </button>
        </form>

        {/* Blocked IPs Table */}
        <div className="flex-1 overflow-y-auto p-6">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-mono">
                <th className="pb-3 font-semibold">Attacker IP</th>
                <th className="pb-3 font-semibold">Threat Score</th>
                <th className="pb-3 font-semibold">Assigned Profile</th>
                <th className="pb-3 font-semibold">Block Reason</th>
                <th className="pb-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {(blocklist || []).map((item) => (
                <tr key={item.id || item.ip} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2.5 font-bold text-red-400">{item.ip}</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-800/40 font-semibold">
                      {item.threat_score} / 100
                    </span>
                  </td>
                  <td className="py-2.5 text-slate-300 font-sans">{item.cluster_profile || 'Attacker'}</td>
                  <td className="py-2.5 text-slate-400 font-sans max-w-xs truncate">{item.reason}</td>
                  <td className="py-2.5 text-right font-sans">
                    <button
                      onClick={() => handleRemoveIp(item.ip)}
                      className="p-1 rounded text-slate-500 hover:text-red-400 transition-colors"
                      title="Unblock this IP"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {(!blocklist || blocklist.length === 0) && (
                <tr>
                  <td colSpan="5" className="py-8 text-center text-slate-500 font-sans">
                    No IPs currently in the blocklist. Attacking IPs with high threat scores will be auto-quarantined.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
