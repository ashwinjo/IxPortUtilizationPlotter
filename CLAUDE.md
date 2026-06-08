# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Real-time monitoring solution for Ixia/Keysight IxOS chassis. Python pollers query chassis REST APIs in parallel and push metrics to InfluxDB (port data) and Prometheus (CPU/memory/sensors). Grafana visualizes both.

## Setup

```bash
cp .env.example .env
# Edit .env: set INFLUXDB_TOKEN, CHASSIS_LIST, and port/credential values

# Start Docker stack (InfluxDB + Prometheus + Grafana)
docker compose up -d

# Start Python pollers (creates venv 'ixmon', installs deps, runs all three pollers)
chmod +x run_pollers.sh stop_pollers.sh
./run_pollers.sh
```

## Commands

```bash
# Pollers
./run_pollers.sh                        # Start all three pollers (background, with venv)
./stop_pollers.sh                       # Stop all pollers

# Logs
tail -f portInfoPoller.log
tail -f perfMetricsPoller.log
tail -f sensorsPoller.log

# Docker
docker compose up -d
docker compose logs -f
docker compose ps
docker compose stop

# Debug config
python3 config.py                       # Print current config + warnings

# Manually clear InfluxDB measurement (destructive)
python3 influxDBclient.py
```

## Architecture

### Data Flow

```
IxOS Chassis (HTTPS :443)
    |
    +--> portInfoPoller.py  ---> InfluxDB :8086  (measurement: portUtilization)
    +--> perfMetricsPoller.py -> Prometheus :9001/metrics
    +--> sensorsPoller.py -----> Prometheus :9002/metrics
                                     |
                              Prometheus scrapes :9090
                                     |
                              Grafana :3000 (both datasources)
```

### Key Files

| File | Role |
|------|------|
| `config.py` | Single source of truth for all config; reads `.env` first, falls back to hardcoded defaults |
| `RestApi/IxOSRestInterface.py` | HTTP client for IxOS REST API; authenticates via `/platform/api/v1/auth/session`, queries `/chassis/api/v2/ixos/*` |
| `portInfoPoller.py` | Polls port ownership/link/transmit state → writes to InfluxDB |
| `perfMetricsPoller.py` | Polls CPU/memory → exposes as Prometheus Gauges on port 9001 |
| `sensorsPoller.py` | Polls temperature/current/fan sensors → exposes as Prometheus Gauges on port 9002 |
| `influxDBclient.py` | InfluxDB write/query/delete helpers used by portInfoPoller |
| `prometheus.yml` | Prometheus scrape config (points to host machine ports 9001, 9002) |
| `grafana/provisioning/` | Auto-provisioned datasource configs for InfluxDB and Prometheus |

### Parallel Polling Pattern

All three pollers use the same pattern: `ThreadPoolExecutor(max_workers=len(CHASSIS_LIST))` with `as_completed()`. Each chassis is polled simultaneously — adding chassis does not increase wall-clock poll time.

### IxOS REST API

- Auth: POST to `/platform/api/v1/auth/session` returns `apiKey` (stored as `x-api-key` header)
- Data: GET from `/chassis/api/v2/ixos/{ports,cards,chassis,sensors,perfcounters}`
- `IxRestSession` auto-authenticates in `__init__` when username/password are provided

## Configuration

All configuration flows through `config.py` which reads `.env`. Key variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `CHASSIS_LIST` | JSON array of `{ip, username, password}` objects | hardcoded in config.py |
| `POLLING_INTERVAL` | portInfoPoller + sensorsPoller interval (seconds) | 10 |
| `POLLING_INTERVAL_PERF_METRICS` | perfMetricsPoller interval (seconds) | 60 |
| `INFLUXDB_URL` | InfluxDB endpoint for poller | `http://localhost:8086` |
| `INFLUXDB_TOKEN` | Auth token (must match Docker init token) | hardcoded fallback |
| `INFLUXDB_ORG` | InfluxDB org | `keysight` |
| `INFLUXDB_BUCKET` | InfluxDB bucket | `ixosChassisStatistics` |
| `INFLUXDB_PORT` | Docker-exposed InfluxDB port | 8086 |

`CHASSIS_LIST` in `.env` must be valid JSON (e.g., `[{"ip":"10.0.0.1","username":"admin","password":"admin"}]`). Env var takes precedence over hardcoded list.

## InfluxDB Schema

Measurement: `portUtilization`
- Tags: `chassis` (IP), `card` (card number), `port` (fullyQualifiedPortName or portNumber)
- Fields: `owner`, `linkState`, `transmitState` (string: "active"/"idle"), `totalPorts`, `ownedPorts`, `freePorts` (int)

## Requirements

Two separate `requirements.txt` files — both are installed by `run_pollers.sh`:
- `requirements.txt` (root): `influxdb-client`, `prometheus-client`, `python-dotenv`, `requests`
- `RestApi/requirements.txt`: `requests`, `flask`, `pandas`
