from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg, Sum, Q, F, Case, When
from django.utils import timezone
from datetime import timedelta, datetime
import json
import csv

from users.models import User
from exams.models import Exam, Test, TestAttempt
from questions.models import Question, UserAnswer
from .models import UserAnalytics, TestAnalytics, QuestionAnalytics


@login_required
def analytics_dashboard(request):
    """Main analytics dashboard"""
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    context = {}
    
    if request.user.role == 'admin':
        context = get_admin_analytics()
    elif request.user.role == 'teacher':
        context = get_teacher_analytics(request.user)
    
    return render(request, 'analytics/dashboard.html', context)


def get_admin_analytics():
    """Get system-wide analytics for admin"""
    # Overall statistics
    total_users = User.objects.count()
    total_tests = Test.objects.count()
    total_questions = Question.objects.count()
    total_attempts = TestAttempt.objects.count()
    
    # User distribution
    user_distribution = User.objects.values('role').annotate(count=Count('id'))
    
    # Monthly test attempts
    last_6_months = timezone.now() - timedelta(days=180)
    monthly_attempts = TestAttempt.objects.filter(
        start_time__gte=last_6_months
    ).extra(
        select={'month': 'strftime("%%Y-%%m", start_time)'}
    ).values('month').annotate(count=Count('id')).order_by('month')
    
    # Top performing tests
    top_tests = Test.objects.annotate(
        attempts_count=Count('attempts'),
        avg_score=Avg('attempts__percentage')
    ).filter(attempts_count__gt=0).order_by('-attempts_count')[:10]
    
    # Recent activity
    recent_attempts = TestAttempt.objects.select_related(
        'user', 'test'
    ).order_by('-start_time')[:20]
    
    return {
        'total_users': total_users,
        'total_tests': total_tests,
        'total_questions': total_questions,
        'total_attempts': total_attempts,
        'user_distribution': list(user_distribution),
        'monthly_attempts': list(monthly_attempts),
        'top_tests': top_tests,
        'recent_attempts': recent_attempts,
    }


def get_teacher_analytics(user):
    """Get teacher-specific analytics"""
    # Teacher's tests and questions
    teacher_tests = Test.objects.filter(created_by=user)
    teacher_questions = Question.objects.filter(created_by=user)
    
    # Overall statistics
    total_tests = teacher_tests.count()
    total_questions = teacher_questions.count()
    total_attempts = TestAttempt.objects.filter(test__created_by=user).count()
    unique_students = TestAttempt.objects.filter(
        test__created_by=user
    ).values('user').distinct().count()
    
    # Test performance
    test_performance = teacher_tests.annotate(
        attempts_count=Count('attempts'),
        avg_score=Avg('attempts__percentage'),
        pass_rate=Avg(
            Case(
                When(attempts__percentage__gte=F('pass_percentage'), then=1),
                default=0,
                output_field=Count('attempts')
            )
        ) * 100
    ).filter(attempts_count__gt=0)
    
    # Student performance distribution
    score_distribution = TestAttempt.objects.filter(
        test__created_by=user,
        status='evaluated'
    ).extra(
        select={
            'score_range': '''
                CASE 
                    WHEN percentage >= 90 THEN 'A (90-100%)'
                    WHEN percentage >= 80 THEN 'B (80-89%)'
                    WHEN percentage >= 70 THEN 'C (70-79%)'
                    WHEN percentage >= 60 THEN 'D (60-69%)'
                    ELSE 'F (Below 60%)'
                END
            '''
        }
    ).values('score_range').annotate(count=Count('id'))
    
    # Question difficulty analysis
    question_difficulty = teacher_questions.values('difficulty').annotate(
        count=Count('id')
    )
    
    return {
        'total_tests': total_tests,
        'total_questions': total_questions,
        'total_attempts': total_attempts,
        'unique_students': unique_students,
        'test_performance': test_performance,
        'score_distribution': list(score_distribution),
        'question_difficulty': list(question_difficulty),
    }


