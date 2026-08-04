#!/bin/bash
echo "Starting Xray on 127.0.0.1:10000..."
/usr/local/xray/xray run -config /usr/local/xray/config.json &
sleep 2
echo "Starting Panel on 0.0.0.0:8080..."
cd /app && exec python main.py
