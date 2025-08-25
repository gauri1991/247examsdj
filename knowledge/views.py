from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import GlobalSubject, GlobalTopic, TopicTemplate, SyllabusTopicMapping, TopicImportTemplate
import json


@login_required
def topic_browser(request):
    """Main topic browser interface for content creators and exam creators"""
    
    # Get filter parameters
    category = request.GET.get('category', '')
    level = request.GET.get('level', '')
    subject_id = request.GET.get('subject_id', '')
    difficulty = request.GET.get('difficulty', '')
    search = request.GET.get('search', '')
    
    # Build queryset
    subjects = GlobalSubject.objects.filter(is_active=True)
    
    if category:
        subjects = subjects.filter(category=category)
    if level:
        subjects = subjects.filter(level=level)
    if subject_id:
        subjects = subjects.filter(id=subject_id)
    if search:
        subjects = subjects.filter(
            Q(name__icontains=search) | Q(description__icontains=search) | Q(code__icontains=search)
        )
    
    subjects = subjects.annotate(topic_count=Count('global_topics')).order_by('category', 'name')
    
    # Get categories and levels for filters
    categories = GlobalSubject.CATEGORY_CHOICES
    levels = GlobalSubject.LEVEL_CHOICES
    
    context = {
        'subjects': subjects,
        'categories': categories,
        'levels': levels,
        'filters': {
            'category': category,
            'level': level,
            'subject_id': subject_id,
            'difficulty': difficulty,
            'search': search,
        }
    }
    
    return render(request, 'knowledge/topic_browser.html', context)


@login_required
def subjects_list_api(request):
    """API endpoint to get all subjects with their details"""
    subjects = GlobalSubject.objects.filter(is_active=True).annotate(
        topic_count=Count('global_topics')
    ).order_by('category', 'name')
    
    subjects_data = []
    for subject in subjects:
        subjects_data.append({
            'id': str(subject.id),
            'name': subject.name,
            'code': subject.code,
            'description': subject.description,
            'category': subject.category,
            'level': subject.level,
            'icon': subject.icon,
            'color_code': subject.color_code,
            'topic_count': subject.topic_count,
            'is_featured': subject.is_featured,
            'popularity_score': subject.popularity_score,
        })
    
    return JsonResponse({
        'success': True,
        'subjects': subjects_data,
        'total': len(subjects_data)
    })


@login_required
def subject_topics_api(request, subject_id):
    """API endpoint to get topics for a specific subject"""
    
    subject = get_object_or_404(GlobalSubject, id=subject_id, is_active=True)
    
    # Get root topics with their children
    root_topics = GlobalTopic.objects.filter(
        subject=subject,
        parent=None,
        is_active=True,
        is_template=True
    ).prefetch_related(
        Prefetch(
            'children',
            queryset=GlobalTopic.objects.filter(is_active=True).order_by('order')
        )
    ).order_by('order')
    
    def serialize_topic(topic):
        return {
            'id': str(topic.id),
            'title': topic.title,
            'description': topic.description,
            'topic_type': topic.topic_type,
            'difficulty': topic.difficulty,
            'priority': topic.priority,
            'estimated_hours': float(topic.estimated_hours),
            'usage_count': topic.usage_count,
            'path': topic.path,
            'depth_level': topic.depth_level,
            'is_approved': topic.is_approved,
            'learning_objectives': topic.learning_objectives,
            'keywords': topic.keywords,
            'children': [serialize_topic(child) for child in topic.get_children()]
        }
    
    topics_data = [serialize_topic(topic) for topic in root_topics]
    
    return JsonResponse({
        'success': True,
        'subject': {
            'id': str(subject.id),
            'name': subject.name,
            'code': subject.code,
            'category': subject.category,
            'level': subject.level,
            'icon': subject.icon,
            'color_code': subject.color_code,
        },
        'topics': topics_data
    })


