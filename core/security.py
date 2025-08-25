"""
Security utilities for the exam portal application.
Provides input sanitization, validation, and other security features.
"""

import re
import bleach
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.conf import settings
from typing import Any, Dict, List, Optional


# Allowed HTML tags and attributes for user content
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
    'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'width', 'height'],
}


def sanitize_html(content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        content: Raw HTML content
        
    Returns:
        Sanitized HTML content
    """
    if not content:
        return ''
    
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )


def sanitize_user_input(data: str) -> str:
    """
    Sanitize user input by removing potentially dangerous content.
    
    Args:
        data: Raw user input
        
    Returns:
        Sanitized input
    """
    if not data:
        return ''
    
    # Remove null bytes and other control characters
    data = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', data)
    
    # Escape HTML entities
    data = escape(data)
    
    return data.strip()


def validate_file_upload(uploaded_file) -> bool:
    """
    Validate uploaded file for security.
    
    Args:
        uploaded_file: Django UploadedFile object
        
    Returns:
        True if file is safe, False otherwise
        
    Raises:
        ValidationError: If file is not safe
    """
    # Check file size
    max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 5242880)  # 5MB
    if uploaded_file.size > max_size:
        raise ValidationError(f'File size exceeds maximum allowed size of {max_size} bytes.')
    
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv']
    file_extension = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''
    
    if f'.{file_extension}' not in allowed_extensions:
        raise ValidationError(f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}')
    
    # Check for dangerous content in filename
    dangerous_patterns = [
        r'\.\./',  # Directory traversal
        r'<script',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'data:',  # Data URLs
        r'vbscript:',  # VBScript protocol
    ]
    
    filename_lower = uploaded_file.name.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, filename_lower):
            raise ValidationError('Filename contains potentially dangerous content.')
    
    return True


def validate_question_content(question_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize question content.
    
    Args:
        question_data: Dictionary containing question data
        
    Returns:
        Sanitized question data
    """
    sanitized_data = {}
    
    # Sanitize text fields
    text_fields = ['question_text', 'explanation', 'topic', 'subtopic', 'expected_answer']
    for field in text_fields:
        if field in question_data:
            if field in ['question_text', 'explanation', 'expected_answer']:
                # Allow limited HTML for rich content
                sanitized_data[field] = sanitize_html(question_data[field])
            else:
                # Plain text only
                sanitized_data[field] = sanitize_user_input(question_data[field])
    
    # Validate numeric fields
    numeric_fields = ['marks', 'negative_marks']
    for field in numeric_fields:
        if field in question_data:
            try:
                value = float(question_data[field])
                if field == 'marks' and (value < 0 or value > 100):
                    raise ValidationError(f'{field} must be between 0 and 100.')
                if field == 'negative_marks' and (value < 0 or value > 50):
                    raise ValidationError(f'{field} must be between 0 and 50.')
                sanitized_data[field] = value
            except (ValueError, TypeError):
                raise ValidationError(f'{field} must be a valid number.')
    
    # Validate choice fields
    if 'question_type' in question_data:
        allowed_types = ['mcq', 'multi_select', 'true_false', 'fill_blank', 'essay']
        if question_data['question_type'] not in allowed_types:
            raise ValidationError('Invalid question type.')
        sanitized_data['question_type'] = question_data['question_type']
    
    if 'difficulty' in question_data:
        allowed_difficulties = ['easy', 'medium', 'hard']
        if question_data['difficulty'] not in allowed_difficulties:
            raise ValidationError('Invalid difficulty level.')
        sanitized_data['difficulty'] = question_data['difficulty']
    
    return sanitized_data


def validate_test_attempt_data(attempt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize test attempt data.
    
    Args:
        attempt_data: Dictionary containing test attempt data
        
    Returns:
        Sanitized attempt data
    """
    sanitized_data = {}
    
    # Validate answers
    if 'answers' in attempt_data:
        sanitized_answers = []
        for answer in attempt_data['answers']:
            sanitized_answer = {}
            
            # Sanitize text answers
            if 'text_answer' in answer:
                sanitized_answer['text_answer'] = sanitize_user_input(answer['text_answer'])
            
            # Validate boolean answers
            if 'boolean_answer' in answer:
                sanitized_answer['boolean_answer'] = bool(answer['boolean_answer'])
            
            # Validate selected options (ensure they're valid UUIDs)
            if 'selected_options' in answer:
                sanitized_options = []
                for option_id in answer['selected_options']:
                    if isinstance(option_id, str) and len(option_id) == 36:  # Basic UUID validation
                        sanitized_options.append(option_id)
                sanitized_answer['selected_options'] = sanitized_options
            
            sanitized_answers.append(sanitized_answer)
        
        sanitized_data['answers'] = sanitized_answers
    
    return sanitized_data


def check_suspicious_activity(request, action: str) -> bool:
    """
    Check for suspicious activity patterns.
    
    Args:
        request: Django request object
        action: Action being performed
        
    Returns:
        True if activity seems suspicious, False otherwise
    """
    # Get user's IP address
    ip_address = get_client_ip(request)
    
    # Check for common suspicious patterns
    suspicious_indicators = [
        # Check user agent
        not request.META.get('HTTP_USER_AGENT', '').strip(),
        
        # Check for automated requests (basic check)
        'bot' in request.META.get('HTTP_USER_AGENT', '').lower(),
        'curl' in request.META.get('HTTP_USER_AGENT', '').lower(),
        'wget' in request.META.get('HTTP_USER_AGENT', '').lower(),
        
        # Check for unusual referrer patterns
        request.META.get('HTTP_REFERER', '') and 
        not any(allowed_host in request.META.get('HTTP_REFERER', '') 
                for allowed_host in getattr(settings, 'ALLOWED_HOSTS', [])),
    ]
    
    return any(suspicious_indicators)


def get_client_ip(request) -> str:
    """
    Get the client's IP address from the request.
    
    Args:
        request: Django request object
        
    Returns:
        Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def log_security_event(request, event_type: str, details: str = '') -> None:
    """
    Log security-related events.
    
    Args:
        request: Django request object
        event_type: Type of security event
        details: Additional details about the event
    """
    import logging
    
    logger = logging.getLogger('security')
    
    ip_address = get_client_ip(request)
    user = getattr(request, 'user', None)
    user_info = f"User: {user.username if user and user.is_authenticated else 'Anonymous'}"
    
    logger.warning(
        f"Security Event: {event_type} | IP: {ip_address} | {user_info} | Details: {details}"
    )


class SecurityMiddleware:
    """
    Custom security middleware for additional protection.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check for suspicious activity
        if check_suspicious_activity(request, 'general'):
            log_security_event(request, 'SUSPICIOUS_ACTIVITY', 'Automated request detected')
        
        response = self.get_response(request)
        
        # Add additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response