#!/bin/sh
python manage.py collectstatic --no-input
hypercorn thps_run.wsgi:application
wait