@login_required
def topic_detail_api(request, topic_id):
    """API endpoint to get detailed information about a specific topic"""
    
    topic = get_object_or_404(GlobalTopic, id=topic_id, is_active=True)
    
    # Get breadcrumb
    breadcrumb = [{'id': str(t.id), 'title': t.title} for t in topic.get_breadcrumb()]
    
    # Get prerequisites
    prerequisites = [
        {'id': str(p.id), 'title': p.title, 'subject': p.subject.name}
        for p in topic.prerequisites.filter(is_active=True)
    ]
    
    # Get dependent topics
    dependent_topics = [
        {'id': str(d.id), 'title': d.title, 'subject': d.subject.name}
        for d in topic.dependent_topics.filter(is_active=True)
    ]
    
    # Get usage statistics
    usage_stats = {
        'total_usage': topic.usage_count,
        'recent_exams': []  # Could be expanded to show recent exam usage
    }
    
    data = {
        'success': True,
        'topic': {
            'id': str(topic.id),
            'title': topic.title,
            'description': topic.description,
            'topic_type': topic.topic_type,
            'difficulty': topic.difficulty,
            'priority': topic.priority,
            'estimated_hours': float(topic.estimated_hours),
            'suggested_duration': topic.get_suggested_duration(),
            'learning_objectives': topic.learning_objectives,
            'keywords': topic.keywords,
            'reference_materials': topic.reference_materials,
            'path': topic.path,
            'depth_level': topic.depth_level,
            'is_approved': topic.is_approved,
            'approval_notes': topic.approval_notes,
            'created_at': topic.created_at.isoformat(),
            'updated_at': topic.updated_at.isoformat(),
        },
        'subject': {
            'id': str(topic.subject.id),
            'name': topic.subject.name,
            'code': topic.subject.code,
            'category': topic.subject.category,
        },
        'breadcrumb': breadcrumb,
        'prerequisites': prerequisites,
        'dependent_topics': dependent_topics,
        'usage_stats': usage_stats,
    }
    
    return JsonResponse(data)


@login_required 
def exam_topic_selector(request):
    """Interface for exam creators to select and import topics"""
    
    # Get available subjects and templates
    subjects = GlobalSubject.objects.filter(is_active=True).annotate(
        topic_count=Count('global_topics', filter=Q(global_topics__is_active=True))
    ).order_by('category', 'name')
    
    templates = TopicImportTemplate.objects.filter(
        is_active=True,
        is_public=True
    ).select_related('source_subject').order_by('-usage_count')
    
    context = {
        'subjects': subjects,
        'templates': templates,
        'categories': GlobalSubject.CATEGORY_CHOICES,
        'levels': GlobalSubject.LEVEL_CHOICES,
        'difficulty_levels': GlobalTopic.DIFFICULTY_CHOICES,
    }
    
    return render(request, 'knowledge/exam_topic_selector.html', context)


@login_required
def compatible_topics_api(request, exam_id):
    """API to find topics compatible with a specific exam"""
    
    # This would integrate with the existing exam system
    # For now, return general compatible topics
    
    category_filter = request.GET.get('category')
    difficulty_filter = request.GET.get('difficulty')
    limit = int(request.GET.get('limit', 20))
    
    # Build filters
    filters = Q(is_active=True, is_template=True, is_approved=True)
    
    if category_filter:
        filters &= Q(subject__category=category_filter)
    
    if difficulty_filter:
        filters &= Q(difficulty=difficulty_filter)
    
    # Get compatible topics with scoring  
    topics = GlobalTopic.objects.filter(filters).select_related('subject').order_by(
        '-usage_count', '-subject__popularity_score'
    )[:limit]
    
    topics_data = []
    for topic in topics:
        # Calculate compatibility score (simplified)
        compatibility_score = min(100, (topic.usage_count * 10) + (topic.subject.popularity_score * 5))
        
        topics_data.append({
            'id': str(topic.id),
            'title': topic.title,
            'description': topic.description[:200] + ('...' if len(topic.description) > 200 else ''),
            'subject': {
                'name': topic.subject.name,
                'code': topic.subject.code,
                'category': topic.subject.category,
                'color_code': topic.subject.color_code,
            },
            'difficulty': topic.difficulty,
            'estimated_hours': float(topic.estimated_hours),
            'usage_count': topic.usage_count,
            'compatibility_score': compatibility_score,
            'match_reasons': [
                'High usage in similar exams',
                'Popular in subject category',
                'Appropriate difficulty level'
            ]
        })
    
    return JsonResponse({
        'success': True,
        'exam_id': exam_id,
        'compatible_topics': topics_data,
        'total_found': len(topics_data)
    })


