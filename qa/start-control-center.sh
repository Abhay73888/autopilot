#!/usr/bin/env bash
# qa/start-control-center.sh — Automated Local Setup & Server Launcher for AUTOPILOT
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "================================================================================"
echo "AUTOPILOT • Starting Control Center & API Gateway"
echo "================================================================================"

# 1. Kill any existing/stale uvicorn servers on port 8000
echo "--> Checking for stale server processes on port 8000..."
if command -v lsof >/dev/null 2>&1; then
    STALE_PIDS=$(lsof -ti :8000 || true)
    if [ -n "$STALE_PIDS" ]; then
        echo "Killing stale processes on port 8000: $STALE_PIDS"
        kill -9 $STALE_PIDS 2>/dev/null || true
    fi
elif command -v netstat >/dev/null 2>&1; then
    # Fallback for Windows/Git Bash
    STALE_PIDS=$(netstat -ano | grep ":8000 " | awk '{print $5}' | sort -u || true)
    for pid in $STALE_PIDS; do
        if [ "$pid" != "0" ] && [ -n "$pid" ]; then
            echo "Killing stale PID: $pid"
            taskkill -F -PID "$pid" 2>/dev/null || true
        fi
    done
fi

# 2. Check Python environment
PYTHON_CMD="python3"
if ! command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python"
fi

if [ ! -d ".venv" ]; then
    echo "--> Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

# Source virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
fi

# 3. Ensure API and core requirements
echo "--> Verifying dependencies..."
pip install -q -r requirements.txt || true
pip install -q -r requirements-api.txt || true

# 4. Check Node & jsdom
if command -v npm >/dev/null 2>&1; then
    if [ ! -d "node_modules/jsdom" ]; then
        echo "--> Installing jsdom for automated DOM testing..."
        npm install -s jsdom
    fi
fi

# 5. Launch FastAPI server with mandatory PYTHONPATH=.
echo "--> Launching AUTOPILOT server on http://0.0.0.0:8000..."
export PYTHONPATH="."
exec $PYTHON_CMD -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
