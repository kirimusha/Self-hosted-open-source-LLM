#!/bin/bash

BACKUP_DIR="/opt/wbs-system/backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="wbs_postgres"
DB_USER="wbs_admin"
DB_NAME="wbs_database"

mkdir -p $BACKUP_DIR

docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > "$BACKUP_DIR/backup_$DATE.sql"

find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete

echo "Backup created: backup_$DATE.sql"