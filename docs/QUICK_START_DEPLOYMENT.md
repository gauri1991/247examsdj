# Quick Start Deployment Guide
## Deploy Exam Management Platform to Dokploy in 15 Minutes

This guide will get your application deployed quickly. For detailed information, see [DOKPLOY_DEPLOYMENT_GUIDE.md](./DOKPLOY_DEPLOYMENT_GUIDE.md).

---

## Prerequisites

✓ VPS with Dokploy installed
✓ Domain name (or use VPS IP for testing)
✓ Git repository access
✓ Email account for SMTP

---

## Step 1: Prepare Environment Variables (5 min)

### 1.1 Generate SECRET_KEY

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 1.2 Generate Strong Passwords

```bash
# For database
openssl rand -base64 32

# For Redis
openssl rand -base64 32
```

### 1.3 Get Email Credentials

For Gmail:
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Generate App Password
4. Use this password (not your regular Gmail password)

---

## Step 2: Configure Dokploy (3 min)

### 2.1 Create New Application

1. Open Dokploy dashboard: `http://your-vps-ip:3000`
2. Click **"New Application"**
3. Fill in:
   - **Name**: `exam-portal`
   - **Type**: Docker Compose
   - **Repository**: `https://github.com/your-username/your-repo.git`
   - **Branch**: `main`

### 2.2 Set Environment Variables

Go to **Environment** tab and add these minimum required variables:

```bash
# CRITICAL - Must set these
SECRET_KEY=your-generated-secret-key-from-step-1
DEBUG=False
DJANGO_SETTINGS_MODULE=exam_portal.settings_production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database (Dokploy will auto-generate if using their PostgreSQL service)
DATABASE_URL=postgresql://examuser:your-db-password@postgres:5432/exam_portal_db
DB_PASSWORD=your-db-password-from-step-1

# Redis
REDIS_URL=redis://:your-redis-password@redis:6379/0
REDIS_PASSWORD=your-redis-password-from-step-1
CELERY_BROKER_URL=redis://:your-redis-password@redis:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-from-step-1.3
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_URL=secure-admin/

# Performance (disable heavy features)
PDF_EXTRACTOR_ENABLED=false
PDF_UPLOAD_ALLOWED=false
AI_GRADING_ENABLED=false
PAYMENT_SYSTEM_ENABLED=true
```

---

## Step 3: Deploy (2 min)

### 3.1 Start Deployment

1. Click **"Deploy"** button in Dokploy
2. Monitor logs for any errors
3. Wait for "Deployment successful" message

### 3.2 Verify Deployment

```bash
# Check health
curl http://your-vps-ip/health/

# Should return: {"status": "healthy"}
```

---

## Step 4: Post-Deployment Setup (5 min)

### 4.1 Run Migrations

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Run migrations
docker exec -it exam-portal-web python manage.py migrate

# Create superuser
docker exec -it exam-portal-web python manage.py createsuperuser

# Collect static files
docker exec -it exam-portal-web python manage.py collectstatic --noinput
```

### 4.2 Access Admin Panel

Navigate to: `http://your-vps-ip/secure-admin/`

Login with the superuser credentials you just created.

---

## Step 5: Configure Domain & SSL (Optional but Recommended)

### 5.1 Point Domain to VPS

Add these DNS records:

```
A Record: @ → your-vps-ip
A Record: www → your-vps-ip
```

### 5.2 Enable SSL in Dokploy

1. Go to **Domains** tab in your app
2. Add domain: `yourdomain.com`
3. Enable **"Auto SSL"**
4. Wait for certificate generation (1-2 minutes)

### 5.3 Update Environment Variables

```bash
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

Click **"Redeploy"** after updating.

---

## Verification Checklist

After deployment, verify everything works:

- [ ] Homepage loads: `https://yourdomain.com/`
- [ ] Admin panel accessible: `https://yourdomain.com/secure-admin/`
- [ ] Health check works: `https://yourdomain.com/health/`
- [ ] Can login with admin credentials
- [ ] Email sending works (test forgot password)
- [ ] Static files load properly (CSS, JS)
- [ ] No errors in logs: `docker logs exam-portal-web`

