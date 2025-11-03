# Environment Variables Reference

Complete list of all environment variables used in the IxOS Port Utilization Plotter.

## Overview

This project uses environment variables for configuration flexibility. Variables can be set in:
1. `.env` file (recommended)
2. Shell environment (`export VAR=value`)
3. Inline when running commands (`VAR=value command`)

## Variable Categories

### 🐳 Docker Service Configuration

These variables are used by `docker-compose.yml` to configure the containerized services.

| Variable | Used By | Default | Description |
|----------|---------|---------|-------------|
| `INFLUXDB_PORT` | docker-compose.yml | `8086` | Host port for InfluxDB service |
| `PROMETHEUS_PORT` | docker-compose.yml | `9090` | Host port for Prometheus service |
| `GRAFANA_PORT` | docker-compose.yml | `3000` | Host port for Grafana service |
| `INFLUXDB_ADMIN_USER` | docker-compose.yml | `admin` | InfluxDB admin username |
| `INFLUXDB_ADMIN_PASSWORD` | docker-compose.yml | `admin` | InfluxDB admin password |
| `INFLUXDB_ORG` | docker-compose.yml | `keysight` | InfluxDB organization name |
| `INFLUXDB_BUCKET` | docker-compose.yml | `ixosChassisStatistics` | InfluxDB bucket name |
| `INFLUXDB_TOKEN` | docker-compose.yml | `your-super-secret-token-change-me` | InfluxDB API token |
| `INFLUXDB_RETENTION` | docker-compose.yml | `0` | Data retention (0=infinite, or seconds) |
| `GRAFANA_ADMIN_USER` | docker-compose.yml | `admin` | Grafana admin username |
| `GRAFANA_ADMIN_PASSWORD` | docker-compose.yml | `admin` | Grafana admin password |

### 🐍 IxOS Poller Configuration

These variables are read by `config.py` for the host-based Python poller.

| Variable | Used By | Default | Description |
|----------|---------|---------|-------------|
| `CHASSIS_LIST` | config.py | `[]` | JSON array of chassis to monitor |
| `POLLING_INTERVAL` | config.py | `10` | Polling interval in seconds for Influx DB |
| `POLLING_INTERVAL_PERF_METRICS` | config.py | `10` | Polling interval in seconds for Prometheus |
| `INFLUXDB_URL` | config.py | `http://localhost:8086` | InfluxDB connection URL |
| `INFLUXDB_TOKEN` | config.py | (hardcoded fallback) | InfluxDB API token (must match Docker) |
| `INFLUXDB_ORG` | config.py | `keysight` | InfluxDB organization (must match Docker) |
| `INFLUXDB_BUCKET` | config.py | `ixosChassisStatistics` | InfluxDB bucket (must match Docker) |

## Shared Variables

Some variables are used by **both** Docker services and the IxOS poller:

| Variable | Docker Use | Poller Use | Must Match? |
|----------|-----------|------------|-------------|
| `INFLUXDB_TOKEN` | Initialize InfluxDB | Authenticate writes | ✅ **YES** |
| `INFLUXDB_ORG` | Create organization | Specify org in queries | ✅ **YES** |
| `INFLUXDB_BUCKET` | Create bucket | Specify bucket for writes | ✅ **YES** |

**Important:** These three variables must have the same values in both contexts!

## Configuration Examples

### Example 1: Basic Setup (Default Ports)

```bash
# .env file

# Docker Services
INFLUXDB_PORT=8086
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
INFLUXDB_TOKEN=my-secure-token-12345
INFLUXDB_ORG=keysight
INFLUXDB_BUCKET=ixosChassisStatistics

# Grafana
GRAFANA_ADMIN_PASSWORD=admin

# IxOS Poller
INFLUXDB_URL=http://localhost:8086
POLLING_INTERVAL=10
```

Then configure chassis in `config.py`:
```python
CHASSIS_LIST = [
    {"ip": "10.36.75.205", "username": "admin", "password": "admin"},
]
```

### Example 2: Custom Ports

```bash
# .env file

# Docker Services - Custom ports
INFLUXDB_PORT=8087
PROMETHEUS_PORT=9091
GRAFANA_PORT=3001
INFLUXDB_TOKEN=my-secure-token-12345

# IxOS Poller - Must match custom InfluxDB port
INFLUXDB_URL=http://localhost:8087
POLLING_INTERVAL=10
```

### Example 3: Using Environment Variables for Chassis

```bash
# .env file

# All configuration via environment variables
INFLUXDB_PORT=8086
INFLUXDB_TOKEN=my-secure-token-12345
INFLUXDB_URL=http://localhost:8086
POLLING_INTERVAL=15

# Configure chassis via environment
CHASSIS_LIST=[{"ip":"10.36.75.205","username":"admin","password":"admin"},{"ip":"10.36.75.206","username":"admin","password":"admin"}]
```

### Example 4: Remote InfluxDB

```bash
# .env file

# Docker Services run on remote server (10.0.1.100)
INFLUXDB_PORT=8086
INFLUXDB_TOKEN=my-secure-token-12345

# IxOS Poller connects to remote InfluxDB
INFLUXDB_URL=http://10.0.1.100:8086
```

## Configuration Precedence

Variables are resolved in this order (highest priority first):

1. **Environment variables** set in shell
2. **`.env` file** in project root
3. **Default values** in code


## Summary Table

| Variable | Docker | Poller | Default | Required | Description |
|----------|--------|--------|---------|----------|-------------|
| INFLUXDB_PORT | ✅ | ❌ | 8086 | ❌ | InfluxDB host port |
| PROMETHEUS_PORT | ✅ | ❌ | 9090 | ❌ | Prometheus host port |
| GRAFANA_PORT | ✅ | ❌ | 3000 | ❌ | Grafana host port |
| INFLUXDB_TOKEN | ✅ | ✅ | (must set) | ✅ | InfluxDB API token |
| INFLUXDB_ORG | ✅ | ✅ | keysight | ❌ | InfluxDB organization |
| INFLUXDB_BUCKET | ✅ | ✅ | ixosChassisStatistics | ❌ | InfluxDB bucket |
| INFLUXDB_URL | ❌ | ✅ | http://localhost:8086 | ❌ | Poller connection URL |
| POLLING_INTERVAL | ❌ | ✅ | 10 | ❌ | Seconds between polls |
| CHASSIS_LIST | ❌ | ✅ | [] | ✅* | Chassis to monitor |
| GRAFANA_ADMIN_PASSWORD | ✅ | ❌ | admin | ❌ | Grafana password |

*Required in either `.env` or `config.py`

---

**For complete setup instructions, see [README.md](README.md) and [SOLUTION_DEPLOYMENT.md)](documents/SOLUTION_DEPLOYMENT.md)**

