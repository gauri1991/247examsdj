"""
URL configuration for exam_portal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),

    # Health and monitoring endpoints
    path('health/', include('core.monitoring_urls')),

    # Template views (no namespaces to maintain existing URL names)
    path('users/', include('users.urls')),
    path('exams/', include('exams.urls')),
    path('questions/', include('questions.urls')),
    path('analytics/', include('analytics.urls')),
    path('knowledge/', include('knowledge.urls')),

    # Centralized API endpoints
    path('api/users/', include('users.api_urls')),
    path('api/exams/', include('exams.api_urls')),
    path('api/questions/', include('questions.api_urls')),
]

# Conditionally include feature-dependent URLs
if settings.FEATURES.get('PDF_EXTRACTOR_ENABLED', False):
    urlpatterns.append(path('pdf-extractor/', include('pdf_extractor.urls')))

if settings.FEATURES.get('PAYMENT_SYSTEM_ENABLED', False):
    urlpatterns.append(path('payments/', include('payments.urls')))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Add debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