@staff_member_required
def topic_editor(request):
    """Interactive topic and category editor interface"""
    subjects = GlobalSubject.objects.filter(is_active=True).annotate(
        topic_count=Count('global_topics')
    ).order_by('category', 'name')
    
    context = {
        'subjects': subjects,
    }
    
    return render(request, 'knowledge/topic_editor.html', context)


@staff_member_required
def admin_topic_manager(request):
    """Admin interface for managing global topics and subjects"""
    
    # Get statistics
    stats = {
        'total_subjects': GlobalSubject.objects.filter(is_active=True).count(),
        'total_topics': GlobalTopic.objects.filter(is_active=True).count(),
        'pending_approval': GlobalTopic.objects.filter(is_active=True, is_approved=False).count(),
        'templates': TopicImportTemplate.objects.filter(is_active=True).count(),
    }
    
    # Get recent activity
    recent_topics = GlobalTopic.objects.filter(is_active=True).select_related('subject', 'created_by').order_by('-created_at')[:10]
    popular_subjects = GlobalSubject.objects.filter(is_active=True).order_by('-popularity_score')[:10]
    
    context = {
        'stats': stats,
        'recent_topics': recent_topics,
        'popular_subjects': popular_subjects,
    }
    
    return render(request, 'knowledge/admin_topic_manager.html', context)


@login_required
def topic_search_api(request):
    """API for searching topics across all subjects"""
    
    query = request.GET.get('q', '').strip()
    subject_filter = request.GET.get('subject')
    category_filter = request.GET.get('category')
    difficulty_filter = request.GET.get('difficulty')
    limit = int(request.GET.get('limit', 20))
    
    if not query:
        return JsonResponse({'success': False, 'error': 'Search query required'})
    
    # Build search filters
    search_filter = Q(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(keywords__contains=query.lower())
    )
    
    filters = Q(is_active=True, is_template=True) & search_filter
    
    if subject_filter:
        filters &= Q(subject_id=subject_filter)
    if category_filter:
        filters &= Q(subject__category=category_filter)
    if difficulty_filter:
        filters &= Q(difficulty=difficulty_filter)
    
    # Search topics
    topics = GlobalTopic.objects.filter(filters).select_related(
        'subject'
    ).order_by('-usage_count')[:limit]
    
    results = []
    for topic in topics:
        results.append({
            'id': str(topic.id),
            'title': topic.title,
            'description': topic.description[:150] + ('...' if len(topic.description) > 150 else ''),
            'subject': {
                'name': topic.subject.name,
                'code': topic.subject.code,
                'category': topic.subject.get_category_display(),
                'color_code': topic.subject.color_code,
            },
            'difficulty': topic.get_difficulty_display(),
            'topic_type': topic.get_topic_type_display(),
            'estimated_hours': float(topic.estimated_hours),
            'usage_count': topic.usage_count,
            'path': topic.path,
        })
    
    return JsonResponse({
        'success': True,
        'query': query,
        'results': results,
        'total': len(results)
    })


