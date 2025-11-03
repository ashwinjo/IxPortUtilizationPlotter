# ============================================
# START BOTH POLLERS
# ============================================
nohup python3 portInfoPoller.py > portInfoPoller.log 2>&1 &
nohup python3 perfMetricsPoller.py > perfMetricsPoller.log 2>&1 &

# ============================================
# CHECK STATUS
# ============================================
ps aux | grep -E "portInfoPoller|perfMetricsPoller"
lsof -i :9001  # Check if metrics endpoint is up

# ============================================
# VIEW LOGS
# ============================================
tail -f portInfoPoller.log      # Port info logs
tail -f perfMetricsPoller.log   # Performance metrics logs
tail -f *.log                   # Both logs

# ============================================
# TEST METRICS ENDPOINT
# ============================================
curl http://localhost:9001/metrics

# ============================================
# STOP BOTH POLLERS
# ============================================
pkill -f portInfoPoller.py
pkill -f perfMetricsPoller.py

# ============================================
# VERIFY STOPPED
# ============================================
ps aux | grep -E "portInfoPoller|perfMetricsPoller"