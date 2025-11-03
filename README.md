# IxOS Metrics Plotter

**Real-time monitoring and visualization of Ixia/Keysight IxOS chassis port utilization with parallel polling, time-series storage, and interactive dashboards.**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.7+-green?logo=python)](https://www.python.org/)
[![InfluxDB](https://img.shields.io/badge/InfluxDB-2.x-orange)](https://www.influxdata.com/)
[![Grafana](https://img.shields.io/badge/Grafana-9.x+-yellow?logo=grafana)](https://grafana.com/)

---

## 🎯 Overview

Monitor multiple IxOS chassis simultaneously with real-time visibility into:
- **Port Ownership** - Track which user/session owns each port
- **Link Status** - Monitor port connectivity (up/down)
- **Transmit State** - Track traffic state (active/idle)
- **Resource Utilization** - View total, owned, and free ports

**Key Benefits:**
- ⚡ **Parallel polling** - Monitor 10+ chassis in ~2 seconds
- 📊 **Time-series visualization** - Historical analysis with Grafana
- 🐳 **One-command deployment** - Docker Compose for quick setup
- 🔄 **Synchronized timestamps** - Aligned data across all chassis

---

## 🏗️ Solution Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        IxOS CHASSIS FLEET                           │
│   [Chassis 1] ─── [Chassis 2] ─── ... ─── [Chassis N]             │
│      :8443            :8443                    :8443                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST API (Parallel Polling)
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      HOST MACHINE                                   │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  IxOS Poller (Python)                                      │    │
│  │  • portInfoPoller.py  → Port metrics (InfluxDB)           │    │
│  │  • perfMetricsPoller.py → Performance metrics (Prometheus)│    │
│  │  • Parallel polling with ThreadPoolExecutor                │    │
│  └────────────────────┬───────────────────┬────────────────────┘    │
└───────────────────────┼───────────────────┼─────────────────────────┘
                        │                   │
        HTTP :8086      │                   │ HTTP :9001
                        │                   │
┌───────────────────────▼───────────────────▼─────────────────────────┐
│                      DOCKER COMPOSE STACK                           │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │   InfluxDB       │  │   Prometheus     │  │    Grafana      │  │
│  │   :8086          │  │   :9090          │  │    :3000        │  │
│  │                  │  │                  │  │                 │  │
│  │ • Port metrics   │  │ • Perf metrics   │  │ • Dashboards    │  │
│  │ • Time-series DB │  │ • System health  │  │ • Visualization │  │
│  │ • Infinite store │  │ • 15d retention  │  │ • Multi-source  │  │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘  │
│                                                                     │
│  📦 Persistent Volumes: influxdb-data, prometheus-data, grafana-data │
└─────────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. Python poller queries all chassis in parallel (2-3s for 10+ chassis)
2. Port metrics → InfluxDB | Performance metrics → Prometheus
3. Grafana visualizes both data sources with synchronized timestamps

---

## ✨ Features

- ⚡ **Parallel Polling** - ThreadPoolExecutor for simultaneous chassis queries
- 🔄 **Synchronized Timestamps** - Aligned data across all chassis
- 📊 **Dual Storage** - InfluxDB (port data) + Prometheus (system metrics)
- 🎨 **Interactive Dashboards** - State Timeline, Time Series, Gauges
- 🐳 **Docker Compose** - One-command infrastructure deployment
- 🛡️ **Health Monitoring** - Automatic service health checks
- 💾 **Persistent Storage** - Data survives container restarts
- 🔧 **Configurable** - Environment-based configuration

---

## 📋 Prerequisites

- **Docker** 20.10+ & **Docker Compose** 2.0+
- **Python** 3.7+ with pip
- Network access to IxOS chassis (REST API enabled)
- 2GB free disk space

---

## 🚀 Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/yourusername/IxPortUtilizationPlotter.git
cd IxPortUtilizationPlotter
cp env.example .env
```

### 2. Edit Configuration

**`.env` file (Docker services):**
```bash
INFLUXDB_TOKEN=your-super-secret-token-change-me
INFLUXDB_ORG=keysight
INFLUXDB_BUCKET=ixosChassisStatistics
```

**`config.py` file (IxOS Poller):**
```python
CHASSIS_LIST = [
    {"ip": "10.36.75.205", "username": "admin", "password": "admin"},
]
POLLING_INTERVAL = 10  # seconds
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "your-super-secret-token-change-me"  # Must match .env
```

### 3. Start Services

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start Docker infrastructure (InfluxDB, Prometheus, Grafana)
docker compose up -d

# Start pollers on host
chmod +x run_pollers.sh stop_pollers.sh
./run_pollers.sh
```

### 4. Access Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **InfluxDB** | http://localhost:8086 | admin / admin |
| **Prometheus** | http://localhost:9090 | No auth |

### 5. Create Grafana Dashboard

1. Login to Grafana → **Create** → **Dashboard**
2. Add **State Timeline** panel
3. Select **InfluxDB-IxOS** data source
4. Use this query:

```flux
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
  |> filter(fn: (r) => r["chassis"] == "10.36.75.205")
  |> filter(fn: (r) => r["_field"] == "owner")
```

5. **Value Mappings:** Free → Green | */* (owned) → Red

---

## 📊 Common Queries

### Port Utilization (Total, Owned, Free)

```flux
from(bucket: "ixosChassisStatistics")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
  |> filter(fn: (r) => r["chassis"] == "${ChassisIP}")
  |> filter(fn: (r) => r["_field"] == "totalPorts" or 
                       r["_field"] == "ownedPorts" or 
                       r["_field"] == "freePorts")
```

**Visualization:** Time Series (line chart) - Shows all three metrics

### Link State Monitoring

```flux
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_field"] == "linkState")
```

**Visualization:** State Timeline - Color-code linkUp (green) vs linkDown (red)

### Performance Metrics (Prometheus)

```promql
# CPU utilization
cpu_utilization{chassis="10.36.75.205"}

# Memory utilization
memory_utilization{chassis="10.36.75.205"}
```

**Visualization:** Gauge or Time Series

---

## 🔧 Management Commands

```bash
# View logs
docker compose logs -f                 # All services
docker compose logs -f influxdb        # Specific service
tail -f portInfoPoller.log             # Poller logs

# Control services
docker compose stop                    # Stop all
docker compose restart                 # Restart all
./stop_pollers.sh                      # Stop pollers

# Health checks
docker compose ps                      # Service status
curl http://localhost:8086/health      # InfluxDB health
curl http://localhost:9090/-/healthy   # Prometheus health
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[SOLUTION_DEPLOYMENT.md](documents/SOLUTION_DEPLOYMENT.md)** | Complete deployment guide with troubleshooting |
| **[ENVIRONMENT_VARIABLES.md](documents/ENVIRONMENT_VARIABLES.md)** | All environment variables reference |
| **config.py** | Chassis list and poller configuration |
| **prometheus.yml** | Prometheus scrape configuration |

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| **No data in Grafana** | Verify `INFLUXDB_TOKEN` matches in `.env` and `config.py` |
| **Connection timeout** | Check chassis is reachable: `ping <chassis_ip>` |
| **Port already in use** | Customize ports in `.env`: `INFLUXDB_PORT=8087` |
| **Poller not starting** | Check logs: `tail -f portInfoPoller.log` |
| **Stale data in timeline** | Add `elapsed()` filter to Flux query (see Common Queries) |

**Detailed troubleshooting:** See [SOLUTION_DEPLOYMENT.md](documents/SOLUTION_DEPLOYMENT.md)

---

## 📊 Data Schema

**Measurement:** `portUtilization`

| Type | Name | Description | Example |
|------|------|-------------|---------|
| **Tags** | `chassis` | Chassis IP | `10.36.75.205` |
| | `card` | Card number | `1` |
| | `port` | Port number | `5` |
| **Fields** | `owner` | Port owner | `Free` or `user/session` |
| | `linkState` | Link status | `linkUp`, `linkDown` |
| | `transmitState` | Traffic state | `active`, `idle` |
| | `totalPorts` | Total ports | `48` |
| | `ownedPorts` | Owned ports | `12` |
| | `freePorts` | Available ports | `36` |

---

## 🎨 Performance

**Parallel vs Sequential Polling:**

| Chassis Count | Sequential | Parallel | Improvement |
|---------------|------------|----------|-------------|
| 1 chassis | 2s | 2s | 0% |
| 5 chassis | 10s | 2-3s | 70-80% |
| 10 chassis | 20s | 2-3s | 85-90% |
| 20 chassis | 40s | 3-4s | 90-92% |

---

## 📁 Project Structure

```
IxPortUtilizationPlotter/
├── 🐳 Docker Infrastructure
│   ├── docker-compose.yml         # Service orchestration
│   ├── prometheus.yml             # Prometheus config
│   └── grafana/provisioning/      # Auto-configured data sources
│
├── 🐍 Python Pollers
│   ├── portInfoPoller.py          # Port metrics (InfluxDB)
│   ├── perfMetricsPoller.py       # Performance metrics (Prometheus)
│   ├── influxDBclient.py          # InfluxDB operations
│   ├── IxOSRestAPICaller.py       # IxOS REST API client
│   └── RestApi/                   # Low-level REST interface
│
├── ⚙️ Configuration
│   ├── .env                       # Docker environment vars
│   ├── config.py                  # Chassis list & settings
│   └── requirements.txt           # Python dependencies
│
├── 🚀 Management Scripts
│   ├── run_pollers.sh             # Start pollers
│   └── stop_pollers.sh            # Stop pollers
│
└── 📚 Documentation
    ├── README.md                  # This file
    ├── SOLUTION_DEPLOYMENT.md     # Detailed deployment guide
    └── ENVIRONMENT_VARIABLES.md   # Configuration reference
```

---

## 📸 Dashboard Examples

### Port Ownership State Timeline
![Port Ownership Timeline](images/image%20(4).png)

**Features:**
- 🟢 **Green** = Free ports (available)
- 🔴 **Red** = Owned ports (user/session)
- 🕐 **Synchronized timestamps** across all chassis
- 📊 **Real-time updates** with historical view

### Multi-Port Monitoring
![Multi-Port Dashboard](images/image%20(5).png)

**Visualization:** Multiple chassis monitored simultaneously with instant visibility into port transitions and resource utilization.

---

## 🤝 Contributing

Contributions welcome! Open an issue or submit a pull request.

---

## 📄 License

Open source project for Keysight/Ixia IxOS chassis monitoring.

---

**Built with ❤️ for network test automation teams**

📊 **Happy Monitoring!**
