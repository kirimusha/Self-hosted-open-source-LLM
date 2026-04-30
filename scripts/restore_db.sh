#!/bin/bash

BACKUP_FILE=$1
CONTAINER_NAME="wbs_postgres"
DB_USER="wbs_admin"
DB_NAME="wbs_database"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore_db.sh backup_file.sql"
    echo "Available backups:"
    ls -la /opt/wbs-system/backups/
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: File $BACKUP_FILE not found"
    exit 1
fi

echo "WARNING: This will overwrite current database!"
read -p "Are you sure? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

docker exec -i $CONTAINER_NAME psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
docker exec -i $CONTAINER_NAME psql -U $DB_USER $DB_NAME < "$BACKUP_FILE"

echo "Database restored from $BACKUP_FILE"