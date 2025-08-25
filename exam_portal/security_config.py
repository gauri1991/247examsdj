"""
Security configuration for the exam portal application.
Contains security settings, monitoring, and incident response configurations.
"""

from django.conf import settings
import logging

# Security Headers Configuration
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
}

# Rate Limiting Configuration
RATE_LIMITS = {
    'api_general': '100/m',      # General API calls
    'api_strict': '30/m',        # Sensitive API calls
    'login': '5/m',              # Login attempts
    'registration': '3/m',       # Registration attempts
    'password_reset': '3/m',     # Password reset requests
    'test_submission': '10/m',   # Test submissions
    'file_upload': '10/m',       # File uploads
    'search': '60/m',            # Search requests
}

# Content Security Policy
CSP_DIRECTIVES = {
    'default-src': ["'self'"],
    'script-src': [
        "'self'",
        "'unsafe-inline'",  # Required for Alpine.js
        "https://unpkg.com",
        "https://cdn.jsdelivr.net",
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",  # Required for Tailwind CSS
        "https://cdn.jsdelivr.net",
    ],
    'img-src': ["'self'", "data:", "https:"],
    'font-src': ["'self'", "data:", "https:"],
    'connect-src': ["'self'"],
    'frame-src': ["'none'"],
    'object-src': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
}

# File Upload Security
FILE_UPLOAD_CONFIG = {
    'max_size': 5 * 1024 * 1024,  # 5MB
    'allowed_extensions': [
        '.jpg', '.jpeg', '.png', '.gif',  # Images
        '.pdf',                           # Documents
        '.doc', '.docx',                  # Word documents
        '.xls', '.xlsx', '.csv',          # Spreadsheets
    ],
    'blocked_extensions': [
        '.exe', '.bat', '.sh', '.php', '.jsp',
        '.asp', '.aspx', '.js', '.html', '.htm',
        '.zip', '.rar', '.tar', '.gz',
    ],
    'scan_for_malware': True,
    'quarantine_suspicious': True,
}

# Input Validation Rules
INPUT_VALIDATION = {
    'max_text_length': 10000,
    'max_title_length': 200,
    'max_name_length': 100,
    'allowed_html_tags': [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
        'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'
    ],
    'blocked_patterns': [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'onclick=',
    ],
}

# Security Monitoring
SECURITY_MONITORING = {
    'failed_login_threshold': 5,
    'suspicious_activity_threshold': 10,
    'brute_force_window_minutes': 15,
    'account_lockout_duration_minutes': 30,
    'monitor_user_agents': True,
    'monitor_ip_changes': True,
    'log_all_auth_events': True,
}

# Incident Response
INCIDENT_RESPONSE = {
    'auto_block_ips': True,
    'notify_admins': True,
    'admin_emails': getattr(settings, 'ADMIN_EMAILS', []),
    'emergency_contact': getattr(settings, 'EMERGENCY_CONTACT', ''),
    'incident_log_retention_days': 90,
}

# Security Levels
SECURITY_LEVELS = {
    'low': {
        'rate_limit_multiplier': 2.0,
        'require_2fa': False,
        'strict_csp': False,
        'additional_logging': False,
    },
    'medium': {
        'rate_limit_multiplier': 1.0,
        'require_2fa': False,
        'strict_csp': True,
        'additional_logging': True,
    },
    'high': {
        'rate_limit_multiplier': 0.5,
        'require_2fa': True,
        'strict_csp': True,
        'additional_logging': True,
    },
}

# Current security level (can be overridden in settings)
CURRENT_SECURITY_LEVEL = getattr(settings, 'SECURITY_LEVEL', 'medium')

def get_security_config():
    """Get the current security configuration based on the security level."""
    base_config = {
        'headers': SECURITY_HEADERS,
        'rate_limits': RATE_LIMITS,
        'csp': CSP_DIRECTIVES,
        'file_upload': FILE_UPLOAD_CONFIG,
        'input_validation': INPUT_VALIDATION,
        'monitoring': SECURITY_MONITORING,
        'incident_response': INCIDENT_RESPONSE,
    }
    
    # Apply security level modifications
    level_config = SECURITY_LEVELS.get(CURRENT_SECURITY_LEVEL, SECURITY_LEVELS['medium'])
    
    # Adjust rate limits based on security level
    multiplier = level_config['rate_limit_multiplier']
    adjusted_limits = {}
    for key, limit in RATE_LIMITS.items():
        rate, period = limit.split('/')
        adjusted_rate = max(1, int(int(rate) * multiplier))
        adjusted_limits[key] = f"{adjusted_rate}/{period}"
    
    base_config['rate_limits'] = adjusted_limits
    base_config['security_level'] = level_config
    
    return base_config

def log_security_incident(incident_type, details, severity='medium'):
    """Log a security incident."""
    logger = logging.getLogger('security')
    
    incident_data = {
        'type': incident_type,
        'details': details,
        'severity': severity,
        'security_level': CURRENT_SECURITY_LEVEL,
    }
    
    if severity == 'high':
        logger.critical(f"SECURITY INCIDENT: {incident_data}")
    elif severity == 'medium':
        logger.warning(f"SECURITY EVENT: {incident_data}")
    else:
        logger.info(f"SECURITY LOG: {incident_data}")

def should_block_request(request_data):
    """Determine if a request should be blocked based on security rules."""
    config = get_security_config()
    monitoring = config['monitoring']
    
    # Check for suspicious patterns
    suspicious_indicators = []
    
    # User agent checks
    if monitoring['monitor_user_agents']:
        user_agent = request_data.get('user_agent', '').lower()
        if not user_agent or any(bot in user_agent for bot in ['bot', 'crawler', 'scraper']):
            suspicious_indicators.append('suspicious_user_agent')
    
    # Rate limiting checks (handled by decorators)
    
    # IP reputation checks (could be extended with external services)
    
    return len(suspicious_indicators) > 0, suspicious_indicators

# Export configuration
__all__ = [
    'get_security_config',
    'log_security_incident',
    'should_block_request',
    'SECURITY_HEADERS',
    'RATE_LIMITS',
    'CSP_DIRECTIVES',
    'FILE_UPLOAD_CONFIG',
]