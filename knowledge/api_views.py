from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
import uuid

from .models import GlobalSubject, GlobalTopic, TopicTemplate, SyllabusTopicMapping, TopicImportTemplate
from .serializers import (
    GlobalSubjectSerializer, GlobalTopicListSerializer, GlobalTopicDetailSerializer,
    TopicHierarchySerializer, TopicTemplateSerializer, SyllabusTopicMappingSerializer,
    TopicImportTemplateSerializer, TopicSearchSerializer, TopicBulkActionSerializer,
    TopicStatsSerializer, TopicRecommendationSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# Subject API Views
class GlobalSubjectListCreateAPIView(generics.ListCreateAPIView):
    queryset = GlobalSubject.objects.all()
    serializer_class = GlobalSubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at', 'popularity_score']
    filterset_fields = ['category', 'level', 'is_active', 'is_featured']
    pagination_class = StandardResultsSetPagination
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class GlobalSubjectRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GlobalSubject.objects.all()
    serializer_class = GlobalSubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'


# Topic API Views
class GlobalTopicListCreateAPIView(generics.ListCreateAPIView):
    queryset = GlobalTopic.objects.select_related('subject', 'parent').prefetch_related('children')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'description', 'keywords']
    ordering_fields = ['title', 'created_at', 'usage_count', 'estimated_hours']
    filterset_fields = ['subject', 'topic_type', 'difficulty', 'priority', 'is_active', 'is_approved']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GlobalTopicDetailSerializer
        return GlobalTopicListSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class GlobalTopicRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GlobalTopic.objects.select_related('subject', 'parent', 'created_by', 'approved_by').prefetch_related('children', 'prerequisites')
    serializer_class = GlobalTopicDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'


