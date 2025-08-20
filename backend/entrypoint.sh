#!/bin/bash
set -euo pipefail

python manage.py migrate
python manage.py collectstatic --no-input

# If CMD passed starts with ./start.sh or /app/start.sh, let that manage processes.
if [ "${1:-}" = "/app/start.sh" ] || [ "${1:-}" = "./start.sh" ]; then
	exec "$@"
fi

# Fallback legacy behaviour: run hypercorn + celery (no start.sh provided)
echo "(entrypoint) Falling back to legacy hypercorn+celery startup" >&2
hypercorn --bind 0.0.0.0:${PORT:-8001} website.wsgi:application &
WEB_PID=$!
celery -A website worker --loglevel=info -E &
CELERY_PID=$!
trap 'kill $WEB_PID $CELERY_PID' TERM INT
wait $WEB_PID $CELERY_PID