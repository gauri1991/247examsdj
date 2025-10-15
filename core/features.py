"""
Feature Flag System for Exam Portal
Provides centralized feature flag management with environment variable configuration.
"""
from django.conf import settings
from functools import wraps
from django.http import Http404
from django.shortcuts import render


class FeatureFlags:
    """
    Centralized feature flag management system.
    All feature flags are configured via environment variables in settings.py
    """

    @staticmethod
    def is_enabled(feature_name):
        """
        Check if a feature is enabled.

        Args:
            feature_name: Name of the feature flag (e.g., 'PDF_EXTRACTOR_ENABLED')

        Returns:
            bool: True if feature is enabled, False otherwise
        """
        return getattr(settings, 'FEATURES', {}).get(feature_name, False)

    @staticmethod
    def get_all():
        """
        Get all feature flags and their status.

        Returns:
            dict: Dictionary of all feature flags
        """
        return getattr(settings, 'FEATURES', {})

    @staticmethod
    def require(feature_name, redirect_url=None, raise_404=True):
        """
        Decorator to require a feature flag for a view.

        Args:
            feature_name: Name of the feature flag
            redirect_url: Optional URL to redirect to if feature is disabled
            raise_404: If True and redirect_url is None, raise 404. Otherwise show error page.

        Usage:
            @FeatureFlags.require('PDF_EXTRACTOR_ENABLED')
            def pdf_upload_view(request):
                ...
        """
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                if not FeatureFlags.is_enabled(feature_name):
                    if redirect_url:
                        from django.shortcuts import redirect
                        return redirect(redirect_url)
                    elif raise_404:
                        raise Http404("Feature not available")
                    else:
                        return render(request, 'core/feature_disabled.html', {
                            'feature_name': feature_name
                        }, status=403)
                return view_func(request, *args, **kwargs)
            return wrapper
        return decorator


# Convenience functions for commonly used features
def is_pdf_extractor_enabled():
    """Check if PDF extractor feature is enabled."""
    return FeatureFlags.is_enabled('PDF_EXTRACTOR_ENABLED')


def is_ai_grading_enabled():
    """Check if AI grading feature is enabled."""
    return FeatureFlags.is_enabled('AI_GRADING_ENABLED')


def is_advanced_analytics_enabled():
    """Check if advanced analytics feature is enabled."""
    return FeatureFlags.is_enabled('ADVANCED_ANALYTICS_ENABLED')


def is_payment_system_enabled():
    """Check if payment system is enabled."""
    return FeatureFlags.is_enabled('PAYMENT_SYSTEM_ENABLED')


def is_proctoring_enabled():
    """Check if proctoring feature is enabled."""
    return FeatureFlags.is_enabled('PROCTORING_ENABLED')


# Export commonly used items
__all__ = [
    'FeatureFlags',
    'is_pdf_extractor_enabled',
    'is_ai_grading_enabled',
    'is_advanced_analytics_enabled',
    'is_payment_system_enabled',
    'is_proctoring_enabled',
]
