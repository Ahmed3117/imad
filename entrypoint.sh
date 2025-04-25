#!/bin/sh
set -e
# copy static files to volume

cp -r /static_source/* /app/static/

# Run Django migrations
python /app/manage.py migrate
# Start the application

python -m uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --reload
