# Distributed Threat Intelligence Platform

[![CI/CD Pipeline](https://github.com/threatintel/platform/actions/workflows/ci.yml/badge.svg)](https://github.com/threatintel/platform/actions)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-lightgrey.svg)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7.0-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)

A high-throughput, distributed cyber threat intelligence and honeypot telemetry analytics platform. The system ingests live honeypot attacks, enriches events with GeoIP and ASN metadata, caches high-read queries via Redis, classifies threat actors into behavioral profiles using **scikit-learn K-Means clustering**, and generates automated perimeter firewall block-lists.

---

## 🏛️ System Architecture

The platform is designed around 3 decoupled Python/Flask microservices and a React.js analytics dashboard, orchestrated with Docker Compose:

```
               +-------------------------------------------------------------+
               |                    Honeypot Sensors                         |
               |       (Cowrie SSH/Telnet, Dionaea SMB, Web Honeypots)       |
               +-------------------------------------------------------------+
                                              |
                                              | HTTP POST /ingest
                                              v
                              +-------------------------------+
                              |      Collector Service        |  [Port: 5001]
                              |  - Event Ingestion API        |
                              |  - Telemetry Validation       |
                              +-------------------------------+
                                     |                |
                       RPUSH event   |                | Staging Raw Insert
                                     v                v
                   +-------------------+    +-------------------+
                   |    Redis Queue    |    | PostgreSQL / DB   |
                   | (honeypot_events) |    |  (threat_events)  |
                   +-------------------+    +-------------------+
                             |
                   BLPOP     |
                             v
               +-------------------------------+
               |       Enricher Service        |  [Port: 5002]
               |  - GeoIP & ASN Resolution     |
               |  - Threat Score Heuristics    |
               |  - Aggregates IP Profiles     |
               |  - Invalidates Redis Cache    |
               +-------------------------------+
                             |
             Writes Enriched | Records & IP Profiles
                             v
             +-----------------------------------+
             |       PostgreSQL Database         |
             |  - threat_events                  |
             |  - ip_profiles                    |
             |  - blocklist                      |
             +-----------------------------------+
                             ^
                             | Read / Query
                             v
               +-------------------------------+
               |       API Server Service      |  [Port: 5000]
               |  - REST Analytics Endpoints   | <---> [ Redis Cache Layer ]
               |  - scikit-learn K-Means ML    |       (TTL: 60s, Key: stats:*)
               |  - Firewall Block-List Engine |
               +-------------------------------+
                             ^
                             | REST API / JSON
                             v
               +-------------------------------+
               |    React.js SOC Dashboard     |  [Port: 3000]
               |  - Chart.js Visualizations    |
               |  - K-Means Scatter Projection |
               |  - Live Honeypot Event Feed   |
               |  - Firewall Rules Exporter    |
               +-------------------------------+
```

---

## 🧩 Microservices Breakdown

| Microservice | Technology | Port | Responsibilities |
| :--- | :--- | :--- | :--- |
| **Collector** | Python, Flask, Redis | `5001` | Ingests live telemetry events from distributed honeypots (Cowrie, Dionaea, etc.), validates payload structure, logs raw records to the datastore, and dispatches events to the Redis ingestion queue (`honeypot_events_queue`). Includes attack burst simulation endpoints. |
| **Enricher** | Python, GeoIP, Worker | `5002` | Asynchronously pops events from the Redis queue, queries geolocation (country, city, coordinates, ASN, ISP), calculates normalized threat risk scores (10–100), aggregates behavioral stats into `ip_profiles`, and purges stale Redis API caches. |
| **API Server** | Flask, scikit-learn, Redis | `5000` | Exposes read-heavy REST API analytics endpoints cached via Redis, executes unsupervised **K-Means clustering** over per-IP behavior features, and generates downloadable firewall block-lists (`iptables`, `ufw`, `plain`). |
| **Frontend** | React 18, Chart.js, Vite | `3000` | Interactive SOC dashboard featuring attack volume over time, top offending source IPs, attacking countries, port distribution, K-Means behavioral 2D scatter plots, and live payload inspection. |

---

## ⚡ Redis In-Memory Caching Layer

Read-heavy analytics queries (`/api/stats/overview`, `/api/stats/timeline`, `/api/stats/top-ips`, `/api/stats/countries`, `/api/stats/ports`) are cached in Redis:
- **Cache Hit Latency**: `< 2ms` without querying PostgreSQL.
- **Cache Invalidation**: Automatically invalidated by the **Enricher** via `stats:*` pattern clearing whenever new honeypot events are ingested or processed.
- **Failover / Offline Fallback**: Includes a built-in thread-safe memory cache fallback when Redis is not running in local development mode.

---

## 🧠 K-Means Behavioral Clustering (scikit-learn)

The API server analyzes attacker behavior by extracting 4 per-IP feature vectors from the `ip_profiles` table:
1. `targeted_ports_count`: Number of distinct network ports probed.
2. `usernames_tried_count`: Volume of credential permutations attempted.
3. `request_rate`: Ingress frequency (events / minute).
4. `threat_score`: Heuristic threat score based on critical service targets and exploit strings.

### Generated Behavioral Profiles:
- 🔴 **High-Frequency Distributed Bots**: Aggressive request bursts, high threat scores, automated botnet probes.
- 🟡 **SSH/Credential Brute Forcers**: High density of username/password attempts against authentication ports (22, 23).
- 🔵 **Broad Port Scanners**: Wide horizontal port coverage across services (80, 443, 3389, 445, 6379) searching for perimeter openings.
- 🟢 **Targeted Exploit Probers**: Low-and-slow targeted reconnaissance against isolated endpoints.

The results are projected as an interactive **Chart.js 2D Scatter Chart** on the dashboard (Request Rate vs. Targeted Ports with bubble diameters scaling to authentication attempts).

---

## 🛡️ Firewall Block-List Engine

The platform automatically flags IPs with high threat scores ($\ge 80$) and provides rule exports:
- **`iptables`**:
  ```bash
  iptables -A INPUT -s 185.220.101.5 -j DROP -m comment --comment "Score:95 - Critical threat score"
  ```
- **`UFW`**:
  ```bash
  ufw deny from 185.220.101.5 comment "ThreatScore 95"
  ```
- **Plain Text**: Single IP per line for direct integration into Fail2ban, Suricata, or cloud firewalls (AWS WAF / Cloudflare).

---

## 🚀 Quick Start with Docker Compose

To build and run all microservices, database, and Redis cache in containers:

```bash
# 1. Clone the repository
git clone https://github.com/your-username/threat-intelligence-platform.git
cd threat-intelligence-platform

# 2. Build and start all 6 containers
docker compose up --build -d

# 3. Check container health status
docker compose ps
```

The services will be accessible at:
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **API Server**: [http://localhost:5000](http://localhost:5000)
- **Collector API**: [http://localhost:5001](http://localhost:5001)
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

---

## 💻 Local Development Setup (Without Docker)

The platform is designed with seamless SQLite and in-memory Redis fallbacks, allowing you to run and test it on any machine:

### 1. Install Backend Dependencies
```bash
python -m pip install flask flask-cors redis scikit-learn numpy pytest requests
```

### 2. Start Microservices

**Terminal 1 (Collector):**
```bash
python services/collector/app.py
```

**Terminal 2 (Enricher):**
```bash
python services/enricher/worker.py
```

**Terminal 3 (API Server):**
```bash
python services/api_server/app.py
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the live dashboard!

---

## 🧪 Running Automated Tests

Run the test suite across all 3 microservices with `pytest`:

```bash
python -m pytest -v services/
```

**Included Tests:**
- `services/collector/test_collector.py`: Validates event ingestion, schema checks, missing field rejections, and honeypot attack simulation.
- `services/enricher/test_enricher.py`: Validates deterministic GeoIP mapping, coordinates calculation, and threat scoring heuristics.
- `services/api_server/test_api.py`: Validates health status, stats aggregation, scikit-learn clustering endpoints, and firewall block-list lifecycle (add, export, remove).

---

## 🔄 CI/CD Pipeline (GitHub Actions)

The platform includes automated **CI** and **CD** pipelines located in `.github/workflows/`:

### 1. Continuous Integration (`ci.yml`)
Triggered on every `push` and `pull_request`:
- Spawns live **PostgreSQL 15** & **Redis 7** service containers in GitHub Actions.
- Sets up Python 3.11 and runs database migrations from `db/init.sql`.
- Executes the full unit and integration test suite (`pytest -v services/`).
- Validates Docker build feasibility across all microservices (`collector`, `enricher`, `api_server`, `frontend`).

### 2. Continuous Deployment (`cd.yml`)
Triggered on merge to `main`, semantic release tags (`v*.*.*`), or via manual **Workflow Dispatch**:
- **Image Publishing**: Builds multi-arch container images using Docker Buildx and publishes them to **GitHub Container Registry (GHCR)** tagged with `:latest`, `:${{ github.sha }}`, and semantic release tags.
- **Production Rollout**: Uses [`scripts/deploy.sh`](file:///c:/Users/Hardik/OneDrive/Desktop/Threat%20Intelligence%20Platform/scripts/deploy.sh) and [`docker-compose.prod.yml`](file:///c:/Users/Hardik/OneDrive/Desktop/Threat%20Intelligence%20Platform/docker-compose.prod.yml) to perform zero-downtime rolling container updates on the production host.
- **Automated Health Checks**: Runs curl smoke tests against `/api/health` and `/health` post-deploy to guarantee zero downtime.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health, Redis status, and DB type |
| `GET` | `/api/stats/overview` | Overall metrics (total attacks, IPs, countries, blocked count) |
| `GET` | `/api/stats/timeline` | Hourly attack counts over the last 24 hours |
| `GET` | `/api/stats/top-ips` | Top 10 offending source IPs with threat scores |
| `GET` | `/api/stats/countries` | Attack distribution grouped by country |
| `GET` | `/api/stats/ports` | Targeted destination ports and services |
| `GET` | `/api/events` | Paginated raw and enriched honeypot events (`limit`, `offset`, `search`) |
| `POST` | `/api/events/seed` | Populates demo multi-vector attack events |
| `GET/POST`| `/api/clustering` | Runs or retrieves K-Means behavioral clustering (`k=4`) |
| `GET` | `/api/blocklist` | Current firewall block-list entries |
| `POST` | `/api/blocklist` | Manually add an IP to the block-list |
| `DELETE`| `/api/blocklist/<ip>` | Remove an IP from the block-list |
| `GET` | `/api/blocklist/export`| Export rules formatted as `iptables`, `ufw`, or `plain` |
| `POST` | `/ingest` | Ingest honeypot event (Collector port `5001`) |
| `POST` | `/simulate` | Simulate burst of realistic attacks (Collector port `5001`) |

---

## 📄 License
MIT License. Created for distributed cyber threat intelligence analysis and research.
