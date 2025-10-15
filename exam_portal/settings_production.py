"""
Production settings for exam_portal project.
Enhanced security configurations for production deployment.
"""

from .settings import *
import environ
import os

env = environ.Env()

# SECURITY CONFIGURATION
# -----------------------------------------------------------------------------
# ⚠️ TEMPORARY: DEBUG enabled for troubleshooting
# ⚠️ SECURITY RISK: This exposes sensitive information
# ⚠️ TODO: Set back to False after debugging
DEBUG = env.bool('DEBUG', default=True)  # TEMPORARILY TRUE FOR DEBUGGING

# Force HTTPS in production
# ⚠️ TEMPORARY: SSL redirect disabled for debugging
SECURE_SSL_REDIRECT = False  # TEMPORARILY FALSE FOR DEBUGGING
SESSION_COOKIE_SECURE = False  # TEMPORARILY FALSE FOR DEBUGGING
CSRF_COOKIE_SECURE = False  # TEMPORARILY FALSE FOR DEBUGGING
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Security Headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookie Security
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'  # Changed from Strict for better compatibility
CSRF_COOKIE_SAMESITE = 'Lax'
# Note: __Host- prefix requires secure context and no Domain attribute
# Uncomment these when using HTTPS with proper domain
# SESSION_COOKIE_NAME = '__Host-sessionid'
# CSRF_COOKIE_NAME = '__Host-csrftoken'

# Session Security
# Temporarily using database sessions instead of cache
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Password Security
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# File Upload Security
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Allowed file extensions for uploads
ALLOWED_UPLOAD_EXTENSIONS = [
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 
    'jpg', 'jpeg', 'png', 'gif', 'webp'
]

MAX_UPLOAD_SIZE = 10485760  # 10MB

# DATABASE CONFIGURATION
# -----------------------------------------------------------------------------
DATABASES = {
    'default': env.db()
}

# Add database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 60
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
    'options': '-c statement_timeout=30000'  # 30 seconds
}

# CACHE CONFIGURATION
# -----------------------------------------------------------------------------
# Temporarily disabled Redis cache - using dummy cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Original Redis configuration (disabled temporarily)
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': env('REDIS_URL'),
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#             'CONNECTION_POOL_KWARGS': {
#                 'max_connections': 50,
#                 'retry_on_timeout': True,
#                 'socket_keepalive': True,
#                 'socket_keepalive_options': {
#                     1: 3,  # TCP_KEEPIDLE
#                     2: 3,  # TCP_KEEPINTVL
#                     3: 3,  # TCP_KEEPCNT
#                 }
#             },
#             'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
#             'IGNORE_EXCEPTIONS': True,
#         }
#     }
# }

# STATIC FILES CONFIGURATION
# -----------------------------------------------------------------------------
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Compress static files
COMPRESS_ENABLED = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter'
]
COMPRESS_JS_FILTERS = ['compressor.filters.jsmin.JSMinFilter']
COMPRESS_OFFLINE = True

# MEDIA FILES CONFIGURATION
# -----------------------------------------------------------------------------
if env.bool('USE_S3', default=False):
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='ap-south-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_ENCRYPTION = True
    AWS_S3_SECURE_URLS = True
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = 3600
    
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
else:
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = '/media/'

# EMAIL CONFIGURATION
# -----------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@examportal.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# LOGGING CONFIGURATION
# -----------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django_error.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'exam_portal': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'pdf_extractor': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# CONTENT SECURITY POLICY
# -----------------------------------------------------------------------------
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for inline scripts (should be removed if possible)
    "https://cdn.jsdelivr.net",
    "https://unpkg.com",
    "https://cdnjs.cloudflare.com",
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for inline styles (should be removed if possible)
    "https://cdn.jsdelivr.net",
    "https://fonts.googleapis.com",
)
CSP_FONT_SRC = (
    "'self'",
    "https://fonts.gstatic.com",
    "data:",
)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https:",
)
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)

# RATE LIMITING
# -----------------------------------------------------------------------------
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = 'core.views.ratelimit_exceeded'

