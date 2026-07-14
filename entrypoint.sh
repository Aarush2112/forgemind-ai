#!/bin/sh
set -e

# Use default port if PORT is not set (for local testing)
PORT=${PORT:-8080}

# Ensure data directory exists and handle permissions gracefully
if [ -n "$DATA_DIR" ]; then
  mkdir -p "$DATA_DIR" || true
  # Only try to chown if we are root (UID 0), otherwise it will fail on PaaS systems
  if [ "$(id -u)" = "0" ]; then
    chown -R appuser:appuser "$DATA_DIR" 2>/dev/null || true
  fi
fi

# Drop privileges to appuser and run the application if we are root,
# otherwise run the application directly as the current user.
if [ "$(id -u)" = "0" ]; then
  exec su -m appuser -c "uvicorn main:app --host 0.0.0.0 --port $PORT"
else
  exec uvicorn main:app --host 0.0.0.0 --port $PORT
fi
