from django.urls import path, include
from . import views

app_name = 'knowledge'

urlpatterns = [
    # Main interfaces
    path('topics/', views.topic_browser, name='topic_browser'),
    path('exam-selector/', views.exam_topic_selector, name='exam_topic_selector'),
    path('admin/manager/', views.admin_topic_manager, name='admin_topic_manager'),
    path('editor/', views.topic_editor, name='topic_editor'),
    
    # Legacy API endpoints (keep for backward compatibility)
    path('api/subjects/', views.subjects_list_api, name='subjects_list_api'),
    path('api/subjects/<uuid:subject_id>/topics/', views.subject_topics_api, name='subject_topics_api'),
    path('api/topics/<uuid:topic_id>/', views.topic_detail_api, name='topic_detail_api'),
    path('api/exams/<uuid:exam_id>/compatible-topics/', views.compatible_topics_api, name='compatible_topics_api'),
    path('api/search/', views.topic_search_api, name='topic_search_api'),
    path('api/admin/stats/', views.admin_taxonomy_stats_api, name='admin_taxonomy_stats_api'),
    
    # Edit API endpoints
    path('api/subjects/<uuid:subject_id>/update/', views.update_subject_api, name='update_subject_api'),
    path('api/subjects/<uuid:subject_id>/delete/', views.delete_subject_api, name='delete_subject_api'),
    path('api/topics/<uuid:topic_id>/update/', views.update_topic_api, name='update_topic_api'),
    path('api/topics/<uuid:topic_id>/delete/', views.delete_topic_api, name='delete_topic_api'),
    path('api/topics/reorder/', views.reorder_topics_api, name='reorder_topics_api'),
]