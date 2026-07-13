#!/bin/sh
set -e

# Ensure data directory exists and is owned by appuser
mkdir -p "$DATA_DIR"
chown -R appuser:appuser "$DATA_DIR"

# Drop privileges to appuser and run the application, preserving environment
exec su -m appuser -c "uvicorn main:app --host 0.0.0.0 --port $PORT"