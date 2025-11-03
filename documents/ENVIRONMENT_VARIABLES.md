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
| `POLLING_INTERVAL` | config.py | `10` | Polling interval in seconds |
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

Example:
```bash
# 1. Set in .env file
echo "POLLING_INTERVAL=10" >> .env

# 2. Override via shell environment
export POLLING_INTERVAL=20

# 3. Override inline
POLLING_INTERVAL=30 python3 portInfoPoller.py

# Result: Uses 30 (inline wins)
```

## Variable Validation

### Required Variables

These **must** be configured:

- ✅ `INFLUXDB_TOKEN` - Must be set to a secure value
- ✅ At least one chassis configured (in `config.py` or `CHASSIS_LIST`)

### Optional Variables

These have working defaults:

- `INFLUXDB_PORT` - Default: 8086
- `PROMETHEUS_PORT` - Default: 9090
- `GRAFANA_PORT` - Default: 3000
- `POLLING_INTERVAL` - Default: 10 seconds
- `INFLUXDB_ORG` - Default: keysight
- `INFLUXDB_BUCKET` - Default: ixosChassisStatistics

## Port Configuration Impact

When you change service ports, you may need to update multiple places:

### Changing `INFLUXDB_PORT`

**Update in `.env`:**
```bash
INFLUXDB_PORT=8087
INFLUXDB_URL=http://localhost:8087  # Must match!
```

**OR update `config.py` if not using env vars:**
```python
INFLUXDB_URL = "http://localhost:8087"
```

### Changing `PROMETHEUS_PORT`

Only affects Docker services - no impact on poller:
```bash
PROMETHEUS_PORT=9091
```

Access at: http://localhost:9091

### Changing `GRAFANA_PORT`

Only affects Docker services - no impact on poller:
```bash
GRAFANA_PORT=3001
```

Access at: http://localhost:3001

## Checking Current Configuration

### View Docker Service Configuration

```bash
# Show variables Docker Compose will use
docker compose config

# Show only specific variable
grep INFLUXDB_PORT .env
```

### View Poller Configuration

```bash
# Print current config.py settings
python3 config.py

# Output shows:
# - Chassis count and IPs
# - Polling interval
# - InfluxDB connection details
# - Any configuration warnings
```

### Verify Variable Matching

Ensure shared variables match:

```bash
# Check .env file
grep INFLUXDB_TOKEN .env
grep INFLUXDB_ORG .env
grep INFLUXDB_BUCKET .env

# Check what poller will use
python3 -c "import config; print(config.INFLUXDB_TOKEN)"
python3 -c "import config; print(config.INFLUXDB_ORG)"
python3 -c "import config; print(config.INFLUXDB_BUCKET)"
```

## Common Issues

### Issue 1: Poller Can't Connect to InfluxDB

**Symptom:** `✗ Error writing data: unauthorized access`

**Cause:** `INFLUXDB_TOKEN` mismatch between Docker and poller

**Solution:**
```bash
# Ensure .env has correct token
grep INFLUXDB_TOKEN .env

# Verify poller uses same token
python3 -c "import config; print(config.INFLUXDB_TOKEN)"

# They must match!
```

### Issue 2: Wrong Port After Changing `INFLUXDB_PORT`

**Symptom:** Poller tries to connect but fails

**Cause:** `INFLUXDB_URL` not updated to match new port

**Solution:**
```bash
# In .env
INFLUXDB_PORT=8087
INFLUXDB_URL=http://localhost:8087  # Must match port!
```

### Issue 3: Docker Services Use Different Org/Bucket

**Symptom:** No data shows in Grafana

**Cause:** Poller writes to different org/bucket than Docker services

**Solution:** Ensure consistency:
```bash
# In .env - used by both
INFLUXDB_ORG=keysight
INFLUXDB_BUCKET=ixosChassisStatistics
```

### Issue 4: CHASSIS_LIST JSON Parse Error

**Symptom:** `⚠️  Warning: Invalid CHASSIS_LIST JSON`

**Cause:** Malformed JSON in environment variable

**Solution:**
```bash
# Correct format (all on one line):
CHASSIS_LIST=[{"ip":"10.36.75.205","username":"admin","password":"admin"}]

# Invalid (don't do this):
# CHASSIS_LIST=[
#   {"ip":"10.36.75.205"}
# ]
```

## Best Practices

1. **Use `.env` file** - Centralized configuration
2. **Keep secrets in .env** - Don't commit to git
3. **Match shared variables** - TOKEN, ORG, BUCKET must align
4. **Document custom ports** - If you change defaults
5. **Validate after changes** - Run `python3 validate_setup.py`
6. **Use strong tokens** - Change default `INFLUXDB_TOKEN`
7. **Test connection** - Before running full poller

## Security Considerations

### Sensitive Variables

These contain sensitive information:

- `INFLUXDB_TOKEN` - API authentication
- `INFLUXDB_ADMIN_PASSWORD` - Database admin password
- `GRAFANA_ADMIN_PASSWORD` - Dashboard admin password
- `CHASSIS_LIST` - Contains chassis passwords

### Protection

```bash
# Secure .env file permissions
chmod 600 .env

# Add to .gitignore (already done)
echo ".env" >> .gitignore

# Never commit .env
git add .gitignore
git commit -m "Protect .env file"
```

### Production Deployment

For production, consider:

1. **Use Docker secrets** instead of environment variables
2. **Rotate tokens** regularly
3. **Use strong passwords** (not defaults)
4. **Restrict file permissions** (`chmod 600 .env`)
5. **Use secret management tools** (HashiCorp Vault, AWS Secrets Manager)

## Quick Reference

### View All Environment Variables

```bash
# Show all variables in .env
cat .env

# Show variables that config.py will use
python3 config.py

# Show what Docker Compose will use
docker compose config
```

### Test Configuration

```bash
# Validate setup
python3 validate_setup.py

# Test InfluxDB connection
curl http://localhost:${INFLUXDB_PORT:-8086}/health

# Check if token works
curl -H "Authorization: Token $INFLUXDB_TOKEN" \
     http://localhost:${INFLUXDB_PORT:-8086}/api/v2/buckets
```

---

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

**For complete setup instructions, see [README.md](README.md) and [DOCKER_DEPLOYMENT.md](documents/DOCKER_DEPLOYMENT.md)**

