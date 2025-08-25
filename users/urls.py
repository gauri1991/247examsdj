from django.urls import path
from . import views

# Template views only - API endpoints moved to api_urls.py
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('admin/', views.admin_management, name='admin-management'),
    
    # Custom Admin User Management URLs
    path('admin/users/', views.admin_users_list, name='admin-users-list'),
    path('admin/users/create/', views.admin_user_create, name='admin-user-create'),
    path('admin/users/<uuid:user_id>/edit/', views.admin_user_edit, name='admin-user-edit'),
    path('admin/users/<uuid:user_id>/delete/', views.admin_user_delete, name='admin-user-delete'),
    path('admin/users/<uuid:user_id>/toggle-status/', views.admin_user_toggle_status, name='admin-user-toggle-status'),
    
    # Custom Admin Exam Management URLs
    path('admin/exams/', views.admin_exams_list, name='admin-exams-list'),
    path('admin/exams/<uuid:exam_id>/edit/', views.admin_exam_edit, name='admin-exam-edit'),
    path('admin/exams/<uuid:exam_id>/toggle-status/', views.admin_exam_toggle_status, name='admin-exam-toggle-status'),
    
    # Custom Admin Question Management URLs
    path('admin/questions/', views.admin_questions_list, name='admin-questions-list'),
    
    # Custom Admin Bulk Operations URLs  
    path('admin/users/bulk-activate/', views.admin_bulk_activate_users, name='admin-bulk-activate-users'),
    path('admin/users/bulk-deactivate/', views.admin_bulk_deactivate_users, name='admin-bulk-deactivate-users'),
    path('admin/users/export/', views.admin_export_users, name='admin-export-users'),
    
    # Custom Admin User Groups & Permissions URLs
    path('admin/user-groups/', views.admin_user_groups, name='admin-user-groups'),
    path('admin/permissions/', views.admin_permissions, name='admin-permissions'),
    
    # Custom Admin Settings URLs
    path('admin/settings/email/', views.admin_email_settings, name='admin-email-settings'),
    
    # Question Bank Permission Management APIs
    path('admin/api/question-bank-permissions/', views.question_bank_permissions_api, name='question-bank-permissions-api'),
    path('admin/api/teachers/', views.get_teachers_for_permissions, name='get-teachers-for-permissions'),
    path('admin/api/bulk-permissions/', views.bulk_permission_management, name='bulk-permission-management'),
    
    # User Settings API endpoints
    path('api/change-password/', views.change_password_api, name='change-password-api'),
    path('api/update-privacy/', views.update_privacy_settings_api, name='update-privacy-api'),
    path('api/update-exam-preferences/', views.update_exam_preferences_api, name='update-exam-preferences-api'),
    path('api/update-system-settings/', views.update_system_settings_api, name='update-system-settings-api'),
    path('api/delete-account/', views.delete_account_api, name='delete-account-api'),
    path('api/get-preferences/', views.get_user_preferences_api, name='get-preferences-api'),
]