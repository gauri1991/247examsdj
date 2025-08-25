#!/bin/bash

# Backup script for exam portal
# Run this as a cron job for regular backups

set -e

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Load environment variables
source /app/.env

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}/{db,media,logs}

echo "Starting backup at $(date)"

# Database backup
echo "Backing up database..."
PGPASSWORD=${DB_PASSWORD} pg_dump \
    -h db \
    -U ${DB_USER:-examuser} \
    -d exam_portal \
    -f ${BACKUP_DIR}/db/exam_portal_${DATE}.sql \
    --verbose \
    --no-owner \
    --no-privileges

# Compress database backup
gzip ${BACKUP_DIR}/db/exam_portal_${DATE}.sql

# Media files backup
echo "Backing up media files..."
tar -czf ${BACKUP_DIR}/media/media_${DATE}.tar.gz -C /app media/

# Logs backup (optional)
echo "Backing up logs..."
tar -czf ${BACKUP_DIR}/logs/logs_${DATE}.tar.gz -C /app logs/

# Upload to S3 (if configured)
if [ ! -z "${AWS_ACCESS_KEY_ID}" ] && [ ! -z "${AWS_SECRET_ACCESS_KEY}" ] && [ ! -z "${BACKUP_S3_BUCKET}" ]; then
    echo "Uploading backups to S3..."
    aws s3 cp ${BACKUP_DIR}/db/exam_portal_${DATE}.sql.gz s3://${BACKUP_S3_BUCKET}/db/ --storage-class GLACIER_IR
    aws s3 cp ${BACKUP_DIR}/media/media_${DATE}.tar.gz s3://${BACKUP_S3_BUCKET}/media/ --storage-class GLACIER_IR
    aws s3 cp ${BACKUP_DIR}/logs/logs_${DATE}.tar.gz s3://${BACKUP_S3_BUCKET}/logs/ --storage-class GLACIER_IR
fi

# Clean up old backups
echo "Cleaning up old backups..."
find ${BACKUP_DIR}/db -name "*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR}/media -name "*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR}/logs -name "*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete

echo "Backup completed at $(date)"

# Send notification (if configured)
if [ ! -z "${BACKUP_NOTIFICATION_EMAIL}" ]; then
    echo "Backup completed successfully for exam_portal at ${DATE}" | \
    mail -s "Backup Success: exam_portal" ${BACKUP_NOTIFICATION_EMAIL}
fi