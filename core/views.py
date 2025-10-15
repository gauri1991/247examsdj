from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta

from users.models import User
from exams.models import Exam, Test, TestAttempt
from questions.models import Question, QuestionBank
from analytics.models import UserAnalytics


@login_required
def dashboard(request):
    """Enhanced dashboard view with rich content"""
    user = request.user
    context = {
        'user': user,
        'stats': {},
        'recent_exams': [],
        'trending_exams': [],
        'upcoming_exams': [],
        'recent_activity': [],
        'performance_data': {},
        'quick_stats': {}
    }
    
    if user.role == 'student':
        # Student statistics
        attempts = TestAttempt.objects.filter(user=user)
        context['stats'] = {
            'tests_taken': attempts.count(),
            'tests_passed': attempts.filter(
                percentage__gte=40  # Assuming 40% is passing
            ).count(),
            'average_score': attempts.aggregate(
                avg=Avg('percentage')
            )['avg'] or 0,
            'time_spent': attempts.aggregate(
                total=Sum('time_spent_seconds')
            )['total'] or 0
        }
        # Convert seconds to hours
        context['stats']['time_spent'] = round(context['stats']['time_spent'] / 3600, 1)
        
        # Recent exams (available for taking)
        context['recent_exams'] = Exam.objects.filter(
            is_active=True
        ).select_related('organization').annotate(
            tests_count=Count('tests', filter=Q(tests__is_published=True))
        ).order_by('-created_at')[:6]
        
        # Trending exams (most attempted)
        context['trending_exams'] = Exam.objects.filter(
            is_active=True
        ).select_related('organization').annotate(
            attempts_count=Count('tests__attempts')
        ).filter(attempts_count__gt=0).order_by('-attempts_count')[:4]
        
        # Recent test attempts for activity
        recent_attempts = TestAttempt.objects.filter(
            user=user
        ).select_related('test', 'test__exam', 'test__exam__organization').order_by('-start_time')[:5]
        
        for attempt in recent_attempts:
            context['recent_activity'].append({
                'type': 'test_attempt',
                'title': f"Completed {attempt.test.title}",
                'description': f"Score: {attempt.percentage:.1f}% in {attempt.test.exam.name}",
                'time': attempt.start_time,
                'status': 'completed' if attempt.status == 'evaluated' else 'pending',
                'url': f'/exams/results/{attempt.id}/' if attempt.status == 'evaluated' else None,
                'score': attempt.percentage,
                'organization': attempt.test.exam.organization.short_name if attempt.test.exam.organization else None
            })
        
        # Performance data for charts
        if attempts.exists():
            recent_attempts_data = attempts.order_by('-start_time')[:10]
            context['performance_data'] = {
                'scores': [float(attempt.percentage) for attempt in recent_attempts_data],
                'dates': [attempt.start_time.strftime('%m/%d') for attempt in recent_attempts_data],
                'tests': [attempt.test.title[:20] for attempt in recent_attempts_data]
            }
        
    elif user.role == 'teacher':
        # Teacher statistics
        teacher_exams = Exam.objects.filter(created_by=user)
        teacher_tests = Test.objects.filter(created_by=user)
        
        context['stats'] = {
            'total_exams': teacher_exams.count(),
            'active_tests': teacher_tests.filter(is_published=True).count(),
            'total_students': TestAttempt.objects.filter(
                test__created_by=user
            ).values('user').distinct().count(),
            'total_questions': Question.objects.filter(created_by=user).count()
        }
        
        # Recent exams created by teacher
        context['recent_exams'] = teacher_exams.select_related('organization').annotate(
            tests_count=Count('tests'),
            attempts_count=Count('tests__attempts')
        ).order_by('-created_at')[:6]
        
        # Most popular exams by attempts
        context['trending_exams'] = teacher_exams.select_related('organization').annotate(
            attempts_count=Count('tests__attempts')
        ).filter(attempts_count__gt=0).order_by('-attempts_count')[:4]
        
        # Recent student attempts on teacher's tests
        recent_student_attempts = TestAttempt.objects.filter(
            test__created_by=user
        ).select_related('test', 'test__exam', 'user').order_by('-start_time')[:8]
        
        for attempt in recent_student_attempts:
            context['recent_activity'].append({
                'type': 'student_attempt',
                'title': f"{attempt.user.get_full_name() or attempt.user.username} attempted {attempt.test.title}",
                'description': f"Score: {attempt.percentage:.1f}% in {attempt.test.exam.name}",
                'time': attempt.start_time,
                'status': 'evaluated',
                'score': attempt.percentage,
                'student': attempt.user.get_full_name() or attempt.user.username
            })
    
    elif user.role == 'admin':
        # Admin statistics
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        total_exams = Exam.objects.count()
        total_tests = Test.objects.count()
        total_attempts = TestAttempt.objects.count()
        
        context['stats'] = {
            'total_exams': total_exams,
            'total_tests': total_tests,
            'total_users': User.objects.count(),
            'total_attempts': total_attempts
        }
        
        # Recent exams across the platform
        context['recent_exams'] = Exam.objects.select_related('organization', 'created_by').annotate(
            tests_count=Count('tests'),
            attempts_count=Count('tests__attempts')
        ).order_by('-created_at')[:6]
        
        # Most popular exams platform-wide
        context['trending_exams'] = Exam.objects.select_related('organization').annotate(
            attempts_count=Count('tests__attempts')
        ).filter(attempts_count__gt=0).order_by('-attempts_count')[:4]
        
        # Recent platform activity
        recent_attempts = TestAttempt.objects.select_related(
            'test', 'test__exam', 'user'
        ).order_by('-start_time')[:8]
        
        for attempt in recent_attempts:
            context['recent_activity'].append({
                'type': 'platform_attempt',
                'title': f"{attempt.user.get_full_name() or attempt.user.username} attempted {attempt.test.title}",
                'description': f"Score: {attempt.percentage:.1f}% in {attempt.test.exam.name}",
                'time': attempt.start_time,
                'status': 'evaluated',
                'score': attempt.percentage
            })
    
    # Quick stats for all users
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    context['quick_stats'] = {
        'exams_this_week': Exam.objects.filter(created_at__date__gte=week_ago).count(),
        'attempts_today': TestAttempt.objects.filter(start_time__date=today).count(),
        'active_exams': Exam.objects.filter(is_active=True).count(),
        'total_organizations': Exam.objects.values('organization').distinct().count()
    }
    
    return render(request, 'users/dashboard.html', context)


