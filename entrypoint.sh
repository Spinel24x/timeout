#!/bin/bash

echo "=================================="
echo "  Xray Core - Railway Deployment"
echo "=================================="
echo "Port: ${PORT:-8080}"
echo "Starting Xray..."
echo "=================================="

# Run Xray in background and show logs
/usr/local/xray/xray run -config /usr/local/xray/config.json
