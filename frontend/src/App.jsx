import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import StatCard from './components/StatCard';
import AttackTimelineChart from './components/AttackTimelineChart';
import TopIpsChart from './components/TopIpsChart';
import CountryChart from './components/CountryChart';
import PortDistributionChart from './components/PortDistributionChart';
import ClusteringView from './components/ClusteringView';
import BlocklistModal from './components/BlocklistModal';
import LiveEventFeed from './components/LiveEventFeed';
import EventModal from './components/EventModal';

import {
  ShieldAlert,
  Flame,
  Globe2,
  Lock,
  Layers,
  Radio,
  BrainCircuit,
  BarChart3,
  Server
} from 'lucide-react';

import {
  fetchOverview,
  fetchTimeline,
  fetchTopIps,
  fetchCountries,
  fetchPorts,
  fetchEvents,
  fetchClustering,
  fetchBlocklist,
  simulateAttackBurst,
  seedDemoData
} from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'clustering' | 'live'
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  // Stats state
  const [overview, setOverview] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [topIps, setTopIps] = useState([]);
  const [countries, setCountries] = useState([]);
  const [ports, setPorts] = useState([]);
  const [events, setEvents] = useState([]);
  const [totalEvents, setTotalEvents] = useState(0);
  const [search, setSearch] = useState('');
  const [clustering, setClustering] = useState(null);
  const [blocklist, setBlocklist] = useState([]);

  // Modals
  const [isBlocklistOpen, setIsBlocklistOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const loadAllData = useCallback(async () => {
    try {
      const [ovData, tlData, ipData, coData, poData, clData, blData] = await Promise.all([
        fetchOverview().catch(() => null),
        fetchTimeline().catch(() => null),
        fetchTopIps().catch(() => ({ top_ips: [] })),
        fetchCountries().catch(() => ({ countries: [] })),
        fetchPorts().catch(() => ({ ports: [] })),
        fetchClustering().catch(() => null),
        fetchBlocklist().catch(() => ({ blocklist: [] }))
      ]);

      if (ovData) setOverview(ovData);
      if (tlData) setTimeline(tlData);
      if (ipData?.top_ips) setTopIps(ipData.top_ips);
      if (coData?.countries) setCountries(coData.countries);
      if (poData?.ports) setPorts(poData.ports);
      if (clData) setClustering(clData);
      if (blData?.blocklist) setBlocklist(blData.blocklist);

      // Fetch events
      const evData = await fetchEvents(50, 0, search).catch(() => null);
      if (evData) {
        setEvents(evData.events || []);
        setTotalEvents(evData.total || 0);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    }
  }, [search]);

  useEffect(() => {
    loadAllData();
    // Auto-refresh every 20 seconds
    const interval = setInterval(loadAllData, 20000);
    return () => clearInterval(interval);
  }, [loadAllData]);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      await simulateAttackBurst(8);
      showToast('Simulated honeypot attack traffic burst injected & enriched!', 'success');
      await loadAllData();
    } catch (err) {
      showToast('Simulation failed: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    setLoading(true);
    try {
      await seedDemoData(50);
      showToast('Seeded 50 multi-vector attacks and trained K-Means clusters!', 'success');
      await loadAllData();
    } catch (err) {
      showToast('Seeding failed: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRunClustering = async (k) => {
    setLoading(true);
    try {
      const res = await fetchClustering(k);
      setClustering(res);
      showToast(`scikit-learn K-Means model retrained with k=${k} clusters`, 'success');
    } catch (err) {
      showToast('Clustering failed: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Toast Notification */}
      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-xl shadow-2xl border text-xs font-semibold flex items-center gap-2 animate-bounce ${
            toast.type === 'success'
              ? 'bg-emerald-950 border-emerald-700 text-emerald-200'
              : toast.type === 'error'
              ? 'bg-red-950 border-red-700 text-red-200'
              : 'bg-blue-950 border-blue-700 text-blue-200'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-current"></span>
          <span>{toast.message}</span>
        </div>
      )}

      {/* Top Navbar */}
      <Navbar
        onSimulate={handleSimulate}
        onSeed={handleSeed}
        onOpenBlocklist={() => setIsBlocklistOpen(true)}
        loading={loading}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-6">
        {/* KPI Overview Grid */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard
            title="Total Ingress Attacks"
            value={overview?.total_events}
            subtitle="Interpreted across honeypots"
            icon={Flame}
            color="red"
            badge="Live Telemetry"
          />
          <StatCard
            title="Unique Attackers"
            value={overview?.unique_ips}
            subtitle="Distinct Source IPs tracked"
            icon={ShieldAlert}
            color="amber"
            badge="Tracked Adversaries"
          />
          <StatCard
            title="Origin Countries"
            value={overview?.countries_count}
            subtitle="Enriched via GeoIP Engine"
            icon={Globe2}
            color="cyan"
            badge="Global Spread"
          />
          <StatCard
            title="Critical Threats"
            value={overview?.high_severity_count}
            subtitle="Threat Score ≥ 70 / 100"
            icon={Layers}
            color="purple"
            badge="High Risk"
          />
          <StatCard
            title="Firewall Blocked"
            value={overview?.blocked_ips_count}
            subtitle="Quarantined perimeter rules"
            icon={Lock}
            color="blue"
            badge="Automated Defense"
          />
        </section>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
              activeTab === 'overview'
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Threat Analytics Dashboard</span>
          </button>

          <button
            onClick={() => setActiveTab('clustering')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
              activeTab === 'clustering'
                ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <BrainCircuit className="w-4 h-4" />
            <span>K-Means AI Threat Profiling</span>
          </button>

          <button
            onClick={() => setActiveTab('live')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
              activeTab === 'live'
                ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <Radio className="w-4 h-4" />
            <span>Live Honeypot Telemetry Stream</span>
          </button>
        </div>

        {/* Tab 1: Threat Analytics Dashboard */}
        {activeTab === 'overview' && (
          <div className="space-y-6 animate-fade-in">
            {/* Top Row: Timeline & Top IPs */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AttackTimelineChart
                data={timeline}
                cached={timeline?.source === 'redis_cache'}
              />
              <TopIpsChart
                ips={topIps}
                cached={false}
                onBlockIp={() => setIsBlocklistOpen(true)}
              />
            </div>

            {/* Bottom Row: Countries & Port Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <CountryChart
                countries={countries}
                cached={false}
              />
              <PortDistributionChart
                ports={ports}
                cached={false}
              />
            </div>
          </div>
        )}

        {/* Tab 2: K-Means Clustering */}
        {activeTab === 'clustering' && (
          <div className="animate-fade-in">
            <ClusteringView
              clusterData={clustering}
              onRunClustering={handleRunClustering}
              loading={loading}
            />
          </div>
        )}

        {/* Tab 3: Live Ingress Feed */}
        {activeTab === 'live' && (
          <div className="animate-fade-in">
            <LiveEventFeed
              events={events}
              totalEvents={totalEvents}
              search={search}
              onSearchChange={setSearch}
              onSelectEvent={setSelectedEvent}
            />
          </div>
        )}
      </main>

      {/* Modals */}
      <BlocklistModal
        isOpen={isBlocklistOpen}
        onClose={() => setIsBlocklistOpen(false)}
        blocklist={blocklist}
        onRefresh={loadAllData}
      />

      <EventModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
      />
    </div>
  );
}
