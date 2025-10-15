#!/bin/bash
# Import data to production PostgreSQL database
# Run this script on the production server or via Dokploy exec

set -e  # Exit on error

echo "=========================================="
echo "⚠️  PRODUCTION DATA IMPORT"
echo "=========================================="
echo ""
echo "This script will import data into PostgreSQL."
echo "Make sure you have:"
echo "1. Backed up your production database"
echo "2. Uploaded the data archive to the server"
echo "3. Run migrations (python manage.py migrate)"
echo ""
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Import cancelled."
    exit 0
fi

# Extract archive (if provided as argument)
if [ -n "$1" ]; then
    echo "Extracting archive: $1"
    tar -xzf "$1"
    BACKUP_DIR=$(basename "$1" .tar.gz)
else
    # Assume data is in current directory
    BACKUP_DIR="."
fi

echo ""
echo "=========================================="
echo "Starting data import..."
echo "=========================================="

# Import in order (to respect foreign key constraints)

# 1. Import Users first (other models depend on users)
echo "Importing users..."
python manage.py loaddata "${BACKUP_DIR}/users.json"
echo "✓ Users imported"

# 2. Import Questions (independent)
echo "Importing questions..."
python manage.py loaddata "${BACKUP_DIR}/questions.json"
echo "✓ Questions imported"

# 3. Import Exams (depends on users and questions)
echo "Importing exams..."
python manage.py loaddata "${BACKUP_DIR}/exams.json"
echo "✓ Exams imported"

# 4. Import Analytics (depends on users and exams)
echo "Importing analytics..."
python manage.py loaddata "${BACKUP_DIR}/analytics.json"
echo "✓ Analytics imported"

# 5. Import Knowledge base (depends on users)
echo "Importing knowledge base..."
python manage.py loaddata "${BACKUP_DIR}/knowledge.json"
echo "✓ Knowledge base imported"

# 6. Import PDF Extractor data (if exists)
if [ -f "${BACKUP_DIR}/pdf_extractor.json" ]; then
    echo "Importing PDF extractor data..."
    python manage.py loaddata "${BACKUP_DIR}/pdf_extractor.json"
    echo "✓ PDF extractor data imported"
fi

# 7. Import Payments data (if exists)
if [ -f "${BACKUP_DIR}/payments.json" ]; then
    echo "Importing payments data..."
    python manage.py loaddata "${BACKUP_DIR}/payments.json"
    echo "✓ Payments data imported"
fi

echo ""
echo "=========================================="
echo "✅ Data import completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify data in production: python manage.py shell"
echo "2. Test the application"
echo "3. Update user passwords if needed"
echo "=========================================="
