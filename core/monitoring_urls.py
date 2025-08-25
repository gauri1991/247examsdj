"""
URL configuration for monitoring and health check endpoints
"""

from django.urls import path
from . import monitoring

urlpatterns = [
    path('', monitoring.health_check, name='health_check'),
    path('readiness/', monitoring.readiness_check, name='readiness_check'),
    path('liveness/', monitoring.liveness_check, name='liveness_check'),
    path('metrics/', monitoring.metrics, name='metrics'),
]