#!/bin/bash
set -euo pipefail

python manage.py migrate
python manage.py collectstatic --no-input

if [ "${DEBUG_MODE:-false}" = "True" ]; then
    echo "===============STARTING IN DEVELOPMENT MODE!===============" >&2
    hypercorn --bind 0.0.0.0:${PORT:-8001} --reload website.wsgi:application &
else
    echo "===============STARTING IN PRODUCTION MODE!===============" >&2
    hypercorn --bind 0.0.0.0:${PORT:-8001} --workers 8 website.wsgi:application &
fi

WEB_PID=$!
celery -A website worker --loglevel=info -E &
CELERY_PID=$!
trap 'kill $WEB_PID $CELERY_PID' TERM INT
wait $WEB_PID $CELERY_PID