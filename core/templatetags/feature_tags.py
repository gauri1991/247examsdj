"""
Template tags for feature flag system.

Usage in templates:
    {% load feature_tags %}

    {% if_feature_enabled 'PDF_EXTRACTOR_ENABLED' %}
        <div>PDF Extractor is enabled</div>
    {% endif_feature_enabled %}

    {% feature_enabled 'AI_GRADING_ENABLED' as ai_enabled %}
    {% if ai_enabled %}
        <button>Use AI Grading</button>
    {% endif %}
"""
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def feature_enabled(feature_name):
    """
    Check if a feature is enabled.

    Usage:
        {% feature_enabled 'PDF_EXTRACTOR_ENABLED' as is_enabled %}
        {% if is_enabled %}
            ...
        {% endif %}
    """
    return settings.FEATURES.get(feature_name, False)


@register.simple_tag
def get_feature_flags():
    """
    Get all feature flags.

    Usage:
        {% get_feature_flags as all_features %}
        {% for name, enabled in all_features.items %}
            {{ name }}: {{ enabled }}
        {% endfor %}
    """
    return settings.FEATURES


@register.filter
def feature_check(feature_name):
    """
    Filter to check if a feature is enabled.

    Usage:
        {% if 'PDF_EXTRACTOR_ENABLED'|feature_check %}
            ...
        {% endif %}
    """
    return settings.FEATURES.get(feature_name, False)


@register.inclusion_tag('core/feature_badge.html', takes_context=True)
def feature_badge(context, feature_name):
    """
    Display a badge showing feature status.

    Usage:
        {% feature_badge 'PDF_EXTRACTOR_ENABLED' %}
    """
    is_enabled = settings.FEATURES.get(feature_name, False)
    return {
        'feature_name': feature_name,
        'is_enabled': is_enabled,
    }