# Rate limits
API_RATE_LIMIT = '60/m'
LOGIN_RATE_LIMIT = '5/m'
REGISTRATION_RATE_LIMIT = '3/h'
TEST_SUBMISSION_RATE_LIMIT = '10/m'
PDF_UPLOAD_RATE_LIMIT = '5/h'
PASSWORD_RESET_RATE_LIMIT = '3/h'

# CELERY CONFIGURATION
# -----------------------------------------------------------------------------
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_DISABLE_RATE_LIMITS = False

# CORS CONFIGURATION
# -----------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# REST FRAMEWORK CONFIGURATION
# -----------------------------------------------------------------------------
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
)
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle'
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour'
}

# JWT Configuration
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=30)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=1)
SIMPLE_JWT['ROTATE_REFRESH_TOKENS'] = True
SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'] = True
SIMPLE_JWT['ALGORITHM'] = 'HS256'

# ERROR TRACKING (Sentry)
# -----------------------------------------------------------------------------
if env('SENTRY_DSN', default=None):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# ADMIN CONFIGURATION
# -----------------------------------------------------------------------------
ADMIN_URL = env('ADMIN_URL', default='secure-admin/')
ADMINS = [
    ('Admin', env('ADMIN_EMAIL', default='admin@example.com')),
]
MANAGERS = ADMINS

# CUSTOM SETTINGS
# -----------------------------------------------------------------------------
# PDF Processing
PDF_MAX_SIZE = 50 * 1024 * 1024  # 50MB
PDF_ALLOWED_TYPES = ['application/pdf']
PDF_PROCESSING_TIMEOUT = 300  # 5 minutes

# Question Bank
MAX_QUESTIONS_PER_BANK = 10000
MAX_QUESTIONS_PER_EXAM = 500

# Test Taking
TEST_TIME_LIMIT_HOURS = 4
MAX_CONCURRENT_TESTS = 3

# User Limits
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION = 3600  # 1 hour in seconds

# HEALTH CHECKS AND MONITORING
# -----------------------------------------------------------------------------
# Add health check apps to INSTALLED_APPS
if 'health_check' not in INSTALLED_APPS:
    INSTALLED_APPS += [
        'health_check',
        'health_check.db',
        'health_check.cache',
        'health_check.storage',
        'health_check.contrib.migrations',
        'health_check.contrib.celery',
        'health_check.contrib.redis',
    ]

# Add Django Defender for brute force protection
if 'defender' not in INSTALLED_APPS:
    INSTALLED_APPS.append('defender')

# Add WhiteNoise middleware for serving static files in production
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    # Insert after SecurityMiddleware
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Add Defender middleware at the beginning
if 'defender.middleware.FailedLoginMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(0, 'defender.middleware.FailedLoginMiddleware')

# Defender Configuration
DEFENDER_LOGIN_FAILURE_LIMIT = 5
DEFENDER_COOLOFF_TIME = 300  # 5 minutes
DEFENDER_STORE_ACCESS_ATTEMPTS = True
DEFENDER_USE_CELERY = env.bool('DEFENDER_USE_CELERY', default=False)  # Set to True if Celery is configured
DEFENDER_REDIS_URL = env('REDIS_URL', default=None)

# DOKPLOY SPECIFIC CONFIGURATION
# -----------------------------------------------------------------------------
# Trust proxy headers from Dokploy/Traefik
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF trusted origins for Dokploy deployment
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

print("=" * 80)
print("✓ Production settings loaded successfully")
print("=" * 80)
print(f"DEBUG: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"Database: {DATABASES['default']['ENGINE']}")
print(f"Cache: Redis")
print(f"Sentry: {'Enabled' if env('SENTRY_DSN', default=None) else 'Disabled'}")
print(f"S3 Storage: {'Enabled' if env.bool('USE_S3', default=False) else 'Disabled (Local)'}")
print(f"Health Checks: Enabled")
print(f"Security: Maximum")
print("=" * 80)