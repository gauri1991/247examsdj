from celery import shared_task
from celery.utils.log import get_task_logger
from .cleanup import cleanup_manager
from django.conf import settings
from django.core.mail import mail_admins

logger = get_task_logger(__name__)


@shared_task(name='pdf_extractor.cleanup_files')
def cleanup_files_task():
    """
    Periodic task to clean up old files and temporary data
    """
    logger.info("Starting scheduled PDF cleanup task")
    
    try:
        results = cleanup_manager.perform_full_cleanup()
        
        # Log results
        logger.info(f"Cleanup completed: {results['totals']}")
        
        # Send notification if configured
        if getattr(settings, 'PDF_CLEANUP_NOTIFY_ADMINS', False):
            if results['totals']['total_errors'] > 0:
                mail_admins(
                    'PDF Cleanup Task - Errors Occurred',
                    f"The PDF cleanup task completed with {results['totals']['total_errors']} errors.\n\n"
                    f"Files removed: {results['totals']['files_removed']}\n"
                    f"Documents removed: {results['totals']['documents_removed']}\n"
                    f"Bytes freed: {results['totals']['bytes_freed']:,}\n\n"
                    f"Check the logs for more details.",
                    fail_silently=True
                )
        
        return results
        
    except Exception as e:
        logger.error(f"PDF cleanup task failed: {str(e)}")
        
        # Send error notification
        if getattr(settings, 'PDF_CLEANUP_NOTIFY_ADMINS', False):
            mail_admins(
                'PDF Cleanup Task Failed',
                f"The PDF cleanup task failed with error: {str(e)}",
                fail_silently=True
            )
        
        raise


@shared_task(name='pdf_extractor.cleanup_temp_files')
def cleanup_temp_files_task():
    """
    More frequent task to clean up temporary files only
    """
    logger.info("Starting temporary file cleanup task")
    
    try:
        results = cleanup_manager.cleanup_temporary_files()
        logger.info(f"Temp cleanup completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Temp file cleanup task failed: {str(e)}")
        raise


# Celery beat schedule configuration (add to your celery config)
CELERYBEAT_SCHEDULE = {
    'cleanup-pdf-files': {
        'task': 'pdf_extractor.cleanup_files',
        'schedule': 86400.0,  # Run daily (24 hours)
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not executed
        }
    },
    'cleanup-temp-files': {
        'task': 'pdf_extractor.cleanup_temp_files',
        'schedule': 3600.0,  # Run hourly
        'options': {
            'expires': 600,  # Task expires after 10 minutes if not executed
        }
    },
}