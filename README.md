# IxOS Port Utilization Plotter

Real-time monitoring for Ixia/Keysight IxOS chassis. Polls port ownership, link state, and blocked status — stores time-series data in InfluxDB, exposes CPU/sensor metrics via Prometheus, visualizes everything in Grafana.

---

## Architecture

```
IxOS Chassis (HTTPS :443)
       │
       ├─ portInfoPoller.py ──────► InfluxDB :8087       (port ownership, blocked status)
       ├─ perfMetricsPoller.py ───► Prometheus :9001      (CPU, memory)
       └─ sensorsPoller.py ───────► Prometheus :9002      (temp, fans, current)
                                          │
                               Prometheus :9090 scrapes both
                                          │
                               Grafana :3005  (dashboards — both datasources)
```

Pollers run on the **host machine**. InfluxDB, Prometheus, Grafana run in **Docker**.

---

## Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Python 3.7+
- Network access to IxOS chassis REST API (:443)

---

## Quick Start

### One-Command Bootstrap (recommended for fresh clones)

After cloning, run:

```bash
./start.sh
```

This single script handles everything:
- Copies `.env.example` → `.env` if missing (edit credentials before rerunning if needed)
- Frees any processes blocking required ports
- Creates Docker containers if absent; restarts them if already present
- Waits for containers to be healthy
- Starts all three pollers in the background

**After it completes, configure your Grafana dashboard queries — that is the only remaining step.**

Logs are written to the repo root:
```bash
tail -f portInfoPoller.log      # port ownership / blocked status
tail -f perfMetricsPoller.log   # CPU / memory
tail -f sensorsPoller.log       # temperature / fans / current
```

---

### Manual Setup (alternative)

### 1. Clone

```bash
git clone https://github.com/yourusername/IxPortUtilizationPlotter.git
cd IxPortUtilizationPlotter
```

### 2. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env` — minimum required changes:

```bash
# ── Ports ──────────────────────────────────────────────────
INFLUXDB_PORT=8087
PROMETHEUS_PORT=9090
GRAFANA_PORT=3005

# ── InfluxDB ───────────────────────────────────────────────
INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_PASSWORD=Keysight12345!
INFLUXDB_ORG=keysight
INFLUXDB_BUCKET=portBlockedMetrics
INFLUXDB_TOKEN='your-super-secret-token-here'
INFLUXDB_RETENTION=0                          # 0 = infinite

# ── Grafana ────────────────────────────────────────────────
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin

# ── Pollers ────────────────────────────────────────────────
INFLUXDB_URL=http://localhost:8087
POLLING_INTERVAL=30
POLLING_INTERVAL_PERF_METRICS=30
POLLING_INTERVAL_SENSOR_METRICS=30

# ── Chassis (if not using credentials service) ─────────────
CHASSIS_LIST=[{"ip":"10.x.x.x","username":"admin","password":"admin"}]
```

> **Chassis credentials:** If you run IxiaInventoryExplorer, set `CREDENTIALS_URL` instead of `CHASSIS_LIST`. The poller tries the API first and falls back to `CHASSIS_LIST`.

### 3. Start Docker Stack

```bash
docker compose up -d
docker compose ps        # wait until all show "healthy"
```

This creates:
- InfluxDB with bucket `portBlockedMetrics` (auto-initialized from `.env`)
- Prometheus scraping host ports 9001 and 9002
- Grafana with InfluxDB + Prometheus datasources pre-provisioned

### 4. Start Pollers

```bash
chmod +x run_pollers.sh stop_pollers.sh
./run_pollers.sh
```

Verify data is flowing:

```bash
tail -f portInfoPoller.log      # should show "Written: chassis/card/port"
tail -f perfMetricsPoller.log   # should show CPU/MEM percentages
tail -f sensorsPoller.log       # should show sensor readings
```

### 5. Open Grafana

URL: **http://localhost:3005** — anonymous viewer access enabled by default (no login required for read-only dashboards). Admin login: `admin` / `admin`.

