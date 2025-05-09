#!/bin/sh
set -e
# copy static files to volume

cp -r /static_source/* /app/static/

# Run Django migrations
python /app/manage.py migrate
# Start the application

python -m gunicorn -w 4 --timeout 120 --bind 0.0.0.0:8000 project.wsgi:application
