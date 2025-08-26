#!/bin/bash
set -euo pipefail

if [ -f /app/docker/start.sh ]; then
  exec /app/docker/start.sh "$@"
fi

PORT=${PORT:-8001}
exec python manage.py runserver 0.0.0.0:$PORT
