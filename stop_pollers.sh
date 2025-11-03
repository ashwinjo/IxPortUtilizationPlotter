#!/bin/bash
# stop_pollers.sh - Stop both IxOS pollers

echo "========================================"
echo "Stopping IxOS Pollers"
echo "========================================"

STOPPED=0

if pgrep -f "portInfoPoller.py" > /dev/null; then
    pkill -f portInfoPoller.py
    echo "✓ Stopped portInfoPoller.py"
    STOPPED=$((STOPPED + 1))
else
    echo "ℹ️  portInfoPoller.py was not running"
fi

if pgrep -f "perfMetricsPoller.py" > /dev/null; then
    pkill -f perfMetricsPoller.py
    echo "✓ Stopped perfMetricsPoller.py"
    STOPPED=$((STOPPED + 1))
else
    echo "ℹ️  perfMetricsPoller.py was not running"
fi

echo "========================================"
if [ $STOPPED -eq 0 ]; then
    echo "No pollers were running"
else
    echo "Stopped $STOPPED poller(s)"
fi
echo "========================================"