# Specialized Topic Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def topic_hierarchy_view(request, subject_id=None):
    """Get topics in hierarchical tree structure"""
    try:
        if subject_id:
            subject = get_object_or_404(GlobalSubject, id=subject_id)
            root_topics = GlobalTopic.objects.filter(
                subject=subject, 
                parent=None, 
                is_active=True
            ).order_by('order', 'title')
        else:
            root_topics = GlobalTopic.objects.filter(
                parent=None,
                is_active=True
            ).select_related('subject').order_by('subject__name', 'order', 'title')
        
        serializer = TopicHierarchySerializer(root_topics, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'subject_id': str(subject_id) if subject_id else None
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def topic_search_view(request):
    """Advanced topic search with multiple filters"""
    serializer = TopicSearchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    queryset = GlobalTopic.objects.select_related('subject', 'parent')
    
    # Apply filters
    if data.get('query'):
        query = data['query']
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(keywords__icontains=query)
        )
    
    if data.get('subject_ids'):
        queryset = queryset.filter(subject__id__in=data['subject_ids'])
    
    if data.get('categories'):
        queryset = queryset.filter(subject__category__in=data['categories'])
    
    if data.get('levels'):
        queryset = queryset.filter(subject__level__in=data['levels'])
    
    if data.get('topic_types'):
        queryset = queryset.filter(topic_type__in=data['topic_types'])
    
    if data.get('difficulties'):
        queryset = queryset.filter(difficulty__in=data['difficulties'])
    
    if data.get('priorities'):
        queryset = queryset.filter(priority__in=data['priorities'])
    
    if data.get('is_approved') is not None:
        queryset = queryset.filter(is_approved=data['is_approved'])
    
    if data.get('is_active') is not None:
        queryset = queryset.filter(is_active=data['is_active'])
    
    if data.get('min_hours'):
        queryset = queryset.filter(estimated_hours__gte=data['min_hours'])
    
    if data.get('max_hours'):
        queryset = queryset.filter(estimated_hours__lte=data['max_hours'])
    
    if data.get('depth_level') is not None:
        queryset = queryset.filter(depth_level=data['depth_level'])
    
    # Apply ordering
    ordering = data.get('ordering', 'title')
    if ordering.startswith('-'):
        queryset = queryset.order_by(ordering)
    else:
        queryset = queryset.order_by(ordering)
    
    # Paginate results
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = GlobalTopicListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    serializer = GlobalTopicListSerializer(queryset, many=True)
    return Response({
        'success': True,
        'count': queryset.count(),
        'data': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def topic_bulk_actions_view(request):
    """Perform bulk actions on topics"""
    serializer = TopicBulkActionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    topic_ids = data['topic_ids']
    action = data['action']
    
    # Get topics
    topics = GlobalTopic.objects.filter(id__in=topic_ids)
    if not topics.exists():
        return Response({
            'success': False,
            'error': 'No topics found with provided IDs'
        }, status=status.HTTP_404_NOT_FOUND)
    
    updated_count = 0
    
    try:
        if action == 'approve':
            updated_count = topics.update(
                is_approved=True,
                approved_by=request.user,
                approval_notes=data.get('notes', '')
            )
        
        elif action == 'activate':
            updated_count = topics.update(is_active=True)
        
        elif action == 'deactivate':
            updated_count = topics.update(is_active=False)
        
        elif action == 'delete':
            updated_count = topics.count()
            topics.delete()
        
        elif action == 'update_difficulty':
            if not data.get('difficulty'):
                return Response({
                    'success': False,
                    'error': 'Difficulty level required for this action'
                }, status=status.HTTP_400_BAD_REQUEST)
            updated_count = topics.update(difficulty=data['difficulty'])
        
        elif action == 'update_priority':
            if not data.get('priority'):
                return Response({
                    'success': False,
                    'error': 'Priority level required for this action'
                }, status=status.HTTP_400_BAD_REQUEST)
            updated_count = topics.update(priority=data['priority'])
        
        return Response({
            'success': True,
            'message': f'Successfully {action}d {updated_count} topics',
            'updated_count': updated_count
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error performing bulk action: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def topic_stats_view(request):
    """Get comprehensive topic statistics"""
    try:
        # Basic counts
        total_subjects = GlobalSubject.objects.count()
        total_topics = GlobalTopic.objects.count()
        approved_topics = GlobalTopic.objects.filter(is_approved=True).count()
        pending_topics = total_topics - approved_topics
        
        # Category breakdown
        topics_by_category = dict(
            GlobalSubject.objects.values('category').annotate(
                count=Count('global_topics')
            ).values_list('category', 'count')
        )
        
        # Level breakdown
        topics_by_level = dict(
            GlobalSubject.objects.values('level').annotate(
                count=Count('global_topics')
            ).values_list('level', 'count')
        )
        
        # Difficulty breakdown
        topics_by_difficulty = dict(
            GlobalTopic.objects.values('difficulty').annotate(
                count=Count('id')
            ).values_list('difficulty', 'count')
        )
        
        # Type breakdown
        topics_by_type = dict(
            GlobalTopic.objects.values('topic_type').annotate(
                count=Count('id')
            ).values_list('topic_type', 'count')
        )
        
        # Average hours per topic
        avg_hours = GlobalTopic.objects.aggregate(
            avg_hours=Avg('estimated_hours')
        )['avg_hours'] or 0
        
        # Popular subjects (by usage count)
        popular_subjects = list(
            GlobalSubject.objects.filter(
                popularity_score__gt=0
            ).order_by('-popularity_score')[:10].values(
                'name', 'code', 'popularity_score'
            )
        )
        
        # Recent activity (last 10 created topics)
        recent_activity = list(
            GlobalTopic.objects.select_related('subject').order_by(
                '-created_at'
            )[:10].values(
                'title', 'subject__name', 'created_at', 'created_by__username'
            )
        )
        
        stats_data = {
            'total_subjects': total_subjects,
            'total_topics': total_topics,
            'approved_topics': approved_topics,
            'pending_topics': pending_topics,
            'topics_by_category': topics_by_category,
            'topics_by_level': topics_by_level,
            'topics_by_difficulty': topics_by_difficulty,
            'topics_by_type': topics_by_type,
            'avg_hours_per_topic': round(float(avg_hours), 2),
            'popular_subjects': popular_subjects,
            'recent_activity': recent_activity
        }
        
        serializer = TopicStatsSerializer(stats_data)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def topic_recommendations_view(request):
    """Get topic recommendations based on criteria"""
    user_subjects = request.data.get('subjects', [])
    user_difficulty = request.data.get('difficulty', 'medium')
    user_categories = request.data.get('categories', [])
    completed_topics = request.data.get('completed_topics', [])
    limit = request.data.get('limit', 10)
    
    try:
        # Base queryset
        queryset = GlobalTopic.objects.filter(
            is_active=True,
            is_approved=True
        ).select_related('subject')
        
        # Exclude already completed topics
        if completed_topics:
            queryset = queryset.exclude(id__in=completed_topics)
        
        recommendations = []
        
        for topic in queryset[:50]:  # Limit initial set for performance
            score = 0.0
            reasons = []
            subject_match = False
            difficulty_match = False
            prerequisite_satisfied = True
            
            # Subject matching (highest weight)
            if str(topic.subject.id) in user_subjects:
                score += 0.4
                subject_match = True
                reasons.append(f"Matches your interest in {topic.subject.name}")
            
            # Category matching
            if topic.subject.category in user_categories:
                score += 0.2
                reasons.append(f"Fits your {topic.subject.category} focus")
            
            # Difficulty matching
            difficulty_order = ['beginner', 'easy', 'medium', 'hard', 'expert']
            user_diff_idx = difficulty_order.index(user_difficulty) if user_difficulty in difficulty_order else 2
            topic_diff_idx = difficulty_order.index(topic.difficulty) if topic.difficulty in difficulty_order else 2
            
            if abs(user_diff_idx - topic_diff_idx) <= 1:
                score += 0.2
                difficulty_match = True
                reasons.append(f"Appropriate {topic.difficulty} difficulty level")
            
            # Popularity bonus
            if topic.usage_count > 5:
                score += 0.1
                reasons.append("Popular topic with proven value")
            
            # Prerequisites check (simplified)
            prerequisites = topic.prerequisites.all()
            if prerequisites.exists():
                missing_prerequisites = prerequisites.exclude(id__in=completed_topics)
                if missing_prerequisites.exists():
                    score -= 0.3
                    prerequisite_satisfied = False
                    reasons.append("Some prerequisites not completed")
                else:
                    score += 0.1
                    reasons.append("All prerequisites satisfied")
            
            # Add to recommendations if score is decent
            if score > 0.2:
                recommendations.append({
                    'topic': topic,
                    'score': round(score, 2),
                    'reasons': reasons,
                    'subject_match': subject_match,
                    'difficulty_match': difficulty_match,
                    'prerequisite_satisfied': prerequisite_satisfied
                })
        
        # Sort by score and limit results
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        recommendations = recommendations[:limit]
        
        serializer = TopicRecommendationSerializer(recommendations, many=True)
        return Response({
            'success': True,
            'count': len(recommendations),
            'data': serializer.data
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Template API Views
class TopicTemplateListCreateAPIView(generics.ListCreateAPIView):
    queryset = TopicTemplate.objects.select_related('subject')
    serializer_class = TopicTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'usage_count']
    filterset_fields = ['template_type', 'subject', 'is_active', 'is_public']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TopicTemplateRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TopicTemplate.objects.all()
    serializer_class = TopicTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'


# Import Template API Views
class TopicImportTemplateListCreateAPIView(generics.ListCreateAPIView):
    queryset = TopicImportTemplate.objects.select_related('source_subject')
    serializer_class = TopicImportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    filterset_fields = ['template_type', 'source_subject', 'is_active', 'is_public']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TopicImportTemplateRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TopicImportTemplate.objects.all()
    serializer_class = TopicImportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'


# Mapping API Views
class SyllabusTopicMappingListCreateAPIView(generics.ListCreateAPIView):
    queryset = SyllabusTopicMapping.objects.select_related('global_topic', 'global_topic__subject')
    serializer_class = SyllabusTopicMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['syllabus_id', 'global_topic', 'is_mandatory', 'is_modified']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SyllabusTopicMappingRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SyllabusTopicMapping.objects.all()
    serializer_class = SyllabusTopicMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'