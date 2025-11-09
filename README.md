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

**`.env` file (TO start Docker services):**
```bash

INFLUXDB_PORT=8086
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# InfluxDB Configuration
INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_PASSWORD=admin
INFLUXDB_ORG=keysight
INFLUXDB_BUCKET=ixosChassisStatistics
INFLUXDB_TOKEN='eegHpR9kkgxg5KG7rklj2zQI86-5z7yNETx0P0qQpSnw1owDxSL5IF-uQruOP-J8M_xmrhT3KWECh-QGbsdyYA=='
INFLUXDB_RETENTION=0  # 0 = infinite retention, or specify in seconds

# Grafana Configuration
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
INFLUXDB_TOKEN=<your-super-secret-token-change-me>
```

### 2.1 .Once you have these values set. Start the Containers:

```bash
# Start Docker infrastructure (InfluxDB, Prometheus, Grafana)
docker compose up -d
```


###  In .env file modify following polling intervals and chassis list **

```bash
# Polling interval in seconds - This is for my influxDB to select metrics push intevals
POLLING_INTERVAL=120
# Polling interval in seconds - This is for my prometheus to select metrics push intevals
POLLING_INTERVAL_PERF_METRICS=110
CHASSIS_LIST = [
    {"ip": "10.36.75.205", "username": "admin", "password": "admin"},
]

```

### 3. Start Python Poller to get data from Ixia Chassis

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start pollers on host
chmod +x run_pollers.sh stop_pollers.sh

./run_pollers.sh
```

### 4. Access Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **InfluxDB** | http://localhost:8086 | admin / < you set in .env file > |
| **Prometheus** | http://localhost:9090 | No auth |


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

## 🤝 Contributing

Contributions welcome! Open an issue or submit a pull request.

---

## 📄 License

Open source project for Keysight/Ixia IxOS chassis monitoring.

---

**Built with ❤️ for network test automation teams**

📊 **Happy Monitoring!**
