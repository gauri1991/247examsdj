import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps
import json
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


# Configure logging
logger = logging.getLogger(__name__)


class PDFProcessingError(Exception):
    """Base exception for PDF processing errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = timezone.now()


class FileSecurityError(PDFProcessingError):
    """Raised when file security validation fails"""
    error_code = "FILE_SECURITY_ERROR"


class OCRProcessingError(PDFProcessingError):
    """Raised when OCR processing fails"""
    error_code = "OCR_PROCESSING_ERROR"


class TextExtractionError(PDFProcessingError):
    """Raised when text extraction fails"""
    error_code = "TEXT_EXTRACTION_ERROR"


class QuestionDetectionError(PDFProcessingError):
    """Raised when question detection fails"""
    error_code = "QUESTION_DETECTION_ERROR"


class LayoutAnalysisError(PDFProcessingError):
    """Raised when layout analysis fails"""
    error_code = "LAYOUT_ANALYSIS_ERROR"


class ProcessingTimeoutError(PDFProcessingError):
    """Raised when processing exceeds time limit"""
    error_code = "PROCESSING_TIMEOUT"


class ErrorHandler:
    """
    Centralized error handling for PDF processing
    """
    
    def __init__(self):
        self.error_log = []
        self.max_errors = 100  # Keep last 100 errors in memory
        
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Log an error with context information
        """
        error_data = {
            'timestamp': timezone.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # Add to in-memory log
        self.error_log.append(error_data)
        if len(self.error_log) > self.max_errors:
            self.error_log.pop(0)
        
        # Log to file
        logger.error(
            f"PDF Processing Error: {error_data['error_type']} - {error_data['error_message']}",
            extra={'error_data': error_data}
        )
        
        # If it's a custom PDFProcessingError, add additional details
        if isinstance(error, PDFProcessingError):
            error_data['error_code'] = error.error_code
            error_data['error_details'] = error.details
        
        return error_data
    
    def handle_processing_error(self, error: Exception, processing_job, step: str = None) -> None:
        """
        Handle error during PDF processing
        """
        from .models import ProcessingJob
        
        # Log the error
        error_data = self.log_error(error, {
            'job_id': str(processing_job.id),
            'document_id': str(processing_job.pdf_document.id),
            'processing_step': step or processing_job.current_step,
            'document_name': processing_job.pdf_document.filename
        })
        
        # Update processing job with error details
        processing_job.status = 'failed'
        processing_job.error_details = {
            'error': error_data['error_message'],
            'error_type': error_data['error_type'],
            'error_code': error_data.get('error_code'),
            'step': step or processing_job.current_step,
            'timestamp': error_data['timestamp'],
            'traceback': error_data['traceback'][:500]  # Limit traceback size
        }
        processing_job.save()
        
        # Update document status
        document = processing_job.pdf_document
        document.status = 'failed'
        document.error_message = error_data['error_message']
        document.save()
        
        # Send notification if critical error
        if self._is_critical_error(error):
            self._send_error_notification(error_data, processing_job)
    
    def _is_critical_error(self, error: Exception) -> bool:
        """
        Determine if an error is critical and requires notification
        """
        critical_error_types = [
            FileSecurityError,
            ProcessingTimeoutError,
        ]
        
        return type(error) in critical_error_types
    
    def _send_error_notification(self, error_data: Dict, processing_job) -> None:
        """
        Send email notification for critical errors
        """
        if not getattr(settings, 'SEND_ERROR_NOTIFICATIONS', False):
            return
        
        try:
            subject = f"Critical PDF Processing Error: {error_data['error_type']}"
            message = f"""
            A critical error occurred during PDF processing:
            
            Document: {processing_job.pdf_document.filename}
            User: {processing_job.pdf_document.uploaded_by.email}
            Error Type: {error_data['error_type']}
            Error Message: {error_data['error_message']}
            Processing Step: {error_data['context'].get('processing_step', 'Unknown')}
            Timestamp: {error_data['timestamp']}
            
            Please check the application logs for more details.
            """
            
            admin_emails = getattr(settings, 'ADMIN_EMAIL_LIST', [])
            if admin_emails:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    admin_emails,
                    fail_silently=True
                )
        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent errors from in-memory log
        """
        return self.error_log[-limit:]
    
    def clear_error_log(self) -> None:
        """
        Clear in-memory error log
        """
        self.error_log.clear()


# Global error handler instance
error_handler = ErrorHandler()


def with_error_handling(step_name: str = None):
    """
    Decorator for adding error handling to processing functions
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Try to find processing_job in args or kwargs
                processing_job = None
                for arg in args:
                    if hasattr(arg, 'id') and hasattr(arg, 'current_step'):
                        processing_job = arg
                        break
                
                if not processing_job:
                    processing_job = kwargs.get('processing_job')
                
                if processing_job:
                    error_handler.handle_processing_error(
                        e, 
                        processing_job, 
                        step_name or func.__name__
                    )
                else:
                    # Just log the error if no processing job found
                    error_handler.log_error(e, {
                        'function': func.__name__,
                        'step': step_name
                    })
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator


