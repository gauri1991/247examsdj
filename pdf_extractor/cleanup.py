import os
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from .models import PDFDocument, ProcessingJob

logger = logging.getLogger(__name__)


class FileCleanupManager:
    """
    Manages cleanup of temporary files and old PDF documents
    """
    
    def __init__(self):
        # Configuration
        self.temp_dir = getattr(settings, 'PDF_TEMP_DIR', '/tmp/pdf_processing')
        self.max_file_age_days = getattr(settings, 'PDF_MAX_FILE_AGE_DAYS', 30)
        self.max_temp_age_hours = getattr(settings, 'PDF_MAX_TEMP_AGE_HOURS', 24)
        self.cleanup_batch_size = 100
        
        # Create temp directory if it doesn't exist
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
    
    def cleanup_temporary_files(self) -> Dict[str, Any]:
        """
        Clean up temporary files created during processing
        """
        cleanup_stats = {
            'files_removed': 0,
            'bytes_freed': 0,
            'errors': []
        }
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.max_temp_age_hours)
            
            # Clean up temp directory
            if os.path.exists(self.temp_dir):
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            # Check file age
                            file_stat = os.stat(file_path)
                            file_time = datetime.fromtimestamp(file_stat.st_mtime)
                            
                            if file_time < cutoff_time:
                                file_size = file_stat.st_size
                                os.remove(file_path)
                                cleanup_stats['files_removed'] += 1
                                cleanup_stats['bytes_freed'] += file_size
                                logger.debug(f"Removed temporary file: {file_path}")
                        
                        except Exception as e:
                            cleanup_stats['errors'].append(f"Error removing {file_path}: {str(e)}")
                            logger.error(f"Failed to remove temporary file {file_path}: {str(e)}")
                
                # Remove empty directories
                for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            if not os.listdir(dir_path):
                                os.rmdir(dir_path)
                                logger.debug(f"Removed empty directory: {dir_path}")
                        except Exception as e:
                            logger.error(f"Failed to remove directory {dir_path}: {str(e)}")
            
        except Exception as e:
            cleanup_stats['errors'].append(f"Cleanup error: {str(e)}")
            logger.error(f"Temporary file cleanup failed: {str(e)}")
        
        return cleanup_stats
    
    def cleanup_old_documents(self) -> Dict[str, Any]:
        """
        Clean up old PDF documents and their associated data
        """
        cleanup_stats = {
            'documents_removed': 0,
            'questions_removed': 0,
            'jobs_removed': 0,
            'bytes_freed': 0,
            'errors': []
        }
        
        try:
            cutoff_date = timezone.now() - timedelta(days=self.max_file_age_days)
            
            # Find old documents
            old_documents = PDFDocument.objects.filter(
                uploaded_at__lt=cutoff_date,
                status__in=['completed', 'failed']
            ).select_related('processing_jobs', 'extracted_questions')[:self.cleanup_batch_size]
            
            for document in old_documents:
                try:
                    # Calculate stats before deletion
                    questions_count = document.extracted_questions.count()
                    jobs_count = document.processing_jobs.count()
                    file_size = document.file_size
                    
                    # Delete the file from storage
                    if document.file:
                        try:
                            document.file.delete(save=False)
                            cleanup_stats['bytes_freed'] += file_size
                        except Exception as e:
                            logger.error(f"Failed to delete file for document {document.id}: {str(e)}")
                    
                    # Delete the document (cascades to related objects)
                    document.delete()
                    
                    # Update stats
                    cleanup_stats['documents_removed'] += 1
                    cleanup_stats['questions_removed'] += questions_count
                    cleanup_stats['jobs_removed'] += jobs_count
                    
                    logger.info(f"Cleaned up document {document.filename} (age: {(timezone.now() - document.uploaded_at).days} days)")
                
                except Exception as e:
                    cleanup_stats['errors'].append(f"Error cleaning document {document.id}: {str(e)}")
                    logger.error(f"Failed to clean up document {document.id}: {str(e)}")
        
        except Exception as e:
            cleanup_stats['errors'].append(f"Document cleanup error: {str(e)}")
            logger.error(f"Document cleanup failed: {str(e)}")
        
        return cleanup_stats
    
    def cleanup_failed_jobs(self) -> Dict[str, Any]:
        """
        Clean up failed processing jobs older than a certain age
        """
        cleanup_stats = {
            'jobs_cleaned': 0,
            'errors': []
        }
        
        try:
            # Find old failed jobs
            cutoff_date = timezone.now() - timedelta(days=7)  # Keep failed jobs for 7 days
            
            failed_jobs = ProcessingJob.objects.filter(
                status='failed',
                created_at__lt=cutoff_date
            )[:self.cleanup_batch_size]
            
            for job in failed_jobs:
                try:
                    # Clean up any temporary data associated with the job
                    self._cleanup_job_temp_files(job)
                    
                    # Update job to indicate it was cleaned
                    job.error_details = job.error_details or {}
                    job.error_details['cleaned_up'] = True
                    job.error_details['cleanup_date'] = timezone.now().isoformat()
                    job.save()
                    
                    cleanup_stats['jobs_cleaned'] += 1
                    logger.info(f"Cleaned up failed job {job.id}")
                
                except Exception as e:
                    cleanup_stats['errors'].append(f"Error cleaning job {job.id}: {str(e)}")
                    logger.error(f"Failed to clean up job {job.id}: {str(e)}")
        
        except Exception as e:
            cleanup_stats['errors'].append(f"Failed job cleanup error: {str(e)}")
            logger.error(f"Failed job cleanup failed: {str(e)}")
        
        return cleanup_stats
    
    def _cleanup_job_temp_files(self, job: ProcessingJob) -> None:
        """
        Clean up temporary files associated with a specific job
        """
        # Construct possible temp file paths
        job_temp_dir = os.path.join(self.temp_dir, str(job.id))
        
        if os.path.exists(job_temp_dir):
            try:
                shutil.rmtree(job_temp_dir)
                logger.debug(f"Removed job temp directory: {job_temp_dir}")
            except Exception as e:
                logger.error(f"Failed to remove job temp directory {job_temp_dir}: {str(e)}")
    
    def get_cleanup_summary(self) -> Dict[str, Any]:
        """
        Get summary of items pending cleanup
        """
        cutoff_date = timezone.now() - timedelta(days=self.max_file_age_days)
        
        summary = {
            'old_documents': PDFDocument.objects.filter(
                uploaded_at__lt=cutoff_date,
                status__in=['completed', 'failed']
            ).count(),
            'failed_jobs': ProcessingJob.objects.filter(
                status='failed',
                created_at__lt=timezone.now() - timedelta(days=7)
            ).count(),
            'temp_files': self._count_temp_files()
        }
        
        return summary
    
    def _count_temp_files(self) -> int:
        """
        Count temporary files
        """
        count = 0
        cutoff_time = datetime.now() - timedelta(hours=self.max_temp_age_hours)
        
        if os.path.exists(self.temp_dir):
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_time = datetime.fromtimestamp(os.stat(file_path).st_mtime)
                        if file_time < cutoff_time:
                            count += 1
                    except:
                        pass
        
        return count
    
    def perform_full_cleanup(self) -> Dict[str, Any]:
        """
        Perform full cleanup of all types
        """
        logger.info("Starting full cleanup process")
        
        results = {
            'timestamp': timezone.now().isoformat(),
            'temp_files': self.cleanup_temporary_files(),
            'old_documents': self.cleanup_old_documents(),
            'failed_jobs': self.cleanup_failed_jobs()
        }
        
        # Calculate totals
        results['totals'] = {
            'files_removed': results['temp_files']['files_removed'],
            'documents_removed': results['old_documents']['documents_removed'],
            'bytes_freed': results['temp_files']['bytes_freed'] + results['old_documents']['bytes_freed'],
            'total_errors': len(results['temp_files']['errors']) + 
                           len(results['old_documents']['errors']) + 
                           len(results['failed_jobs']['errors'])
        }
        
        logger.info(f"Cleanup completed. Files removed: {results['totals']['files_removed']}, "
                   f"Documents removed: {results['totals']['documents_removed']}, "
                   f"Bytes freed: {results['totals']['bytes_freed']:,}")
        
        return results


# Singleton instance
cleanup_manager = FileCleanupManager()


class TempFileContext:
    """
    Context manager for temporary files during PDF processing
    """
    
    def __init__(self, prefix: str = 'pdf_', suffix: str = '.tmp'):
        self.prefix = prefix
        self.suffix = suffix
        self.temp_file_path = None
    
    def __enter__(self) -> Path:
        """
        Create a temporary file and return its path
        """
        import tempfile
        
        # Create temp file in the configured temp directory
        temp_dir = cleanup_manager.temp_dir
        
        fd, self.temp_file_path = tempfile.mkstemp(
            prefix=self.prefix,
            suffix=self.suffix,
            dir=temp_dir
        )
        
        # Close the file descriptor as we'll use the path
        os.close(fd)
        
        return Path(self.temp_file_path)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up the temporary file
        """
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
                logger.debug(f"Cleaned up temp file: {self.temp_file_path}")
            except Exception as e:
                logger.error(f"Failed to clean up temp file {self.temp_file_path}: {str(e)}")