#!/bin/bash

echo "=================================="
echo "  Xray Core - Railway Deployment"
echo "=================================="

UUID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen 2>/dev/null || echo $(head -c16 /dev/urandom | xxd -p))
echo "UUID (for reference): $UUID"
echo "Mode: Accepting ALL UUIDs (dynamic)"
echo "Port: ${PORT:-8080}"
echo "WS Path: / (catch-all)"
echo "=================================="

exec /usr/local/xray/xray run -config /usr/local/xray/config.json
