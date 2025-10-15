# Data Migration Guide: SQLite to PostgreSQL

Complete guide for migrating your local SQLite database to production PostgreSQL on Dokploy.

## ⚠️ Important Notes

- **Backup First**: Always backup your production database before importing
- **User Passwords**: Passwords are hashed and will be migrated correctly
- **IDs Preserved**: UUIDs will be preserved, maintaining all relationships
- **Downtime**: Consider putting site in maintenance mode during migration

## Prerequisites

- [x] Production site deployed and accessible
- [x] PostgreSQL database running in Dokploy
- [x] SSH or exec access to production container
- [x] Local SQLite database (`db.sqlite3`) with data

---

## Step 1: Export Data from Local SQLite

### Option A: Using the Export Script (Recommended)

```bash
# Make the script executable
chmod +x scripts/export_data.sh

# Run the export
./scripts/export_data.sh
```

This will create:
- `data_backup_YYYYMMDD_HHMMSS/` directory with JSON fixtures
- `data_backup_YYYYMMDD_HHMMSS.tar.gz` compressed archive

### Option B: Manual Export

```bash
# Activate virtual environment
source venv/bin/activate

# Create backup directory
mkdir -p data_backup
cd data_backup

# Export each app's data
python ../manage.py dumpdata users.User --indent 2 > users.json
python ../manage.py dumpdata exams --indent 2 > exams.json
python ../manage.py dumpdata questions --indent 2 > questions.json
python ../manage.py dumpdata analytics --indent 2 > analytics.json
python ../manage.py dumpdata knowledge --indent 2 > knowledge.json

# Optional: PDF Extractor and Payments
python ../manage.py dumpdata pdf_extractor --indent 2 > pdf_extractor.json
python ../manage.py dumpdata payments --indent 2 > payments.json

# Create archive
cd ..
tar -czf data_backup.tar.gz data_backup/
```

---

## Step 2: Upload Data to Production

### Method 1: Via Dokploy File Upload

1. Go to your Dokploy dashboard
2. Select your application
3. Navigate to "Files" or "Volumes"
4. Upload `data_backup_YYYYMMDD_HHMMSS.tar.gz`

### Method 2: Via SCP (if SSH access available)

```bash
scp data_backup_*.tar.gz user@your-server:/path/to/app/
```

### Method 3: Via Docker Container

```bash
# Find your container ID
docker ps | grep exam

# Copy files to container
docker cp data_backup_*.tar.gz <container_id>:/app/
```

---

## Step 3: Backup Production Database (CRITICAL!)

Before importing, **always backup** your production database:

### Via Dokploy PostgreSQL Backup

```bash
# In Dokploy, go to PostgreSQL service
# Click "Backup" to create a snapshot
```

### Via pg_dump (Manual)

```bash
# Inside the PostgreSQL container
docker exec -it <postgres_container> pg_dump -U examuser exam_portal_db > backup_$(date +%Y%m%d).sql
```

---

## Step 4: Import Data to Production

### Method 1: Using the Import Script

```bash
# SSH into production or use Dokploy exec
docker exec -it <app_container> /bin/bash

# Navigate to app directory
cd /app

# Make script executable
chmod +x scripts/import_data_production.sh

# Run the import
./scripts/import_data_production.sh data_backup_*.tar.gz
```

### Method 2: Manual Import

```bash
# SSH into production container
docker exec -it <app_container> /bin/bash

# Extract archive
tar -xzf data_backup_*.tar.gz
cd data_backup_*/

# Import in order (respecting foreign keys)
python manage.py loaddata users.json
python manage.py loaddata questions.json
python manage.py loaddata exams.json
python manage.py loaddata analytics.json
python manage.py loaddata knowledge.json
python manage.py loaddata pdf_extractor.json  # if exists
python manage.py loaddata payments.json       # if exists
```

---

## Step 5: Verify Data Import

```bash
# Enter Django shell in production
python manage.py shell

# Check data counts
from django.contrib.auth import get_user_model
from exams.models import Exam, Test
from questions.models import QuestionBank, Question

User = get_user_model()
print(f'Users: {User.objects.count()}')
print(f'Exams: {Exam.objects.count()}')
print(f'Tests: {Test.objects.count()}')
print(f'Question Banks: {QuestionBank.objects.count()}')
print(f'Questions: {Question.objects.count()}')
```

---

## Step 6: Post-Import Tasks

### 1. Reset Admin Password (if needed)

```bash
python manage.py changepassword admin
```

### 2. Clear Cache

```bash
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

### 3. Restart Application

```bash
# In Dokploy
# Click "Restart" on your application
```

### 4. Test the Site

- ✅ Login with existing users
- ✅ Verify exams are visible
- ✅ Check question banks
- ✅ Test taking exams
- ✅ Verify analytics data

---

## Troubleshooting

### Issue: "Duplicate key value violates unique constraint"

**Solution**: Clear existing data first

```bash
# WARNING: This deletes all data!
python manage.py flush --no-input
python manage.py migrate
# Then re-run import
```

### Issue: "Foreign key constraint fails"

**Solution**: Import in correct order (users → questions → exams)

```bash
# Use the import script which handles order correctly
./scripts/import_data_production.sh
```

### Issue: "Permission denied"

**Solution**: Check file permissions

```bash
chmod +x scripts/*.sh
chmod 644 data_backup_*/*.json
```

### Issue: Users can't login after import

**Reason**: Password hashes are preserved but users might be using old passwords

**Solution**:
1. Users should use "Forgot Password" to reset
2. Or manually reset via admin:
   ```bash
   python manage.py changepassword <username>
   ```

---

## Alternative: Direct Database Migration

If you have direct database access, you can use pgloader:

```bash
# Install pgloader
sudo apt-get install pgloader

# Create migration config
cat > migration.load << EOF
LOAD DATABASE
     FROM sqlite:///path/to/db.sqlite3
     INTO postgresql://examuser:password@host:5432/exam_portal_db

WITH data only,
     create tables,
     include drop,
     reset sequences;
EOF

# Run migration
pgloader migration.load
```

---

## Quick Reference Commands

### Export from Local
```bash
./scripts/export_data.sh
```

### Upload to Production
```bash
scp data_backup_*.tar.gz user@server:/app/
```

### Import to Production
```bash
docker exec -it <container> /bin/bash
./scripts/import_data_production.sh data_backup_*.tar.gz
```

### Verify
```bash
python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.count())"
```

---

## Safety Checklist

Before migration:
- [ ] Backup production database
- [ ] Test export locally
- [ ] Verify export file integrity
- [ ] Plan maintenance window
- [ ] Notify users (if live site)

After migration:
- [ ] Verify data counts
- [ ] Test user login
- [ ] Test exam taking
- [ ] Check analytics
- [ ] Monitor error logs
- [ ] Keep backup for 7 days

---

## Need Help?

If you encounter issues:
1. Check Django error logs: `docker logs <container_id>`
2. Check PostgreSQL logs: `docker logs <postgres_container>`
3. Restore from backup if needed
4. Contact support with error messages

---

**Important**: Keep your SQLite database backup until you verify everything works in production!
