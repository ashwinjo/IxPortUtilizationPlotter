#!/bin/bash
# run_pollers.sh - Start both IxOS pollers in background

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting IxOS Pollers..."
echo "========================"

# Start portInfoPoller
if pgrep -f "portInfoPoller.py" > /dev/null; then
    echo "⚠️  portInfoPoller.py is already running (PID: $(pgrep -f portInfoPoller.py))"
else
    nohup python3 portInfoPoller.py > portInfoPoller.log 2>&1 &
    echo "✓ Started portInfoPoller.py (PID: $!)"
fi

# Start perfMetricsPoller
if pgrep -f "perfMetricsPoller.py" > /dev/null; then
    echo "⚠️  perfMetricsPoller.py is already running (PID: $(pgrep -f perfMetricsPoller.py))"
else
    nohup python3 perfMetricsPoller.py > perfMetricsPoller.log 2>&1 &
    echo "✓ Started perfMetricsPoller.py (PID: $!)"
fi

echo ""
echo "View logs:"
echo "  tail -f portInfoPoller.log"
echo "  tail -f perfMetricsPoller.log"
echo ""
echo "Stop: ./stop_pollers.sh"