#!/bin/sh
python manage.py migrate
python manage.py collectstatic --no-input
hypercorn --bind 0.0.0.0:8001 website.wsgi:application  &
celery -A website worker --loglevel=info -E
wait