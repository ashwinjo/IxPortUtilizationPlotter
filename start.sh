#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[start]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC}  $*"; }

# ── 1. Ensure .env exists ──────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    warn ".env not found — copied from .env.example"
    warn "Edit .env (CHASSIS_LIST / INFLUXDB_TOKEN) then rerun if needed."
fi

set -a; source .env 2>/dev/null || true; set +a

INFLUXDB_PORT=${INFLUXDB_PORT:-8086}
GRAFANA_PORT=${GRAFANA_PORT:-3000}
PROMETHEUS_PORT=${PROMETHEUS_PORT:-9090}

# ── 2. Free occupied ports ─────────────────────────────────────────
free_port() {
    local port=$1 pids
    pids=$(lsof -ti tcp:"$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        warn "Port $port in use — releasing PID(s): $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

for port in "$INFLUXDB_PORT" "$GRAFANA_PORT" "$PROMETHEUS_PORT" 9001 9002; do
    free_port "$port"
done

# ── 3. Docker containers ───────────────────────────────────────────
log "Checking Docker containers..."

all_exist=true
for svc in influxdb prometheus grafana; do
    if ! docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${svc}$"; then
        all_exist=false; break
    fi
done

if [ "$all_exist" = "false" ]; then
    log "Creating and starting containers..."
    docker compose up -d --build
else
    log "Containers found — restarting..."
    docker compose restart
fi

# ── 4. Wait for healthy ────────────────────────────────────────────
wait_healthy() {
    local svc=$1 count=0
    log "Waiting for $svc to be healthy..."
    while [ $count -lt 30 ]; do
        status=$(docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "unknown")
        [ "$status" = "healthy" ] && return 0
        sleep 2; count=$((count + 1))
    done
    warn "$svc health check timed out — continuing anyway"
}

wait_healthy influxdb
wait_healthy prometheus
wait_healthy grafana

# ── 5. Start pollers ───────────────────────────────────────────────
log "Starting pollers..."
bash "$SCRIPT_DIR/run_pollers.sh"

# ── 6. Summary ─────────────────────────────────────────────────────
echo ""
log "Stack is running."
echo ""
echo "  Grafana    : http://localhost:${GRAFANA_PORT}"
echo "  InfluxDB   : http://localhost:${INFLUXDB_PORT}"
echo "  Prometheus : http://localhost:${PROMETHEUS_PORT}"
echo ""
echo "  Logs:"
echo "    tail -f ${SCRIPT_DIR}/portInfoPoller.log"
echo "    tail -f ${SCRIPT_DIR}/perfMetricsPoller.log"
echo "    tail -f ${SCRIPT_DIR}/sensorsPoller.log"
echo ""
log "Done. Configure Grafana queries to finish setup."
