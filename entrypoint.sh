#!/bin/sh
cd srlc/
python manage.py migrate
python manage.py collectstatic --no-input
hypercorn website.asgi:application --bind 0.0.0.0:8000 &
wait