@login_required
def test_analytics(request, test_id):
    """Detailed analytics for a specific test"""
    test = get_object_or_404(Test, id=test_id)
    
    # Check permissions
    if request.user.role == 'teacher' and test.created_by != request.user:
        messages.error(request, "Access denied.")
        return redirect('analytics-dashboard')
    
    # Test statistics
    attempts = TestAttempt.objects.filter(test=test)
    total_attempts = attempts.count()
    completed_attempts = attempts.filter(status='evaluated')
    
    if total_attempts == 0:
        messages.info(request, "No attempts found for this test.")
        return redirect('analytics-dashboard')
    
    # Basic statistics
    avg_score = completed_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
    completion_rate = (completed_attempts.count() / total_attempts * 100) if total_attempts > 0 else 0
    pass_rate = completed_attempts.filter(
        percentage__gte=test.pass_percentage
    ).count() / completed_attempts.count() * 100 if completed_attempts.count() > 0 else 0
    
    # Time analysis
    avg_time = completed_attempts.aggregate(
        avg=Avg('time_spent_seconds')
    )['avg'] or 0
    avg_time_minutes = int(avg_time / 60) if avg_time else 0
    
    # Score distribution
    score_ranges = [
        ('90-100%', completed_attempts.filter(percentage__gte=90).count()),
        ('80-89%', completed_attempts.filter(percentage__gte=80, percentage__lt=90).count()),
        ('70-79%', completed_attempts.filter(percentage__gte=70, percentage__lt=80).count()),
        ('60-69%', completed_attempts.filter(percentage__gte=60, percentage__lt=70).count()),
        ('Below 60%', completed_attempts.filter(percentage__lt=60).count()),
    ]
    
    # Question-wise performance
    question_performance = []
    for test_question in test.test_questions.all().select_related('question'):
        question = test_question.question
        answers = UserAnswer.objects.filter(
            test_attempt__test=test,
            question=question,
            test_attempt__status='evaluated'
        )
        
        total_answers = answers.count()
        correct_answers = answers.filter(is_correct=True).count()
        accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0
        avg_time = answers.aggregate(avg=Avg('time_spent_seconds'))['avg'] or 0
        
        question_performance.append({
            'question': question,
            'total_answers': total_answers,
            'correct_answers': correct_answers,
            'accuracy': accuracy,
            'avg_time': int(avg_time),
        })
    
    # Sort by accuracy (lowest first for identifying problem questions)
    question_performance.sort(key=lambda x: x['accuracy'])
    
    # Student performance
    student_performance = completed_attempts.select_related('user').order_by('-percentage')
    
    context = {
        'test': test,
        'total_attempts': total_attempts,
        'completed_attempts': completed_attempts.count(),
        'avg_score': avg_score,
        'completion_rate': completion_rate,
        'pass_rate': pass_rate,
        'avg_time_minutes': avg_time_minutes,
        'score_ranges': score_ranges,
        'question_performance': question_performance,
        'student_performance': student_performance,
    }
    
    return render(request, 'analytics/test_analytics.html', context)


@login_required
def student_analytics(request, student_id):
    """Detailed analytics for a specific student"""
    if request.user.role not in ['admin', 'teacher']:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    student = get_object_or_404(User, id=student_id, role='student')
    
    # If teacher, only show students who took their tests
    if request.user.role == 'teacher':
        teacher_test_attempts = TestAttempt.objects.filter(
            user=student,
            test__created_by=request.user
        )
        if not teacher_test_attempts.exists():
            messages.error(request, "Student has not taken any of your tests.")
            return redirect('analytics-dashboard')
    
    # Student's test attempts
    attempts = TestAttempt.objects.filter(user=student).select_related('test')
    if request.user.role == 'teacher':
        attempts = attempts.filter(test__created_by=request.user)
    
    completed_attempts = attempts.filter(status='evaluated')
    
    # Basic statistics
    total_tests = attempts.count()
    completed_tests = completed_attempts.count()
    avg_score = completed_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
    passed_tests = completed_attempts.filter(
        percentage__gte=F('test__pass_percentage')
    ).count()
    pass_rate = (passed_tests / completed_tests * 100) if completed_tests > 0 else 0
    
    # Performance over time
    performance_trend = completed_attempts.order_by('start_time').values(
        'start_time', 'percentage', 'test__title'
    )
    
    # Subject-wise performance (based on exam categories)
    subject_performance = completed_attempts.values(
        'test__exam__category'
    ).annotate(
        avg_score=Avg('percentage'),
        test_count=Count('id')
    ).order_by('-avg_score')
    
    # Strength and weakness analysis
    topic_performance = UserAnswer.objects.filter(
        test_attempt__user=student,
        test_attempt__status='evaluated'
    ).exclude(question__topic='').values(
        'question__topic'
    ).annotate(
        total_questions=Count('id'),
        correct_answers=Count('id', filter=Q(is_correct=True)),
        accuracy=Count('id', filter=Q(is_correct=True)) * 100.0 / Count('id')
    ).order_by('-accuracy')
    
    context = {
        'student': student,
        'total_tests': total_tests,
        'completed_tests': completed_tests,
        'avg_score': avg_score,
        'pass_rate': pass_rate,
        'performance_trend': list(performance_trend),
        'subject_performance': subject_performance,
        'topic_performance': topic_performance,
        'recent_attempts': completed_attempts.order_by('-start_time')[:10],
    }
    
    return render(request, 'analytics/student_analytics.html', context)


