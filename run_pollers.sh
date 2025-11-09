#!/bin/bash
# run_pollers.sh - Start all IxOS pollers in background

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_NAME="ixmon"
VENV_PATH="$SCRIPT_DIR/$VENV_NAME"

echo "Checking Python Virtual Environment..."
echo "======================================="

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment '$VENV_NAME' not found. Creating..."
    
    # Check if python3 is available
    if ! command -v python3 &> /dev/null; then
        echo "❌ Error: python3 is not installed or not in PATH"
        exit 1
    fi
    
    # Create virtual environment
    python3 -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Created virtual environment '$VENV_NAME'"
else
    echo "✓ Virtual environment '$VENV_NAME' found"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to activate virtual environment"
    exit 1
fi
echo "✓ Virtual environment activated"

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip > /dev/null 2>&1

# Install dependencies from root requirements.txt
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
    if [ $? -ne 0 ]; then
        echo "⚠️  Warning: Some dependencies from requirements.txt failed to install"
    else
        echo "✓ Dependencies from requirements.txt installed"
    fi
fi

# Install dependencies from RestApi/requirements.txt
if [ -f "$SCRIPT_DIR/RestApi/requirements.txt" ]; then
    echo "Installing dependencies from RestApi/requirements.txt..."
    pip install -r "$SCRIPT_DIR/RestApi/requirements.txt"
    if [ $? -ne 0 ]; then
        echo "⚠️  Warning: Some dependencies from RestApi/requirements.txt failed to install"
    else
        echo "✓ Dependencies from RestApi/requirements.txt installed"
    fi
fi

echo ""
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

# Start sensorsPoller
if pgrep -f "sensorsPoller.py" > /dev/null; then
    echo "⚠️  sensorsPoller.py is already running (PID: $(pgrep -f sensorsPoller.py))"
else
    nohup python3 sensorsPoller.py > sensorsPoller.log 2>&1 &
    echo "✓ Started sensorsPoller.py (PID: $!)"
fi

echo ""
echo "View logs:"
echo "  tail -f ./logs/portInfoPoller.log"
echo "  tail -f ./logs/perfMetricsPoller.log"
echo "  tail -f ./logs/sensorsPoller.log"
echo ""
echo "Stop: sh ./stop_pollers.sh"
echo ""
echo "Note: Virtual environment '$VENV_NAME' is activated in this script."
echo "      The pollers will run with the dependencies from this environment."
