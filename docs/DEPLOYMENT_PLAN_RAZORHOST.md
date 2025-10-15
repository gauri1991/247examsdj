# 📋 Django Exam Portal - Razorhost Shared Hosting Deployment Plan

## 🎯 Deployment Overview
Deploying Django Exam Management Platform to **Razorhost Shared Hosting (Starter Plan)** using cPanel Python App feature.

---

## ⚠️ Critical Issues to Address BEFORE Deployment

### 🔴 HIGH PRIORITY SECURITY ISSUES

1. **SECRET_KEY Exposure**
   - Current: Using insecure development key
   - **ACTION REQUIRED**: Generate new production SECRET_KEY
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **DEBUG Mode**
   - Current: `DEBUG=True`
   - **ACTION REQUIRED**: Set `DEBUG=False` in production

3. **ALLOWED_HOSTS Vulnerability**
   - Current: Contains wildcard `*`
   - **ACTION REQUIRED**: Set specific domain only

4. **Database Security**
   - Current: SQLite (not suitable for production)
   - **ACTION REQUIRED**: Use MySQL/PostgreSQL

5. **Redis/Celery Dependency**
   - Current: Requires Redis (not available on shared hosting)
   - **ACTION REQUIRED**: Remove or use alternatives

---

## 📝 Pre-Deployment Checklist

### Phase 1: Code Modifications Required

#### 1.1 Create Production Settings
```python
# exam_portal/settings_production.py
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database - Use MySQL provided by Razorhost
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Disable Redis/Celery for shared hosting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}

# Remove Celery configuration
# Comment out all CELERY_* settings

# Static/Media files for cPanel
STATIC_ROOT = '/home/cpanelusername/public_html/static'
MEDIA_ROOT = '/home/cpanelusername/public_html/media'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.yourdomain.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'noreply@yourdomain.com'
EMAIL_HOST_PASSWORD = 'email_password'

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### 1.2 Requirements Modification
Create `requirements_production.txt`:
```txt
Django==5.2.4
django-environ==0.12.0
django-cors-headers==4.7.0
django-crispy-forms==2.4
crispy-tailwind==1.0.3
django-htmx==1.23.2
djangorestframework==3.16.0
djangorestframework_simplejwt==5.5.1
Pillow==11.3.0
PyPDF2==3.0.1
python-magic==0.4.27
mysqlclient==2.2.4
gunicorn==22.0.0
whitenoise==6.7.0
```

#### 1.3 Remove/Modify Heavy Dependencies
- Remove EasyOCR (1.7GB+ dependencies)
- Remove PyTesseract (requires system Tesseract)
- Remove OpenCV dependencies
- Remove NVIDIA CUDA libraries
- Simplify PDF processing

#### 1.4 WSGI Configuration
```python
# passenger_wsgi.py (for cPanel)
import os
import sys

# Add project to path
sys.path.insert(0, '/home/cpanelusername/your_app_directory')

# Set environment variable
os.environ['DJANGO_SETTINGS_MODULE'] = 'exam_portal.settings_production'

# Import Django application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Phase 2: Database Migration Strategy

1. **Export current SQLite data**:
```bash
python manage.py dumpdata --exclude contenttypes --exclude auth.permission > data.json
```

2. **Create MySQL database via cPanel**
3. **Update database settings**
4. **Run migrations on production**:
```bash
python manage.py migrate
python manage.py loaddata data.json
```

### Phase 3: Static Files Configuration

1. **Collect static files locally**:
```bash
python manage.py collectstatic --noinput
```

2. **Compress static files**:
```bash
tar -czf static_files.tar.gz staticfiles/
```

3. **Upload and extract via cPanel File Manager**

---

## 🚀 Deployment Steps on Razorhost cPanel

### Step 1: Prepare cPanel Environment

1. **Login to cPanel**
2. **Create MySQL Database**:
   - MySQL Database Wizard
   - Create database: `examportal_db`
   - Create user: `examportal_user`
   - Grant all privileges

3. **Setup Python App**:
   - Go to "Setup Python App"
   - Python version: 3.11 or 3.12
   - Application root: `/home/username/examportal`
   - Application URL: `yourdomain.com`
   - Application startup file: `passenger_wsgi.py`

### Step 2: Upload Project Files

1. **Via cPanel File Manager**:
   - Create app directory
   - Upload project ZIP (excluding venv, media, __pycache__)
   - Extract files

2. **Via FTP** (alternative):
```bash
# Use FileZilla or similar
Host: ftp.yourdomain.com
Username: cpanel_username
Password: cpanel_password
Port: 21
```

