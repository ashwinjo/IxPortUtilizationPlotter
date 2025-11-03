# Docker Deployment Guide

Complete guide for deploying IxOS Port Utilization Plotter using Docker Compose.

## 📋 Prerequisites

- **Docker** 20.10+ installed
- **Docker Compose** 2.0+ installed
- Network access to your IxOS chassis
- At least 2GB free disk space

## 🚀 Quick Start

### 1. Clone or Download the Repository

```bash
cd /path/to/IxPortUtilizationPlotter
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp env.example .env
```

Edit `.env` file:

```bash
nano .env  # or use your preferred editor
```

**Important configurations in `.env`:**

```bash
# Change this to a secure token
INFLUXDB_TOKEN=your-super-secret-token-change-me

# Optional: Customize ports if defaults conflict
INFLUXDB_PORT=8086
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

**Configure IxOS Poller in `config.py`:**

```python
# Add your chassis
CHASSIS_LIST = [
    {
        "ip": "10.36.75.205",
        "username": "admin",
        "password": "admin",
    },
]

# Adjust polling interval
POLLING_INTERVAL = 10  # seconds

# InfluxDB connection (must match .env)
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "your-super-secret-token-change-me"
```

### 3. Start Docker Services

```bash
./start.sh
```

Or manually:

```bash
docker compose up -d
```

### 4. Run the IxOS Poller

The poller runs on your **host machine** (not in Docker):

```bash
# Run in foreground
python3 portInfoPoller.py

# Or run in background
nohup python3 portInfoPoller.py > poller.log 2>&1 &
```

### 5. Access the Services

- **Grafana:** http://localhost:3000 (admin/admin)
- **InfluxDB:** http://localhost:8086 (admin/admin)
- **Prometheus:** http://localhost:9090 (no authentication)

### 6. Setup Grafana Dashboard

1. Login to Grafana (http://localhost:3000)
2. InfluxDB data source is **auto-configured** as `InfluxDB-IxOS`
3. Create a new dashboard
4. Add a **State Timeline** panel
5. Use this query:

```flux
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
  |> filter(fn: (r) => r["chassis"] == "10.36.75.205")  // Your chassis IP
  |> filter(fn: (r) => r["_field"] == "owner")
  |> elapsed(unit: 1s)
  |> filter(fn: (r) => not exists r.elapsed or r.elapsed <= 30)
  |> drop(columns: ["elapsed"])
```

## 📦 What Gets Deployed

### Services

1. **InfluxDB 2.x** (port 8086)
   - Time-series database for IxOS chassis port metrics
   - Auto-initialized with org and bucket
   - Infinite data retention

2. **Prometheus** (port 9090)
   - Metrics collection and monitoring system
   - Configured to scrape Prometheus, InfluxDB, and Grafana metrics
   - 15-day retention by default

3. **Grafana** (port 3000)
   - Visualization platform
   - Auto-configured with both InfluxDB and Prometheus data sources
   - Persistent dashboards and settings

4. **IxOS Poller** (runs on host machine)
   - Python application
   - Polls chassis in parallel
   - Writes to InfluxDB

### Volumes (Persistent Data)

- `influxdb2-data` - InfluxDB data
- `influxdb2-config` - InfluxDB configuration
- `prometheus-data` - Prometheus metrics and TSDB
- `grafana-data` - Grafana dashboards and settings

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| **Service Ports** | | |
| `INFLUXDB_PORT` | InfluxDB host port | `8086` |
| `PROMETHEUS_PORT` | Prometheus host port | `9090` |
| `GRAFANA_PORT` | Grafana host port | `3000` |
| **InfluxDB Configuration** | | |
| `INFLUXDB_TOKEN` | InfluxDB API token | `your-super-secret-token-change-me` |
| `INFLUXDB_ORG` | Organization name | `keysight` |
| `INFLUXDB_BUCKET` | Bucket name | `ixosChassisStatistics` |
| `INFLUXDB_RETENTION` | Data retention (0=infinite) | `0` |
| **Grafana Configuration** | | |
| `GRAFANA_ADMIN_USER` | Grafana username | `admin` |
| `GRAFANA_ADMIN_PASSWORD` | Grafana password | `admin` |

### Customizing Service Ports

If default ports conflict with existing services on your host:

```bash
# In .env file
INFLUXDB_PORT=8087      # Instead of 8086
PROMETHEUS_PORT=9091    # Instead of 9090
GRAFANA_PORT=3001       # Instead of 3000
```

**Important:** If you change `INFLUXDB_PORT`, also update `config.py`:
```python
INFLUXDB_URL = "http://localhost:8087"  # Match your configured port
```

### Prometheus Configuration

Prometheus is configured via `prometheus.yml`. The default configuration includes:

```yaml
global:
  scrape_interval: 120s  # How often to scrape metrics

