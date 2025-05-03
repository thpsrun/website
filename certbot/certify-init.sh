#!/bin/sh

set -e

echo "Getting certificate..."

certbot certonly \
    --webroot \
    --webroot-path "/vol/www/" \
    -d "$SSL_HOST" \
    --email $EMAIL \
    --rsa-key-size 4096 \
    --agree-tos \
    --noninteractive

if [ $? -ne 0 ]; then
    echo "Certbot encountered an error. Exiting."
    exit 1
fi

#for copying the certificate and configuration to the volume
if [ -f "/etc/letsencrypt/live/${SSL_HOST}/fullchain.pem" ]; then
    echo "SSL cert exists, enabling HTTPS..."
    envsubst '${SSL_HOST}' < /etc/nginx/nginx.prod.conf > /etc/nginx/conf.d/default.conf
else
    echo "Certbot unable to get SSL cert,server HTTP only..."
fi

echo "Setting up auto-renewal..."
apk add --no-cache dcron
echo "0 12 * * * certbot renew --quiet" | crontab -
crond -f