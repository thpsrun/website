#!/bin/bash

cd /app

if [ $# -eq 0 ]; then
    echo "Usage: start.sh [PROCESS_TYPE](server|celery)"
    exit 1
fi

PROCESS_TYPE=$1

if [ "$PROCESS_TYPE" = "server" ]; then
    if [ "${DEBUG:-False}" = "True" ]; then
        echo ""
        echo "........................................Starting in DEBUG Mode......................................................."
        echo ""
        python manage.py runserver 0.0.0.0:8001
    else
        echo ""
        echo "......................................Starting in PRODUCTION Mode..................................................."
        echo ""
        gunicorn \
            --bind 0.0.0.0:8001 \
            --workers 8 \
            --worker-class gthread \
            --log-level DEBUG \
            --access-logfile "-" \
            --error-logfile "-" \
            website.wsgi:application
    fi
elif [ "$PROCESS_TYPE" = "celery" ]; then
    celery -A website worker --loglevel=info -E --max-tasks-per-child=100
fi
