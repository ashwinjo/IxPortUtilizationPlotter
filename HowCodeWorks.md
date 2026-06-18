# How the Code Works

## Overview

Three Python pollers run on the host machine. They query IxOS chassis REST APIs in parallel and push metrics to two datastores. Grafana visualizes both.

---

## Data Flow

```
IxOS Chassis (HTTPS :443)
       │
       ├─ portInfoPoller.py ──────► InfluxDB :8087
       │   polls ports every 30s     bucket: portBlockedMetrics
       │   writes per-port metrics   measurement: portUtilization
       │
       ├─ perfMetricsPoller.py ───► Prometheus exporter :9001
       │   polls CPU/mem every 30s    /metrics endpoint
       │
       └─ sensorsPoller.py ───────► Prometheus exporter :9002
           polls temp/fans/current    /metrics endpoint
                                          │
                               Prometheus :9090 scrapes both
                                          │
                               Grafana :3005 ◄─── InfluxDB :8087
                               (queries both datasources)
```

---

## Port Classification Logic

`portInfoPoller.py` classifies each port into one of three states per poll cycle:

```
port has no owner?          → portStatus = "Free"
port owned + in blocked set → portStatus = "Blocked"
port owned + not blocked    → portStatus = "Utilized"
```

The blocked set is fetched once per poll cycle from `BLOCKED_PORTS_URL` (an external API that tracks ports locked in active IxNetwork sessions). If that API is unreachable, all owned ports fall back to `"Utilized"`.

All chassis are polled **simultaneously** via `ThreadPoolExecutor(max_workers=len(CHASSIS_LIST))`. Adding more chassis does not increase wall-clock poll time.

---

## InfluxDB Schema

```
Measurement: portUtilization

Tags (indexed, used for filtering/grouping):
  chassis       → chassis IP address
  card          → card number (string)
  port          → fully qualified port name or port number

Fields (stored values):
  portStatus    → "Free" | "Utilized" | "Blocked"
  owner         → username/session name (populated even when Blocked)
  linkState     → "UP" | "DOWN" | "NOTRANSCEIVER"
  transmitState → "active" | "idle"
  blocked       → boolean (true if in blocked set)
  totalPorts    → int
  ownedPorts    → int
  freePorts     → int
```

Tags are indexed by InfluxDB — filter on `chassis`, `card`, `port` for fast queries. `owner` is a field (not a tag) to avoid cardinality explosion; retrieve it via `pivot()` in Flux queries.

---

## Credentials & Config Priority

`config.py` resolves chassis list in this order per poll:

```
1. GET {CREDENTIALS_URL}/api/config/credentials   ← IxiaInventoryExplorer API
2. CHASSIS_LIST env var (JSON array)
3. Empty list → no polling
```

`get_chassis_list()` is called fresh every poll cycle — new chassis picked up without restart.

All other config reads `.env` first, falls back to hardcoded defaults:

| Variable | Controls |
|----------|---------|
| `INFLUXDB_BUCKET` | Which bucket to write to |
| `INFLUXDB_TOKEN` | Auth token for InfluxDB |
| `INFLUXDB_URL` | InfluxDB endpoint |
| `POLLING_INTERVAL` | portInfoPoller + sensorsPoller cadence (seconds) |
| `POLLING_INTERVAL_PERF_METRICS` | perfMetricsPoller cadence (seconds) |
| `BLOCKED_PORTS_URL` | API that returns currently blocked port list |

---

## Key Files

| File | Role |
|------|------|
| `config.py` | Single source of truth for all config |
| `portInfoPoller.py` | Polls port ownership/state → writes to InfluxDB |
| `perfMetricsPoller.py` | Polls CPU/memory → Prometheus Gauges on :9001 |
| `sensorsPoller.py` | Polls temp/current/fan → Prometheus Gauges on :9002 |
| `influxDBclient.py` | InfluxDB write/query/delete helpers |
| `RestApi/IxOSRestInterface.py` | HTTP client for IxOS REST API; handles auth |
| `run_pollers.sh` | Starts all three pollers in background with venv |
| `stop_pollers.sh` | Kills all poller processes |
| `docker-compose.yml` | InfluxDB + Prometheus + Grafana stack |
| `grafana/provisioning/` | Auto-provisions InfluxDB + Prometheus datasources |
| `prometheus.yml` | Scrape targets (host machine ports 9001, 9002) |

---

## IxOS REST API

Authentication: `POST /platform/api/v1/auth/session` → returns `apiKey`, stored as `x-api-key` header for subsequent requests.

Data endpoints (all under `/chassis/api/v2/ixos/`):

| Endpoint | Used by |
|----------|---------|
| `ports` | portInfoPoller |
| `cards` | portInfoPoller |
| `chassis` | portInfoPoller |
| `perfcounters` | perfMetricsPoller |
| `sensors` | sensorsPoller |

`IxRestSession` in `RestApi/IxOSRestInterface.py` auto-authenticates on `__init__` when username/password are provided.

---

## Grafana Queries (Flux)

**Blocked port count over time (time series panel):**
```flux
from(bucket: "portBlockedMetrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "portUtilization")
  |> filter(fn: (r) => r.chassis == "${chassis}")
  |> filter(fn: (r) => r._field == "portStatus")
  |> map(fn: (r) => ({r with _value: if r._value == "Blocked" then 1 else 0}))
  |> aggregateWindow(every: v.windowPeriod, fn: sum, createEmpty: false)
```

**Currently blocked ports with owner (table panel):**
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

**Quick sanity check (paste in Explore tab):**
```flux
from(bucket: "portBlockedMetrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "portUtilization")
  |> filter(fn: (r) => r._field == "portStatus")
  |> filter(fn: (r) => r._value == "Blocked")
  |> group(columns: ["chassis", "card", "port"])
  |> count()
```
