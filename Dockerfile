# ==============================================================================
# CLEAN DOCKERFILE - Django Exam Management Platform
# ==============================================================================
# Optimized for Dokploy deployment with external PostgreSQL & Redis
# ==============================================================================

FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=exam_portal.settings_production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 django && mkdir -p /app
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=django:django . .

# Create directories
RUN mkdir -p staticfiles media logs && \
    chown -R django:django staticfiles media logs

# Collect static files with build-time environment variables
# SECRET_KEY default is set in settings.py for build time
ENV SECRET_KEY=django-insecure-build-only-key-DO-NOT-USE-IN-PRODUCTION \
    DEBUG=False \
    DATABASE_URL=sqlite:///tmp/build.db \
    REDIS_URL=redis://localhost:6379/0 \
    CELERY_BROKER_URL=redis://localhost:6379/0 \
    CELERY_RESULT_BACKEND=redis://localhost:6379/0
RUN python manage.py collectstatic --noinput || true
# Unset build-time variables (runtime env vars will override)
ENV SECRET_KEY="" \
    DEBUG="" \
    DATABASE_URL="" \
    REDIS_URL="" \
    CELERY_BROKER_URL="" \
    CELERY_RESULT_BACKEND=""

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Switch to app user
USER django

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "exam_portal.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
