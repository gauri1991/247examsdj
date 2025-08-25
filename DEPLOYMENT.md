# Production Deployment Guide for Exam Portal

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Security Checklist](#security-checklist)
3. [Dokploy Deployment](#dokploy-deployment)
4. [Post-Deployment](#post-deployment)
5. [Monitoring & Maintenance](#monitoring-maintenance)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Server Requirements
- **OS**: Ubuntu 24.04 LTS
- **RAM**: Minimum 4GB (8GB recommended)
- **CPU**: 2+ cores
- **Storage**: 50GB+ SSD
- **Hosting**: Hostinger KVM 4 VPS or equivalent

### Software Requirements
- Docker & Docker Compose
- Dokploy platform
- PostgreSQL 15+
- Redis 7+
- Nginx
- SSL certificates (Let's Encrypt)

## Security Checklist

### 1. Environment Variables
```bash
# Generate secure SECRET_KEY (minimum 50 characters)
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Generate secure passwords
openssl rand -base64 32  # For DB_PASSWORD
openssl rand -base64 32  # For REDIS_PASSWORD
```

### 2. Required Environment Variables
Create `.env` file from `.env.example`:
```bash
cp .env.example .env
nano .env
```

**Critical variables to set:**
- `SECRET_KEY` - Django secret key (generate new one)
- `DB_PASSWORD` - PostgreSQL password
- `REDIS_PASSWORD` - Redis password
- `ALLOWED_HOSTS` - Your domain names
- `DJANGO_SUPERUSER_PASSWORD` - Admin password
- Email configuration (SMTP settings)

### 3. Security Hardening
- ✅ HTTPS enforced with SSL redirect
- ✅ Security headers configured (HSTS, CSP, XSS Protection)
- ✅ Rate limiting enabled
- ✅ SQL injection protection
- ✅ CSRF protection
- ✅ XSS protection
- ✅ File upload restrictions
- ✅ Session security
- ✅ Password complexity requirements

## Dokploy Deployment

### Step 1: Prepare Your VPS
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Dokploy
curl -sSL https://dokploy.com/install.sh | sudo bash
```

### Step 2: Configure Dokploy
1. Access Dokploy dashboard (usually at `http://your-server-ip:3000`)
2. Create new project named "exam-portal"
3. Connect your GitHub repository or upload code
4. Select "Docker Compose" as deployment type

### Step 3: Configure Environment Variables in Dokploy
In Dokploy dashboard:
1. Go to Project Settings → Environment Variables
2. Add all variables from `.env.example`
3. Use secure values for production

### Step 4: Deploy Application
```bash
# From Dokploy dashboard or CLI
dokploy deploy exam-portal

# Or manually with Docker Compose
docker-compose -f docker-compose.yml up -d
```

### Step 5: SSL Certificate Setup
Dokploy automatically configures Let's Encrypt SSL. Ensure:
1. Domain DNS points to your server
2. Ports 80 and 443 are open
3. Email configured for certificate notifications

## Post-Deployment

### 1. Initial Setup
```bash
# Access container
docker exec -it exam-portal-web-1 bash

# Create superuser
python manage.py createsuperuser

# Run initial migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create cache table
python manage.py createcachetable
```

### 2. Verify Deployment
- Check health endpoint: `https://yourdomain.com/health/`
- Check readiness: `https://yourdomain.com/readiness/`
- Access admin panel: `https://yourdomain.com/admin/`
- Test login functionality
- Verify static files loading
- Check PDF upload functionality

### 3. Configure Backups
```bash
# Setup cron job for daily backups
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * /app/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### 4. Setup Monitoring
Configure monitoring endpoints in your monitoring service:
- `/health/` - Basic health check
- `/readiness/` - Comprehensive readiness check
- `/metrics/` - Prometheus metrics

## Monitoring & Maintenance

### Daily Tasks
- Check application logs
- Monitor disk space
- Verify backup completion

### Weekly Tasks
- Review security logs
- Check for security updates
- Analyze performance metrics

### Monthly Tasks
- Update dependencies
- Security audit
- Performance optimization
- Backup restoration test

### Monitoring Commands
```bash
# View logs
docker-compose logs -f web
docker-compose logs -f celery

# Check container status
docker-compose ps

# Monitor resources
docker stats

# Database queries monitoring
docker exec -it exam-portal-db-1 psql -U examuser -d exam_portal -c "SELECT * FROM pg_stat_activity;"

# Redis monitoring
docker exec -it exam-portal-redis-1 redis-cli -a $REDIS_PASSWORD INFO
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check database status
docker-compose ps db

# View database logs
docker-compose logs db

# Test connection
docker exec -it exam-portal-web-1 python manage.py dbshell
```

#### 2. Static Files Not Loading
```bash
# Recollect static files
docker exec -it exam-portal-web-1 python manage.py collectstatic --noinput

# Check nginx configuration
docker exec -it exam-portal-nginx-1 nginx -t

# Restart nginx
docker-compose restart nginx
```

#### 3. High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart web celery

# Clear cache
docker exec -it exam-portal-web-1 python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

#### 4. Celery Tasks Not Running
```bash
# Check Celery status
docker-compose logs celery celery-beat

# Restart Celery
docker-compose restart celery celery-beat

# Monitor Celery tasks (if Flower is installed)
docker-compose exec celery flower --port=5555
```

### Emergency Procedures

#### Rollback Deployment
```bash
# Stop current deployment
docker-compose down

# Restore from backup
./scripts/restore.sh [backup_date]

# Or rollback with Dokploy
dokploy rollback exam-portal
```

#### Database Recovery
```bash
# Restore database from backup
./scripts/restore.sh [YYYYMMDD_HHMMSS]
```

#### Clear All Caches
```bash
docker exec -it exam-portal-redis-1 redis-cli -a $REDIS_PASSWORD FLUSHALL
```

## Security Updates

### Regular Updates
```bash
# Update base images
docker-compose pull
docker-compose up -d

# Update Python packages
docker exec -it exam-portal-web-1 pip install --upgrade -r requirements-production.txt

# Update system packages
docker exec -it exam-portal-web-1 apt update && apt upgrade
```

### Security Scanning
```bash
# Scan for vulnerabilities
docker scan exam-portal-web

# Check for known security issues
docker exec -it exam-portal-web-1 python manage.py check --deploy
```

## Performance Optimization

### 1. Database Optimization
```sql
-- Run these in PostgreSQL
VACUUM ANALYZE;
REINDEX DATABASE exam_portal;
```

### 2. Redis Optimization
```bash
# Configure Redis memory policy
docker exec -it exam-portal-redis-1 redis-cli -a $REDIS_PASSWORD CONFIG SET maxmemory-policy allkeys-lru
```

### 3. Application Optimization
- Enable Django caching
- Use CDN for static files
- Implement database query optimization
- Enable Gzip compression

## Contact & Support

For issues or questions:
1. Check application logs first
2. Review this documentation
3. Contact system administrator
4. For critical issues, check Sentry dashboard (if configured)

## Important URLs

- Application: `https://yourdomain.com`
- Admin Panel: `https://yourdomain.com/admin/`
- Health Check: `https://yourdomain.com/health/`
- Metrics: `https://yourdomain.com/metrics/`
- Dokploy Dashboard: `http://your-server-ip:3000`

## Backup & Recovery

### Backup Locations
- Local: `/backups/`
- S3: `s3://your-backup-bucket/`

### Recovery Time Objectives
- RTO (Recovery Time Objective): < 1 hour
- RPO (Recovery Point Objective): < 24 hours

---

**Last Updated**: 2025-08-04
**Version**: 1.0.0
**Maintained By**: DevOps Team