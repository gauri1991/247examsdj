"""
Context processors for making data available in all templates.
"""
from django.conf import settings


def feature_flags(request):
    """
    Make feature flags available in all templates.

    Usage in templates:
        {% if features.PDF_EXTRACTOR_ENABLED %}
            <a href="{% url 'pdf_extractor:upload' %}">Upload PDF</a>
        {% endif %}
    """
    return {
        'features': getattr(settings, 'FEATURES', {}),
    }
