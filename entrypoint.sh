#!/bin/bash

echo "========================================="
echo "  Starting Services"
echo "========================================="

# Start Xray on port 10000
echo "[1/2] Starting Xray on port 10000..."
/usr/local/xray/xray run -config /usr/local/xray/config.json &
XRAY_PID=$!
sleep 2

# Start Python Panel on port 8080
echo "[2/2] Starting Python Panel on port 8080..."
cd /app
python main.py &
PYTHON_PID=$!

echo "========================================="
echo "  Xray PID: $XRAY_PID (port 10000)"
echo "  Panel PID: $PYTHON_PID (port 8080)"
echo "========================================="

wait $PYTHON_PID
