#!/bin/bash
# Export data from local SQLite database to fixtures
# This script exports all data from db.sqlite3 for migration to production PostgreSQL

set -e  # Exit on error

echo "=========================================="
echo "Exporting data from SQLite database"
echo "=========================================="

# Create backup directory
BACKUP_DIR="data_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "✓ Created backup directory: $BACKUP_DIR"

# Use python from virtual environment (already activated by running this script)
PYTHON="./venv/bin/python"

# Export Users (excluding sensitive data like passwords - they'll be re-created)
echo "Exporting users..."
$PYTHON manage.py dumpdata users.User --indent 2 --output "$BACKUP_DIR/users.json"
echo "✓ Users exported to $BACKUP_DIR/users.json"

# Export Exams
echo "Exporting exams..."
$PYTHON manage.py dumpdata exams.Exam exams.Test exams.TestAttempt exams.Organization exams.TestSection --indent 2 --output "$BACKUP_DIR/exams.json"
echo "✓ Exams exported to $BACKUP_DIR/exams.json"

# Export Questions
echo "Exporting questions..."
$PYTHON manage.py dumpdata questions.QuestionBank questions.Question questions.QuestionOption questions.TestQuestion questions.UserAnswer --indent 2 --output "$BACKUP_DIR/questions.json"
echo "✓ Questions exported to $BACKUP_DIR/questions.json"

# Export Analytics
echo "Exporting analytics..."
$PYTHON manage.py dumpdata analytics --indent 2 --output "$BACKUP_DIR/analytics.json"
echo "✓ Analytics exported to $BACKUP_DIR/analytics.json"

# Export Knowledge/LMS data
echo "Exporting knowledge base..."
$PYTHON manage.py dumpdata knowledge --indent 2 --output "$BACKUP_DIR/knowledge.json"
echo "✓ Knowledge base exported to $BACKUP_DIR/knowledge.json"

# Export PDF Extractor data (if exists)
if $PYTHON manage.py dumpdata pdf_extractor --indent 2 --output "$BACKUP_DIR/pdf_extractor.json" 2>/dev/null; then
    echo "✓ PDF Extractor data exported to $BACKUP_DIR/pdf_extractor.json"
else
    echo "⚠ PDF Extractor app not available, skipping"
fi

# Export Payments data (if exists)
if $PYTHON manage.py dumpdata payments --indent 2 --output "$BACKUP_DIR/payments.json" 2>/dev/null; then
    echo "✓ Payments data exported to $BACKUP_DIR/payments.json"
else
    echo "⚠ Payments app not available, skipping"
fi

# Create a combined file with all data
echo "Creating combined export..."
cat "$BACKUP_DIR"/*.json > "$BACKUP_DIR/all_data.json"
echo "✓ Combined export created: $BACKUP_DIR/all_data.json"

# Create a compressed archive
echo "Creating compressed archive..."
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
echo "✓ Archive created: ${BACKUP_DIR}.tar.gz"

echo ""
echo "=========================================="
echo "Export completed successfully!"
echo "=========================================="
echo "Backup directory: $BACKUP_DIR"
echo "Archive file: ${BACKUP_DIR}.tar.gz"
echo ""
echo "Next steps:"
echo "1. Upload ${BACKUP_DIR}.tar.gz to your production server"
echo "2. Run the import script on production"
echo "=========================================="