### Step 3: Install Dependencies

1. **Enter virtual environment** (via cPanel terminal):
```bash
source /home/username/virtualenv/examportal/3.11/bin/activate
```

2. **Install packages**:
```bash
pip install -r requirements_production.txt
```

### Step 4: Configure Environment

1. **Create .env file**:
```env
SECRET_KEY=your-new-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=mysql://user:pass@localhost:3306/dbname
```

2. **Set permissions**:
```bash
chmod 755 /home/username/examportal
chmod 644 passenger_wsgi.py
```

### Step 5: Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### Step 6: Configure .htaccess

Create `/home/username/public_html/.htaccess`:
```apache
RewriteEngine On
RewriteCond %{REQUEST_URI} !^/static/
RewriteCond %{REQUEST_URI} !^/media/
RewriteRule ^(.*)$ /passenger_wsgi.py/$1 [L]

# Static files
Alias /static /home/username/public_html/static
Alias /media /home/username/public_html/media

# Security headers
Header set X-Frame-Options "DENY"
Header set X-Content-Type-Options "nosniff"
Header set X-XSS-Protection "1; mode=block"
```

---

## 🔧 Post-Deployment Tasks

### 1. Testing
- [ ] Test login functionality
- [ ] Test file uploads
- [ ] Test PDF processing (simplified version)
- [ ] Test exam creation and taking
- [ ] Test payment integration (if using Razorpay)

### 2. Monitoring Setup
- [ ] Setup error logging
- [ ] Configure email alerts for errors
- [ ] Setup uptime monitoring (UptimeRobot)

### 3. Backup Strategy
- [ ] Daily database backups via cPanel
- [ ] Weekly full site backups
- [ ] Store backups offsite

### 4. Performance Optimization
- [ ] Enable cPanel caching
- [ ] Optimize images
- [ ] Minify CSS/JS
- [ ] Enable GZIP compression

---

## ⚡ Limitations on Shared Hosting

### What WON'T Work:
- ❌ Redis/Celery background tasks
- ❌ WebSocket connections
- ❌ Heavy OCR processing (EasyOCR/Tesseract)
- ❌ Real-time features requiring persistent connections
- ❌ Large file processing (memory limits)

### Workarounds:
- ✅ Use database caching instead of Redis
- ✅ Use AJAX polling instead of WebSockets
- ✅ Simplify PDF processing (basic text extraction only)
- ✅ Use cron jobs for scheduled tasks instead of Celery
- ✅ Implement file size limits and chunked uploads

---

## 🔄 Alternative: Recommended Hosting Solutions

For full functionality, consider:

1. **VPS Hosting** (DigitalOcean, Linode, Vultr)
   - Full control
   - Redis/Celery support
   - Better performance
   - ~$5-20/month

2. **PaaS Solutions** (Heroku, Railway, Render)
   - Easy deployment
   - Automatic scaling
   - Built-in Redis support
   - ~$7-25/month

3. **AWS/GCP/Azure** (with free tier)
   - Enterprise features
   - Auto-scaling
   - Managed databases
   - Pay-as-you-go

---

## 📞 Support Resources

- **Razorhost Support**: support@razorhost.com
- **Django Deployment Docs**: https://docs.djangoproject.com/en/5.2/howto/deployment/
- **cPanel Python Docs**: https://docs.cpanel.net/knowledge-base/web-services/python/

---

## ⏱️ Estimated Timeline

1. **Code Modifications**: 2-3 hours
2. **Testing Locally**: 1-2 hours  
3. **cPanel Setup**: 1 hour
4. **File Upload & Configuration**: 1-2 hours
5. **Database Migration**: 1 hour
6. **Testing & Debugging**: 2-3 hours

**Total**: 8-12 hours for complete deployment

---

## 🚨 IMPORTANT NOTES

1. **Shared hosting is NOT ideal for Django** - Consider VPS for production
2. **Performance will be limited** - Expect slower response times
3. **Background tasks won't work** - No Celery/Redis support
4. **Resource limits apply** - CPU, RAM, and process limits
5. **Consider upgrading** to VPS once you have users

---

## Next Steps

1. Review this plan and confirm hosting choice
2. Create production environment variables
3. Test simplified features locally
4. Proceed with deployment or consider VPS alternative

Would you like me to:
1. Create the production settings file?
2. Simplify the requirements for shared hosting?
3. Create deployment scripts?
4. Suggest VPS alternatives with setup guides?