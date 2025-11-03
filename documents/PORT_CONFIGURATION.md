# Port Configuration Guide

## Overview

All Docker service ports (InfluxDB, Prometheus, Grafana) are now fully configurable via environment variables. This allows you to avoid port conflicts with existing services on your Linux/macOS host.

## Default Ports

| Service | Default Port | Purpose |
|---------|--------------|---------|
| **InfluxDB** | 8086 | Time-series database |
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3000 | Visualization dashboard |

## How to Customize Ports

### 1. Edit `.env` File

```bash
# Service Ports (customize if defaults conflict with existing services)
INFLUXDB_PORT=8087       # Changed from default 8086
PROMETHEUS_PORT=9091     # Changed from default 9090
GRAFANA_PORT=3001        # Changed from default 3000
```

### 2. Update IxOS Poller Configuration

Edit `config.py` to match the new InfluxDB port:

```python
# Update InfluxDB URL to match your custom port
INFLUXDB_URL = "http://localhost:8087"  # Use your configured port
INFLUXDB_TOKEN = "your-token-here"
```

### 3. Restart Docker Services

```bash
# Stop services
docker compose down

# Start with new configuration
docker compose up -d
```

### 4. Verify Services

Check that services are running on the new ports:

```bash
# Check service status
docker compose ps

# Test connectivity
curl http://localhost:8087/health        # InfluxDB
curl http://localhost:9091/-/healthy     # Prometheus
curl http://localhost:3001/api/health    # Grafana
```

## Common Port Conflict Scenarios

### Scenario 1: InfluxDB Port Conflict (8086)

**Problem:** Another InfluxDB or service using port 8086

**Solution:**
```bash
# In .env
INFLUXDB_PORT=8087

# In config.py
INFLUXDB_URL = "http://localhost:8087"
```

### Scenario 2: Prometheus Port Conflict (9090)

**Problem:** Another Prometheus instance or service using port 9090

**Solution:**
```bash
# In .env
PROMETHEUS_PORT=9091
```

### Scenario 3: Grafana Port Conflict (3000)

**Problem:** Another Grafana or web service using port 3000

**Solution:**
```bash
# In .env
GRAFANA_PORT=3001
```

Access Grafana at: http://localhost:3001

### Scenario 4: Multiple Conflicts

**Problem:** Multiple ports are already in use

**Solution:** Change all conflicting ports at once:

```bash
# In .env
INFLUXDB_PORT=18086
PROMETHEUS_PORT=19090
GRAFANA_PORT=13000

# In config.py
INFLUXDB_URL = "http://localhost:18086"
```

## Checking Port Availability

Before starting services, check if ports are available:

### On Linux/macOS

```bash
# Check specific port
lsof -i :8086

# Check all our ports
lsof -i :8086 -i :9090 -i :3000

# Using netstat (Linux)
netstat -tulpn | grep -E '8086|9090|3000'

# Find what's using a port
sudo lsof -i :8086 -P -n
```

### Using validate_setup.py

Our validation script automatically checks port availability:

```bash
python3 validate_setup.py
```

Output will show:
```
================================================================================
Checking Port Availability
================================================================================
✓ Port 8086 (InfluxDB) is available
✓ Port 9090 (Prometheus) is available
✓ Port 3000 (Grafana) is available
```

Or if ports are in use:
```
⚠  Port 8086 (InfluxDB) is already in use
   COMMAND    PID    USER   FD   TYPE   DEVICE SIZE/OFF NODE NAME
   influxd   1234    user   8u   IPv4   0x...      0t0  TCP *:8086 (LISTEN)
```

## Docker Compose Port Mapping

The port mapping in `docker-compose.yml` uses the format:

```yaml
ports:
  - "${INFLUXDB_PORT:-8086}:8086"
  #  └─ Host port (configurable) : Container port (fixed)
```

- **Host port** (left side): The port on your Linux host - CONFIGURABLE
- **Container port** (right side): The port inside Docker container - FIXED

You only need to change the host port in `.env` file. The container port remains the same.

## Example Configurations

### Development Environment

```bash
# .env file - Standard ports
INFLUXDB_PORT=8086
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### Production Environment with Port Offsets

```bash
# .env file - Offset by 10000 to avoid conflicts
INFLUXDB_PORT=18086
PROMETHEUS_PORT=19090
GRAFANA_PORT=13000
```

### Running Multiple Instances

If you need to run multiple instances of the stack:

**Instance 1:**
```bash
# .env file
INFLUXDB_PORT=8086
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

**Instance 2:**
```bash
# .env file  
INFLUXDB_PORT=8186
PROMETHEUS_PORT=9190
GRAFANA_PORT=3100
```

## Troubleshooting

### Issue: Service won't start after changing port

**Check:**
1. Port is actually available: `lsof -i :NEW_PORT`
2. `.env` file has been saved
3. Docker services restarted: `docker compose down && docker compose up -d`

### Issue: Poller can't connect to InfluxDB

**Check:**
1. `config.py` has correct port in `INFLUXDB_URL`
2. InfluxDB is running: `docker compose ps influxdb`
3. Port is accessible: `curl http://localhost:YOUR_PORT/health`

### Issue: Grafana data source not working

**Check:**
1. Grafana is using internal Docker network (uses container name, not localhost)
2. The data source URL in Grafana should be: `http://influxdb:8086` (container port, not host port)

### Issue: Can't access web interfaces

**Check:**
1. Using correct host port in browser URL
2. Services are running: `docker compose ps`
3. Firewall not blocking ports

## Environment Variable Precedence

Port configuration follows this precedence:

1. **`.env` file** - Highest priority
2. **Environment variables** - Set in shell
3. **Default values** - Built into docker-compose.yml (8086, 9090, 3000)

Example:
```bash
# Set via environment variable (overrides .env)
export INFLUXDB_PORT=8087

# Or use in .env file
echo "INFLUXDB_PORT=8087" >> .env

# Or use defaults if not specified
# (Uses 8086, 9090, 3000)
```

## Best Practices

1. **Document your port changes** - Keep a record of custom ports
2. **Use consistent offsets** - Makes it easier to remember (e.g., +10000)
3. **Validate before starting** - Run `python3 validate_setup.py`
4. **Update documentation** - If sharing with team, document custom ports
5. **Keep config.py synchronized** - Always match InfluxDB port

## Quick Reference

```bash
# Check current ports from running containers
docker compose ps

# View configured ports from .env
cat .env | grep PORT

# Test service accessibility
curl http://localhost:${INFLUXDB_PORT:-8086}/health
curl http://localhost:${PROMETHEUS_PORT:-9090}/-/healthy
curl http://localhost:${GRAFANA_PORT:-3000}/api/health

# View logs if service won't start
docker compose logs influxdb
docker compose logs prometheus
docker compose logs grafana
```

## Summary

✅ **Flexible Port Configuration** - All ports are customizable  
✅ **No Code Changes Required** - Just edit `.env` file  
✅ **Automatic Detection** - Scripts adapt to configured ports  
✅ **Validation Support** - Built-in port availability checking  
✅ **Multi-Instance Ready** - Run multiple stacks on same host  

---

**For more information, see:**
- [README.md](README.md) - Main documentation
- [env.example](env.example) - Configuration template
- [docker-compose.yml](docker-compose.yml) - Service definitions

