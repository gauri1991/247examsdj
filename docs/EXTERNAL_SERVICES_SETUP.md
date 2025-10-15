# External PostgreSQL and Redis Setup for Dokploy

This guide explains how to set up PostgreSQL and Redis as **separate services** in Dokploy instead of bundling them in docker-compose.yml.

---

## 🎯 Why Use External Services?

### Benefits:
- ✅ **Independent Management**: Upgrade/restart database without touching app
- ✅ **Better Backups**: Dokploy handles automated backups
- ✅ **Easy Monitoring**: View database metrics in Dokploy dashboard
- ✅ **Resource Isolation**: Database gets dedicated resources
- ✅ **Shared Access**: Multiple apps can use same database
- ✅ **Easier Scaling**: Scale database independently
- ✅ **Better Performance**: Optimized resource allocation

### When to Use Bundled Services (Current Setup):
- ✅ Simple deployment (all in one)
- ✅ Development/testing environments
- ✅ Small applications
- ✅ When you want everything together

---

## 📋 Setup Methods

You have **3 options**:

### Option 1: Keep Current Setup (EASIEST - Currently Working)
**What you have now**: PostgreSQL and Redis bundled in docker-compose.yml
**Status**: ✅ Already working!
**Recommendation**: Keep this unless you need advanced features

### Option 2: Use Dokploy's Built-in Services (RECOMMENDED for Production)
**What it is**: Dokploy creates and manages separate database containers
**Best for**: Production environments, multiple apps
**Setup time**: 5-10 minutes

### Option 3: Use External Database Servers (ADVANCED)
**What it is**: Managed database services (AWS RDS, DigitalOcean, etc.)
**Best for**: High-traffic production, critical applications
**Setup time**: 15-30 minutes

---

## 🚀 Option 2: Setup with Dokploy Services (Step-by-Step)

### Step 1: Create PostgreSQL Service in Dokploy

1. **Open Dokploy Dashboard**
   ```
   http://147.93.102.87:3000
   ```

2. **Go to Services Section**
   - Click **"Services"** in left sidebar
   - Click **"Create Service"** button

3. **Select PostgreSQL**
   - Service Type: **PostgreSQL**
   - Fill in details:
     ```
     Service Name: exam-portal-postgres
     Version: 15 (or latest)
     Database Name: exam_portal_db
     Username: examuser
     Password: sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=
     ```
   - Click **"Create"**

4. **Configure Resources** (Optional)
   - Memory: 512MB - 2GB (based on your VPS)
   - Storage: 10GB - 50GB
   - Enable automatic backups

5. **Wait for Service to Start**
   - Status will show "Running"
   - Note the **connection details**

### Step 2: Create Redis Service in Dokploy

1. **In Services Section**
   - Click **"Create Service"** again

2. **Select Redis**
   - Service Type: **Redis**
   - Fill in details:
     ```
     Service Name: exam-portal-redis
     Version: 7 (or latest)
     Password: Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=
     Max Memory: 256MB
     Eviction Policy: allkeys-lru
     ```
   - Click **"Create"**

3. **Wait for Service to Start**
   - Status will show "Running"
   - Note the **connection details**

### Step 3: Get Connection Strings

Dokploy will provide connection strings like:

**PostgreSQL:**
```
Host: exam-portal-postgres (or internal IP)
Port: 5432
URL: postgresql://examuser:sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=@exam-portal-postgres:5432/exam_portal_db
```

**Redis:**
```
Host: exam-portal-redis (or internal IP)
Port: 6379
URL: redis://:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@exam-portal-redis:6379/0
```

### Step 4: Switch to External Services Docker Compose

**Option A: Rename Files (Recommended)**
```bash
# Backup current docker-compose.yml
mv docker-compose.yml docker-compose.bundled.yml

# Use the external services version
mv docker-compose.external-services.yml docker-compose.yml

# Commit changes
git add docker-compose.yml docker-compose.bundled.yml
git commit -m "Switch to external PostgreSQL and Redis services"
git push origin master
```

**Option B: Modify Current File**
Remove `db` and `redis` services from your current docker-compose.yml and remove network dependencies.

### Step 5: Update Environment Variables in Dokploy

In Dokploy Dashboard → Your App → **Environment** tab:

Update these variables with the **external service connection strings**:

```bash
# PostgreSQL (use Dokploy service connection)
DATABASE_URL=postgresql://examuser:sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=@exam-portal-postgres:5432/exam_portal_db
DB_HOST=exam-portal-postgres
DB_PORT=5432
DB_USER=examuser
DB_PASSWORD=sS8liZaidpCoFOiYwy33LbdZNC4/Jy8R3YRChd+eXio=
DB_NAME=exam_portal_db

# Redis (use Dokploy service connection)
REDIS_URL=redis://:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@exam-portal-redis:6379/0
REDIS_PASSWORD=Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=
CELERY_BROKER_URL=redis://:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@exam-portal-redis:6379/1
CELERY_RESULT_BACKEND=redis://:Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=@exam-portal-redis:6379/1
```

