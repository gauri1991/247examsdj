from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recent-activity/', views.recent_activity, name='recent-activity'),
    path('logout/', views.logout_view, name='logout'),
]