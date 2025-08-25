from django.urls import path
from . import api_views

app_name = 'knowledge_api'

urlpatterns = [
    # Subject API endpoints
    path('subjects/', api_views.GlobalSubjectListCreateAPIView.as_view(), name='subject-list-create'),
    path('subjects/<uuid:id>/', api_views.GlobalSubjectRetrieveUpdateDestroyAPIView.as_view(), name='subject-detail'),
    
    # Topic API endpoints
    path('topics/', api_views.GlobalTopicListCreateAPIView.as_view(), name='topic-list-create'),
    path('topics/<uuid:id>/', api_views.GlobalTopicRetrieveUpdateDestroyAPIView.as_view(), name='topic-detail'),
    
    # Specialized topic endpoints
    path('topics/hierarchy/', api_views.topic_hierarchy_view, name='topic-hierarchy'),
    path('topics/hierarchy/<uuid:subject_id>/', api_views.topic_hierarchy_view, name='topic-hierarchy-subject'),
    path('topics/search/', api_views.topic_search_view, name='topic-search'),
    path('topics/bulk-actions/', api_views.topic_bulk_actions_view, name='topic-bulk-actions'),
    path('topics/stats/', api_views.topic_stats_view, name='topic-stats'),
    path('topics/recommendations/', api_views.topic_recommendations_view, name='topic-recommendations'),
    
    # Template API endpoints
    path('templates/', api_views.TopicTemplateListCreateAPIView.as_view(), name='template-list-create'),
    path('templates/<uuid:id>/', api_views.TopicTemplateRetrieveUpdateDestroyAPIView.as_view(), name='template-detail'),
    
    # Import Template API endpoints
    path('import-templates/', api_views.TopicImportTemplateListCreateAPIView.as_view(), name='import-template-list-create'),
    path('import-templates/<uuid:id>/', api_views.TopicImportTemplateRetrieveUpdateDestroyAPIView.as_view(), name='import-template-detail'),
    
    # Mapping API endpoints
    path('mappings/', api_views.SyllabusTopicMappingListCreateAPIView.as_view(), name='mapping-list-create'),
    path('mappings/<uuid:id>/', api_views.SyllabusTopicMappingRetrieveUpdateDestroyAPIView.as_view(), name='mapping-detail'),
]