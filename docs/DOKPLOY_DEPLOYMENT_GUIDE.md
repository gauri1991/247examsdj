# Dokploy Deployment Guide - Exam Management Platform

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Initial Setup](#initial-setup)
4. [Dokploy Configuration](#dokploy-configuration)
5. [Environment Variables Setup](#environment-variables-setup)
6. [Database Setup](#database-setup)
7. [Domain and SSL Configuration](#domain-and-ssl-configuration)
8. [Deployment Process](#deployment-process)
9. [Post-Deployment Tasks](#post-deployment-tasks)
10. [Monitoring and Maintenance](#monitoring-and-maintenance)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Server Requirements (hPanel KVM 2 VPS)
- **OS**: Ubuntu 20.04 LTS or newer
- **RAM**: Minimum 4GB (8GB+ recommended)
- **CPU**: 2+ cores
- **Storage**: 40GB+ SSD
- **Dokploy**: Installed and running

### Local Requirements
- Git installed
- SSH access to VPS
- Domain name (for production)
- Email account for SMTP (Gmail, SendGrid, etc.)

---

## Pre-Deployment Checklist

### 1. Code Preparation
- [ ] All code is committed to Git repository
- [ ] Tests are passing
- [ ] No sensitive data in codebase
- [ ] `.gitignore` is properly configured
- [ ] Requirements files are up to date

### 2. External Services
- [ ] Domain name registered and DNS configured
- [ ] Email SMTP credentials ready
- [ ] PostgreSQL database credentials (or use Dokploy's built-in)
- [ ] Redis instance available (or use Dokploy's built-in)
- [ ] (Optional) AWS S3 bucket for media files
- [ ] (Optional) Sentry account for error tracking

### 3. Security
- [ ] Strong SECRET_KEY generated
- [ ] Database passwords are strong and unique
- [ ] Redis password set
- [ ] SSH keys configured for Git access
- [ ] Admin credentials prepared

---

## Initial Setup

### 1. Access Your VPS

```bash
ssh root@your-vps-ip
```

### 2. Verify Dokploy Installation

```bash
# Check if Dokploy is running
docker ps | grep dokploy

# Access Dokploy dashboard
# Open browser: http://your-vps-ip:3000 (or your configured port)
```

### 3. Prepare Your Repository

Ensure your repository is accessible to Dokploy:
- Public repository: Use HTTPS URL
- Private repository: Add Dokploy SSH key to your Git provider

---

## Dokploy Configuration

### 1. Create New Application

1. Log into Dokploy dashboard
2. Click "New Application"
3. Choose "Docker Compose" as deployment method
4. Fill in application details:
   - **Name**: `exam-portal`
   - **Repository**: `https://github.com/gauri1991/247examsdj.git`
   - **Branch**: `master`

### 2. Configure Build Settings

In the application settings:

**Build Method**: Docker Compose
**Dockerfile**: `Dockerfile`
**Docker Compose File**: `docker-compose.yml`

### 3. Set Resource Limits

**Memory Limit**: 2048MB (adjust based on your VPS)
**CPU Limit**: 2 cores
**Auto Restart**: Enabled

---

## Environment Variables Setup

### 1. Navigate to Environment Tab

In Dokploy dashboard → Your App → Environment

### 2. Add Required Variables

Copy variables from `.env.production` and update with actual values:

#### Core Django Settings
```bash
SECRET_KEY=your-strong-secret-key-here-minimum-50-chars
DEBUG=False
DJANGO_SETTINGS_MODULE=exam_portal.settings_production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DJANGO_LOG_LEVEL=INFO
```

#### Database (PostgreSQL)
```bash
DATABASE_URL=postgresql://examuser:your_db_password@postgres:5432/exam_portal_db
DB_USER=examuser
DB_PASSWORD=your_strong_db_password
DB_NAME=exam_portal_db
DB_HOST=postgres
DB_PORT=5432
```

#### Redis
```bash
REDIS_URL=redis://:your_redis_password@redis:6379/0
REDIS_PASSWORD=your_redis_password
CELERY_BROKER_URL=redis://:your_redis_password@redis:6379/1
CELERY_RESULT_BACKEND=redis://:your_redis_password@redis:6379/1
```

#### Email Configuration
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SERVER_EMAIL=server@yourdomain.com
```

#### Admin
```bash
ADMIN_URL=secure-admin/
ADMIN_EMAIL=admin@yourdomain.com
```

#### Optional: AWS S3
```bash
USE_S3=False  # Set to True if using S3
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=ap-south-1
```

#### Optional: Sentry
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

#### Feature Flags (Performance Optimization)
```bash
# Disable resource-intensive features for better performance
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

## Database Setup

### Option 1: Use Dokploy's PostgreSQL Service

1. In Dokploy, create a new PostgreSQL database service
2. Link it to your application
3. Dokploy will automatically inject `DATABASE_URL`

### Option 2: External PostgreSQL

1. Set up PostgreSQL on VPS or use managed service
2. Create database and user:

```sql
CREATE DATABASE exam_portal_db;
CREATE USER examuser WITH ENCRYPTED PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE exam_portal_db TO examuser;
ALTER DATABASE exam_portal_db OWNER TO examuser;
```

3. Update `DATABASE_URL` environment variable

---

## Domain and SSL Configuration

### 1. DNS Configuration

Point your domain to your VPS IP:

```
A Record: @ → your-vps-ip
A Record: www → your-vps-ip
```

Wait for DNS propagation (can take up to 48 hours)

### 2. SSL Certificate (Let's Encrypt)

Dokploy uses Traefik for SSL termination:

1. In Dokploy dashboard → Your App → Domains
2. Add domain: `yourdomain.com`
3. Enable "Auto SSL" (Let's Encrypt)
4. Dokploy will automatically obtain and renew certificates

### 3. Update Environment Variables

```bash
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECURE_SSL_REDIRECT=True
```

---

## Deployment Process

### 1. Initial Deployment

1. In Dokploy dashboard → Your App
2. Click "Deploy" button
3. Monitor deployment logs
4. Wait for "Deployment successful" message

### 2. Run Migrations

After first deployment, execute migrations:

```bash
# Access application container
docker exec -it exam-portal-web python manage.py migrate

# Create superuser
docker exec -it exam-portal-web python manage.py createsuperuser

# Collect static files
docker exec -it exam-portal-web python manage.py collectstatic --noinput
```

### 3. Verify Deployment

Check health endpoints:

```bash
# Basic health check
curl https://yourdomain.com/health/

# Comprehensive readiness check
curl https://yourdomain.com/health/readiness/

# System metrics
curl https://yourdomain.com/health/metrics/
```

---

## Post-Deployment Tasks

### 1. Create Admin User

```bash
docker exec -it exam-portal-web python manage.py createsuperuser
```

### 2. Access Admin Panel

Navigate to: `https://yourdomain.com/secure-admin/`
(Use the ADMIN_URL you configured)

### 3. Configure Application Settings

1. Log into admin panel
2. Configure site settings
3. Create initial data (question banks, exam templates, etc.)

### 4. Set Up Monitoring

- Configure Sentry alerts
- Set up uptime monitoring (UptimeRobot, Pingdom, etc.)
- Configure log aggregation

### 5. Set Up Backups

#### Database Backups

```bash
# Create backup script
cat > /root/backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec exam-portal-db pg_dump -U examuser exam_portal_db > /backups/db_$DATE.sql
gzip /backups/db_$DATE.sql
# Keep only last 30 days
find /backups -name "db_*.sql.gz" -mtime +30 -delete
EOF

chmod +x /root/backup-db.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line:
0 2 * * * /root/backup-db.sh
```

#### Media Files Backup

If using local storage (not S3):

```bash
# Backup media files
rsync -avz /path/to/media/ /backups/media/
```

---

## Monitoring and Maintenance

### 1. Health Checks

Monitor these endpoints:

- `https://yourdomain.com/health/` - Basic health
- `https://yourdomain.com/health/readiness/` - Service readiness
- `https://yourdomain.com/health/liveness/` - System metrics

### 2. Log Monitoring

```bash
# View application logs
docker logs -f exam-portal-web

# View specific log file
docker exec exam-portal-web tail -f logs/django.log
docker exec exam-portal-web tail -f logs/errors.log
```

### 3. Performance Monitoring

- Monitor CPU and memory usage in Dokploy dashboard
- Check Sentry for errors and performance issues
- Review application logs regularly

### 4. Updates and Maintenance

```bash
# Update application
# In Dokploy: Click "Redeploy" to pull latest code and rebuild

# Run migrations after update
docker exec -it exam-portal-web python manage.py migrate

# Collect updated static files
docker exec -it exam-portal-web python manage.py collectstatic --noinput
```

---

## Troubleshooting

### Common Issues

#### 1. Application Not Starting

```bash
# Check logs
docker logs exam-portal-web

# Common causes:
# - Missing environment variables
# - Database connection issues
# - Migration errors
```

#### 2. Database Connection Errors

```bash
# Verify database is running
docker ps | grep postgres

# Check database connectivity
docker exec exam-portal-web python manage.py dbshell

# Verify DATABASE_URL format
# postgresql://user:password@host:port/database
```

#### 3. Static Files Not Loading

```bash
# Recollect static files
docker exec exam-portal-web python manage.py collectstatic --noinput --clear

# Check STATIC_ROOT permissions
docker exec exam-portal-web ls -la /app/staticfiles
```

#### 4. SSL Certificate Issues

```bash
# Force certificate renewal in Dokploy dashboard
# Or manually with certbot:
certbot renew --force-renewal
```

#### 5. High Memory Usage

- Check feature flags - disable PDF_EXTRACTOR_ENABLED
- Monitor with: `docker stats exam-portal-web`
- Consider upgrading VPS resources

### Getting Help

- **Documentation**: Check this guide and Django docs
- **Logs**: Always check logs first (`docker logs exam-portal-web`)
- **Health Endpoints**: Monitor /health/ endpoints
- **Sentry**: Review error reports in Sentry dashboard
- **Community**: Django and Dokploy community forums

---

## Performance Optimization Tips

### 1. Resource Management

```bash
# Monitor resource usage
docker stats

# Adjust docker-compose.yml resource limits if needed
```

### 2. Caching

- Redis is configured for caching - verify it's working
- Monitor cache hit rates

### 3. Database Optimization

```bash
# Create database indexes (in production)
docker exec exam-portal-web python manage.py showmigrations

# Analyze slow queries
docker exec exam-portal-db psql -U examuser -d exam_portal_db -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### 4. CDN for Static Files

Consider using CloudFlare or AWS CloudFront for static files

---

## Security Best Practices

1. **Regular Updates**: Keep all dependencies updated
2. **Strong Passwords**: Use strong, unique passwords
3. **SSH Keys**: Disable password authentication, use SSH keys only
4. **Firewall**: Configure UFW to allow only necessary ports
5. **Backups**: Maintain regular backups (database + media)
6. **Monitoring**: Set up alerts for suspicious activities
7. **SSL**: Always use HTTPS (enforced by settings)
8. **Admin URL**: Keep ADMIN_URL secret and unique
9. **Rate Limiting**: Configured automatically in production
10. **Logs**: Review logs regularly for security issues

---

## Rollback Procedure

If deployment fails or issues occur:

```bash
# In Dokploy dashboard:
# 1. Go to Deployments tab
# 2. Find previous successful deployment
# 3. Click "Rollback to this version"

# Or via Git:
# 1. Revert to previous commit
# 2. Push to repository
# 3. Redeploy in Dokploy
```

---

## Support and Maintenance

### Regular Maintenance Tasks

- **Daily**: Monitor error logs
- **Weekly**: Review performance metrics
- **Monthly**: Update dependencies, security patches
- **Quarterly**: Review and optimize database
- **Yearly**: SSL certificate renewal (automatic with Let's Encrypt)

### Backup Schedule

- **Database**: Daily at 2 AM
- **Media Files**: Weekly
- **Configuration**: After every change
- **Retention**: 30 days

---

## Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Dokploy Documentation](https://docs.dokploy.com/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)

---

## Conclusion

This guide covers the complete deployment process for the Exam Management Platform on Dokploy. Follow each step carefully, and refer to the troubleshooting section if you encounter issues.

For production deployments, always:
- Test in staging first
- Have backups ready
- Monitor logs during deployment
- Keep this documentation updated

Good luck with your deployment! 🚀
