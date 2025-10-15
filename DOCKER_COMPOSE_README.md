# Docker Compose Configuration - Simple Explanation

## Current Setup: External PostgreSQL & Redis

Your application uses **ONE** docker-compose.yml file that connects to external Dokploy services.

---

## What's Running Where

### In Your Application (docker-compose.yml):
- `web` - Django application (port 8000)
- `celery` - Background task worker
- `celery-beat` - Scheduled task scheduler

### In Dokploy Services (Separate):
- `exam-portal-postgres` - PostgreSQL database
- `exam-portal-redis` - Redis cache

---

## Connection Details

Your application connects to external services using these hostnames:

**PostgreSQL:**
```
Host: resnovate247exams-examportalpostgres-hsexln
Port: 5432
Database: exam_portal_db
User: examuser
```

**Redis:**
```
Host: resnovate247exams-examportalredis-8megq1
Port: 6379
User: default
```

These are configured in Dokploy Environment variables.

---

## ✅ What This Means

1. **Restarting your app does NOT restart the database**
2. **Database and Redis are managed separately in Dokploy**
3. **You can backup/restore database independently**
4. **No db or redis containers in your app's docker-compose**

---

## 🚫 What You Should NOT Do

- ❌ Don't look for `db` or `redis` containers - they're external services
- ❌ Don't try to use different docker-compose files - only one exists
- ❌ Don't change the hostnames - they're your actual Dokploy service names

---

## ✅ How to Deploy

1. Update environment variables in Dokploy (if needed)
2. Push code to Git: `git push origin master`
3. Dokploy automatically rebuilds and redeploys
4. Check logs in Dokploy dashboard

That's it!

---

## 📚 Reference Files

- `docker-compose.yml` - The ONLY compose file (for external services)
- `DOKPLOY_EXTERNAL_SERVICES_CREDENTIALS.md` - All connection details
- `.env.production.generated` - Local environment file (not in Git)

---

**Status:** ✅ Everything is configured correctly
**Last Updated:** 2025-10-15
