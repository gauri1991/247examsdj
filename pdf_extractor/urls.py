from django.urls import path
from . import views

app_name = 'pdf_extractor'

urlpatterns = [
    # Main PDF extraction interface
    path('', views.pdf_extraction_home, name='home'),
    path('upload/', views.pdf_upload, name='upload'),
    
    # Processing and status
    path('processing/<uuid:job_id>/', views.processing_status, name='processing_status'),
    path('processing/<uuid:job_id>/progress/', views.processing_progress_api, name='processing_progress'),
    
    # Results and review
    path('document/<uuid:document_id>/', views.document_detail, name='document_detail'),
    path('document/<uuid:document_id>/questions/', views.extracted_questions, name='extracted_questions'),
    path('question/<uuid:question_id>/review/', views.review_question, name='review_question'),
    
    # Question bank integration
    path('question/<uuid:question_id>/convert/', views.convert_to_question_bank, name='convert_question'),
    path('document/<uuid:document_id>/convert-all/', views.convert_all_questions, name='convert_all'),
    
    # Export functionality
    path('document/<uuid:document_id>/export/<str:format>/', views.export_questions, name='export_questions'),
    
    # Management
    path('documents/', views.document_list, name='document_list'),
    path('document/<uuid:document_id>/edit-metadata/', views.edit_metadata, name='edit_metadata'),
    path('bulk-edit-metadata/', views.bulk_edit_metadata, name='bulk_edit_metadata'),
    path('export-metadata/', views.export_metadata, name='export_metadata'),
    path('import-metadata/', views.import_metadata, name='import_metadata'),
    path('templates/', views.extraction_templates, name='templates'),
    
    # Metadata Templates
    path('metadata-templates/', views.metadata_templates, name='metadata_templates'),
    path('metadata-templates/create/', views.create_metadata_template, name='create_metadata_template'),
    path('metadata-templates/<uuid:template_id>/edit/', views.edit_metadata_template, name='edit_metadata_template'),
    path('metadata-templates/<uuid:template_id>/delete/', views.delete_metadata_template, name='delete_metadata_template'),
    path('apply-metadata-template/', views.apply_metadata_template, name='apply_metadata_template'),
    
    # Interactive Review URLs - New workflow
    path('interactive-review/<uuid:document_id>/', views.interactive_review, name='interactive_review'),
    path('api/auto-detect-regions/<uuid:document_id>/', views.auto_detect_regions_api, name='auto_detect_regions_api'),
    path('api/process-regions/<uuid:document_id>/', views.process_selected_regions_api, name='process_selected_regions_api'),
    path('api/save-questions/<uuid:document_id>/', views.save_extracted_questions_api, name='save_extracted_questions_api'),
    path('api/finish-review/<uuid:document_id>/', views.finish_review_api, name='finish_review_api'),
    path('api/mark-page-no-questions/<uuid:document_id>/', views.mark_page_no_questions_api, name='mark_page_no_questions_api'),
    path('api/mark-page-for-later/<uuid:document_id>/', views.mark_page_for_later_api, name='mark_page_for_later_api'),
    
    # Mixed Question Type APIs - New Region Management
    path('api/mark-regions-unsupported/<uuid:document_id>/', views.mark_regions_unsupported_api, name='mark_regions_unsupported_api'),
    path('api/mark-page-complete/<uuid:document_id>/', views.mark_page_complete_api, name='mark_page_complete_api'),
    path('api/saved-regions/<uuid:document_id>/<int:page_number>/', views.saved_regions_api, name='saved_regions_api'),
    path('api/delete-region/<uuid:document_id>/<uuid:region_id>/', views.delete_saved_region_api, name='delete_saved_region_api'),
    path('api/update-region/<uuid:document_id>/<uuid:region_id>/', views.update_saved_region_api, name='update_saved_region_api'),
    path('api/delete-document/<uuid:document_id>/', views.delete_document_api, name='delete_document_api'),
    path('api/search-questions/<uuid:document_id>/', views.search_questions_api, name='search_questions_api'),
    path('api/question/<uuid:question_id>/delete/', views.delete_question_api, name='delete_question_api'),
    
    # Admin Document Management APIs
    path('api/admin/documents/', views.admin_documents_api, name='admin_documents_api'),
    path('api/admin/document-stats/', views.admin_document_stats_api, name='admin_document_stats_api'),
    path('api/admin/processing-status/', views.admin_processing_status_api, name='admin_processing_status_api'),
    path('api/admin/recent-activity/', views.admin_recent_activity_api, name='admin_recent_activity_api'),
    path('api/admin/analytics/', views.admin_analytics_api, name='admin_analytics_api'),
    
    # Interactive Region Review URLs
    path('review-regions/<uuid:document_id>/', views.region_review_interface, name='region_review_interface'),
    path('api/regions/<uuid:document_id>/<int:page_number>/', views.get_page_regions_api, name='get_page_regions_api'),
    path('api/save-correction/<uuid:document_id>/', views.save_region_correction, name='save_region_correction'),
    path('api/batch-approve/<uuid:document_id>/', views.batch_approve_regions, name='batch_approve_regions'),
    path('complete-review/<uuid:document_id>/', views.complete_review_session, name='complete_review_session'),
    path('visualize/<uuid:document_id>/<int:page_number>/', views.region_visualization, name='region_visualization'),
]