@login_required
def recent_activity(request):
    """HTMX endpoint for recent activity"""
    user = request.user
    activities = []
    
    if user.role == 'student':
        # Get recent test attempts
        recent_attempts = TestAttempt.objects.filter(
            user=user
        ).select_related('test').order_by('-start_time')[:5]
        
        for attempt in recent_attempts:
            activities.append({
                'type': 'test_attempt',
                'title': f"Attempted {attempt.test.title}",
                'description': f"Score: {attempt.percentage:.1f}%",
                'time': attempt.start_time,
                'status': 'completed' if attempt.status == 'evaluated' else 'pending'
            })
    
    elif user.role == 'teacher':
        # Get recent test creations and student attempts
        recent_tests = Test.objects.filter(
            created_by=user
        ).order_by('-created_at')[:3]
        
        for test in recent_tests:
            activities.append({
                'type': 'test_created',
                'title': f"Created test: {test.title}",
                'description': f"{test.test_questions.count()} questions",
                'time': test.created_at,
                'status': 'published' if test.is_published else 'draft'
            })
        
        # Recent student attempts on teacher's tests
        recent_student_attempts = TestAttempt.objects.filter(
            test__created_by=user
        ).select_related('test', 'user').order_by('-start_time')[:5]
        
        for attempt in recent_student_attempts:
            activities.append({
                'type': 'student_attempt',
                'title': f"{attempt.user.get_full_name()} attempted {attempt.test.title}",
                'description': f"Score: {attempt.percentage:.1f}%",
                'time': attempt.start_time,
                'status': 'evaluated'
            })
    
    # Sort activities by time
    activities.sort(key=lambda x: x['time'], reverse=True)
    activities = activities[:10]  # Limit to 10 most recent
    
    return render(request, 'partials/recent_activity.html', {'activities': activities})


def home(request):
    """Landing page - Temporarily redirecting to login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    # TEMPORARY: Redirect to login instead of rendering home template
    # TODO: Fix home.html template rendering issue
    return redirect('login')


@require_http_methods(["POST"])
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')
