from django.urls import path
from . import views

# Template views only - API endpoints moved to api_urls.py
urlpatterns = [
    path('', views.exam_list, name='exam-list'),
    path('manage/', views.enhanced_exam_management, name='exam-management'),
    path('manage/old/', views.exam_management, name='exam-management-old'),
    
    # Organization management
    path('organizations/', views.organization_list, name='organization-list'),
    path('organizations/create/', views.create_organization, name='create-organization'),
    path('organization/<uuid:org_id>/', views.organization_detail, name='organization-detail'),
    
    # Enhanced exam features
    path('<uuid:exam_id>/metadata/', views.exam_metadata_edit, name='exam-metadata-edit'),
    
    # AJAX endpoints
    path('ajax/search/', views.ajax_exam_search, name='ajax-exam-search'),
    path('<uuid:exam_id>/compatible-banks/', views.get_compatible_question_banks, name='compatible-question-banks'),
    path('create/', views.create_exam, name='create-exam'),
    path('<uuid:exam_id>/', views.exam_detail, name='exam-detail'),
    path('<uuid:exam_id>/edit/', views.edit_exam, name='edit-exam'),
    path('<uuid:exam_id>/create-test/', views.create_test, name='create-test'),
    path('test/<uuid:test_id>/', views.test_detail, name='test-detail'),
    path('test/<uuid:test_id>/edit/', views.edit_test, name='edit-test'),
    path('test/<uuid:test_id>/delete/', views.delete_test, name='delete-test'),
    path('test/<uuid:test_id>/start/', views.start_test, name='start-test'),
    path('take/<uuid:attempt_id>/', views.take_test, name='take-test'),
    path('take/<uuid:attempt_id>/save/', views.save_answer, name='save-answer'),
    path('take/<uuid:attempt_id>/submit/', views.submit_test, name='submit-test'),
    path('results/<uuid:attempt_id>/', views.test_results, name='test-results'),
    path('my-attempts/', views.my_attempts, name='my-attempts'),
    
    # Question Selection URLs
    path('test/<uuid:test_id>/configure-questions/', views.configure_question_selection, name='configure-question-selection'),
    path('test/<uuid:test_id>/save-selection-rules/', views.save_selection_rules, name='save-selection-rules'),
    path('test/<uuid:test_id>/preview-selection/', views.preview_question_selection, name='preview-question-selection'),
    path('test/<uuid:test_id>/apply-selection/', views.apply_question_selection, name='apply-question-selection'),
    path('test/<uuid:test_id>/apply-manual-selection/', views.apply_manual_selection, name='apply-manual-selection'),
    path('selection-template/save/', views.save_selection_template, name='save-selection-template'),
    path('selection-template/<uuid:template_id>/load/', views.load_selection_template, name='load-selection-template'),
    
    # Syllabus Tracking URLs
    path('syllabus-tracker/', views.syllabus_tracker, name='syllabus-tracker'),
    path('api/exam/<uuid:exam_id>/syllabus/', views.get_syllabus_data, name='get-syllabus-data'),
    path('api/node/<uuid:node_id>/update-progress/', views.update_topic_progress, name='update-topic-progress'),
    
    # Enterprise Learning System URLs
    path('learn/<uuid:node_id>/', views.learning_page, name='learning-page'),
    path('api/node/<uuid:node_id>/track-progress/', views.track_learning_progress, name='track-learning-progress'),
    
    # LMS Dashboard and Teacher Content Management URLs
    path('lms/', views.lms_dashboard, name='lms-dashboard'),
    path('teacher/content/', views.teacher_content_management, name='teacher-content-management'),
    path('teacher/content/create/<uuid:node_id>/', views.create_learning_content, name='create-learning-content'),
    path('teacher/content/edit/<uuid:content_id>/', views.edit_learning_content, name='edit-learning-content'),
    path('teacher/content/delete/<uuid:content_id>/', views.delete_learning_content, name='delete-learning-content'),
    path('teacher/content/analytics/<uuid:content_id>/', views.content_analytics, name='content-analytics'),
]