---

## Web Interfaces

| Service | URL | Auth |
|---------|-----|------|
| Grafana | http://localhost:3005 | Anonymous (Viewer) — no login needed |
| InfluxDB | http://localhost:8087 | admin / (your password) |
| Prometheus | http://localhost:9090 | none |

> Grafana is configured with `GF_SECURITY_ALLOW_EMBEDDING=true` and `GF_AUTH_ANONYMOUS_ENABLED=true` so dashboards render correctly inside iframes (e.g. IxiaL23LabManager shell).

---

## Grafana Dashboard Setup

### Dashboard Variable: `chassis`

In dashboard Settings → Variables → New variable:
- Type: **Query**
- Datasource: **InfluxDB-IxOS**
- Query:
```flux
import "influxdata/influxdb/schema"
schema.tagValues(bucket: "portBlockedMetrics", tag: "chassis")
```

### Panel: Blocked Port Count Over Time

```flux
from(bucket: "portBlockedMetrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "portUtilization")
  |> filter(fn: (r) => r.chassis == "${chassis}")
  |> filter(fn: (r) => r._field == "portStatus")
  |> map(fn: (r) => ({r with _value: if r._value == "Blocked" then 1 else 0}))
  |> aggregateWindow(every: v.windowPeriod, fn: sum, createEmpty: false)
```

### Panel: Currently Blocked Ports + Owner (Table)

```flux
from(bucket: "portBlockedMetrics")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "portUtilization")
  |> filter(fn: (r) => r.chassis == "${chassis}")
  |> filter(fn: (r) => r._field == "owner" or r._field == "portStatus")
  |> last()
  |> pivot(rowKey: ["chassis", "card", "port"], columnKey: ["_field"], valueColumn: "_value")
  |> filter(fn: (r) => r.portStatus == "Blocked")
  |> keep(columns: ["chassis", "card", "port", "owner", "_time"])
```

### Quick Sanity Check (Explore tab)

Paste in Grafana → Explore → InfluxDB to verify data is flowing:

```flux
from(bucket: "portBlockedMetrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "portUtilization")
  |> filter(fn: (r) => r._field == "portStatus")
  |> filter(fn: (r) => r._value == "Blocked")
  |> group(columns: ["chassis", "card", "port"])
  |> count()
```

---

## Management

```bash
# Pollers
./run_pollers.sh                  # start all three
./stop_pollers.sh                 # stop all

# Logs
tail -f portInfoPoller.log
tail -f perfMetricsPoller.log
tail -f sensorsPoller.log

# Docker
docker compose up -d              # start stack
docker compose down               # stop stack (keeps data)
docker compose down -v            # stop + wipe all data (fresh start)
docker compose ps                 # check health
docker compose logs -f influxdb   # service logs

# Debug config
python3 config.py                 # print current config + warnings
```

---

## Fresh Start / Reset

To wipe all data and reinitialize:

```bash
docker compose down -v   # destroys volumes
docker compose up -d     # reinitializes with current .env settings
```

InfluxDB auto-creates the bucket on first boot using `INFLUXDB_BUCKET` from `.env`.

---

## Port Status Classification

Each port is classified every poll cycle:

| Condition | portStatus |
|-----------|-----------|
| No owner | `Free` |
| Has owner + in blocked list | `Blocked` |
| Has owner + not blocked | `Utilized` |

Blocked list is fetched from `BLOCKED_PORTS_URL` once per cycle. If unreachable, all owned ports default to `Utilized`.

---

## InfluxDB Schema

```
Measurement : portUtilization
Bucket      : portBlockedMetrics

Tags   : chassis | card | port
Fields : portStatus | owner | linkState | transmitState | blocked
         totalPorts | ownedPorts | freePorts
```

---

## Further Reading

- [HowCodeWorks.md](HowCodeWorks.md) — detailed internals: data flow, config priority, API endpoints, Flux query patterns
- `config.py` — all configurable values with env var names
- `prometheus.yml` — Prometheus scrape config
