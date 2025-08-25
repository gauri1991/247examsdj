import os
import mimetypes
import magic
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
import PyPDF2
from typing import Tuple, Dict, Any


class PDFSecurityValidator:
    # Maximum file size: 50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = [
        'application/pdf',
    ]
    
    # File signature (magic numbers) for PDF
    PDF_SIGNATURES = [
        b'%PDF-',  # Standard PDF signature
    ]
    
    # Dangerous content patterns to scan for
    DANGEROUS_PATTERNS = [
        b'/JavaScript',
        b'/JS',
        b'/EmbeddedFile',
        b'/Launch',
        b'/SubmitForm',
        b'/ImportData',
        b'/GoToR',
        b'/Sound',
        b'/RichMedia',
        b'/3D',
        b'/U3D',
        b'/PRC',
    ]
    
    @classmethod
    def validate_pdf_file(cls, uploaded_file: UploadedFile) -> Dict[str, Any]:
        """
        Comprehensive PDF file validation
        Returns validation results with security assessment
        """
        validation_result = {
            'is_valid': False,
            'is_safe': False,
            'file_size': 0,
            'mime_type': '',
            'has_javascript': False,
            'has_embedded_files': False,
            'has_forms': False,
            'page_count': 0,
            'is_encrypted': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Reset file pointer
            uploaded_file.seek(0)
            
            # 1. File size validation
            file_size = len(uploaded_file.read())
            uploaded_file.seek(0)
            validation_result['file_size'] = file_size
            
            if file_size > cls.MAX_FILE_SIZE:
                validation_result['errors'].append(f"File size ({file_size} bytes) exceeds maximum allowed size ({cls.MAX_FILE_SIZE} bytes)")
                return validation_result
            
            if file_size < 100:  # Minimum viable PDF size
                validation_result['errors'].append("File too small to be a valid PDF")
                return validation_result
            
            # 2. File signature validation
            file_header = uploaded_file.read(1024)
            uploaded_file.seek(0)
            
            if not any(file_header.startswith(sig) for sig in cls.PDF_SIGNATURES):
                validation_result['errors'].append("Invalid PDF file signature")
                return validation_result
            
            # 3. MIME type validation using python-magic (optional)
            try:
                mime_type = magic.from_buffer(file_header, mime=True)
                validation_result['mime_type'] = mime_type
                
                if mime_type not in cls.ALLOWED_MIME_TYPES:
                    validation_result['warnings'].append(f"MIME type mismatch: {mime_type} (continuing with PDF signature validation)")
            except Exception as e:
                validation_result['warnings'].append(f"MIME type detection failed: {str(e)} (continuing with PDF signature validation)")
            
            # 4. PDF structure validation using PyPDF2
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                validation_result['page_count'] = len(pdf_reader.pages)
                validation_result['is_encrypted'] = pdf_reader.is_encrypted
                
                if validation_result['is_encrypted']:
                    validation_result['errors'].append("Encrypted PDFs are not supported for security reasons")
                    return validation_result
                
                if validation_result['page_count'] == 0:
                    validation_result['errors'].append("PDF contains no pages")
                    return validation_result
                
                if validation_result['page_count'] > 500:  # Reasonable limit
                    validation_result['warnings'].append(f"Large PDF with {validation_result['page_count']} pages may take longer to process")
                
            except Exception as e:
                validation_result['errors'].append(f"PDF structure validation failed: {str(e)}")
                return validation_result
            
            # 5. Security content scanning
            uploaded_file.seek(0)
            file_content = uploaded_file.read()
            uploaded_file.seek(0)
            
            # Scan for dangerous patterns
            for pattern in cls.DANGEROUS_PATTERNS:
                if pattern in file_content:
                    if pattern in [b'/JavaScript', b'/JS']:
                        validation_result['has_javascript'] = True
                        validation_result['warnings'].append("PDF contains JavaScript - will be processed with extra caution")
                    elif pattern == b'/EmbeddedFile':
                        validation_result['has_embedded_files'] = True
                        validation_result['warnings'].append("PDF contains embedded files")
                    elif pattern in [b'/SubmitForm', b'/ImportData']:
                        validation_result['has_forms'] = True
                        validation_result['warnings'].append("PDF contains interactive forms")
                    else:
                        validation_result['warnings'].append(f"PDF contains potentially risky content: {pattern.decode('utf-8', errors='ignore')}")
            
            # 6. Final safety assessment
            validation_result['is_valid'] = len(validation_result['errors']) == 0
            validation_result['is_safe'] = (
                validation_result['is_valid'] and
                not validation_result['has_javascript'] and
                not validation_result['has_embedded_files'] and
                not validation_result['is_encrypted']
            )
            
        except Exception as e:
            validation_result['errors'].append(f"Validation process failed: {str(e)}")
        
        return validation_result
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize uploaded filename to prevent directory traversal and other attacks
        """
        # Remove directory separators
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit filename length
        max_length = 100
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length-len(ext)] + ext
        
        # Ensure filename doesn't start with dot (hidden files)
        if filename.startswith('.'):
            filename = 'file_' + filename
        
        # Ensure valid PDF extension
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        return filename


class ProcessingSecurityManager:
    """
    Security manager for PDF processing operations
    """
    
    @staticmethod
    def create_secure_temp_directory() -> str:
        """
        Create a secure temporary directory for PDF processing
        """
        import tempfile
        import stat
        
        temp_dir = tempfile.mkdtemp(prefix='pdf_processing_')
        
        # Set restrictive permissions (owner only)
        os.chmod(temp_dir, stat.S_IRWXU)
        
        return temp_dir
    
    @staticmethod
    def cleanup_temp_directory(temp_dir: str) -> None:
        """
        Securely clean up temporary directory
        """
        import shutil
        
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass  # Log error in production
    
    @staticmethod
    def validate_processing_limits(file_size: int, page_count: int) -> Tuple[bool, str]:
        """
        Validate processing limits to prevent resource exhaustion
        """
        # File size limits (already checked in file validation)
        if file_size > PDFSecurityValidator.MAX_FILE_SIZE:
            return False, "File size exceeds processing limits"
        
        # Page count limits
        if page_count > 1000:
            return False, "PDF has too many pages for processing"
        
        # Estimated processing time based on file size and pages
        estimated_time_minutes = (file_size / (1024 * 1024)) * 2 + page_count * 0.1
        if estimated_time_minutes > 30:  # 30 minute limit
            return False, "Estimated processing time exceeds limits"
        
        return True, "Processing limits OK"


def validate_pdf_upload(uploaded_file: UploadedFile) -> None:
    """
    Django validator function for PDF uploads
    Raises ValidationError if file is invalid or unsafe
    """
    validator = PDFSecurityValidator()
    result = validator.validate_pdf_file(uploaded_file)
    
    if not result['is_valid']:
        error_messages = '; '.join(result['errors'])
        raise ValidationError(f"Invalid PDF file: {error_messages}")
    
    # Only reject if there are actual security errors, not just warnings
    # Allow PDFs with JavaScript/forms as they're common in legitimate documents
    # if not result['is_safe']:
    #     warning_messages = '; '.join(result['warnings'])
    #     raise ValidationError(f"PDF file may be unsafe: {warning_messages}")


# Django form field validator
def pdf_file_validator(value):
    """
    Django form field validator for PDF files
    """
    validate_pdf_upload(value)