scrape_configs:
  - job_name: prometheus-app
    static_configs:
      - targets:
          - host.docker.internal:9001  # Your application metrics
```

To add more scrape targets, edit `prometheus.yml` and restart:
```bash
docker compose restart prometheus
```

## 📊 Management Commands

### View Logs

All services:
```bash
docker compose logs -f
```

Specific service:
```bash
docker compose logs -f influxdb
docker compose logs -f prometheus
docker compose logs -f grafana
```

### Check Status

```bash
docker compose ps
```

### Restart Services

All services:
```bash
docker compose restart
```

Specific service:
```bash
docker compose restart influxdb
docker compose restart prometheus
docker compose restart grafana
```

### Stop Stack

```bash
./stop.sh
```

Or:
```bash
docker compose down
```

### Stop and Remove Data

**⚠️ WARNING: This deletes all historical data!**

```bash
./stop.sh --volumes
```

Or:
```bash
docker compose down -v
```

### Update Configuration

1. Edit `.env` file
2. Rebuild and restart:

```bash
docker compose down
docker compose up -d --build
```

### View Resource Usage

```bash
docker stats
```

## 🔍 Troubleshooting

### Check if Services are Running

```bash
docker compose ps
```

Expected output:
```
NAME            STATUS          PORTS
influxdb        Up (healthy)    0.0.0.0:8086->8086/tcp
prometheus      Up (healthy)    0.0.0.0:9090->9090/tcp
grafana         Up (healthy)    0.0.0.0:3000->3000/tcp
```

### Check Service Health

**InfluxDB:**
```bash
curl http://localhost:8086/health
# Should return: {"name":"influxdb","message":"ready for queries and writes","status":"pass"}
```

**Prometheus:**
```bash
curl http://localhost:9090/-/healthy
# Should return: Prometheus is Healthy.
```

**Grafana:**
```bash
curl http://localhost:3000/api/health
# Should return: {"database":"ok","version":"..."}
```

### Service Won't Start

**InfluxDB:**
```bash
# Check logs
docker compose logs influxdb

# Restart service
docker compose restart influxdb
```

**Prometheus:**
```bash
# Check logs
docker compose logs prometheus

# Verify configuration is valid
docker compose exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Check targets status
curl http://localhost:9090/api/v1/targets
```

**Grafana:**
```bash
# Check logs
docker compose logs grafana

# Verify data sources
curl -u admin:admin http://localhost:3000/api/datasources
```

### Prometheus Not Scraping Targets

Check target status in Prometheus UI:
1. Open http://localhost:9090/targets
2. Look for targets marked as "DOWN"

**Common issues:**
- Target not reachable from Docker network
- Incorrect target URL in `prometheus.yml`
- Firewall blocking metrics endpoint

**Solution:**
```bash
# Test connectivity from Prometheus container
docker compose exec prometheus wget -O- http://host.docker.internal:9001/metrics

# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload
```

### InfluxDB Token Error

If you see authentication errors:

1. Get the auto-generated token:
```bash
docker compose exec influxdb influx auth list
```

2. Update `.env` with the correct token
3. Restart services:
```bash
docker compose restart
```

### Grafana Can't Connect to InfluxDB

1. Verify InfluxDB is healthy:
```bash
docker compose ps influxdb
```

2. Check token is correct in `.env`
3. Restart Grafana:
```bash
docker compose restart grafana
```

### Port Already in Use

If you see "port already allocated":

**Check which ports are in use:**
```bash
lsof -i :8086   # InfluxDB
lsof -i :9090   # Prometheus
lsof -i :3000   # Grafana
```

**Solution:** Customize ports in `.env` file:
```bash
# Edit .env
INFLUXDB_PORT=8087
PROMETHEUS_PORT=9091
GRAFANA_PORT=3001
```

Then restart:
```bash
docker compose down
docker compose up -d
```

**Note:** If you change `INFLUXDB_PORT`, also update `config.py`:
```python
INFLUXDB_URL = "http://localhost:8087"
```

## 📊 Using Prometheus

### Accessing Prometheus

Open http://localhost:9090 in your browser. The Prometheus web interface provides:

- **Graph** - Query and visualize metrics
- **Alerts** - View active alerts (if configured)
- **Status** - View targets, configuration, and service health

### Basic Prometheus Queries (PromQL)

**Check if services are up:**
```promql
up
```

**View all targets:**
```promql
up{job="prometheus-app"}
```

**CPU usage rate:**
```promql
rate(process_cpu_seconds_total[5m])
```

**Memory usage:**
```promql
process_resident_memory_bytes
```

### Using Prometheus in Grafana

Prometheus is auto-configured as a data source in Grafana.

1. Login to Grafana (http://localhost:3000)
2. Create a new dashboard
3. Add a panel
4. Select **Prometheus** as the data source
5. Use PromQL queries:

```promql
# Example: Service uptime
up{job="prometheus-app"}

# Example: Query duration
rate(prometheus_http_request_duration_seconds_sum[5m])
```

### Adding Custom Metrics

To add your own metrics endpoints to Prometheus:

1. **Edit `prometheus.yml`:**
```yaml
scrape_configs:
  - job_name: prometheus-app
    static_configs:
      - targets:
          - host.docker.internal:9001
  
  # Add your custom target
  - job_name: my-application
    static_configs:
      - targets:
          - host.docker.internal:9100
    scrape_interval: 30s
```

2. **Restart Prometheus:**
```bash
docker compose restart prometheus
```

3. **Verify target is being scraped:**
   - Open http://localhost:9090/targets
   - Look for your new job

### Prometheus Data Retention

By default, Prometheus retains data for 15 days. To change this, edit `docker-compose.yml`:

```yaml
prometheus:
  command:
    - --config.file=/etc/prometheus/prometheus.yml
    - --storage.tsdb.path=/prometheus
    - --web.console.libraries=/etc/prometheus/console_libraries
    - --web.console.templates=/etc/prometheus/consoles
    - --web.enable-lifecycle
    - --storage.tsdb.retention.time=30d  # Keep for 30 days
```

Then restart:
```bash
docker compose down
docker compose up -d
```

### Prometheus API

Query Prometheus programmatically:

```bash
# Instant query
curl 'http://localhost:9090/api/v1/query?query=up'

# Range query
curl 'http://localhost:9090/api/v1/query_range?query=up&start=2024-01-01T00:00:00Z&end=2024-01-01T01:00:00Z&step=15s'

