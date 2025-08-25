from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router for clean /api/exams/ endpoints
router = DefaultRouter()
router.register('', views.ExamViewSet, basename='exam-api')  # /api/exams/
router.register('tests', views.TestViewSet, basename='test-api')  # /api/exams/tests/
router.register('attempts', views.TestAttemptViewSet, basename='attempt-api')  # /api/exams/attempts/

urlpatterns = [
    path('', include(router.urls)),
]