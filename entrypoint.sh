#!/bin/bash

# Generate UUID if not provided
if [ -z "$UUID" ]; then
    UUID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen 2>/dev/null || echo $(head -c16 /dev/urandom | xxd -p))
    echo "Generated UUID: $UUID"
fi

# Set WS path from UUID
WS_PATH="/${UUID}"

# Update Xray config with environment variables
sed -i "s|\"id\": \".*\"|\"id\": \"$UUID\"|g" /usr/local/xray/config.json
sed -i "s|\"path\": \".*\"|\"path\": \"$WS_PATH\"|g" /usr/local/xray/config.json

# Set port (default 8080 for Railway)
PORT=${PORT:-8080}
sed -i "s|\"port\": 8080|\"port\": $PORT|g" /usr/local/xray/config.json

echo "=== Xray Configuration ==="
echo "UUID: $UUID"
echo "WS Path: $WS_PATH"
echo "Port: $PORT"
echo "=========================="

# Start Xray
exec /usr/local/xray/xray run -config /usr/local/xray/config.json
