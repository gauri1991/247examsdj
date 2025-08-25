from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router for clean /api/questions/ endpoints
router = DefaultRouter()
router.register('banks', views.QuestionBankViewSet, basename='questionbank')  # /api/questions/banks/
router.register('', views.QuestionViewSet, basename='question')  # /api/questions/
router.register('answers', views.UserAnswerViewSet, basename='useranswer')  # /api/questions/answers/

urlpatterns = [
    path('', include(router.urls)),
]