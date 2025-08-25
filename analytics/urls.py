from django.urls import path
from . import views

urlpatterns = [
    # Template views
    path('', views.analytics_dashboard, name='analytics-dashboard'),
    path('dashboard/', views.analytics_dashboard, name='analytics'),
    path('test/<uuid:test_id>/', views.test_analytics, name='test-analytics'),
    path('student/<uuid:student_id>/', views.student_analytics, name='student-analytics'),
    path('export/', views.export_analytics, name='export-analytics'),
    
    # API endpoints
    path('api/', views.analytics_api, name='analytics-api'),
]