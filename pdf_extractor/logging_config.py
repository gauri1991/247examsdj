import os
import logging.config
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
        },
        'simple': {
            'format': '%(asctime)s - %(levelname)s - %(message)s'
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file_all': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'pdf_extractor_all.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        },
        'file_errors': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'pdf_extractor_errors.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        },
        'file_processing': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'pdf_processing.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'loggers': {
        'pdf_extractor': {
            'handlers': ['console', 'file_all', 'file_errors'],
            'level': 'DEBUG',
            'propagate': False
        },
        'pdf_extractor.processing': {
            'handlers': ['file_processing'],
            'level': 'INFO',
            'propagate': False
        },
        'pdf_extractor.error_handling': {
            'handlers': ['file_errors'],
            'level': 'ERROR',
            'propagate': False
        }
    }
}

def setup_logging():
    """
    Configure logging for PDF extractor
    """
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger('pdf_extractor')
    logger.info("PDF Extractor logging configured")
    return logger