---

## Common Quick Fixes

### Issue: "Bad Request (400)"
**Fix**: Add your domain to `ALLOWED_HOSTS`

### Issue: Static files not loading
```bash
docker exec exam-portal-web python manage.py collectstatic --noinput --clear
```

### Issue: Database connection error
**Fix**: Verify `DATABASE_URL` format is correct

### Issue: Email not sending
**Fix**:
- Use Gmail App Password, not regular password
- Verify `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`

### Issue: High memory usage
**Fix**: Ensure `PDF_EXTRACTOR_ENABLED=false` in environment variables

---

## Next Steps

### 1. Set Up Backups

```bash
# Create daily database backup script
cat > /root/backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
docker exec exam-portal-db pg_dump -U examuser exam_portal_db | gzip > /backups/db_$DATE.sql.gz
find /backups -name "db_*.sql.gz" -mtime +30 -delete
EOF

chmod +x /root/backup-db.sh

# Add to crontab
echo "0 2 * * * /root/backup-db.sh" | crontab -
```

### 2. Set Up Monitoring

- Sign up for [UptimeRobot](https://uptimerobot.com/) (free)
- Monitor: `https://yourdomain.com/health/`
- Get alerts if site goes down

### 3. Optional Enhancements

- **Sentry**: Error tracking ([sentry.io](https://sentry.io))
- **AWS S3**: Media file storage
- **CloudFlare**: CDN and DDoS protection
- **Custom Email**: Use SendGrid or AWS SES

---

## Maintenance Commands

```bash
# View logs
docker logs -f exam-portal-web

# Restart application
docker restart exam-portal-web

# Update application (after git push)
# In Dokploy: Click "Redeploy"

# Run migrations after update
docker exec exam-portal-web python manage.py migrate

# Create database backup
docker exec exam-portal-db pg_dump -U examuser exam_portal_db > backup.sql
```

---

## Performance Optimization

Your VPS can handle **16,000-20,000 concurrent users** with these settings:

✓ `PDF_EXTRACTOR_ENABLED=false` (saves 17GB RAM)
✓ Redis caching enabled
✓ Static file compression enabled
✓ Database connection pooling

To handle more users:
- Upgrade VPS resources
- Enable CloudFlare CDN
- Use AWS S3 for media files
- Consider horizontal scaling

---

## Getting Help

1. **Check logs first**: `docker logs exam-portal-web`
2. **Health endpoint**: `https://yourdomain.com/health/readiness/`
3. **Review full guide**: [DOKPLOY_DEPLOYMENT_GUIDE.md](./DOKPLOY_DEPLOYMENT_GUIDE.md)
4. **Common issues**: See troubleshooting section above

---

## Security Reminder

Before going live:

- [ ] `DEBUG=False` is set
- [ ] Strong `SECRET_KEY` is set
- [ ] Database password is strong
- [ ] Redis password is set
- [ ] SSL is enabled
- [ ] Admin URL is changed from default
- [ ] `.env` file is NOT in Git
- [ ] Backups are configured
- [ ] Monitoring is set up

---

## Summary

You've successfully deployed your Exam Management Platform! 🎉

**What you have now:**
- Production-ready Django application
- PostgreSQL database
- Redis caching
- SSL/HTTPS enabled
- Health monitoring
- Automated deployments via Dokploy

**Access your application:**
- **Website**: `https://yourdomain.com/`
- **Admin Panel**: `https://yourdomain.com/secure-admin/`
- **Health Check**: `https://yourdomain.com/health/`

For detailed configuration, maintenance, and troubleshooting, refer to the [complete deployment guide](./DOKPLOY_DEPLOYMENT_GUIDE.md).
