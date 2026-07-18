#!/bin/sh
set -e

# Use default port if PORT is not set (for local testing)
PORT=${PORT:-8080}

# Ensure data directory exists
if [ -n "$DATA_DIR" ]; then
  mkdir -p "$DATA_DIR" 2>/dev/null || true
fi

# Run the application directly
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
