#!/bin/sh
python manage.py migrate
python manage.py collectstatic --no-input
hypercorn --bind 0.0.0.0:8000 website.wsgi:application 
wait