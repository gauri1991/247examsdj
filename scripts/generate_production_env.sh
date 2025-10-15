#!/bin/bash

# ==============================================================================
# Production Environment Generator for Dokploy Deployment
# ==============================================================================
# This script generates secure credentials and creates a production .env file
# Usage: bash scripts/generate_production_env.sh
# ==============================================================================

set -e

echo "🔐 Generating Production Environment Variables..."
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Generate SECRET_KEY (without needing Django installed)
echo -e "${BLUE}📝 Generating Django SECRET_KEY...${NC}"
SECRET_KEY=$(python3 -c 'import secrets; import string; chars = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"; print("".join(secrets.choice(chars) for _ in range(50)))')
echo -e "${GREEN}✓ SECRET_KEY generated${NC}"
echo ""

# Generate DB_PASSWORD
echo -e "${BLUE}📝 Generating Database Password...${NC}"
DB_PASSWORD=$(openssl rand -base64 32)
echo -e "${GREEN}✓ DB_PASSWORD generated${NC}"
echo ""

# Generate REDIS_PASSWORD
echo -e "${BLUE}📝 Generating Redis Password...${NC}"
REDIS_PASSWORD=$(openssl rand -base64 32)
echo -e "${GREEN}✓ REDIS_PASSWORD generated${NC}"
echo ""

# VPS IP
VPS_IP="147.93.102.87"

# Create production environment file
OUTPUT_FILE=".env.production.generated"

echo -e "${BLUE}📄 Creating ${OUTPUT_FILE}...${NC}"
cat > "${OUTPUT_FILE}" << EOF
# ==============================================================================
# PRODUCTION ENVIRONMENT VARIABLES
# ==============================================================================
# Generated on: $(date)
# VPS IP: ${VPS_IP}
# ==============================================================================
# IMPORTANT: Copy these values to Dokploy Environment tab
# ==============================================================================

# ===== CRITICAL - DJANGO CORE =====
SECRET_KEY=${SECRET_KEY}
DEBUG=False
DJANGO_SETTINGS_MODULE=exam_portal.settings_production
ALLOWED_HOSTS=${VPS_IP}
CSRF_TRUSTED_ORIGINS=http://${VPS_IP},https://${VPS_IP}
DJANGO_LOG_LEVEL=INFO

# ===== DATABASE (PostgreSQL) =====
DATABASE_URL=postgresql://examuser:${DB_PASSWORD}@postgres:5432/exam_portal_db
DB_USER=examuser
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=exam_portal_db
DB_HOST=postgres
DB_PORT=5432

# ===== REDIS =====
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_PASSWORD=${REDIS_PASSWORD}
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1

# ===== EMAIL (Gmail - UPDATE WITH YOUR CREDENTIALS) =====
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

# ===== OPTIONAL: AWS S3 (Uncomment if using) =====
# USE_S3=False
# AWS_ACCESS_KEY_ID=your-aws-key
# AWS_SECRET_ACCESS_KEY=your-aws-secret
# AWS_STORAGE_BUCKET_NAME=your-bucket-name
# AWS_S3_REGION_NAME=ap-south-1

# ===== OPTIONAL: SENTRY (Uncomment if using) =====
# SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
# SENTRY_ENVIRONMENT=production
# SENTRY_TRACES_SAMPLE_RATE=0.1

# ==============================================================================
# NEXT STEPS:
# ==============================================================================
# 1. Update EMAIL_HOST_USER and EMAIL_HOST_PASSWORD with your Gmail credentials
# 2. Update ADMIN_EMAIL with your actual email
# 3. Copy ALL variables to Dokploy Dashboard -> Environment tab
# 4. Click "Redeploy" in Dokploy
# 5. Run migrations: docker exec -it exam-portal-web python manage.py migrate
# 6. Create superuser: docker exec -it exam-portal-web python manage.py createsuperuser
# ==============================================================================
EOF

echo -e "${GREEN}✓ Environment file created: ${OUTPUT_FILE}${NC}"
echo ""

# Display summary
echo "=================================================="
echo -e "${GREEN}✅ SUCCESS! All credentials generated!${NC}"
echo "=================================================="
echo ""
echo -e "${YELLOW}📋 GENERATED CREDENTIALS:${NC}"
echo ""
echo "SECRET_KEY (first 20 chars): ${SECRET_KEY:0:20}..."
echo "DB_PASSWORD (first 10 chars): ${DB_PASSWORD:0:10}..."
echo "REDIS_PASSWORD (first 10 chars): ${REDIS_PASSWORD:0:10}..."
echo ""
echo -e "${YELLOW}📍 VPS IP: ${VPS_IP}${NC}"
echo ""
echo "=================================================="
echo -e "${BLUE}📄 ENVIRONMENT FILE: ${OUTPUT_FILE}${NC}"
echo "=================================================="
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT NEXT STEPS:${NC}"
echo ""
echo "1. Review the generated file:"
echo "   cat ${OUTPUT_FILE}"
echo ""
echo "2. Update EMAIL settings with your Gmail credentials:"
echo "   - Get Gmail App Password: https://myaccount.google.com/apppasswords"
echo "   - Update EMAIL_HOST_USER and EMAIL_HOST_PASSWORD"
echo ""
echo "3. Copy ALL variables to Dokploy:"
echo "   - Open Dokploy Dashboard: http://${VPS_IP}:3000"
echo "   - Go to your app -> Environment tab"
echo "   - Add all variables from ${OUTPUT_FILE}"
echo ""
echo "4. Click 'Redeploy' in Dokploy"
echo ""
echo "5. After deployment, run migrations:"
echo "   docker exec -it exam-portal-web python manage.py migrate"
echo "   docker exec -it exam-portal-web python manage.py createsuperuser"
echo ""
echo "6. Access your application:"
echo "   http://${VPS_IP}/"
echo "   http://${VPS_IP}/secure-admin/"
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Ready for deployment!${NC}"
echo "=================================================="
echo ""
echo -e "${YELLOW}⚠️  SECURITY WARNING:${NC}"
echo "The generated file contains sensitive credentials."
echo "DO NOT commit ${OUTPUT_FILE} to Git!"
echo "It's already in .gitignore for safety."
echo ""
