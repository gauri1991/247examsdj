# 🔧 Configure External PostgreSQL and Redis - Step by Step

You've deployed PostgreSQL and Redis separately in Dokploy. Here's what you need to do next:

---

## ✅ Step 1: Your Actual Service Details (CONFIRMED)

### 1.1 PostgreSQL Connection Details ✅

**Your Actual Configuration:**
```
Service Name:       exam-portal-postgres
Internal Hostname:  resnovate247exams-examportalpostgres-hsexln
Port:              5432
Database Name:     exam_portal_db
Username:          examuser
Password:          sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=
```

**Connection String:**
```
postgresql://examuser:sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=@resnovate247exams-examportalpostgres-hsexln:5432/exam_portal_db
```

### 1.2 Redis Connection Details ✅

**Your Actual Configuration:**
```
Service Name:       exam-portal-redis
Internal Hostname:  resnovate247exams-examportalredis-8megq1
Port:              6379
Username:          default
Password:          Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=
```

**Connection String:**
```
redis://default:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@resnovate247exams-examportalredis-8megq1:6379/0
```

---

## Step 2: Update Environment Variables in Dokploy

### 2.1 Navigate to Environment Settings

1. **Dokploy Dashboard** → **Applications** → Your `exam-portal` app
2. Click on **Environment** tab
3. You'll see all your current environment variables

### 2.2 Update Database Connection Variables ✅

**Use these EXACT values (already configured for your services):**

```bash
# DATABASE CONNECTION - COPY THESE EXACT VALUES TO DOKPLOY
DATABASE_URL=postgresql://examuser:sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=@resnovate247exams-examportalpostgres-hsexln:5432/exam_portal_db
DB_HOST=resnovate247exams-examportalpostgres-hsexln
DB_PORT=5432
DB_USER=examuser
DB_PASSWORD=sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=
DB_NAME=exam_portal_db
```

### 2.3 Update Redis Connection Variables ✅

**Use these EXACT values (already configured for your services):**

```bash
# REDIS CONNECTION - COPY THESE EXACT VALUES TO DOKPLOY
REDIS_URL=redis://default:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@resnovate247exams-examportalredis-8megq1:6379/0
REDIS_PASSWORD=Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=
CELERY_BROKER_URL=redis://default:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@resnovate247exams-examportalredis-8megq1:6379/1
CELERY_RESULT_BACKEND=redis://default:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@resnovate247exams-examportalredis-8megq1:6379/1
```

**IMPORTANT:** Notice the Redis URLs include `default:` username - this is required!

### 2.4 Keep All Other Variables

**DO NOT REMOVE** these existing variables:

```bash
# CRITICAL - Keep these unchanged
SECRET_KEY=argh0cz2Srv!i+Ma0(+LSSdbE7lU@FC=BjxpzOsZJ^GutB01Bd
DEBUG=False
DJANGO_SETTINGS_MODULE=exam_portal.settings_production
ALLOWED_HOSTS=147.93.102.87
CSRF_TRUSTED_ORIGINS=http://147.93.102.87,https://147.93.102.87
DJANGO_LOG_LEVEL=INFO

# EMAIL - Keep these
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# ADMIN - Keep these
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_URL=secure-admin/

# FEATURES - Keep these
PDF_EXTRACTOR_ENABLED=false
PDF_UPLOAD_ALLOWED=false
AI_GRADING_ENABLED=false
PAYMENT_SYSTEM_ENABLED=true
ADVANCED_ANALYTICS_ENABLED=true
```

---

## Step 3: Migrate Existing Data (IMPORTANT!)

If you had data in the bundled database, you need to migrate it:

### 3.1 Export Data from Old Database

**SSH into your VPS:**
```bash
ssh root@147.93.102.87
```

**Export existing data:**
```bash
# Find the old database container (if still running)
docker ps -a | grep db

# Export data
docker exec resnovate247exams-examportal-p6hk1u-db-1 pg_dump -U examuser exam_portal > /tmp/exam_portal_backup.sql

# Verify backup file
ls -lh /tmp/exam_portal_backup.sql
```

### 3.2 Import Data to New Database

**Find your new PostgreSQL container:**
```bash
# List all containers to find Dokploy's PostgreSQL
docker ps | grep postgres
```

**Import data:**
```bash
# Replace <NEW_POSTGRES_CONTAINER> with actual container name
docker exec -i <NEW_POSTGRES_CONTAINER> psql -U examuser -d exam_portal_db < /tmp/exam_portal_backup.sql
```

**Example:**
```bash
docker exec -i postgres-abc123 psql -U examuser -d exam_portal_db < /tmp/exam_portal_backup.sql
```

### 3.3 Verify Data Migration

```bash
# Connect to new database
docker exec -it <NEW_POSTGRES_CONTAINER> psql -U examuser -d exam_portal_db

# Check tables
\dt

# Check data (example)
SELECT COUNT(*) FROM auth_user;

# Exit
\q
```

---

## Step 4: Redeploy Application

### 4.1 In Dokploy Dashboard

1. Go to your **exam-portal** application
2. Click **"Redeploy"** button
3. Monitor the deployment logs

### 4.2 Watch for Success Messages

You should see:
```
✅ Docker Compose Deployed
✅ Container web Running
✅ Container celery Running
✅ Container celery-beat Running
```

**Note:** You will NOT see `db` and `redis` containers anymore - they're separate services now!

---

## Step 5: Run Migrations and Verify

### 5.1 SSH into VPS

```bash
ssh root@147.93.102.87
```

### 5.2 Run Django Migrations

```bash
# Find your web container
docker ps | grep web

# Run migrations
docker exec -it resnovate247exams-examportal-p6hk1u-web-1 python manage.py migrate
```

### 5.3 Create Superuser (if needed)

