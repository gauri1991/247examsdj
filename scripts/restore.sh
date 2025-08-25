#!/bin/bash

# Restore script for exam portal
# Usage: ./restore.sh [backup_date]

set -e

# Configuration
BACKUP_DIR="/backups"
BACKUP_DATE=${1:-$(ls -t ${BACKUP_DIR}/db/*.sql.gz 2>/dev/null | head -1 | sed 's/.*exam_portal_\(.*\)\.sql\.gz/\1/')}

if [ -z "${BACKUP_DATE}" ]; then
    echo "Error: No backup found or date provided"
    echo "Usage: $0 [YYYYMMDD_HHMMSS]"
    exit 1
fi

# Load environment variables
source /app/.env

echo "Starting restore from backup ${BACKUP_DATE} at $(date)"

# Confirm restoration
read -p "This will restore from backup ${BACKUP_DATE}. Are you sure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Stop application
echo "Stopping application..."
supervisorctl stop all

# Database restore
echo "Restoring database..."
DB_BACKUP="${BACKUP_DIR}/db/exam_portal_${BACKUP_DATE}.sql.gz"

if [ -f "${DB_BACKUP}" ]; then
    # Drop existing database and recreate
    PGPASSWORD=${DB_PASSWORD} psql \
        -h db \
        -U ${DB_USER:-examuser} \
        -d postgres \
        -c "DROP DATABASE IF EXISTS exam_portal;"
    
    PGPASSWORD=${DB_PASSWORD} psql \
        -h db \
        -U ${DB_USER:-examuser} \
        -d postgres \
        -c "CREATE DATABASE exam_portal;"
    
    # Restore from backup
    gunzip -c ${DB_BACKUP} | PGPASSWORD=${DB_PASSWORD} psql \
        -h db \
        -U ${DB_USER:-examuser} \
        -d exam_portal
    
    echo "Database restored successfully"
else
    echo "Database backup not found: ${DB_BACKUP}"
    exit 1
fi

# Media files restore
echo "Restoring media files..."
MEDIA_BACKUP="${BACKUP_DIR}/media/media_${BACKUP_DATE}.tar.gz"

if [ -f "${MEDIA_BACKUP}" ]; then
    rm -rf /app/media/*
    tar -xzf ${MEDIA_BACKUP} -C /app/
    chown -R django:django /app/media
    echo "Media files restored successfully"
else
    echo "Warning: Media backup not found: ${MEDIA_BACKUP}"
fi

# Run migrations
echo "Running database migrations..."
python /app/manage.py migrate --noinput

# Restart application
echo "Starting application..."
supervisorctl start all

echo "Restore completed at $(date)"