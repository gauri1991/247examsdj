# 🔑 Dokploy External Services - Connection Credentials

**Last Updated:** 2025-10-15
**VPS IP:** 147.93.102.87
**Dokploy Dashboard:** http://147.93.102.87:3000

---

## 📊 PostgreSQL Service

### Internal Credentials (For Application Containers)

```
Service Name:       exam-portal-postgres
Internal Hostname:  resnovate247exams-examportalpostgres-hsexln
Internal Port:      5432
Database Name:      exam_portal_db
Username:          examuser
Password:          sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=
```

### Connection String (Internal)

```bash
# For Django DATABASE_URL
postgresql://examuser:sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=@resnovate247exams-examportalpostgres-hsexln:5432/exam_portal_db

# For direct psql connection
psql postgresql://examuser:sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=@resnovate247exams-examportalpostgres-hsexln:5432/exam_portal_db
```

### External Credentials (For Internet Access)

```
External Host:      147.93.102.87
External Port:      5432
Database Name:      exam_portal_db
Username:          examuser
Password:          sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=
```

### External Connection (From Your Local Machine)

```bash
# Connect from your laptop/desktop
psql postgresql://examuser:sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=@147.93.102.87:5432/exam_portal_db

# Using PgAdmin or DBeaver
Host: 147.93.102.87
Port: 5432
Database: exam_portal_db
Username: examuser
Password: sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=
```

---

## 🔴 Redis Service

### Internal Credentials (For Application Containers)

```
Service Name:       exam-portal-redis
Internal Hostname:  resnovate247exams-examportalredis-8megq1
Internal Port:      6379
Username:          default
Password:          Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=
```

### Connection String (Internal)

```bash
# For Django REDIS_URL (Cache - DB 0)
redis://default:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@resnovate247exams-examportalredis-8megq1:6379/0

# For Celery Broker (DB 1)
redis://default:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@resnovate247exams-examportalredis-8megq1:6379/1

# For Celery Result Backend (DB 1)
redis://default:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@resnovate247exams-examportalredis-8megq1:6379/1
```

### External Credentials (For Internet Access)

```
External Host:      147.93.102.87
External Port:      6379
Username:          default
Password:          Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=
```

### External Connection (From Your Local Machine)

```bash
# Connect from your laptop/desktop using redis-cli
redis-cli -h 147.93.102.87 -p 6379 -a Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=

# Or using Redis Desktop Manager / RedisInsight
Host: 147.93.102.87
Port: 6379
Username: default
Password: Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=
```

---

## ⚙️ Complete Environment Variables for Dokploy

Copy these exact values to **Dokploy Dashboard → Applications → exam-portal → Environment tab**:

```bash
# ===== CRITICAL - DJANGO CORE =====
SECRET_KEY=argh0cz2Srv!i+Ma0(+LSSdbE7lU@FC=BjxpzOsZJ^GutB01Bd
DEBUG=False
DJANGO_SETTINGS_MODULE=exam_portal.settings_production
ALLOWED_HOSTS=147.93.102.87
CSRF_TRUSTED_ORIGINS=http://147.93.102.87,https://147.93.102.87
DJANGO_LOG_LEVEL=INFO

# ===== DATABASE (EXTERNAL POSTGRESQL) =====
# IMPORTANT: Password is URL-encoded in DATABASE_URL (/ = %2F, + = %2B, = = %3D)
DATABASE_URL=postgresql://examuser:sS8liZaidpCoFOiYwy33LbdZNC4%2FJy8R3YRChd%2BeXio%3D@resnovate247exams-examportalpostgres-hsexln:5432/exam_portal_db
DB_HOST=resnovate247exams-examportalpostgres-hsexln
DB_PORT=5432
DB_USER=examuser
DB_PASSWORD=sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=
DB_NAME=exam_portal_db

# ===== REDIS (EXTERNAL REDIS) =====
# IMPORTANT: Password is URL-encoded in REDIS URLs (/ = %2F, + = %2B, = = %3D)
REDIS_URL=redis://default:Hm%2FrYtzPAgQUX%2Fw0F3FjzyjsAMxuT9hX1UNGBjPbdhY%3D@resnovate247exams-examportalredis-8megq1:6379/0
REDIS_PASSWORD=Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=
CELERY_BROKER_URL=redis://default:Hm%2FrYtzPAgQUX%2Fw0F3FjzyjsAMxuT9hX1UNGBjPbdhY%3D@resnovate247exams-examportalredis-8megq1:6379/1
CELERY_RESULT_BACKEND=redis://default:Hm%2FrYtzPAgQUX%2Fw0F3FjzyjsAMxuT9hX1UNGBjPbdhY%3D@resnovate247exams-examportalredis-8megq1:6379/1

# ===== EMAIL (UPDATE WITH YOUR CREDENTIALS) =====
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password-here
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

## 🔧 Quick Test Commands

### Test PostgreSQL Connection from Application Container

```bash
# SSH into VPS
ssh root@147.93.102.87

# Find web container
docker ps | grep web

# Test database connection
docker exec -it <WEB_CONTAINER_NAME> python manage.py dbshell

# Should get PostgreSQL prompt. Type \q to exit.
```

### Test Redis Connection from Application Container

```bash
# Test Redis connection
docker exec -it <WEB_CONTAINER_NAME> python manage.py shell

# In Python shell:
from django.core.cache import cache
cache.set('test', 'working')
print(cache.get('test'))
exit()
```

### Check Service Health in Dokploy

1. Open Dokploy Dashboard: http://147.93.102.87:3000
2. Go to **Services**
3. Verify both services show **green status** (running)
4. Check **Logs** tab for any errors

---

## 📋 Deployment Checklist

After updating these credentials:

- [ ] Copy all environment variables to Dokploy Environment tab
- [ ] Verify service names match exactly (case-sensitive!)
- [ ] Click "Redeploy" in Dokploy
- [ ] Wait for deployment to complete (green status)
- [ ] SSH into VPS and run migrations:
  ```bash
  docker exec -it <WEB_CONTAINER> python manage.py migrate
  ```
- [ ] Collect static files:
  ```bash
  docker exec -it <WEB_CONTAINER> python manage.py collectstatic --noinput
  ```
- [ ] Test database connection (see commands above)
- [ ] Test Redis connection (see commands above)
- [ ] Access application: http://147.93.102.87:8000
- [ ] Check health endpoint: http://147.93.102.87:8000/health/
- [ ] Verify admin panel: http://147.93.102.87:8000/secure-admin/

---

## 🔒 Security Notes

1. **Never commit this file to public repositories** - Contains sensitive credentials
2. **External ports (5432, 6379) are exposed** - Only for development/testing
3. **For production** - Consider:
   - Using firewall rules to restrict access
   - Disabling external ports after initial setup
   - Using private networks within Dokploy
   - Rotating passwords periodically

---

## 📞 Troubleshooting

### Connection Refused Errors

```bash
# Check if services are running
docker ps | grep postgres
docker ps | grep redis

# Check service logs in Dokploy
# Dashboard → Services → Click service → Logs tab
```

### Authentication Failed

```bash
# Verify exact credentials in Dokploy service configuration
# Ensure no extra spaces in passwords
# Verify username is correct (examuser for Postgres, default for Redis)
```

### Can't Find Service Hostname

```bash
# List all Docker networks
docker network ls

# Inspect Dokploy network
docker network inspect <DOKPLOY_NETWORK>

# Verify services are on same network
```

---

**Status:** ✅ Ready for deployment
**Created:** 2025-10-15
**Purpose:** External PostgreSQL and Redis service credentials for Dokploy deployment
