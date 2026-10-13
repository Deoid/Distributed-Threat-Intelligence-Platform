const API_BASE = '/api';
const COLLECTOR_BASE = ''; // proxied via vite or directly

export async function fetchOverview() {
  const res = await fetch(`${API_BASE}/stats/overview`);
  if (!res.ok) throw new Error('Failed to fetch overview');
  return res.json();
}

export async function fetchTimeline() {
  const res = await fetch(`${API_BASE}/stats/timeline`);
  if (!res.ok) throw new Error('Failed to fetch timeline');
  return res.json();
}

export async function fetchTopIps() {
  const res = await fetch(`${API_BASE}/stats/top-ips`);
  if (!res.ok) throw new Error('Failed to fetch top IPs');
  return res.json();
}

export async function fetchCountries() {
  const res = await fetch(`${API_BASE}/stats/countries`);
  if (!res.ok) throw new Error('Failed to fetch countries');
  return res.json();
}

export async function fetchPorts() {
  const res = await fetch(`${API_BASE}/stats/ports`);
  if (!res.ok) throw new Error('Failed to fetch ports');
  return res.json();
}

export async function fetchEvents(limit = 50, offset = 0, search = '') {
  const query = new URLSearchParams({ limit, offset, search });
  const res = await fetch(`${API_BASE}/events?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch events');
  return res.json();
}

export async function fetchClustering(k = 4) {
  const res = await fetch(`${API_BASE}/clustering?k=${k}`);
  if (!res.ok) throw new Error('Failed to fetch clustering');
  return res.json();
}

export async function fetchBlocklist() {
  const res = await fetch(`${API_BASE}/blocklist`);
  if (!res.ok) throw new Error('Failed to fetch blocklist');
  return res.json();
}

export async function addToBlocklist(ip, reason, threatScore, clusterProfile) {
  const res = await fetch(`${API_BASE}/blocklist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ip, reason, threat_score: threatScore, cluster_profile: clusterProfile })
  });
  if (!res.ok) throw new Error('Failed to add to blocklist');
  return res.json();
}

export async function removeFromBlocklist(ip) {
  const res = await fetch(`${API_BASE}/blocklist/${encodeURIComponent(ip)}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to remove from blocklist');
  return res.json();
}

export function getBlocklistExportUrl(format = 'iptables', minScore = 0) {
  return `${API_BASE}/blocklist/export?format=${format}&min_score=${minScore}`;
}

export async function simulateAttackBurst(count = 10, sourceIp = null) {
  const res = await fetch(`/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ count, source_ip: sourceIp })
  });
  if (!res.ok) {
    // If collector proxy isn't hit directly, fallback to api server seed endpoint
    const fallbackRes = await fetch(`${API_BASE}/events/seed?count=${count}`, { method: 'POST' });
    return fallbackRes.json();
  }
  return res.json();
}

export async function seedDemoData(count = 50) {
  const res = await fetch(`${API_BASE}/events/seed?count=${count}`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to seed demo data');
  return res.json();
}
