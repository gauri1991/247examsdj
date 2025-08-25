from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Clean API endpoints for /api/users/
urlpatterns = [
    path('register/', views.RegisterAPIView.as_view(), name='api-register'),
    path('login/', views.LoginAPIView.as_view(), name='api-login'),
    path('refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('profile/', views.ProfileAPIView.as_view(), name='api-profile'),
    path('list/', views.UserListAPIView.as_view(), name='api-user-list'),
]