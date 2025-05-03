#!/bin/bash

set -e

echo "Checking for fullchain.pem"
if [ ! -f "/etc/letsencrypt/live/${SSL_HOST}/fullchain.pem" ]; then
  echo "No SSL cert, enabling HTTP only..."
  envsubst '' < /etc/nginx/nginx.conf > /etc/nginx/conf.d/default.conf
else
  echo "SSL cert exists, enabling HTTPS..."
  envsubst '${SSL_HOST}' < /etc/nginx/nginx.conf > /etc/nginx/conf.d/default.conf
fi

# Monitor /etc/nginx/ and /etc/letsencrypt/ for configuration or SSL changes
inotifywait -m -r -e modify,move,close_write /etc/nginx/conf.d/default.conf /etc/letsencrypt |
while read path action file; do
    echo "Change detected in $file: $action"
    echo "Reloading nginx!"
    nginx -s reload
done &


nginx-debug -g 'daemon off;'