# Get all metrics
curl 'http://localhost:9090/api/v1/label/__name__/values'
```

## 🔐 Security Considerations

### Production Deployment

**Change default passwords:**
```bash
# In .env file
GRAFANA_ADMIN_PASSWORD=strong-password-here
INFLUXDB_ADMIN_PASSWORD=strong-password-here
INFLUXDB_TOKEN=long-random-token-here
```

**Use secrets for sensitive data:**

Create `secrets/` directory:
```bash
mkdir -p secrets
echo "strong-password" > secrets/grafana_password
chmod 600 secrets/*
```

Update `docker-compose.yml` to use secrets (Docker Swarm mode).

**Network security:**
- Don't expose ports publicly
- Use reverse proxy (nginx, traefik) with SSL
- Restrict access with firewall rules

## 🚀 Advanced Usage

### Running on Different Host

To run on a server:

1. **Transfer files:**
```bash
scp -r IxPortUtilizationPlotter user@server:/opt/
```

2. **SSH into server:**
```bash
ssh user@server
cd /opt/IxPortUtilizationPlotter
```

3. **Configure and start:**
```bash
cp env.example .env
nano .env  # Configure
./start.sh
```

### Auto-Start on Boot

Create systemd service:

```bash
sudo nano /etc/systemd/system/ixos-poller.service
```

```ini
[Unit]
Description=IxOS Port Utilization Poller
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/IxPortUtilizationPlotter
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable ixos-poller
sudo systemctl start ixos-poller
```

### Backup and Restore

**Backup volumes:**
```bash
# Backup InfluxDB data
docker run --rm \
  -v influxdb2-data:/source \
  -v $(pwd)/backups:/backup \
  alpine tar -czf /backup/influxdb-backup-$(date +%Y%m%d).tar.gz -C /source .

# Backup Grafana data
docker run --rm \
  -v grafana-data:/source \
  -v $(pwd)/backups:/backup \
  alpine tar -czf /backup/grafana-backup-$(date +%Y%m%d).tar.gz -C /source .
```

**Restore volumes:**
```bash
# Restore InfluxDB
docker run --rm \
  -v influxdb2-data:/target \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /target && tar -xzf /backup/influxdb-backup-20251102.tar.gz"

# Restore Grafana
docker run --rm \
  -v grafana-data:/target \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /target && tar -xzf /backup/grafana-backup-20251102.tar.gz"
```

## 📝 Upgrade Guide

### Update Images

```bash
# Pull latest images
docker compose pull

# Rebuild and restart
docker compose up -d --build
```

### Update Application Code

Since the IxOS poller runs on the host machine (not in Docker):

```bash
# Pull latest code
git pull

# Restart Docker services only
docker compose restart

# Restart the host-based poller
pkill -f portInfoPoller.py
python3 portInfoPoller.py &
```

## 🎯 Performance Tuning

### Resource Limits

Add to `docker-compose.yml` for any service:

```yaml
services:
  prometheus:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          memory: 256M
```

### Polling Optimization

For many chassis (10+), edit `config.py`:
```python
# Increase polling interval
POLLING_INTERVAL = 15  # seconds
```

### InfluxDB Optimization

For high-volume data:
```yaml
influxdb:
  environment:
    - INFLUXD_QUERY_CONCURRENCY=4
    - INFLUXD_QUERY_QUEUE_SIZE=20
```

## 🔄 Data Sources Comparison

Your setup includes both **InfluxDB** and **Prometheus**, each serving different purposes:

### InfluxDB
**Purpose:** IxOS chassis port metrics (primary application data)

**Best For:**
- ✅ Port ownership tracking
- ✅ Link state monitoring
- ✅ Custom application metrics
- ✅ Long-term storage (infinite retention)
- ✅ High-cardinality data

**Query Language:** Flux

**Example Use Case:**
```flux
from(bucket: "ixosChassisStatistics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portUtilization")
```

### Prometheus
**Purpose:** System and infrastructure metrics

**Best For:**
- ✅ Service health monitoring
- ✅ Container metrics
- ✅ Alerting
- ✅ Pull-based metrics collection
- ✅ System resource monitoring

**Query Language:** PromQL

**Example Use Case:**
```promql
up{job="prometheus-app"}
```

### Using Both Together

Create comprehensive dashboards in Grafana that combine:

**Row 1:** Port ownership (InfluxDB)
- State Timeline panel
- Shows which ports are in use

**Row 2:** System health (Prometheus)
- CPU, Memory, Network usage
- Service uptime

This gives you both application-level AND infrastructure-level visibility! 📊

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [InfluxDB Documentation](https://docs.influxdata.com/influxdb/v2.0/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Main README](README.md)

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `docker compose logs -f`
2. Verify configuration: `cat .env`
3. Check service status: `docker compose ps`
4. Review this guide
5. Open an issue on GitHub

---

**Happy Monitoring! 📊🚀**

