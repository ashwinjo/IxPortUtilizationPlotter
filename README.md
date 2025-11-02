# IxPortUtilizationPlotter

Open-source monitoring tool for visualizing Ixia/Keysight IxOS chassis port utilization and ownership in real-time using InfluxDB and Grafana dashboards.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [InfluxDB Data Schema](#influxdb-data-schema)
- [Grafana Setup](#grafana-setup)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)
- [Screenshots & Dashboard Examples](#screenshots--dashboard-examples)

---

## 🎯 Overview

This tool continuously monitors multiple Ixia/Keysight IxOS chassis (both Linux and Windows-based) and collects port-level statistics including:
- Port ownership information
- Link state (up/down)
- Transmit state (active/idle)
- Port utilization metrics (total, owned, free ports)

Data is stored in **InfluxDB** and visualized in **Grafana** for real-time monitoring and historical analysis.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    IxOS Chassis (10.36.75.205)                  │
│  ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐     │
│  │Port 1│Port 2│Port 3│Port 4│Port 5│Port 6│Port 7│Port 8│ ... │
│  └──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘     │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST API
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      portInfoPoller.py                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Parallel Thread Pool (ThreadPoolExecutor)              │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │   │
│  │  │Thread 1│  │Thread 2│  │Thread 3│  │Thread N│  ...   │   │
│  │  │Chassis1│  │Chassis2│  │Chassis3│  │ChassisN│        │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │         IxOSRestAPICaller.py                            │   │
│  │  - get_chassis_ports_information()                      │   │
│  │  - Processes REST API responses                         │   │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐   │
│  │         RestApi/IxOSRestInterface.py                    │   │
│  │  - IxRestSession (authentication & HTTP)                │   │
│  │  - get_ports(), get_chassis(), get_cards()              │   │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Write synchronized data
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      influxDBclient.py                          │
│  - write_data_to_influxdb()                                     │
│  - Batch writes all chassis data with synchronized timestamps   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      InfluxDB (Time Series DB)                  │
│  Bucket: ixosChassisStatistics                                  │
│  Measurement: portUtilization                                   │
│    Tags: chassis, card, port                                    │
│    Fields: owner, linkState, transmitState, totalPorts, etc.    │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Flux queries
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      Grafana Dashboard                          │
│  - State Timeline panels for port ownership visualization       │
│  - Real-time monitoring with auto-refresh                       │
│  - Historical trend analysis                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Parallel Polling** - All chassis are polled simultaneously using ThreadPoolExecutor
2. **REST API Calls** - Each thread makes REST API calls to its assigned chassis
3. **Data Collection** - Port information is collected and normalized
4. **Synchronized Write** - All data is written to InfluxDB in a single batch with near-identical timestamps
5. **Visualization** - Grafana queries InfluxDB and displays real-time state timelines

---

## ✨ Features

### Core Features
- ✅ **Parallel chassis polling** - Poll 10+ chassis simultaneously with synchronized timestamps
- ✅ **Multi-chassis support** - Monitor unlimited number of chassis
- ✅ **Cross-platform chassis support** - Works with Linux and Windows-based IxOS chassis
- ✅ **Real-time monitoring** - Configurable polling intervals (default: 10 seconds)
- ✅ **Port ownership tracking** - Track which user/session owns each port
- ✅ **Link and transmit state monitoring** - Monitor port link status and traffic state
- ✅ **Automatic error handling** - Graceful handling of chassis connection failures
- ✅ **Time-series data storage** - Historical data retention in InfluxDB

### Advanced Features
- 🔄 **Synchronized timestamps** - All chassis data points share the same timestamp for aligned visualization
- 📊 **Grafana State Timeline** - Visual representation of port states over time
- 🎨 **Color-coded states** - Free (green) vs. Owned (red) ports
- 🔍 **Detailed logging** - Per-chassis polling status and performance metrics
- ⚡ **High performance** - 10 chassis polled in ~2-3 seconds vs. 20+ seconds sequential

---

## 📦 Prerequisites

### Required Software
- **Python 3.7+**
- **InfluxDB 2.x** - Time-series database
- **Grafana 9.x+** - Visualization platform
- **Ixia IxOS Chassis** - With REST API enabled

### Python Packages
```
influxdb-client
requests
concurrent.futures (built-in Python 3.2+)
```

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/IxPortUtilizationPlotter.git
cd IxPortUtilizationPlotter
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install influxdb-client requests
```

### 3. Install InfluxDB

**macOS (Homebrew):**
```bash
brew install influxdb
brew services start influxdb
```

**Linux:**
```bash
wget https://dl.influxdata.com/influxdb/releases/influxdb2-2.7.1-linux-amd64.tar.gz
tar xvzf influxdb2-2.7.1-linux-amd64.tar.gz
sudo cp influxdb2-2.7.1-linux-amd64/influxd /usr/local/bin/
influxd
```

**Access InfluxDB UI:** http://localhost:8086

### 4. Install Grafana

**macOS (Homebrew):**
```bash
brew install grafana
brew services start grafana
```

**Linux:**
```bash
sudo apt-get install -y adduser libfontconfig1
wget https://dl.grafana.com/oss/release/grafana_9.5.2_amd64.deb
sudo dpkg -i grafana_9.5.2_amd64.deb
sudo systemctl start grafana-server
```

**Access Grafana UI:** http://localhost:3000 (default: admin/admin)

---

## ⚙️ Configuration

### 1. InfluxDB Setup

1. Open InfluxDB UI: http://localhost:8086
2. Create initial user and organization:
   - **Username:** admin
   - **Password:** [your-password]
   - **Organization:** keysight
   - **Bucket:** ixosChassisStatistics
3. Generate an API token:
   - Go to **Data** → **API Tokens** → **Generate API Token**
   - Copy the token for use in config.py

### 2. Configure Application

Edit `config.py`:

```python
# List of chassis to monitor
CHASSIS_LIST = [
    {
        "ip": "10.36.75.205",
        "username": "admin",
        "password": "admin",
    },
    {
        "ip": "10.36.75.206",
        "username": "admin",
        "password": "admin",
    },
    # Add more chassis as needed
]

# Polling interval in seconds
POLLING_INTERVAL = 10

# InfluxDB connection details
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "your-influxdb-token-here"
```

### 3. Configure Grafana Data Source

1. Open Grafana: http://localhost:3000
2. Go to **Configuration** → **Data Sources** → **Add data source**
3. Select **InfluxDB**
4. Configure:
   - **Query Language:** Flux
   - **URL:** http://localhost:8086
   - **Organization:** keysight
   - **Token:** [Your InfluxDB API token]
   - **Default Bucket:** ixosChassisStatistics
5. Click **Save & Test**

---

## 🎮 Usage

### Start Monitoring

Run the port information poller:

```bash
python portInfoPoller.py
```

**Expected Output:**
```
Starting parallel chassis poller for 2 chassis...
Polling interval: 10 seconds
Chassis IPs: ['10.36.75.205', '10.36.75.206']
--------------------------------------------------------------------------------

[Poll #1] Starting parallel poll at 06:00:00
✓ Successfully polled 10.36.75.205 - 48 ports
✓ Successfully polled 10.36.75.206 - 48 ports
[Poll #1] Collected 96 total ports in 2.34s
✓ Written: 10.36.75.205/1/1 -> Owner=Free, LinkState=linkDown, TransmitState=idle
✓ Written: 10.36.75.205/1/2 -> Owner=ChassisLab/admin, LinkState=linkUp, TransmitState=active
...
[Poll #1] Written to InfluxDB
--------------------------------------------------------------------------------
```

### Run as Background Service

**Using nohup:**
```bash
nohup python portInfoPoller.py > poller.log 2>&1 &
```

**Using systemd (Linux):**
Create `/etc/systemd/system/ixos-poller.service`:
```ini
[Unit]
Description=IxOS Port Utilization Poller
After=network.target influxdb.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/IxPortUtilizationPlotter
ExecStart=/usr/bin/python3 portInfoPoller.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ixos-poller
sudo systemctl start ixos-poller
sudo systemctl status ixos-poller
```

---

## 📊 InfluxDB Data Schema

### Measurement: `portUtilization`

**Tags** (indexed for fast queries):
- `chassis` - Chassis IP address (e.g., "10.36.75.205")
- `card` - Card number (e.g., "1")
- `port` - Port number (e.g., "5")

**Fields** (actual data values):
- `owner` (string) - Port owner (e.g., "Free", "ChassisLab/admin")
- `linkState` (string) - Link status (e.g., "linkUp", "linkDown")
- `transmitState` (string) - Transmit status (e.g., "active", "idle")
- `cardNumber` (string) - Card number (duplicate for convenience)
- `portNumber` (string) - Port number (duplicate for convenience)
- `totalPorts` (integer) - Total ports on chassis
- `ownedPorts` (integer) - Number of owned/reserved ports
- `freePorts` (integer) - Number of available ports

### Example Data Point
```json
{
  "_measurement": "portUtilization",
  "_time": "2025-11-02T06:42:30Z",
  "chassis": "10.36.75.205",
  "card": "1",
  "port": "5",
  "owner": "ChassisLab/admin",
  "linkState": "linkUp",
  "transmitState": "active",
  "totalPorts": 48,
  "ownedPorts": 12,
  "freePorts": 36
}
```

---

## 📈 Grafana Setup

### Create a State Timeline Panel

1. **Create New Dashboard**
   - Go to **Dashboards** → **New Dashboard** → **Add visualization**
   - Select your InfluxDB data source

2. **Configure Query**

Use this Flux query for port ownership visualization:

```flux
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
  |> filter(fn: (r) => r["chassis"] == "10.36.75.205")  // Change to your chassis IP
  |> filter(fn: (r) => r["_field"] == "owner")
  |> elapsed(unit: 1s)
  |> filter(fn: (r) => not exists r.elapsed or r.elapsed <= 30)  // Only show recent data
  |> drop(columns: ["elapsed"])
```

**Important:** The `elapsed()` filter prevents Grafana from stretching old data when polling stops.

3. **Configure Visualization**
   - **Panel type:** State Timeline
   - **Time range:** Last 15 minutes (or adjust as needed)
   - **Refresh:** 5s or 10s
   - **Legend:** Show legend

4. **Configure Value Mappings**
   - Go to **Value mappings**
   - Add mapping: `Free` → Color: Green
   - Add mapping: Match pattern `*/*` (for usernames) → Color: Red

5. **Panel Options**
   - **Title:** "Port Ownership - {chassis_ip}"
   - **Description:** "Real-time port ownership tracking"

### Multi-Chassis Dashboard

Create multiple panels, one per chassis:

```flux
// Panel 1: Chassis 10.36.75.205
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
  |> filter(fn: (r) => r["chassis"] == "10.36.75.205")
  |> filter(fn: (r) => r["_field"] == "owner")
  |> elapsed(unit: 1s)
  |> filter(fn: (r) => not exists r.elapsed or r.elapsed <= 30)
  |> drop(columns: ["elapsed"])

// Panel 2: Chassis 10.36.75.206
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
  |> filter(fn: (r) => r["chassis"] == "10.36.75.206")
  |> filter(fn: (r) => r["_field"] == "owner")
  |> elapsed(unit: 1s)
  |> filter(fn: (r) => not exists r.elapsed or r.elapsed <= 30)
  |> drop(columns: ["elapsed"])
```

### Available Queries

**Query all fields for analysis:**
```flux
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
  |> filter(fn: (r) => r["chassis"] == "10.36.75.205")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
```

**Query link state:**
```flux
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
  |> filter(fn: (r) => r["_field"] == "linkState")
```

**Query transmit state:**
```flux
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
  |> filter(fn: (r) => r["_field"] == "transmitState")
```

**Query port utilization stats:**
```flux
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
  |> filter(fn: (r) => r["_field"] == "freePorts" or r["_field"] == "ownedPorts")
  |> aggregateWindow(every: 1m, fn: last)
```

---

## 🔧 Troubleshooting

### Issue: Query Returns "No Data"

**Problem:** Field name mismatch in Flux query

**Solution:** Verify you're using correct field names:
- ✅ Correct: `r["_field"] == "owner"`
- ❌ Wrong: `r["_field"] == "portOwner"`

Available fields: `owner`, `linkState`, `transmitState`, `cardNumber`, `portNumber`, `totalPorts`, `ownedPorts`, `freePorts`

### Issue: State Timeline Shows Data Beyond Polling Stop Time

**Problem:** Grafana extends the last known state to the end of the query range

**Solution:** Add elapsed filter to your query:
```flux
|> elapsed(unit: 1s)
|> filter(fn: (r) => not exists r.elapsed or r.elapsed <= 30)
|> drop(columns: ["elapsed"])
```

This prevents showing stale data when polling stops.

### Issue: Staggered Timestamps Between Chassis

**Problem:** Sequential polling causes time differences

**Solution:** The code now uses parallel polling with `ThreadPoolExecutor`. All chassis are polled simultaneously, resulting in synchronized timestamps.

### Issue: Connection Timeout

**Symptoms:**
```
✗ Error polling 10.36.75.205: Connection timeout
```

**Solutions:**
1. Verify chassis is reachable: `ping 10.36.75.205`
2. Check REST API is enabled on chassis
3. Verify firewall rules allow HTTP/HTTPS
4. Confirm username/password in `config.py`

### Issue: InfluxDB Write Errors

**Symptoms:**
```
✗ Error writing data for 10.36.75.205/1/1: unauthorized access
```

**Solutions:**
1. Verify InfluxDB token in `config.py`
2. Check bucket name matches: `ixosChassisStatistics`
3. Verify InfluxDB is running: `curl http://localhost:8086/health`
4. Check token permissions include write access to bucket

### Issue: High Memory Usage

**Solution:** Adjust polling interval or reduce number of chassis polled simultaneously.

---

## 🔍 Technical Details

### Parallel Polling Implementation

The tool uses Python's `concurrent.futures.ThreadPoolExecutor` for parallel I/O operations:

```python
with ThreadPoolExecutor(max_workers=len(config.CHASSIS_LIST)) as executor:
    future_to_chassis = {
        executor.submit(poll_single_chassis, chassis): chassis 
        for chassis in config.CHASSIS_LIST
    }
    
    for future in as_completed(future_to_chassis):
        port_details = future.result()
        all_port_details.extend(port_details)
```

**Benefits:**
- All chassis polled simultaneously (parallel I/O)
- Results collected as they complete
- Error in one chassis doesn't block others
- Synchronized timestamps across all chassis

### Performance Metrics

| Metric | Sequential | Parallel | Improvement |
|--------|-----------|----------|-------------|
| 1 chassis | 2s | 2s | 0% |
| 5 chassis | 10s | 2-3s | 70-80% |
| 10 chassis | 20s | 2-3s | 85-90% |
| 20 chassis | 40s | 3-4s | 90-92% |

### REST API Endpoints Used

The tool interfaces with IxOS REST API endpoints:
- `/api/v1/auth/session` - Authentication
- `/api/v1/sessions/{id}/ixnetwork/ports` - Port information
- `/api/v1/sessions/{id}/ixnetwork/chassis` - Chassis information
- `/api/v1/sessions/{id}/ixnetwork/cards` - Card information

### Data Types

**InfluxDB Field Type Mapping:**
- `owner`, `linkState`, `transmitState` → String
- `cardNumber`, `portNumber` → String (for flexibility)
- `totalPorts`, `ownedPorts`, `freePorts` → Integer

**Timestamp:** UTC timezone, synchronized across all chassis in batch write

### Error Handling

1. **Connection Errors** - Logged and placeholder data inserted
2. **Authentication Errors** - Chassis skipped with error message
3. **API Errors** - Caught and logged, polling continues
4. **InfluxDB Errors** - Logged per data point with context

### Logging

Console output includes:
- ✓ Success indicators (green checkmarks)
- ✗ Error indicators (red X marks)
- ⚠ Warning indicators
- Poll timing and performance metrics
- Per-chassis status updates

---

## 📝 File Structure

```
IxPortUtilizationPlotter/
├── README.md                       # This file
├── requirements.txt                # Python dependencies
├── config.py                       # Configuration (chassis list, InfluxDB)
├── portInfoPoller.py              # Main polling script (parallel execution)
├── influxDBclient.py              # InfluxDB write/read operations
├── IxOSRestAPICaller.py           # IxOS REST API abstraction layer
├── RestApi/
│   ├── __init__.py
│   ├── IxOSRestInterface.py       # Low-level REST API interface
│   └── requirements.txt           # RestApi module dependencies
└── appa.json                      # Application metadata
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License

This project is open source. Please check the repository for license details.

---

## 🙏 Acknowledgments

- Built for Keysight/Ixia IxOS chassis monitoring
- Uses InfluxDB for time-series data storage
- Visualized with Grafana dashboards
- IxOS REST API documentation

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact the maintainers

---

## 📸 Screenshots & Dashboard Examples

### Grafana State Timeline Visualization

Below are examples of the real-time port ownership visualization in Grafana:

#### Port Ownership State Timeline
![Port Ownership Timeline](images/image%20(4).png)

*State Timeline showing port ownership over time. Green indicates "Free" ports, while red/colored sections show ports owned by specific users/sessions. Each row represents a chassis-card-port combination.*

#### Multi-Port Monitoring Dashboard
![Multi-Port Dashboard](images/image%20(5).png)

*Complete dashboard view showing multiple ports being monitored simultaneously. The timeline clearly shows when ports transition between free and owned states, providing instant visibility into resource utilization.*

### Key Visual Elements

- **Green Sections** - Ports in "Free" state (available for use)
- **Red/Colored Sections** - Ports owned by users (showing username/session)
- **Timeline** - X-axis shows time progression with synchronized timestamps
- **Port Labels** - Y-axis shows chassis-card-port identifiers (e.g., `10.36.75.205-1-1`)
- **Real-time Updates** - Dashboard auto-refreshes to show current state
- **Historical View** - Scroll back to see port usage patterns over time

### Dashboard Features Demonstrated

1. **Synchronized Timestamps** - All chassis data appears at the same time point
2. **State Duration** - Visual representation of how long ports remain in each state
3. **Multi-Chassis View** - Monitor multiple chassis simultaneously
4. **Instant Visibility** - Quickly identify which ports are in use and by whom
5. **Gap Handling** - Empty spaces indicate periods when polling stopped (no stale data stretched)

---

## 🔄 Changelog

### Version 2.0 (Latest)
- ✨ Added parallel chassis polling for synchronized timestamps
- 🚀 Performance improvement: 85-90% faster for multiple chassis
- 🔧 Fixed field name mismatches in queries
- 📊 Added elapsed() filter to prevent stale data visualization
- 📝 Comprehensive documentation and troubleshooting guide

### Version 1.0
- Initial release
- Sequential chassis polling
- Basic InfluxDB integration
- Grafana visualization support

---

**Happy Monitoring! 📊🚀**
