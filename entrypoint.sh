#!/bin/sh
python manage.py collectstatic --no-input
gunicorn thps_run.wsgi:application --bind 0.0.0.0:8000 &
wait