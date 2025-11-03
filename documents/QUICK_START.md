# Quick Start Guide

Get up and running in 5 minutes! 🚀

## Prerequisites

- Docker and Docker Compose installed
- Network access to IxOS chassis

## Steps

### 1. Configure Environment

```bash
# Copy example configuration
cp env.example .env

# Edit configuration
nano .env
```

**Minimum required changes in `.env`:**
```bash
# Change the token for security
INFLUXDB_TOKEN=change-this-to-a-secure-random-token

# Add your chassis
CHASSIS_LIST=[{"ip":"10.36.75.205","username":"admin","password":"admin"}]
```

### 2. Validate Setup (Optional)

```bash
python3 validate_setup.py
```

### 3. Start Stack

```bash
./start.sh
```

### 4. Access Services

- **Grafana:** http://localhost:3000
  - Username: `admin`
  - Password: `admin`

- **InfluxDB:** http://localhost:8086
  - Username: `admin`
  - Password: `keysight12345`

- **Prometheus:** http://localhost:9090
  - No authentication required (local access)

### 5. Create Grafana Dashboard

1. Login to Grafana
2. Click **+** → **Dashboard** → **Add visualization**
3. Select **InfluxDB-IxOS** data source
4. Choose **State Timeline** visualization
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

6. Click **Apply** and **Save**

## Common Commands

```bash
# View logs
docker compose logs -f ixos-poller

# Check status
docker compose ps

# Restart
docker compose restart

# Stop
docker compose down

# Stop and remove data
docker compose down -v  # ⚠️ Deletes all data!
```

## Troubleshooting

### No data in Grafana?

1. Check poller is running:
   ```bash
   docker compose logs ixos-poller
   ```

2. Verify chassis connectivity:
   ```bash
   docker compose exec ixos-poller ping 10.36.75.205
   ```

3. Check InfluxDB has data:
   ```bash
   docker compose exec influxdb influx query 'from(bucket:"ixosChassisStatistics") |> range(start:-5m) |> limit(n:1)'
   ```

### Port conflicts?

Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8087:8086"  # Use 8087 instead of 8086
```

### Need help?

See detailed documentation:
- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Full Docker guide
- [README.md](README.md) - Complete documentation

## Next Steps

- **Add more chassis:** Edit `CHASSIS_LIST` in `.env`
- **Adjust polling interval:** Change `POLLING_INTERVAL` in `.env`
- **Customize Grafana:** Create multiple panels for different chassis
- **Set up alerts:** Configure Grafana alerting
- **Production deployment:** See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

---

**Happy Monitoring! 📊**