class ProcessingLogger:
    """
    Structured logging for PDF processing pipeline
    """
    
    def __init__(self, job_id: str = None, document_id: str = None):
        self.job_id = job_id
        self.document_id = document_id
        self.logger = logging.getLogger(f"{__name__}.processing")
        
    def log_step_start(self, step: str, details: Dict = None) -> None:
        """
        Log the start of a processing step
        """
        log_data = {
            'event': 'step_start',
            'step': step,
            'job_id': self.job_id,
            'document_id': self.document_id,
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        }
        
        self.logger.info(
            f"Processing step started: {step}",
            extra={'log_data': log_data}
        )
    
    def log_step_complete(self, step: str, duration_seconds: float = None, 
                         results: Dict = None) -> None:
        """
        Log the completion of a processing step
        """
        log_data = {
            'event': 'step_complete',
            'step': step,
            'job_id': self.job_id,
            'document_id': self.document_id,
            'timestamp': timezone.now().isoformat(),
            'duration_seconds': duration_seconds,
            'results': results or {}
        }
        
        self.logger.info(
            f"Processing step completed: {step} ({duration_seconds:.2f}s)",
            extra={'log_data': log_data}
        )
    
    def log_warning(self, message: str, details: Dict = None) -> None:
        """
        Log a warning during processing
        """
        log_data = {
            'event': 'warning',
            'message': message,
            'job_id': self.job_id,
            'document_id': self.document_id,
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        }
        
        self.logger.warning(
            f"Processing warning: {message}",
            extra={'log_data': log_data}
        )
    
    def log_extraction_result(self, page_number: int, questions_found: int, 
                            confidence_avg: float) -> None:
        """
        Log extraction results for a page
        """
        log_data = {
            'event': 'extraction_result',
            'page_number': page_number,
            'questions_found': questions_found,
            'confidence_avg': confidence_avg,
            'job_id': self.job_id,
            'document_id': self.document_id,
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.info(
            f"Page {page_number}: Found {questions_found} questions (avg confidence: {confidence_avg:.2f})",
            extra={'log_data': log_data}
        )
    
    def log_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Log performance metrics
        """
        log_data = {
            'event': 'performance_metrics',
            'metrics': metrics,
            'job_id': self.job_id,
            'document_id': self.document_id,
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.info(
            "Performance metrics recorded",
            extra={'log_data': log_data}
        )


def setup_logging():
    """
    Set up logging configuration for PDF extractor
    """
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
    )
    
    json_formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", '
        '"message": "%(message)s", "data": %(log_data)s}'
    )
    
    # File handler for all logs
    all_handler = logging.handlers.RotatingFileHandler(
        'logs/pdf_extractor_all.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(detailed_formatter)
    
    # File handler for errors only
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/pdf_extractor_errors.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # JSON handler for structured logs
    json_handler = logging.handlers.RotatingFileHandler(
        'logs/pdf_extractor_json.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    json_handler.setLevel(logging.INFO)
    json_handler.setFormatter(json_formatter)
    
    # Configure logger
    pdf_logger = logging.getLogger('pdf_extractor')
    pdf_logger.setLevel(logging.DEBUG)
    pdf_logger.addHandler(all_handler)
    pdf_logger.addHandler(error_handler)
    pdf_logger.addHandler(json_handler)
    
    return pdf_logger