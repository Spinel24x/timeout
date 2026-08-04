#!/bin/bash

echo "Starting Xray..."
/usr/local/xray/xray run -config /usr/local/xray/config.json &

sleep 2

echo "Starting Python Panel..."
cd /app
python main.py
