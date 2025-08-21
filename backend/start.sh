#!/bin/bash
# Wrapper placed inside backend so volume mount keeps start.sh accessible.
# Delegates to image copy in /app/docker if present; otherwise replicates logic.
set -euo pipefail

if [ -f /app/docker/start.sh ]; then
  exec /app/docker/start.sh "$@"
fi

# Fallback minimal: run dev server
PORT=${PORT:-8001}
exec python manage.py runserver 0.0.0.0:$PORT
