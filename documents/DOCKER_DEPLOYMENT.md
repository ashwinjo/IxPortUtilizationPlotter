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

**Important configurations to change:**

```bash
# Change this to a secure token
INFLUXDB_TOKEN=your-super-secret-token-change-me

# Add your chassis (JSON array format)
CHASSIS_LIST=[{"ip":"10.36.75.205","username":"admin","password":"admin"}]

# Optional: Adjust polling interval
POLLING_INTERVAL=10
```

### 3. Start the Stack

```bash
./start.sh
```

Or manually:

```bash
docker compose up -d
```

### 4. Access the Services

- **Grafana:** http://localhost:3000 (admin/admin)
- **InfluxDB:** http://localhost:8086 (admin/admin)

### 5. Setup Grafana Dashboard

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
   - Time-series database
   - Auto-initialized with org and bucket
   - Infinite data retention

2. **Grafana** (port 3000)
   - Visualization platform
   - Auto-configured InfluxDB data source
   - Persistent dashboards and settings

3. **IxOS Poller** (no exposed ports)
   - Python application
   - Polls chassis in parallel
   - Writes to InfluxDB

### Volumes (Persistent Data)

- `influxdb2-data` - InfluxDB data
- `influxdb2-config` - InfluxDB configuration
- `grafana-data` - Grafana dashboards and settings

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INFLUXDB_TOKEN` | InfluxDB API token | `your-super-secret-token-change-me` |
| `INFLUXDB_ORG` | Organization name | `keysight` |
| `INFLUXDB_BUCKET` | Bucket name | `ixosChassisStatistics` |
| `INFLUXDB_RETENTION` | Data retention (0=infinite) | `0` |
| `GRAFANA_ADMIN_USER` | Grafana username | `admin` |
| `GRAFANA_ADMIN_PASSWORD` | Grafana password | `admin` |
| `POLLING_INTERVAL` | Polling interval (seconds) | `10` |
| `CHASSIS_LIST` | JSON array of chassis | `[]` |

### Chassis Configuration Format

Single chassis:
```json
[{"ip":"10.36.75.205","username":"admin","password":"admin"}]
```

Multiple chassis:
```json
[
  {"ip":"10.36.75.205","username":"admin","password":"admin"},
  {"ip":"10.36.75.206","username":"admin","password":"admin"},
  {"ip":"10.36.75.207","username":"admin","password":"admin"}
]
```

**Note:** Keep it on one line in the `.env` file!

## 📊 Management Commands

### View Logs

All services:
```bash
docker compose logs -f
```

Specific service:
```bash
docker compose logs -f ixos-poller
docker compose logs -f influxdb
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
docker compose restart ixos-poller
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
grafana         Up (healthy)    0.0.0.0:3000->3000/tcp
ixos-poller     Up              
```

### Check Poller Logs

```bash
docker compose logs -f ixos-poller
```

You should see:
```
Starting parallel chassis poller for X chassis...
[Poll #1] Starting parallel poll at HH:MM:SS
✓ Successfully polled 10.36.75.205 - 48 ports
✓ Written: 10.36.75.205/1/1 -> Owner=Free...
```

### Service Won't Start

**InfluxDB:**
```bash
# Check logs
docker compose logs influxdb

# Restart service
docker compose restart influxdb
```

**Grafana:**
```bash
# Check logs
docker compose logs grafana

# Verify InfluxDB is healthy first
docker compose ps influxdb
```

**Poller:**
```bash
# Check logs for errors
docker compose logs ixos-poller

# Verify CHASSIS_LIST in .env
docker compose exec ixos-poller python config.py
```

### Cannot Connect to Chassis

Check from within container:
```bash
docker compose exec ixos-poller ping 10.36.75.205
```

If it fails:
- Verify chassis IP is correct
- Check firewall rules
- Ensure chassis REST API is enabled

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

**Option 1:** Stop existing service
```bash
# Find what's using the port
lsof -i :8086  # or :3000
kill <PID>
```

**Option 2:** Change port in `docker-compose.yml`
```yaml
ports:
  - "8087:8086"  # Use different host port
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

```bash
# Pull latest code
git pull

# Rebuild poller image
docker compose build ixos-poller

# Restart with new image
docker compose up -d ixos-poller
```

## 🎯 Performance Tuning

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  ixos-poller:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          memory: 256M
```

### Polling Optimization

For many chassis (10+):
```bash
# In .env
POLLING_INTERVAL=15  # Increase interval
```

### InfluxDB Optimization

For high-volume data:
```yaml
influxdb:
  environment:
    - INFLUXD_QUERY_CONCURRENCY=4
    - INFLUXD_QUERY_QUEUE_SIZE=20
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [InfluxDB Documentation](https://docs.influxdata.com/influxdb/v2.0/)
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