@login_required
def export_analytics(request):
    """Export analytics data to CSV"""
    if request.user.role == 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    export_type = request.GET.get('type', 'test_results')
    
    if export_type == 'test_results':
        return export_test_results(request)
    elif export_type == 'student_performance':
        return export_student_performance(request)
    elif export_type == 'question_analysis':
        return export_question_analysis(request)
    
    return JsonResponse({'error': 'Invalid export type'}, status=400)


def export_test_results(request):
    """Export test results to CSV"""
    # Get test attempts based on user role
    attempts = TestAttempt.objects.filter(status='evaluated').select_related(
        'user', 'test', 'test__exam'
    )
    
    if request.user.role == 'teacher':
        attempts = attempts.filter(test__created_by=request.user)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="test_results.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Student Name', 'Student Email', 'Test Title', 'Exam', 'Score (%)',
        'Marks Obtained', 'Total Marks', 'Time Spent (minutes)', 'Status',
        'Start Time', 'End Time'
    ])
    
    for attempt in attempts:
        writer.writerow([
            attempt.user.get_full_name(),
            attempt.user.email,
            attempt.test.title,
            attempt.test.exam.name,
            f"{attempt.percentage:.1f}",
            attempt.marks_obtained,
            attempt.test.total_marks,
            int(attempt.time_spent_seconds / 60),
            'Passed' if attempt.percentage >= attempt.test.pass_percentage else 'Failed',
            attempt.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            attempt.end_time.strftime('%Y-%m-%d %H:%M:%S') if attempt.end_time else '',
        ])
    
    return response


@login_required
def analytics_api(request):
    """API endpoint for analytics data (for charts)"""
    chart_type = request.GET.get('type')
    
    if chart_type == 'monthly_attempts':
        return get_monthly_attempts_data(request)
    elif chart_type == 'score_distribution':
        return get_score_distribution_data(request)
    elif chart_type == 'test_performance':
        return get_test_performance_data(request)
    
    return JsonResponse({'error': 'Invalid chart type'}, status=400)


def get_monthly_attempts_data(request):
    """Get monthly test attempts data for charts"""
    last_12_months = timezone.now() - timedelta(days=365)
    
    attempts = TestAttempt.objects.filter(start_time__gte=last_12_months)
    if request.user.role == 'teacher':
        attempts = attempts.filter(test__created_by=request.user)
    
    monthly_data = attempts.extra(
        select={'month': 'strftime("%%Y-%%m", start_time)'}
    ).values('month').annotate(count=Count('id')).order_by('month')
    
    return JsonResponse({
        'labels': [item['month'] for item in monthly_data],
        'data': [item['count'] for item in monthly_data]
    })


def get_score_distribution_data(request):
    """Get score distribution data for charts"""
    attempts = TestAttempt.objects.filter(status='evaluated')
    if request.user.role == 'teacher':
        attempts = attempts.filter(test__created_by=request.user)
    
    distribution = [
        ('90-100%', attempts.filter(percentage__gte=90).count()),
        ('80-89%', attempts.filter(percentage__gte=80, percentage__lt=90).count()),
        ('70-79%', attempts.filter(percentage__gte=70, percentage__lt=80).count()),
        ('60-69%', attempts.filter(percentage__gte=60, percentage__lt=70).count()),
        ('Below 60%', attempts.filter(percentage__lt=60).count()),
    ]
    
    return JsonResponse({
        'labels': [item[0] for item in distribution],
        'data': [item[1] for item in distribution]
    })
