import React from 'react';
import { X, Terminal, Shield, Globe, Server, Hash } from 'lucide-react';

export default function EventModal({ event, onClose }) {
  if (!event) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-card w-full max-w-2xl bg-slate-900 border border-slate-700 shadow-2xl rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white font-mono">
              Event #{event.id} Inspection
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 text-xs font-mono">
          <div className="grid grid-cols-2 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div>
              <span className="text-slate-500 block">Attacker IP:</span>
              <span className="text-cyan-400 font-bold text-sm">{event.source_ip}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Threat Score:</span>
              <span className="text-red-400 font-bold text-sm">{event.threat_score} / 100</span>
            </div>
            <div>
              <span className="text-slate-500 block">Geolocation:</span>
              <span className="text-slate-200">
                {event.city || 'Unknown'}, {event.country} ({event.country_code})
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">ASN / ISP:</span>
              <span className="text-slate-200 truncate block">{event.asn || 'AS Unknown'} ({event.isp || 'Unknown ISP'})</span>
            </div>
            <div>
              <span className="text-slate-500 block">Destination Port:</span>
              <span className="text-purple-400 font-bold">{event.destination_port} ({event.protocol})</span>
            </div>
            <div>
              <span className="text-slate-500 block">Honeypot Sensor:</span>
              <span className="text-amber-400 font-bold">{event.honeypot_type}</span>
            </div>
          </div>

          {/* Credentials Tried */}
          {(event.username || event.password) && (
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
              <span className="text-slate-500 block mb-1">Captured Authentication Payload:</span>
              <div className="text-amber-300">
                <span>Username: </span>
                <span className="text-white font-bold">{event.username || '<none>'}</span>
              </div>
            </div>
          )}

          {/* Raw Payload / Hex / Command */}
          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
            <span className="text-slate-500 block mb-1">Raw Payload / Command:</span>
            <pre className="text-slate-300 bg-slate-900/80 p-3 rounded-lg overflow-x-auto text-[11px] whitespace-pre-wrap leading-relaxed">
              {event.raw_payload || 'No raw payload content recorded.'}
            </pre>
          </div>
        </div>

        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
