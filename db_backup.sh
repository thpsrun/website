#!/bin/bash

set -a
source .env
set +a

DATE=$(date +"%Y-%m-%d_%H-%M")
BACKUP_NAME="db_backup_$DATE.sql.gz"
BACKUP_DIR="backups/"
REMOTE_PATH="B2:$B2_BUCKET/backups"

mkdir -p "$BACKUP_DIR"

docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "postgres" \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_DIR/$BACKUP_NAME"

rclone copy "$BACKUP_DIR/$BACKUP_NAME" "$REMOTE_PATH"

find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed!"