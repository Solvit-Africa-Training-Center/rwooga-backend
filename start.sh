#!/bin/bash
set -e
echo "Running migrations..."
python manage.py migrate --noinput
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:$PORT --workers=1 --threads=2 --timeout=300 rwoogaBackend.wsgi:application