```bash
docker exec -it resnovate247exams-examportal-p6hk1u-web-1 python manage.py createsuperuser
```

### 5.4 Collect Static Files

```bash
docker exec -it resnovate247exams-examportal-p6hk1u-web-1 python manage.py collectstatic --noinput
```

---

## Step 6: Verify Connections

### 6.1 Test PostgreSQL Connection

```bash
# From your web container
docker exec -it resnovate247exams-examportal-p6hk1u-web-1 python manage.py dbshell
```

You should get a PostgreSQL prompt. Type `\q` to exit.

### 6.2 Test Redis Connection

```bash
# Test from web container
docker exec -it resnovate247exams-examportal-p6hk1u-web-1 python manage.py shell

# In Python shell:
>>> from django.core.cache import cache
>>> cache.set('test', 'working')
>>> cache.get('test')
'working'
>>> exit()
```

### 6.3 Check Application Health

```bash
curl http://147.93.102.87:8000/health/
```

Expected response:
```json
{"status": "healthy"}
```

### 6.4 Check Application Logs

```bash
# Web application logs
docker logs -f resnovate247exams-examportal-p6hk1u-web-1

# Look for successful connections:
# - "Connecting to database..."
# - "Redis connection successful..."
```

---

## 📋 Complete Environment Variables - COPY TO DOKPLOY ✅

Here are your **exact environment variables** - Copy ALL of these to Dokploy Environment tab:

```bash
# ===== CRITICAL - DJANGO CORE =====
SECRET_KEY=argh0cz2Srv!i+Ma0(+LSSdbE7lU@FC=BjxpzOsZJ^GutB01Bd
DEBUG=False
DJANGO_SETTINGS_MODULE=exam_portal.settings_production
ALLOWED_HOSTS=147.93.102.87
CSRF_TRUSTED_ORIGINS=http://147.93.102.87,https://147.93.102.87
DJANGO_LOG_LEVEL=INFO

# ===== DATABASE (EXTERNAL POSTGRESQL) =====
DATABASE_URL=postgresql://examuser:sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=@resnovate247exams-examportalpostgres-hsexln:5432/exam_portal_db
DB_HOST=resnovate247exams-examportalpostgres-hsexln
DB_PORT=5432
DB_USER=examuser
DB_PASSWORD=sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=
DB_NAME=exam_portal_db

# ===== REDIS (EXTERNAL REDIS) =====
REDIS_URL=redis://default:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@resnovate247exams-examportalredis-8megq1:6379/0
REDIS_PASSWORD=Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=
CELERY_BROKER_URL=redis://default:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@resnovate247exams-examportalredis-8megq1:6379/1
CELERY_RESULT_BACKEND=redis://default:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@resnovate247exams-examportalredis-8megq1:6379/1

# ===== EMAIL =====
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SERVER_EMAIL=server@yourdomain.com

# ===== ADMIN =====
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_URL=secure-admin/

# ===== PERFORMANCE & FEATURES =====
PDF_EXTRACTOR_ENABLED=false
PDF_UPLOAD_ALLOWED=false
AI_GRADING_ENABLED=false
PROCTORING_ENABLED=false
ADVANCED_ANALYTICS_ENABLED=true
PAYMENT_SYSTEM_ENABLED=true
BULK_OPERATIONS_ENABLED=true
EXAM_TEMPLATES_ENABLED=true
COLLABORATIVE_EDITING=false
```

---

## 🔍 Troubleshooting

### Issue: "Connection refused" errors

**Cause:** Wrong service name or port

**Solution:**
1. Double-check service names in Dokploy
2. Verify services are running (green status)
3. Check if services are in same network

### Issue: "Authentication failed"

**Cause:** Wrong credentials

**Solution:**
1. Verify password matches in both service and environment variables
2. Check username is correct
3. Ensure database name exists

### Issue: "No such table" errors

**Cause:** Migrations not run or data not migrated

**Solution:**
1. Run migrations: `docker exec -it web-container python manage.py migrate`
2. Check if data was imported correctly

### Issue: Old containers still running

**Solution:**
```bash
# Stop and remove old containers
docker stop resnovate247exams-examportal-p6hk1u-db-1
docker rm resnovate247exams-examportal-p6hk1u-db-1
docker stop resnovate247exams-examportal-p6hk1u-redis-1
docker rm resnovate247exams-examportal-p6hk1u-redis-1
```

---

## ✅ Verification Checklist

After completing all steps, verify:

- [ ] PostgreSQL service is running in Dokploy
- [ ] Redis service is running in Dokploy
- [ ] Environment variables updated with correct service names
- [ ] Data migrated from old database (if applicable)
- [ ] Application redeployed successfully
- [ ] Migrations completed without errors
- [ ] Can connect to database from application
- [ ] Can connect to Redis from application
- [ ] Health endpoint returns healthy status
- [ ] Admin panel is accessible
- [ ] Old db/redis containers removed (optional cleanup)

---

## 🎉 Success!

Once all checks pass, your application is now using **external PostgreSQL and Redis services**!

### Benefits You Now Have:

✅ **Independent Database Management** - Restart app without affecting database
✅ **Automated Backups** - Dokploy handles backup scheduling
✅ **Better Monitoring** - View database metrics in Dokploy
✅ **Resource Isolation** - Database has dedicated resources
✅ **Easier Scaling** - Scale database independently from app
✅ **Shared Access** - Other apps can use same database

---

## 📞 Need Help?

If you encounter issues:

1. **Check service names** are correct in environment variables
2. **Verify services are running** in Dokploy dashboard (green status)
3. **Check application logs**: `docker logs -f web-container`
4. **Test connections manually** using commands in Step 6

---

**Last Updated:** After switching to external services
**Status:** Ready for deployment ✅
