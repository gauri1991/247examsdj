"""
Custom decorators for the exam portal application.
Provides rate limiting, security checks, and other utilities.
"""

from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
try:
    from django_ratelimit.decorators import ratelimit
    from django_ratelimit.core import is_ratelimited
    RATELIMIT_AVAILABLE = True
except ImportError:
    RATELIMIT_AVAILABLE = False
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def is_ratelimited(*args, **kwargs):
        return False
from .security import check_suspicious_activity, log_security_event


def api_rate_limit(rate=None):
    """
    Rate limiting decorator for API endpoints.
    
    Args:
        rate: Rate limit string (e.g., '60/m' for 60 requests per minute)
    """
    if not RATELIMIT_AVAILABLE or not getattr(settings, 'RATELIMIT_ENABLE', True):
        def decorator(view_func):
            return view_func
        return decorator
        
    if rate is None:
        rate = getattr(settings, 'API_RATE_LIMIT', '60/m')
    
    def decorator(view_func):
        @wraps(view_func)
        @ratelimit(key='ip', rate=rate, method='ALL', block=True)
        def wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def login_rate_limit(view_func):
    """
    Rate limiting decorator for login attempts.
    """
    if not RATELIMIT_AVAILABLE or not getattr(settings, 'RATELIMIT_ENABLE', True):
        return view_func
        
    rate = getattr(settings, 'LOGIN_RATE_LIMIT', '5/m')
    
    @wraps(view_func)
    @ratelimit(key='ip', rate=rate, method='POST', block=False)
    def wrapped_view(request, *args, **kwargs):
        if request.method == 'POST' and is_ratelimited(request, group='login', key='ip', rate=rate, method='POST'):
            log_security_event(request, 'RATE_LIMIT_EXCEEDED', f'Login attempts exceeded: {rate}')
            
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'error': 'Too many login attempts. Please try again later.'
                }, status=429)
            else:
                messages.error(request, 'Too many login attempts. Please try again later.')
                return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapped_view


def test_submission_rate_limit(view_func):
    """
    Rate limiting decorator for test submissions.
    """
    if not RATELIMIT_AVAILABLE or not getattr(settings, 'RATELIMIT_ENABLE', True):
        return view_func
        
    rate = getattr(settings, 'TEST_SUBMISSION_RATE_LIMIT', '10/m')
    
    @wraps(view_func)
    @ratelimit(key='user', rate=rate, method='POST', block=False)
    def wrapped_view(request, *args, **kwargs):
        if request.method == 'POST' and is_ratelimited(request, group='test_submission', key='user', rate=rate, method='POST'):
            log_security_event(request, 'RATE_LIMIT_EXCEEDED', f'Test submissions exceeded: {rate}')
            
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'error': 'Too many test submissions. Please slow down.'
                }, status=429)
            else:
                messages.error(request, 'Too many test submissions. Please slow down.')
                return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapped_view


def require_role(allowed_roles):
    """
    Decorator to require specific user roles.
    
    Args:
        allowed_roles: List of allowed roles or single role string
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.role not in allowed_roles:
                log_security_event(request, 'UNAUTHORIZED_ACCESS', f'User role: {request.user.role}, Required: {allowed_roles}')
                
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'error': 'Access denied'}, status=403)
                else:
                    messages.error(request, 'Access denied.')
                    return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def security_check(view_func):
    """
    Decorator to perform security checks on requests.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Check for suspicious activity
        if check_suspicious_activity(request, view_func.__name__):
            log_security_event(request, 'SUSPICIOUS_ACTIVITY', f'View: {view_func.__name__}')
            
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': 'Request blocked for security reasons'}, status=403)
            else:
                return HttpResponseForbidden('Request blocked for security reasons')
        
        return view_func(request, *args, **kwargs)
    return wrapped_view


def ajax_required(view_func):
    """
    Decorator to require AJAX requests.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        return view_func(request, *args, **kwargs)
    return wrapped_view


def htmx_required(view_func):
    """
    Decorator to require HTMX requests.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.headers.get('HX-Request'):
            return JsonResponse({'error': 'HTMX request required'}, status=400)
        return view_func(request, *args, **kwargs)
    return wrapped_view


def validate_test_access(view_func):
    """
    Decorator to validate test access permissions and timing.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        from exams.models import Test, TestAttempt
        from django.shortcuts import get_object_or_404
        from django.utils import timezone
        
        # Get test ID from URL parameters
        test_id = kwargs.get('test_id') or kwargs.get('id')
        if not test_id:
            return JsonResponse({'error': 'Test ID required'}, status=400)
        
        test = get_object_or_404(Test, id=test_id)
        
        # Check if test is active
        now = timezone.now()
        if test.start_time and now < test.start_time:
            return JsonResponse({'error': 'Test has not started yet'}, status=403)
        
        if test.end_time and now > test.end_time:
            return JsonResponse({'error': 'Test has ended'}, status=403)
        
        # Check if user has already completed the test
        if request.user.is_authenticated:
            existing_attempt = TestAttempt.objects.filter(
                test=test, 
                user=request.user,
                status='evaluated'
            ).first()
            
            if existing_attempt and not test.allow_retake:
                return JsonResponse({'error': 'Test already completed'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapped_view


def log_user_action(action_name):
    """
    Decorator to log user actions for audit purposes.
    
    Args:
        action_name: Name of the action being performed
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            import logging
            
            logger = logging.getLogger('user_actions')
            
            user = request.user if request.user.is_authenticated else None
            user_info = f"User: {user.username}" if user else "Anonymous"
            
            # Log the action
            logger.info(f"Action: {action_name} | {user_info} | IP: {request.META.get('REMOTE_ADDR', 'Unknown')}")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def cache_control(max_age=300, private=False, no_cache=False):
    """
    Decorator to set cache control headers.
    
    Args:
        max_age: Maximum age in seconds
        private: Whether the response is private
        no_cache: Whether to disable caching
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            
            if no_cache:
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            else:
                cache_type = 'private' if private else 'public'
                response['Cache-Control'] = f'{cache_type}, max-age={max_age}'
            
            return response
        return wrapped_view
    return decorator