@staff_member_required  
def admin_taxonomy_stats_api(request):
    """API endpoint for admin panel taxonomy statistics"""
    
    try:
        # Calculate statistics
        stats = {
            'total_subjects': GlobalSubject.objects.filter(is_active=True).count(),
            'total_topics': GlobalTopic.objects.filter(is_active=True).count(),
            'total_templates': TopicImportTemplate.objects.filter(is_active=True).count(),
            'pending_approval': GlobalTopic.objects.filter(is_active=True, is_approved=False).count(),
        }
        
        # Get popular subjects (top 5)
        popular_subjects = list(
            GlobalSubject.objects.filter(is_active=True, popularity_score__gt=0)
            .order_by('-popularity_score')[:5]
            .values('name', 'code', 'popularity_score')
        )
        
        # Get popular topics (top 5)
        popular_topics = list(
            GlobalTopic.objects.filter(is_active=True, usage_count__gt=0)
            .select_related('subject')
            .order_by('-usage_count')[:5]
            .values('title', 'usage_count', 'subject__name')
        )
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'popular_subjects': popular_subjects,
            'popular_topics': popular_topics
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def update_subject_api(request, subject_id):
    """API endpoint to update subject details"""
    try:
        subject = get_object_or_404(GlobalSubject, id=subject_id)
        data = json.loads(request.body)
        
        # Update fields
        if 'name' in data:
            subject.name = data['name']
        if 'code' in data:
            subject.code = data['code']
        if 'description' in data:
            subject.description = data['description']
        if 'category' in data:
            subject.category = data['category']
        if 'level' in data:
            subject.level = data['level']
        if 'icon' in data:
            subject.icon = data['icon']
        if 'color_code' in data:
            subject.color_code = data['color_code']
        if 'is_active' in data:
            subject.is_active = data['is_active']
        if 'is_featured' in data:
            subject.is_featured = data['is_featured']
            
        subject.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Subject updated successfully',
            'subject': {
                'id': str(subject.id),
                'name': subject.name,
                'code': subject.code,
                'description': subject.description,
                'category': subject.category,
                'level': subject.level,
                'icon': subject.icon,
                'color_code': subject.color_code,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def update_topic_api(request, topic_id):
    """API endpoint to update topic details"""
    try:
        topic = get_object_or_404(GlobalTopic, id=topic_id)
        data = json.loads(request.body)
        
        # Update fields
        if 'title' in data:
            topic.title = data['title']
        if 'description' in data:
            topic.description = data['description']
        if 'topic_type' in data:
            topic.topic_type = data['topic_type']
        if 'difficulty' in data:
            topic.difficulty = data['difficulty']
        if 'priority' in data:
            topic.priority = data['priority']
        if 'estimated_hours' in data:
            topic.estimated_hours = data['estimated_hours']
        if 'learning_objectives' in data:
            topic.learning_objectives = data['learning_objectives']
        if 'keywords' in data:
            topic.keywords = data['keywords']
        if 'is_active' in data:
            topic.is_active = data['is_active']
        if 'is_approved' in data:
            topic.is_approved = data['is_approved']
            topic.approved_by = request.user if data['is_approved'] else None
        if 'order' in data:
            topic.order = data['order']
            
        topic.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Topic updated successfully',
            'topic': {
                'id': str(topic.id),
                'title': topic.title,
                'description': topic.description,
                'topic_type': topic.topic_type,
                'difficulty': topic.difficulty,
                'priority': topic.priority,
                'estimated_hours': float(topic.estimated_hours),
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["DELETE"])
def delete_subject_api(request, subject_id):
    """API endpoint to delete a subject"""
    try:
        subject = get_object_or_404(GlobalSubject, id=subject_id)
        
        # Check if subject has topics
        topic_count = subject.global_topics.count()
        if topic_count > 0:
            return JsonResponse({
                'success': False,
                'error': f'Cannot delete subject with {topic_count} topics. Delete topics first.'
            }, status=400)
        
        subject_name = subject.name
        subject.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Subject "{subject_name}" deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["DELETE"])
def delete_topic_api(request, topic_id):
    """API endpoint to delete a topic"""
    try:
        topic = get_object_or_404(GlobalTopic, id=topic_id)
        
        # Check if topic has children
        children_count = topic.children.count()
        if children_count > 0:
            return JsonResponse({
                'success': False,
                'error': f'Cannot delete topic with {children_count} subtopics. Delete subtopics first.'
            }, status=400)
        
        topic_title = topic.title
        topic.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Topic "{topic_title}" deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def reorder_topics_api(request):
    """API endpoint to reorder topics within a parent"""
    try:
        data = json.loads(request.body)
        topic_orders = data.get('topic_orders', [])
        
        for item in topic_orders:
            topic_id = item.get('topic_id')
            new_order = item.get('order')
            
            if topic_id and new_order is not None:
                topic = GlobalTopic.objects.get(id=topic_id)
                topic.order = new_order
                topic.save(update_fields=['order'])
        
        return JsonResponse({
            'success': True,
            'message': 'Topics reordered successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)