**Important**: Replace `exam-portal-postgres` and `exam-portal-redis` with actual service names from Dokploy.

### Step 6: Redeploy Application

1. In Dokploy Dashboard → Your App
2. Click **"Redeploy"**
3. Monitor deployment logs

### Step 7: Run Migrations

```bash
ssh root@147.93.102.87

# Run migrations
docker exec -it resnovate247exams-examportal-p6hk1u-web-1 python manage.py migrate

# Create superuser
docker exec -it resnovate247exams-examportal-p6hk1u-web-1 python manage.py createsuperuser
```

---

## 🔍 Verify Connection

### Test PostgreSQL Connection
```bash
# From VPS
docker exec -it <dokploy-postgres-container> psql -U examuser -d exam_portal_db -c "SELECT 1;"
```

### Test Redis Connection
```bash
# From VPS
docker exec -it <dokploy-redis-container> redis-cli -a "Hm/rYtzPAgQUX/w0F3FjzyjsAMxuT9hX1UNGBjPbdhY=" ping
```

### Test from Application
```bash
# Check logs for successful connections
docker logs resnovate247exams-examportal-p6hk1u-web-1
```

---

## 🔄 Comparison: Bundled vs External

| Feature | Bundled (Current) | External (Dokploy) | External (Managed) |
|---------|-------------------|--------------------|--------------------|
| **Setup Complexity** | ⭐ Easy | ⭐⭐ Medium | ⭐⭐⭐ Complex |
| **Deployment Speed** | ⭐⭐⭐ Fast | ⭐⭐ Medium | ⭐ Slower |
| **Backups** | Manual | Automatic | Automatic |
| **Monitoring** | Basic | Good | Excellent |
| **Scalability** | Limited | Good | Excellent |
| **Cost** | Included | Included | Extra cost |
| **Independence** | ❌ Coupled | ✅ Separate | ✅ Separate |
| **Best For** | Development | Production | Enterprise |

---

## 🎯 Recommendation

### Keep Current Setup (Bundled) If:
- ✅ It's working fine (which it is!)
- ✅ Single application deployment
- ✅ Small to medium traffic (<10k users)
- ✅ You want simplicity

### Switch to External If:
- 🎯 Multiple applications need same database
- 🎯 You want better backup management
- 🎯 You need to scale database independently
- 🎯 High traffic (>20k concurrent users)
- 🎯 You want to monitor database separately

---

## 📊 Current Status

**Your Current Setup:**
- PostgreSQL: ✅ Bundled in docker-compose.yml (Working)
- Redis: ✅ Bundled in docker-compose.yml (Working)
- Status: ✅ Deployed and healthy

**No immediate need to change unless you want the benefits listed above.**

---

## 🔧 Rollback (If Needed)

If you switch and want to go back:

```bash
# Restore original docker-compose.yml
mv docker-compose.bundled.yml docker-compose.yml

# Restore original environment variables
# (pointing to 'db' and 'redis' instead of external services)

# Commit and push
git add docker-compose.yml
git commit -m "Rollback to bundled database services"
git push origin master

# Redeploy in Dokploy
```

---

## 🆘 Troubleshooting

### Connection Refused
- **Check service names** match in environment variables
- **Verify services are running** in Dokploy dashboard
- **Check network configuration** (services in same network)

### Authentication Failed
- **Verify passwords** match in both service and app
- **Check username** is correct
- **Ensure DATABASE_URL** format is correct

### Data Loss After Switch
- **Backup before switching!**
- **Export data** from bundled database first:
  ```bash
  docker exec resnovate247exams-examportal-p6hk1u-db-1 pg_dump -U examuser exam_portal > backup.sql
  ```
- **Import to new database**:
  ```bash
  docker exec -i <new-postgres-container> psql -U examuser exam_portal_db < backup.sql
  ```

---

## 📚 Additional Resources

- [Dokploy Services Documentation](https://docs.dokploy.com/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Redis Docker Hub](https://hub.docker.com/_/redis)
- [Django Database Configuration](https://docs.djangoproject.com/en/4.2/ref/databases/)

---

## 💡 Summary

**Current Status**: ✅ Your bundled setup is working perfectly!

**Do you need to change?**
- **No, not required** - your current setup is production-ready
- **Optional** - if you want better management, monitoring, and scalability

**If you decide to switch:**
1. Use `docker-compose.external-services.yml`
2. Create services in Dokploy
3. Update environment variables
4. Redeploy

**If you're happy with current setup:**
- Keep using it! It's working great! ✅
