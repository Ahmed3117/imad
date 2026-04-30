#!/bin/sh
set -e

python - <<'PY'
import os
import socket
import time

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "3306"))
deadline = time.time() + 60

while True:
    try:
        with socket.create_connection((host, port), timeout=3):
            break
    except OSError:
        if time.time() > deadline:
            raise
        time.sleep(2)
PY

# Copy static files to volume
cp -r /static_source/* /app/static/

# Run Django migrations
python /app/manage.py migrate

# Start the application
python -m uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --workers 8
