from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.urls import reverse
from datetime import timedelta
import json

from rest_framework import generics, status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    Exam, Test, TestSection, TestAttempt, Organization, ExamMetadata, Syllabus, Subject, 
    SyllabusNode, StudentSyllabusProgress, LearningContent, InteractiveElement, Assessment, 
    StudentLearningProgress, AssessmentAttempt, LearningAnalytics
)
from .serializers import (
    ExamSerializer, TestSerializer, TestSectionSerializer,
    TestAttemptSerializer, TestDetailSerializer
)
from questions.models import UserAnswer, Question, TestQuestion
from core.decorators import (
    api_rate_limit, test_submission_rate_limit, require_role,
    security_check, validate_test_access, log_user_action, cache_control
)
from core.security import sanitize_user_input, validate_test_attempt_data, log_security_event
from core.exam_utils import find_compatible_question_banks, get_exam_question_bank_suggestions
from core.question_selection import QuestionSelectionEngine


# Template Views
@login_required
@cache_control(max_age=300, private=True)
@log_user_action('view_exam_list')
def exam_list(request):
    """List available exams for students"""
    exams = Exam.objects.filter(is_active=True).select_related('organization').prefetch_related('tests').annotate(
        tests_count=Count('tests')
    )
    
    # Search functionality with input sanitization
    search = sanitize_user_input(request.GET.get('search', ''))
    if search:
        exams = exams.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(category__icontains=search) |
            Q(organization__name__icontains=search)
        )
    
    # Category filter with input sanitization
    category = sanitize_user_input(request.GET.get('category', ''))
    if category:
        exams = exams.filter(category=category)
    
    # Organization filter
    organization_id = request.GET.get('organization')
    if organization_id:
        exams = exams.filter(organization_id=organization_id)
    
    # Year filter
    year = request.GET.get('year')
    if year:
        exams = exams.filter(year=year)
    
    # Get filter options
    categories = Exam.objects.filter(is_active=True).values_list('category', flat=True).distinct().order_by('category')
    organizations = Organization.objects.filter(is_active=True, exams__is_active=True).distinct().order_by('name')
    years = Exam.objects.filter(is_active=True).values_list('year', flat=True).distinct().order_by('-year')
    
    paginator = Paginator(exams, 12)
    page = request.GET.get('page')
    exams = paginator.get_page(page)
    
    context = {
        'exams': exams,
        'categories': [c for c in categories if c],
        'organizations': organizations,
        'years': [y for y in years if y],
        'search': search,
        'selected_category': category,
        'selected_organization': organization_id,
        'selected_year': year,
    }
    return render(request, 'exams/exam_list.html', context)


@login_required
def exam_management(request):
    """Exam management view for teachers and admins"""
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    # Get exams based on user role
    if request.user.role == 'admin':
        exams = Exam.objects.all().annotate(
            tests_count=Count('tests'),
            active_tests_count=Count('tests', filter=Q(tests__is_published=True))
        )
    else:
        exams = Exam.objects.filter(created_by=request.user).annotate(
            tests_count=Count('tests'),
            active_tests_count=Count('tests', filter=Q(tests__is_published=True))
        )
    
    # Search functionality
    search = sanitize_user_input(request.GET.get('search', ''))
    if search:
        exams = exams.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(category__icontains=search)
        )
    
    # Add ordering to prevent pagination warnings
    exams = exams.order_by('-created_at')
    
    paginator = Paginator(exams, 15)
    page = request.GET.get('page')
    exams = paginator.get_page(page)
    
    context = {
        'exams': exams,
        'search': search,
    }
    return render(request, 'exams/exam_management.html', context)


@login_required
def create_exam(request):
    """Create new exam view"""
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Basic Information
        name = sanitize_user_input(request.POST.get('name', ''))
        description = sanitize_user_input(request.POST.get('description', ''))
        category = sanitize_user_input(request.POST.get('category', ''))
        
        # Exam Specific
        exam_type = sanitize_user_input(request.POST.get('exam_type', ''))
        organization_id = request.POST.get('organization')
        year = request.POST.get('year', '')
        
        # Subject Organization
        subject = sanitize_user_input(request.POST.get('subject', ''))
        topic = sanitize_user_input(request.POST.get('topic', ''))
        subtopic = sanitize_user_input(request.POST.get('subtopic', ''))
        
        # Target & Difficulty
        difficulty_level = request.POST.get('difficulty_level', 'intermediate')
        target_audience = request.POST.get('target_audience', 'general')
        
        # Language & Location
        language = sanitize_user_input(request.POST.get('language', 'english'))
        state_specific = sanitize_user_input(request.POST.get('state_specific', ''))
        
        # Tags and metadata
        tags_str = sanitize_user_input(request.POST.get('tags', ''))
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        
        # Settings
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        
        # Custom fields
        custom_fields = {}
        for key, value in request.POST.items():
            if key.startswith('custom_'):
                field_name = key.replace('custom_', '')
                if value.strip():
                    custom_fields[field_name] = sanitize_user_input(value)
        
        if not name:
            messages.error(request, "Exam name is required.")
        else:
            # Parse year
            year_int = None
            if year and year.isdigit():
                year_int = int(year)
            
            exam_data = {
                'name': name,
                'description': description,
                'category': category,
                'exam_type': exam_type,
                'subject': subject,
                'topic': topic,
                'subtopic': subtopic,
                'difficulty_level': difficulty_level,
                'target_audience': target_audience,
                'language': language,
                'state_specific': state_specific,
                'tags': tags,
                'custom_fields': custom_fields,
                'is_active': is_active,
                'is_featured': is_featured,
                'created_by': request.user
            }
            
            if organization_id:
                exam_data['organization_id'] = organization_id
            if year_int:
                exam_data['year'] = year_int
            
            exam = Exam.objects.create(**exam_data)
            messages.success(request, f"Exam '{name}' created successfully.")
            return redirect('exam-detail', exam_id=exam.id)
    
    # Get organizations for the dropdown
    organizations = Organization.objects.filter(is_active=True).order_by('name')
    
    context = {
        'organizations': organizations,
    }
    return render(request, 'exams/create_exam.html', context)


@login_required
def create_test(request, exam_id):
    """Create new test for an exam"""
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Check if user can create tests for this exam
    if request.user.role != 'admin' and exam.created_by != request.user:
        messages.error(request, "You don't have permission to create tests for this exam.")
        return redirect('exam-detail', exam_id=exam_id)
    
    if request.method == 'POST':
        title = sanitize_user_input(request.POST.get('title', ''))
        description = sanitize_user_input(request.POST.get('description', ''))
        duration_minutes = request.POST.get('duration_minutes', 60)
        total_marks = request.POST.get('total_marks', 100)
        pass_percentage = request.POST.get('pass_percentage', 60)
        max_attempts = request.POST.get('max_attempts', 1)
        is_published = request.POST.get('is_published') == 'on'
        
        try:
            duration_minutes = int(duration_minutes)
            total_marks = int(total_marks)
            pass_percentage = int(pass_percentage)
            max_attempts = int(max_attempts)
        except ValueError:
            messages.error(request, "Please enter valid numbers for numeric fields.")
            return render(request, 'exams/create_test.html', {'exam': exam})
        
        if not title:
            messages.error(request, "Test name is required.")
        else:
            test = Test.objects.create(
                exam=exam,
                title=title,
                description=description,
                duration_minutes=duration_minutes,
                total_marks=total_marks,
                pass_percentage=pass_percentage,
                max_attempts=max_attempts,
                is_published=is_published,
                created_by=request.user
            )
            messages.success(request, f"Test '{title}' created successfully. Now configure question selection.")
            return redirect('configure-question-selection', test_id=test.id)
    
    context = {'exam': exam}
    return render(request, 'exams/create_test.html', context)


@login_required  
def edit_exam(request, exam_id):
    """Edit existing exam"""
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Check if user can edit this exam
    if request.user.role != 'admin' and exam.created_by != request.user:
        messages.error(request, "You don't have permission to edit this exam.")
        return redirect('exam-detail', exam_id=exam_id)
    
    if request.method == 'POST':
        name = sanitize_user_input(request.POST.get('name', ''))
        description = sanitize_user_input(request.POST.get('description', ''))
        category = sanitize_user_input(request.POST.get('category', ''))
        is_active = request.POST.get('is_active') == 'on'
        
        if not name:
            messages.error(request, "Exam name is required.")
        else:
            exam.name = name
            exam.description = description
            exam.category = category
            exam.is_active = is_active
            exam.save()
            
            messages.success(request, f"Exam '{name}' updated successfully.")
            return redirect('exam-detail', exam_id=exam.id)
    
    context = {'exam': exam}
    return render(request, 'exams/edit_exam.html', context)


@login_required
def edit_test(request, test_id):
    """Edit existing test"""
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    test = get_object_or_404(Test, id=test_id)
    
    # Check if user can edit this test
    if request.user.role != 'admin' and test.created_by != request.user:
        messages.error(request, "You don't have permission to edit this test.")
        return redirect('test-detail', test_id=test_id)
    
    if request.method == 'POST':
        title = sanitize_user_input(request.POST.get('title', ''))
        description = sanitize_user_input(request.POST.get('description', ''))
        duration_minutes = request.POST.get('duration_minutes', '')
        total_marks = request.POST.get('total_marks', '')
        pass_percentage = request.POST.get('pass_percentage', '')
        max_attempts = request.POST.get('max_attempts', '')
        is_published = request.POST.get('is_published') == 'on'
        
        try:
            # Use current values as defaults if fields are empty
            duration_minutes = int(duration_minutes) if duration_minutes else test.duration_minutes
            total_marks = int(total_marks) if total_marks else test.total_marks
            pass_percentage = float(pass_percentage) if pass_percentage else float(test.pass_percentage)
            max_attempts = int(max_attempts) if max_attempts else test.max_attempts
        except ValueError:
            messages.error(request, "Please enter valid numbers for numeric fields.")
            return render(request, 'exams/edit_test.html', {'test': test})
        
        if not title:
            messages.error(request, "Test name is required.")
        else:
            test.title = title
            test.description = description
            test.duration_minutes = duration_minutes
            test.total_marks = total_marks
            test.pass_percentage = pass_percentage
            test.max_attempts = max_attempts
            test.is_published = is_published
            test.save()
            
            messages.success(request, f"Test '{title}' updated successfully.")
            return redirect('exam-detail', exam_id=test.exam.id)
    
    context = {'test': test}
    return render(request, 'exams/edit_test.html', context)


@login_required
@require_http_methods(["POST"])
def delete_test(request, test_id):
    """Delete a test"""
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    test = get_object_or_404(Test, id=test_id)
    exam_id = test.exam.id
    
    # Check if user can delete this test
    if request.user.role != 'admin' and test.created_by != request.user:
        messages.error(request, "You don't have permission to delete this test.")
        return redirect('exam-detail', exam_id=exam_id)
    
    test_title = test.title
    test.delete()
    
    messages.success(request, f"Test '{test_title}' has been deleted successfully.")
    return redirect('exam-detail', exam_id=exam_id)


@login_required
def exam_detail(request, exam_id):
    """Exam detail view with available tests"""
    exam = get_object_or_404(Exam, id=exam_id, is_active=True)
    tests = exam.tests.filter(is_published=True).annotate(
        attempts_count=Count('attempts'),
        avg_score=Avg('attempts__percentage')
    )
    
    # Get counts for dashboard
    published_tests_count = exam.tests.filter(is_published=True).count()
    draft_tests_count = exam.tests.filter(is_published=False).count()
    total_attempts = TestAttempt.objects.filter(test__exam=exam).count()
    
    # Get user's attempts for each test
    user_attempts = {}
    if request.user.is_authenticated:
        attempts = TestAttempt.objects.filter(
            user=request.user,
            test__in=tests
        ).select_related('test')
        
        for attempt in attempts:
            if attempt.test_id not in user_attempts:
                user_attempts[attempt.test_id] = []
            user_attempts[attempt.test_id].append(attempt)
    
    context = {
        'exam': exam,
        'tests': tests,
        'user_attempts': user_attempts,
        'published_tests_count': published_tests_count,
        'draft_tests_count': draft_tests_count,
        'total_attempts': total_attempts,
    }
    return render(request, 'exams/exam_detail.html', context)


@login_required
def test_detail(request, test_id):
    """Test detail view before starting"""
    test = get_object_or_404(Test, id=test_id)
    
    # Check permissions
    if not test.is_published and test.created_by != request.user:
        messages.error(request, "This test is not available.")
        return redirect('exam-list')
    
    # Get user's previous attempts
    attempts = TestAttempt.objects.filter(
        user=request.user,
        test=test
    ).order_by('-start_time')
    
    # Check if user can take the test
    can_take_test = True
    error_message = None
    
    # Check if test is published (only published tests can be taken by students)
    if not test.is_published and test.created_by != request.user:
        can_take_test = False
        error_message = "This test is not yet published and not available for students"
    
    if attempts.count() >= test.max_attempts:
        can_take_test = False
        error_message = f"You have reached the maximum number of attempts ({test.max_attempts})"
    
    # Check time restrictions
    now = timezone.now()
    if test.start_time and now < test.start_time:
        can_take_test = False
        error_message = f"Test will be available from {test.start_time.strftime('%B %d, %Y at %I:%M %p')}"
    
    if test.end_time and now > test.end_time:
        can_take_test = False
        error_message = "Test has ended"
    
    # Check for active attempt
    active_attempt = attempts.filter(status='in_progress').first()
    
    context = {
        'test': test,
        'attempts': attempts,
        'can_take_test': can_take_test,
        'error_message': error_message,
        'active_attempt': active_attempt,
    }
    return render(request, 'exams/test_detail.html', context)


@login_required
def start_test(request, test_id):
    """Start a new test attempt"""
    test = get_object_or_404(Test, id=test_id)
    
    # Validation checks
    if not test.is_published and test.created_by != request.user:
        messages.error(request, "This test is not available.")
        return redirect('exam-list')
    
    # Check existing attempts
    attempts_count = TestAttempt.objects.filter(user=request.user, test=test).count()
    if attempts_count >= test.max_attempts:
        messages.error(request, f"You have reached the maximum number of attempts ({test.max_attempts})")
        return redirect('test-detail', test_id=test_id)
    
    # Check for active attempt
    active_attempt = TestAttempt.objects.filter(
        user=request.user, 
        test=test, 
        status='in_progress'
    ).first()
    
    if active_attempt:
        return redirect('take-test', attempt_id=active_attempt.id)
    
    # Check time restrictions
    now = timezone.now()
    if test.start_time and now < test.start_time:
        messages.error(request, "Test has not started yet.")
        return redirect('test-detail', test_id=test_id)
    
    if test.end_time and now > test.end_time:
        messages.error(request, "Test has ended.")
        return redirect('test-detail', test_id=test_id)
    
    # Create new attempt
    # Calculate attempt number
    attempt_number = TestAttempt.objects.filter(user=request.user, test=test).count() + 1
    
    attempt = TestAttempt.objects.create(
        test=test,
        user=request.user,
        attempt_number=attempt_number,
        total_questions=test.test_questions.count()
    )
    
    messages.success(request, f"Test started successfully! (Attempt {attempt_number} of {test.max_attempts})")
    return redirect('take-test', attempt_id=attempt.id)


@login_required
@security_check
@log_user_action('take_test')
def take_test(request, attempt_id):
    """Main test-taking interface"""
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    
    if attempt.status != 'in_progress':
        messages.info(request, "This test attempt has been completed.")
        return redirect('test-results', attempt_id=attempt_id)
    
    # Check if test time has expired
    test_duration = timedelta(minutes=attempt.test.duration_minutes)
    time_elapsed = timezone.now() - attempt.start_time
    
    if time_elapsed >= test_duration:
        # Auto-submit the test
        attempt.status = 'submitted'
        attempt.end_time = timezone.now()
        attempt.save()
        messages.info(request, "Test time has expired. Your answers have been submitted.")
        return redirect('test-results', attempt_id=attempt_id)
    
    # Get test questions
    test_questions = TestQuestion.objects.filter(
        test=attempt.test
    ).select_related('question').prefetch_related('question__options').order_by('order')
    
    # Randomize if enabled
    if attempt.test.randomize_questions:
        test_questions = test_questions.order_by('?')
    
    # Get user's existing answers
    user_answers = UserAnswer.objects.filter(
        test_attempt=attempt
    ).select_related('question').prefetch_related('selected_options')
    
    answers_dict = {answer.question_id: answer for answer in user_answers}
    
    # Calculate progress
    answered_count = user_answers.count()
    progress_percentage = (answered_count / attempt.total_questions * 100) if attempt.total_questions > 0 else 0
    
    # Calculate remaining time
    remaining_time = test_duration - time_elapsed
    remaining_seconds = int(remaining_time.total_seconds())
    
    context = {
        'attempt': attempt,
        'test_questions': test_questions,
        'answers_dict': answers_dict,
        'answered_count': answered_count,
        'progress_percentage': progress_percentage,
        'remaining_seconds': remaining_seconds,
        'current_question_index': int(request.GET.get('q', 1)) - 1,
    }
    return render(request, 'exams/take_test.html', context)


@login_required
@require_http_methods(["POST"])
@test_submission_rate_limit
@security_check
@log_user_action('save_answer')
def save_answer(request, attempt_id):
    """Save user answer via HTMX"""
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    
    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'Test is not active'}, status=400)
    
    question_id = request.POST.get('question_id')
    question = get_object_or_404(Question, id=question_id)
    
    # Get or create user answer
    user_answer, created = UserAnswer.objects.get_or_create(
        test_attempt=attempt,
        question=question,
        defaults={'time_spent_seconds': 0}
    )
    
    # Save answer based on question type
    if question.question_type == 'mcq':
        selected_option_id = request.POST.get('selected_option')
        if selected_option_id:
            user_answer.selected_options.clear()
            user_answer.selected_options.add(selected_option_id)
    
    elif question.question_type == 'multi_select':
        selected_options = request.POST.getlist('selected_options')
        user_answer.selected_options.clear()
        if selected_options:
            user_answer.selected_options.add(*selected_options)
    
    elif question.question_type == 'true_false':
        boolean_answer = request.POST.get('boolean_answer')
        if boolean_answer is not None:
            user_answer.boolean_answer = boolean_answer.lower() == 'true'
    
    elif question.question_type in ['fill_blank', 'essay']:
        text_answer = request.POST.get('text_answer', '')
        user_answer.text_answer = sanitize_user_input(text_answer)
    
    # Mark for review
    user_answer.is_marked_for_review = request.POST.get('mark_for_review') == 'true'
    user_answer.save()
    
    # Update attempt stats
    attempt.attempted_questions = UserAnswer.objects.filter(test_attempt=attempt).count()
    attempt.save()
    
    return JsonResponse({
        'success': True,
        'answered_count': attempt.attempted_questions,
        'progress': (attempt.attempted_questions / attempt.total_questions * 100) if attempt.total_questions > 0 else 0
    })


@login_required
@require_http_methods(["POST"])
@test_submission_rate_limit
@security_check
@log_user_action('submit_test')
def submit_test(request, attempt_id):
    """Submit test attempt"""
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    
    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'Test is not active'}, status=400)
    
    # Calculate results
    attempt.end_time = timezone.now()
    attempt.time_spent_seconds = int((attempt.end_time - attempt.start_time).total_seconds())
    
    # Evaluate answers
    user_answers = UserAnswer.objects.filter(test_attempt=attempt).prefetch_related('selected_options')
    correct_answers = 0
    total_marks = 0
    
    for answer in user_answers:
        question = answer.question
        is_correct = False
        marks_obtained = 0
        
        if question.question_type == 'mcq':
            correct_options = question.options.filter(is_correct=True)
            selected_options = answer.selected_options.all()
            
            if len(selected_options) == 1 and len(correct_options) == 1:
                if selected_options[0] in correct_options:
                    is_correct = True
                    marks_obtained = question.marks
                else:
                    marks_obtained = -question.negative_marks
        
        elif question.question_type == 'multi_select':
            correct_options = set(question.options.filter(is_correct=True))
            selected_options = set(answer.selected_options.all())
            
            if correct_options == selected_options:
                is_correct = True
                marks_obtained = question.marks
            else:
                marks_obtained = -question.negative_marks
        
        elif question.question_type == 'true_false':
            # Simple true/false evaluation
            if hasattr(answer, 'boolean_answer') and answer.boolean_answer is not None:
                # This would need to be compared with the correct answer stored somewhere
                # For now, assuming first option is correct answer
                correct_option = question.options.filter(is_correct=True).first()
                if correct_option:
                    expected_answer = correct_option.option_text.lower() == 'true'
                    if answer.boolean_answer == expected_answer:
                        is_correct = True
                        marks_obtained = question.marks
                    else:
                        marks_obtained = -question.negative_marks
        
        answer.is_correct = is_correct
        answer.marks_obtained = marks_obtained
        answer.save()
        
        if is_correct:
            correct_answers += 1
        total_marks += marks_obtained
    
    attempt.correct_answers = correct_answers
    attempt.marks_obtained = max(0, total_marks)  # Don't allow negative total
    attempt.percentage = (attempt.marks_obtained / attempt.test.total_marks * 100) if attempt.test.total_marks > 0 else 0
    attempt.status = 'evaluated'
    attempt.save()
    
    return JsonResponse({
        'success': True,
        'redirect_url': f'/exams/results/{attempt_id}/'
    })


@login_required
@cache_control(max_age=600, private=True)
@log_user_action('view_test_results')
def test_results(request, attempt_id):
    """Display test results"""
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    
    if attempt.status == 'in_progress':
        messages.info(request, "Test is still in progress.")
        return redirect('take-test', attempt_id=attempt_id)
    
    # Get detailed results
    user_answers = UserAnswer.objects.filter(
        test_attempt=attempt
    ).select_related('question').prefetch_related('selected_options', 'question__options')
    
    # Group by sections if any
    sections_data = {}
    for answer in user_answers:
        section_name = "General"  # Default section
        if hasattr(answer.question, 'test_question') and answer.question.test_question.section:
            section_name = answer.question.test_question.section.name
        
        if section_name not in sections_data:
            sections_data[section_name] = {
                'questions': [],
                'correct': 0,
                'total': 0,
                'marks': 0
            }
        
        sections_data[section_name]['questions'].append(answer)
        sections_data[section_name]['total'] += 1
        if answer.is_correct:
            sections_data[section_name]['correct'] += 1
        sections_data[section_name]['marks'] += answer.marks_obtained
    
    # Calculate statistics
    pass_status = attempt.percentage >= attempt.test.pass_percentage
    
    context = {
        'attempt': attempt,
        'user_answers': user_answers,
        'sections_data': sections_data,
        'pass_status': pass_status,
        'show_detailed_results': attempt.test.allow_review,
    }
    return render(request, 'exams/test_results.html', context)


@login_required
def my_attempts(request):
    """List user's test attempts"""
    attempts = TestAttempt.objects.filter(
        user=request.user
    ).select_related('test', 'test__exam').order_by('-start_time')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        attempts = attempts.filter(status=status_filter)
    
    paginator = Paginator(attempts, 20)
    page = request.GET.get('page')
    attempts = paginator.get_page(page)
    
    context = {
        'attempts': attempts,
        'status_filter': status_filter,
    }
    return render(request, 'exams/my_attempts.html', context)


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]  # Restored for security
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Handle anonymous users for testing
        if not self.request.user.is_authenticated:
            return queryset.filter(is_active=True)  # Show only active exams for anonymous users
        
        if self.request.user.role == 'student':
            queryset = queryset.filter(is_active=True)
        elif self.request.user.role == 'teacher':
            queryset = queryset.filter(Q(created_by=self.request.user) | Q(is_active=True))
        return queryset
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            # For anonymous users, don't set created_by or handle appropriately
            serializer.save()


class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        exam_id = self.request.query_params.get('exam')
        if exam_id:
            queryset = queryset.filter(exam_id=exam_id)
        
        if self.request.user.role == 'student':
            queryset = queryset.filter(is_published=True)
        elif self.request.user.role == 'teacher':
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(is_published=True)
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TestDetailSerializer
        return TestSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def start_attempt(self, request, pk=None):
        test = self.get_object()
        user = request.user
        
        # Check if test is available
        now = timezone.now()
        if test.start_time and now < test.start_time:
            return Response(
                {'error': 'Test has not started yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if test.end_time and now > test.end_time:
            return Response(
                {'error': 'Test has ended'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check existing attempts
        attempts_count = TestAttempt.objects.filter(test=test, user=user).count()
        if attempts_count >= test.max_attempts:
            return Response(
                {'error': f'Maximum attempts ({test.max_attempts}) reached'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new attempt
        attempt = TestAttempt.objects.create(
            test=test,
            user=user,
            total_questions=test.test_questions.count()
        )
        
        serializer = TestAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def submit_attempt(self, request, pk=None):
        test = self.get_object()
        
        try:
            attempt = TestAttempt.objects.get(
                test=test,
                user=request.user,
                status='in_progress'
            )
        except TestAttempt.DoesNotExist:
            return Response(
                {'error': 'No active attempt found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate results
        attempt.end_time = timezone.now()
        attempt.time_spent_seconds = (attempt.end_time - attempt.start_time).total_seconds()
        
        # Get all answers
        answers = UserAnswer.objects.filter(test_attempt=attempt)
        attempt.attempted_questions = answers.count()
        
        correct_answers = 0
        total_marks = 0
        
        for answer in answers:
            if answer.is_correct:
                correct_answers += 1
                total_marks += answer.marks_obtained
        
        attempt.correct_answers = correct_answers
        attempt.marks_obtained = total_marks
        attempt.percentage = (total_marks / test.total_marks) * 100 if test.total_marks > 0 else 0
        attempt.status = 'submitted'
        attempt.save()
        
        serializer = TestAttemptSerializer(attempt)
        return Response(serializer.data)


class TestAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TestAttempt.objects.all()
    serializer_class = TestAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 'student':
            queryset = queryset.filter(user=self.request.user)
        elif self.request.user.role == 'teacher':
            queryset = queryset.filter(test__created_by=self.request.user)
        
        test_id = self.request.query_params.get('test')
        if test_id:
            queryset = queryset.filter(test_id=test_id)
        
        return queryset


# Organization Management Views
@login_required
@require_role(['teacher', 'admin'])
def organization_list(request):
    """List all organizations with exam counts"""
    organizations = Organization.objects.filter(is_active=True).annotate(
        exams_count=Count('exams'),
        active_exams_count=Count('exams', filter=Q(exams__is_active=True))
    ).order_by('name')
    
    context = {
        'organizations': organizations,
    }
    return render(request, 'exams/organization_list.html', context)


@login_required
@require_role(['teacher', 'admin'])
def create_organization(request):
    """Create new organization"""
    if request.method == 'POST':
        name = sanitize_user_input(request.POST.get('name', ''))
        short_name = sanitize_user_input(request.POST.get('short_name', ''))
        organization_type = request.POST.get('organization_type', 'government')
        website = request.POST.get('website', '')
        email = request.POST.get('email', '')
        phone = sanitize_user_input(request.POST.get('phone', ''))
        description = sanitize_user_input(request.POST.get('description', ''))
        address = sanitize_user_input(request.POST.get('address', ''))
        
        if not name:
            messages.error(request, "Organization name is required.")
        else:
            try:
                organization = Organization.objects.create(
                    name=name,
                    short_name=short_name,
                    organization_type=organization_type,
                    website=website,
                    email=email,
                    phone=phone,
                    description=description,
                    address=address,
                    created_by=request.user
                )
                
                # Handle logo upload
                if request.FILES.get('logo'):
                    organization.logo = request.FILES['logo']
                    organization.save()
                
                messages.success(request, f"Organization '{name}' created successfully.")
                return redirect('organization-detail', org_id=organization.id)
            except Exception as e:
                messages.error(request, f"Error creating organization: {str(e)}")
    
    return render(request, 'exams/create_organization.html')


@login_required
def organization_detail(request, org_id):
    """View organization details and its exams"""
    organization = get_object_or_404(Organization, id=org_id)
    
    # Get all exams for this organization
    exams = organization.exams.all().annotate(
        tests_count=Count('tests'),
        total_attempts=Count('tests__attempts')
    ).order_by('-year', '-created_at')
    
    # Group exams by year
    exams_by_year = {}
    for exam in exams:
        year = exam.year or 'Other'
        if year not in exams_by_year:
            exams_by_year[year] = []
        exams_by_year[year].append(exam)
    
    context = {
        'organization': organization,
        'exams': exams,
        'exams_by_year': dict(sorted(exams_by_year.items(), reverse=True)),
    }
    return render(request, 'exams/organization_detail.html', context)


@login_required
def enhanced_exam_management(request):
    """Enhanced exam management with organization view and search"""
    view_mode = request.GET.get('view', 'organization')  # organization, list, grid, calendar
    
    if view_mode == 'organization':
        # Organization view
        organizations = Organization.objects.filter(is_active=True).annotate(
            exams_count=Count('exams'),
            active_exams_count=Count('exams', filter=Q(exams__is_active=True))
        ).order_by('name')
        
        context = {
            'organizations': organizations,
            'view_mode': view_mode,
        }
        return render(request, 'exams/exam_management_organization.html', context)
    
    elif view_mode == 'calendar':
        # Calendar view - show exams with important dates
        from datetime import datetime, timedelta
        import json
        today = timezone.now().date()
        current_year = today.year
        current_month = today.month
        
        # Get exams with metadata for calendar display
        exams_with_metadata = Exam.objects.filter(
            is_active=True,
            metadata__isnull=False
        ).select_related('organization', 'metadata')
        
        # Prepare exam events for calendar
        exam_events = []
        for exam in exams_with_metadata:
            metadata = exam.metadata
            base_event = {
                'exam_name': exam.name,
                'exam_url': f'/exams/{exam.id}/',
                'organization': exam.organization.name if exam.organization else '',
            }
            
            # Add different types of events based on metadata
            if metadata.exam_start_date:
                exam_events.append({
                    **base_event,
                    'title': f'{exam.name} (Exam)',
                    'date': metadata.exam_start_date.isoformat(),
                    'type': 'exam-date',
                    'type_display': 'Exam Date',
                    'description': f'Exam date for {exam.name}'
                })
            
            if metadata.form_start_date:
                exam_events.append({
                    **base_event,
                    'title': f'{exam.name} (Application Start)',
                    'date': metadata.form_start_date.date().isoformat(),
                    'type': 'application',
                    'type_display': 'Application Period',
                    'description': f'Application period starts for {exam.name}'
                })
            
            if metadata.result_date:
                exam_events.append({
                    **base_event,
                    'title': f'{exam.name} (Results)',
                    'date': metadata.result_date.isoformat(),
                    'type': 'result',
                    'type_display': 'Result Declaration',
                    'description': f'Results for {exam.name}'
                })
            
            if metadata.admit_card_date:
                exam_events.append({
                    **base_event,
                    'title': f'{exam.name} (Admit Card)',
                    'date': metadata.admit_card_date.isoformat(),
                    'type': 'admit-card',
                    'type_display': 'Admit Card Release',
                    'description': f'Admit card release for {exam.name}'
                })
        
        # Prepare months data
        months = [
            {'number': i, 'name': datetime(2024, i, 1).strftime('%B')} 
            for i in range(1, 13)
        ]
        
        # Available years (current year ± 2)
        available_years = list(range(current_year - 2, current_year + 3))
        
        context = {
            'exam_events': json.dumps(exam_events),
            'current_month': current_month,
            'current_year': current_year,
            'current_month_name': datetime(current_year, current_month, 1).strftime('%B'),
            'months': months,
            'available_years': available_years,
            'view_mode': view_mode,
        }
        return render(request, 'exams/exam_management_calendar.html', context)
    
    else:
        # Default list/grid view
        exams = Exam.objects.all().select_related('organization').annotate(
            tests_count=Count('tests'),
            active_tests_count=Count('tests', filter=Q(tests__is_published=True)),
            total_attempts=Count('tests__attempts')
        )
        
        # Apply filters
        organization_id = request.GET.get('organization')
        if organization_id:
            exams = exams.filter(organization_id=organization_id)
        
        year = request.GET.get('year')
        if year:
            exams = exams.filter(year=year)
        
        search = request.GET.get('search', '')
        if search:
            exams = exams.filter(
                Q(name__icontains=search) | 
                Q(organization__name__icontains=search) |
                Q(category__icontains=search)
            )
        
        # Get filter options
        organizations = Organization.objects.filter(is_active=True)
        years = Exam.objects.values_list('year', flat=True).distinct().order_by('-year')
        categories = Exam.objects.values_list('category', flat=True).distinct().order_by('category')
        
        context = {
            'exams': exams.order_by('-created_at'),
            'organizations': organizations,
            'years': [y for y in years if y],
            'categories': [c for c in categories if c],
            'view_mode': view_mode,
            'search': search,
            'selected_organization': organization_id,
            'selected_year': year,
        }
        
        if view_mode == 'grid':
            return render(request, 'exams/exam_management_grid.html', context)
        elif view_mode == 'list':
            return render(request, 'exams/exam_management_list.html', context)
        else:
            return render(request, 'exams/exam_management_list.html', context)


@login_required
def exam_metadata_edit(request, exam_id):
    """Edit exam metadata - dates, eligibility, etc."""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Check permissions
    if request.user.role != 'admin' and exam.created_by != request.user:
        messages.error(request, "You don't have permission to edit this exam.")
        return redirect('exam-detail', exam_id=exam_id)
    
    # Get or create metadata
    metadata, created = ExamMetadata.objects.get_or_create(exam=exam)
    
    if request.method == 'POST':
        # Update dates
        date_fields = [
            'notification_date', 'form_start_date', 'form_end_date', 
            'form_extended_date', 'fee_payment_last_date', 
            'correction_window_start', 'correction_window_end',
            'admit_card_date', 'exam_start_date', 'exam_end_date', 'result_date'
        ]
        
        for field in date_fields:
            value = request.POST.get(field)
            if value:
                setattr(metadata, field, value)
        
        # Update other fields
        metadata.min_age = request.POST.get('min_age') or None
        metadata.max_age = request.POST.get('max_age') or None
        metadata.eligibility_criteria = sanitize_user_input(request.POST.get('eligibility_criteria', ''))
        metadata.official_notification_url = request.POST.get('official_notification_url', '')
        metadata.syllabus_url = request.POST.get('syllabus_url', '')
        metadata.apply_online_url = request.POST.get('apply_online_url', '')
        
        # Update fee structure (JSON)
        fee_structure = {}
        for category in ['general', 'obc', 'sc_st', 'female', 'pwd']:
            fee = request.POST.get(f'fee_{category}')
            if fee:
                fee_structure[category] = float(fee)
        metadata.fee_structure = fee_structure
        
        # Update tags
        tags = request.POST.get('tags', '').split(',')
        metadata.tags = [tag.strip() for tag in tags if tag.strip()]
        
        metadata.save()
        messages.success(request, "Exam metadata updated successfully.")
        return redirect('exam-detail', exam_id=exam_id)
    
    context = {
        'exam': exam,
        'metadata': metadata,
    }
    return render(request, 'exams/exam_metadata_edit.html', context)


@login_required
def ajax_exam_search(request):
    """AJAX endpoint for exam search autocomplete"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search in exams and organizations
    exams = Exam.objects.filter(
        Q(name__icontains=query) | 
        Q(organization__name__icontains=query) |
        Q(category__icontains=query)
    ).select_related('organization')[:10]
    
    results = []
    for exam in exams:
        results.append({
            'id': str(exam.id),
            'text': exam.name,
            'organization': exam.organization.name if exam.organization else 'N/A',
            'category': exam.category,
            'year': exam.year or 'N/A',
            'url': f'/exams/{exam.id}/'
        })
    
    # Also search organizations
    orgs = Organization.objects.filter(
        Q(name__icontains=query) | Q(short_name__icontains=query)
    )[:5]
    
    for org in orgs:
        results.append({
            'id': f'org_{org.id}',
            'text': org.name,
            'type': 'organization',
            'exams_count': org.exams.count(),
            'url': f'/exams/organization/{org.id}/'
        })
    
    return JsonResponse({'results': results})


@login_required
@require_role(['teacher', 'admin'])
def get_compatible_question_banks(request, exam_id):
    """Get question banks compatible with the given exam"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Check permissions
    if request.user.role == 'teacher' and exam.created_by != request.user:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        suggestions = get_exam_question_bank_suggestions(exam)
        
        # Format response
        response_data = {
            'exam': {
                'id': str(exam.id),
                'name': exam.name,
                'exam_type': exam.exam_type,
                'category': exam.category,
                'tags': exam.tags
            },
            'suggestions': {
                'total_count': suggestions['total_count'],
                'exact_matches': [
                    {
                        'id': str(match['bank'].id),
                        'name': match['bank'].name,
                        'description': match['bank'].description[:200] + '...' if len(match['bank'].description) > 200 else match['bank'].description,
                        'questions_count': match['bank'].total_questions,
                        'score': round(match['score'], 2),
                        'reasons': match['reasons']
                    }
                    for match in suggestions['exact_matches']
                ],
                'good_matches': [
                    {
                        'id': str(match['bank'].id),
                        'name': match['bank'].name,
                        'description': match['bank'].description[:200] + '...' if len(match['bank'].description) > 200 else match['bank'].description,
                        'questions_count': match['bank'].total_questions,
                        'score': round(match['score'], 2),
                        'reasons': match['reasons']
                    }
                    for match in suggestions['good_matches']
                ],
                'partial_matches': [
                    {
                        'id': str(match['bank'].id),
                        'name': match['bank'].name,
                        'description': match['bank'].description[:200] + '...' if len(match['bank'].description) > 200 else match['bank'].description,
                        'questions_count': match['bank'].total_questions,
                        'score': round(match['score'], 2),
                        'reasons': match['reasons']
                    }
                    for match in suggestions['partial_matches']
                ]
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Question Selection Views
@login_required
def configure_question_selection(request, test_id):
    """Configure question selection rules for a test"""
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    test = get_object_or_404(Test, id=test_id)
    
    # Check permissions
    if request.user.role != 'admin' and test.created_by != request.user:
        messages.error(request, "You don't have permission to configure this test.")
        return redirect('test-detail', test_id=test_id)
    
    # Get or create selection rule
    from .models import TestSelectionRule, SelectionRuleTemplate
    selection_rule, created = TestSelectionRule.objects.get_or_create(test=test)
    
    # Get available templates
    templates = SelectionRuleTemplate.objects.filter(
        Q(created_by=request.user) | Q(is_public=True)
    ).order_by('-created_at')
    
    # Get question statistics for the exam
    from questions.models import Question, QuestionBank
    from django.db.models import Count
    
    # Get compatible question banks with scores
    suggestions = get_exam_question_bank_suggestions(test.exam)
    
    # Format compatible banks for template
    compatible_banks = []
    all_matches = suggestions['exact_matches'] + suggestions['good_matches'] + suggestions['partial_matches']
    
    for match in all_matches:
        bank = match['bank']
        # Add computed attributes needed by template
        bank.questions_count = bank.questions.count() if hasattr(bank, 'questions') else Question.objects.filter(question_bank=bank).count()
        bank.match_score = round(match['score'] * 100, 1)  # Convert to percentage
        compatible_banks.append(bank)
    
    # Get bank IDs for statistics
    bank_ids = [bank.id for bank in compatible_banks]
    
    # Get question statistics
    question_stats = {
        'total_available': Question.objects.filter(question_bank_id__in=bank_ids).count(),
        'by_difficulty': dict(Question.objects.filter(question_bank_id__in=bank_ids)
                             .values('difficulty').annotate(count=Count('id'))),
        'by_type': dict(Question.objects.filter(question_bank_id__in=bank_ids)
                       .values('question_type').annotate(count=Count('id'))),
        'by_category': dict(Question.objects.filter(question_bank_id__in=bank_ids)
                           .values('question_bank__category').annotate(count=Count('id'))),
    }
    
    # Calculate progress bar percentage for total questions
    total_questions = selection_rule.total_questions or 50  # Default to 50 if not set
    total_available = question_stats['total_available']
    
    if total_available > 0:
        progress_percentage = min((total_questions / total_available) * 100, 100)  # Cap at 100%
    else:
        progress_percentage = 0
    
    context = {
        'test': test,
        'selection_rule': selection_rule,
        'templates': templates,
        'question_stats': question_stats,
        'compatible_banks': compatible_banks,
        'progress_percentage': round(progress_percentage, 1),  # Round to 1 decimal place
        'difficulty_choices': [
            ('basic', 'Basic'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        'question_types': Question.QUESTION_TYPES,
    }
    
    return render(request, 'exams/configure_question_selection.html', context)


@login_required
@require_http_methods(["POST"])
def save_selection_rules(request, test_id):
    """Save question selection rules"""
    if request.user.role == 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    test = get_object_or_404(Test, id=test_id)
    
    # Check permissions
    if request.user.role != 'admin' and test.created_by != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        from .models import TestSelectionRule
        selection_rule, created = TestSelectionRule.objects.get_or_create(test=test)
        
        # Update selection rule fields
        selection_rule.selection_mode = data.get('selection_mode', 'random')
        selection_rule.total_questions = int(data.get('total_questions', 50))
        
        # Update distributions
        selection_rule.difficulty_distribution = data.get('difficulty_distribution', {})
        selection_rule.category_distribution = data.get('category_distribution', {})
        selection_rule.question_type_distribution = data.get('question_type_distribution', {})
        
        # Update filters
        selection_rule.year_range = data.get('year_range', {})
        selection_rule.included_topics = data.get('included_topics', [])
        selection_rule.excluded_topics = data.get('excluded_topics', [])
        selection_rule.included_banks = data.get('included_banks', [])
        selection_rule.excluded_questions = data.get('excluded_questions', [])
        
        # Update advanced rules
        selection_rule.ensure_topic_coverage = data.get('ensure_topic_coverage', True)
        selection_rule.avoid_duplicates_from_attempts = data.get('avoid_duplicates_from_attempts', True)
        selection_rule.priority_new_questions = data.get('priority_new_questions', False)
        
        selection_rule.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Selection rules saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)


@login_required
def apply_manual_selection(request, test_id):
    """Apply manually selected questions to the test"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    if request.user.role == 'student':
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    test = get_object_or_404(Test, id=test_id)
    
    # Check permissions
    if request.user.role != 'admin' and test.created_by != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        # Get the list of selected question IDs from the request
        question_ids = request.POST.getlist('question_ids[]')
        
        if not question_ids:
            return JsonResponse({'success': False, 'error': 'No questions selected'})
        
        # Validate that all question IDs exist
        from questions.models import Question
        questions = Question.objects.filter(id__in=question_ids)
        
        if len(questions) != len(question_ids):
            return JsonResponse({'success': False, 'error': 'Some selected questions do not exist'})
        
        # Clear existing test questions and add the manually selected ones
        test.questions.clear()
        test.questions.set(questions)
        
        # Update test metadata
        test.total_questions = len(questions)
        test.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully added {len(questions)} questions to the test',
            'redirect_url': f'/exams/test/{test_id}/'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def preview_question_selection(request, test_id):
    """Preview questions that will be selected based on current rules"""
    if request.user.role == 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    test = get_object_or_404(Test, id=test_id)
    
    # Check permissions
    if request.user.role != 'admin' and test.created_by != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        from .models import TestSelectionRule
        selection_rule = TestSelectionRule.objects.get(test=test)
        
        # Run selection engine
        engine = QuestionSelectionEngine(test.exam, selection_rule)
        selected_questions = engine.select_questions()
        
        # Get distribution preview
        preview = engine.get_distribution_preview()
        
        # Validate selection
        is_valid, errors = engine.validate_selection()
        
        # Serialize questions for response
        questions_data = []
        for q in selected_questions[:10]:  # Show first 10 as preview
            questions_data.append({
                'id': str(q.id),
                'text': q.question_text[:100] + '...' if len(q.question_text) > 100 else q.question_text,
                'type': q.question_type,
                'difficulty': q.difficulty,
                'category': q.question_bank.category if q.question_bank else 'N/A',
                'bank': q.question_bank.name if q.question_bank else 'N/A',
            })
        
        return JsonResponse({
            'success': True,
            'preview': preview,
            'sample_questions': questions_data,
            'is_valid': is_valid,
            'validation_errors': errors
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def apply_question_selection(request, test_id):
    """Apply the selection rules and add questions to the test"""
    if request.user.role == 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    test = get_object_or_404(Test, id=test_id)
    
    # Check permissions
    if request.user.role != 'admin' and test.created_by != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        from .models import TestSelectionRule
        selection_rule = TestSelectionRule.objects.get(test=test)
        
        # Run selection engine
        engine = QuestionSelectionEngine(test.exam, selection_rule)
        selected_questions = engine.select_questions()
        
        # Validate before applying
        is_valid, errors = engine.validate_selection()
        
        if not is_valid and not request.POST.get('force', False):
            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': 'Validation failed. Add force=true to apply anyway.'
            }, status=400)
        
        # Apply selection to test
        marks_per_question = request.POST.get('marks_per_question')
        if marks_per_question:
            marks_per_question = int(marks_per_question)
        
        success = engine.apply_selection_to_test(marks_per_question)
        
        if success:
            messages.success(request, f"Successfully added {len(selected_questions)} questions to the test.")
            return JsonResponse({
                'success': True,
                'message': f'Added {len(selected_questions)} questions to the test',
                'redirect_url': reverse('test-detail', args=[test.id])
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to apply selection'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def save_selection_template(request):
    """Save current selection rules as a reusable template"""
    if request.user.role == 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        from .models import SelectionRuleTemplate
        
        template = SelectionRuleTemplate.objects.create(
            name=data.get('name', 'Untitled Template'),
            description=data.get('description', ''),
            created_by=request.user,
            selection_mode=data.get('selection_mode', 'random'),
            total_questions=int(data.get('total_questions', 50)),
            difficulty_distribution=data.get('difficulty_distribution', {}),
            category_distribution=data.get('category_distribution', {}),
            question_type_distribution=data.get('question_type_distribution', {}),
            year_range=data.get('year_range', {}),
            included_topics=data.get('included_topics', []),
            excluded_topics=data.get('excluded_topics', []),
            ensure_topic_coverage=data.get('ensure_topic_coverage', True),
            avoid_duplicates_from_attempts=data.get('avoid_duplicates_from_attempts', True),
            priority_new_questions=data.get('priority_new_questions', False),
            is_public=data.get('is_public', False)
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Template saved successfully',
            'template_id': str(template.id)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)


@login_required
def load_selection_template(request, template_id):
    """Load a selection template"""
    if request.user.role == 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    from .models import SelectionRuleTemplate
    template = get_object_or_404(SelectionRuleTemplate, id=template_id)
    
    # Check access
    if not template.is_public and template.created_by != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    return JsonResponse({
        'name': template.name,
        'description': template.description,
        'selection_mode': template.selection_mode,
        'total_questions': template.total_questions,
        'difficulty_distribution': template.difficulty_distribution,
        'category_distribution': template.category_distribution,
        'question_type_distribution': template.question_type_distribution,
        'year_range': template.year_range,
        'included_topics': template.included_topics,
        'excluded_topics': template.excluded_topics,
        'ensure_topic_coverage': template.ensure_topic_coverage,
        'avoid_duplicates_from_attempts': template.avoid_duplicates_from_attempts,
        'priority_new_questions': template.priority_new_questions,
    })


@login_required
def apply_manual_selection(request, test_id):
    """Apply manually selected questions to a test"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if request.user.role == 'student':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    test = get_object_or_404(Test, id=test_id)
    
    # Check permissions
    if test.exam.created_by != request.user and request.user.role != 'admin':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        question_ids = data.get('question_ids', [])
        
        if not question_ids:
            return JsonResponse({'error': 'No questions selected'}, status=400)
        
        # Import Question model
        from questions.models import Question
        
        # Get the selected questions
        questions = Question.objects.filter(id__in=question_ids)
        
        if not questions.exists():
            return JsonResponse({'error': 'No valid questions found'}, status=400)
        
        # Clear existing test questions
        test.questions.clear()
        
        # Add selected questions to the test
        test.questions.set(questions)
        
        # Update test metadata
        test.total_questions = questions.count()
        test.save()
        
        # Update selection rules to manual mode
        selection_rule = test.selection_rule
        if selection_rule:
            selection_rule.selection_mode = 'manual'
            selection_rule.total_questions = questions.count()
            selection_rule.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully applied {questions.count()} questions to the test',
            'total_questions': questions.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to apply questions: {str(e)}'
        }, status=500)


# ============== SYLLABUS TRACKING VIEWS ==============

@login_required
def syllabus_tracker(request):
    """Main syllabus tracker page for students"""
    # Get exams that have syllabus defined
    user_exams = Exam.objects.filter(is_active=True).select_related('syllabus')
    exams_with_syllabus = [exam for exam in user_exams if hasattr(exam, 'syllabus') and exam.syllabus]
    
    context = {
        'exams': exams_with_syllabus,
        'selected_exam_id': request.GET.get('exam_id'),
    }
    return render(request, 'exams/syllabus_tracker.html', context)


@login_required
@require_http_methods(["GET"])
def get_syllabus_data(request, exam_id):
    """API endpoint to fetch syllabus data for a specific exam"""
    try:
        exam = get_object_or_404(Exam, id=exam_id)
        
        if not hasattr(exam, 'syllabus'):
            return JsonResponse({
                'success': False,
                'error': 'No syllabus defined for this exam'
            }, status=404)
        
        syllabus = exam.syllabus
        
        # Get all nodes with their progress for the current user
        from django.db.models import Prefetch
        nodes = SyllabusNode.objects.filter(
            syllabus=syllabus,
            is_active=True
        ).prefetch_related(
            Prefetch(
                'student_progress',
                queryset=StudentSyllabusProgress.objects.filter(student=request.user),
                to_attr='user_progress'
            )
        ).order_by('depth_level', 'order')
        
        # Build hierarchical structure
        def build_node_tree(parent=None):
            node_list = []
            for node in nodes.filter(parent=parent):
                progress = node.user_progress[0] if node.user_progress else None
                
                node_data = {
                    'id': str(node.id),
                    'title': node.title,
                    'description': node.description,
                    'node_type': node.node_type,
                    'depth_level': node.depth_level,
                    'estimated_hours': float(node.estimated_hours),
                    'difficulty': node.difficulty,
                    'weightage': float(node.weightage),
                    'is_optional': node.is_optional,
                    'tags': node.tags,
                    'progress': {
                        'status': progress.status if progress else 'not_started',
                        'percentage': progress.progress_percentage if progress else 0,
                        'confidence_level': progress.confidence_level if progress else 3,
                        'study_hours': float(progress.study_hours) if progress else 0,
                        'revision_count': progress.revision_count if progress else 0,
                        'test_ready': progress.test_ready if progress else False,
                        'last_updated': progress.updated_at.isoformat() if progress else None
                    },
                    'children': build_node_tree(parent=node)
                }
                node_list.append(node_data)
            
            return node_list
        
        syllabus_tree = build_node_tree()
        
        # Calculate overall statistics
        total_nodes = nodes.count()
        completed_nodes = StudentSyllabusProgress.objects.filter(
            student=request.user,
            node__syllabus=syllabus,
            status='completed'
        ).count()
        
        in_progress_nodes = StudentSyllabusProgress.objects.filter(
            student=request.user,
            node__syllabus=syllabus,
            status='in_progress'
        ).count()
        
        overall_progress = (completed_nodes / total_nodes * 100) if total_nodes > 0 else 0
        
        response_data = {
            'success': True,
            'exam': {
                'id': str(exam.id),
                'name': exam.name,
                'description': exam.description,
            },
            'syllabus': {
                'id': str(syllabus.id),
                'version': syllabus.version,
                'description': syllabus.description,
                'total_topics': total_nodes,
                'estimated_hours': syllabus.estimated_hours,
                'tree': syllabus_tree
            },
            'statistics': {
                'total_topics': total_nodes,
                'completed_topics': completed_nodes,
                'in_progress_topics': in_progress_nodes,
                'not_started_topics': total_nodes - completed_nodes - in_progress_nodes,
                'overall_progress': round(overall_progress, 1)
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def update_topic_progress(request, node_id):
    """Update progress for a specific syllabus node"""
    try:
        data = json.loads(request.body)
        node = get_object_or_404(SyllabusNode, id=node_id)
        
        # Get or create progress record
        progress, created = StudentSyllabusProgress.objects.get_or_create(
            student=request.user,
            node=node
        )
        
        # Update fields based on request data
        if 'status' in data:
            progress.status = data['status']
        
        if 'progress_percentage' in data:
            progress.update_progress(data['progress_percentage'])
        
        if 'confidence_level' in data:
            progress.confidence_level = data['confidence_level']
        
        if 'notes' in data:
            progress.notes = data['notes']
        
        if 'study_hours' in data:
            progress.study_hours = data['study_hours']
        
        # Handle special actions
        if data.get('action') == 'mark_completed':
            progress.mark_completed()
        elif data.get('action') == 'mark_revision':
            progress.mark_revision()
        
        progress.save()
        
        return JsonResponse({
            'success': True,
            'progress': {
                'status': progress.status,
                'percentage': progress.progress_percentage,
                'confidence_level': progress.confidence_level,
                'study_hours': float(progress.study_hours),
                'revision_count': progress.revision_count,
                'test_ready': progress.test_ready,
                'readiness_score': progress.calculate_readiness_score()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============== ENTERPRISE LEARNING SYSTEM VIEWS ==============

@login_required
def learning_page(request, node_id):
    """Enterprise-grade learning page for individual syllabus concepts"""
    try:
        node = get_object_or_404(SyllabusNode, id=node_id)
        
        # Track page view
        current_time = timezone.now()
        
        # Get or create user's syllabus progress
        syllabus_progress, created = StudentSyllabusProgress.objects.get_or_create(
            student=request.user,
            node=node
        )
        
        # Update last accessed time
        syllabus_progress.last_revised_at = current_time
        if syllabus_progress.status == 'not_started':
            syllabus_progress.status = 'in_progress'
            syllabus_progress.started_at = current_time
        syllabus_progress.save()
        
        context = {
            'node': node,
            'breadcrumb': node.get_breadcrumb(),
        }
        
        return render(request, 'exams/learning_page.html', context)
        
    except Exception as e:
        return render(request, 'exams/error.html', {
            'error': f'Failed to load learning page: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def track_learning_progress(request, node_id):
    """Track detailed learning progress and analytics"""
    try:
        data = json.loads(request.body)
        node = get_object_or_404(SyllabusNode, id=node_id)
        
        action = data.get('action')
        progress_data = data.get('data', {})
        current_time = timezone.now()
        
        if action == 'time_update':
            # Update time spent
            time_spent = progress_data.get('timeSpent', 0)
            syllabus_progress = StudentSyllabusProgress.objects.get_or_create(
                student=request.user,
                node=node
            )[0]
            
            syllabus_progress.study_hours = time_spent / 60  # Convert to hours
            syllabus_progress.last_revised_at = current_time
            syllabus_progress.save()
        
        elif action == 'mark_completed':
            syllabus_progress = StudentSyllabusProgress.objects.get_or_create(
                student=request.user,
                node=node
            )[0]
            
            syllabus_progress.status = 'completed'
            syllabus_progress.progress_percentage = 100
            syllabus_progress.completed_at = current_time
            syllabus_progress.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Progress tracked successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============== TEACHER CONTENT MANAGEMENT VIEWS ==============

@login_required
@require_role(['teacher', 'admin'])
def teacher_content_management(request):
    """Main teacher content management dashboard"""
    # Get syllabus nodes that need content
    available_nodes = SyllabusNode.objects.filter(
        is_active=True,
        node_type='concept'  # Only leaf nodes need content
    ).select_related('syllabus__exam').prefetch_related('learning_content')
    
    # Filter by exam if specified
    exam_id = request.GET.get('exam_id')
    if exam_id:
        available_nodes = available_nodes.filter(syllabus__exam_id=exam_id)
    
    # Get content statistics
    total_nodes = available_nodes.count()
    nodes_with_content = available_nodes.filter(learning_content__isnull=False).distinct().count()
    teacher_created = LearningContent.objects.filter(
        created_by=request.user,
        is_ai_generated=False
    ).count()
    
    # Get recent teacher content
    recent_content = LearningContent.objects.filter(
        created_by=request.user,
        is_ai_generated=False
    ).select_related('node').order_by('-created_at')[:10]
    
    # Get available exams for filtering
    exams_with_syllabus = Exam.objects.filter(
        syllabus__isnull=False,
        is_active=True
    ).distinct()
    
    context = {
        'available_nodes': available_nodes.order_by('syllabus__exam__name', 'title'),
        'total_nodes': total_nodes,
        'nodes_with_content': nodes_with_content,
        'teacher_created': teacher_created,
        'recent_content': recent_content,
        'exams_with_syllabus': exams_with_syllabus,
        'selected_exam_id': exam_id,
    }
    
    return render(request, 'exams/teacher_content_management.html', context)


@login_required
@require_role(['teacher', 'admin'])
def create_learning_content(request, node_id):
    """Create new learning content for a syllabus node"""
    node = get_object_or_404(SyllabusNode, id=node_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create learning content
            content = LearningContent.objects.create(
                node=node,
                level=data.get('level', 'basic'),
                content_type=data.get('content_type', 'theory'),
                title=data.get('title', ''),
                content=data.get('content', ''),
                interactive_data=data.get('interactive_data', {}),
                estimated_read_time=int(data.get('estimated_read_time', 5)),
                order=int(data.get('order', 0)),
                is_ai_generated=False,
                is_approved=True,  # Teacher content is auto-approved
                created_by=request.user,
                difficulty_rating=float(data.get('difficulty_rating', 3.0))
            )
            
            # Create interactive elements if provided
            interactive_elements = data.get('interactive_elements', [])
            for element_data in interactive_elements:
                InteractiveElement.objects.create(
                    content=content,
                    element_type=element_data.get('element_type', 'graph'),
                    title=element_data.get('title', ''),
                    description=element_data.get('description', ''),
                    config_data=element_data.get('config_data', {}),
                    javascript_code=element_data.get('javascript_code', ''),
                    python_code=element_data.get('python_code', ''),
                    is_active=True
                )
            
            # Create assessments if provided
            assessments = data.get('assessments', [])
            for assessment_data in assessments:
                Assessment.objects.create(
                    content=content,
                    question_type=assessment_data.get('question_type', 'mcq'),
                    schedule_type=assessment_data.get('schedule_type', 'immediate'),
                    question_text=assessment_data.get('question_text', ''),
                    question_data=assessment_data.get('question_data', {}),
                    max_points=int(assessment_data.get('max_points', 1)),
                    difficulty_weight=float(assessment_data.get('difficulty_weight', 1.0)),
                    is_active=True
                )
            
            return JsonResponse({
                'success': True,
                'content_id': str(content.id),
                'message': 'Learning content created successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # GET request - return form data
    existing_content = LearningContent.objects.filter(node=node).order_by('level', 'order')
    
    context = {
        'node': node,
        'existing_content': existing_content,
        'breadcrumb': node.get_breadcrumb(),
        'level_choices': LearningContent.LEVEL_CHOICES,
        'content_type_choices': LearningContent.CONTENT_TYPE_CHOICES,
        'element_type_choices': InteractiveElement.ELEMENT_TYPE_CHOICES,
        'question_type_choices': Assessment.QUESTION_TYPE_CHOICES,
        'schedule_type_choices': Assessment.SCHEDULE_TYPE_CHOICES,
    }
    
    return render(request, 'exams/create_learning_content.html', context)


@login_required
@require_role(['teacher', 'admin'])
def edit_learning_content(request, content_id):
    """Edit existing learning content"""
    content = get_object_or_404(LearningContent, id=content_id)
    
    # Check permissions
    if request.user.role != 'admin' and content.created_by != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update content fields
            content.level = data.get('level', content.level)
            content.content_type = data.get('content_type', content.content_type)
            content.title = data.get('title', content.title)
            content.content = data.get('content', content.content)
            content.interactive_data = data.get('interactive_data', content.interactive_data)
            content.estimated_read_time = int(data.get('estimated_read_time', content.estimated_read_time))
            content.order = int(data.get('order', content.order))
            content.difficulty_rating = float(data.get('difficulty_rating', content.difficulty_rating))
            content.updated_at = timezone.now()
            content.save()
            
            # Update interactive elements
            if 'interactive_elements' in data:
                content.interactive_elements.all().delete()  # Remove existing
                for element_data in data['interactive_elements']:
                    InteractiveElement.objects.create(
                        content=content,
                        element_type=element_data.get('element_type', 'graph'),
                        title=element_data.get('title', ''),
                        description=element_data.get('description', ''),
                        config_data=element_data.get('config_data', {}),
                        javascript_code=element_data.get('javascript_code', ''),
                        python_code=element_data.get('python_code', ''),
                        is_active=True
                    )
            
            # Update assessments
            if 'assessments' in data:
                content.assessments.all().delete()  # Remove existing
                for assessment_data in data['assessments']:
                    Assessment.objects.create(
                        content=content,
                        question_type=assessment_data.get('question_type', 'mcq'),
                        schedule_type=assessment_data.get('schedule_type', 'immediate'),
                        question_text=assessment_data.get('question_text', ''),
                        question_data=assessment_data.get('question_data', {}),
                        max_points=int(assessment_data.get('max_points', 1)),
                        difficulty_weight=float(assessment_data.get('difficulty_weight', 1.0)),
                        is_active=True
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'Learning content updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # GET request - return existing data
    interactive_elements = list(content.interactive_elements.values())
    assessments = list(content.assessments.values())
    
    context = {
        'content': content,
        'interactive_elements': interactive_elements,
        'assessments': assessments,
        'node': content.node,
        'breadcrumb': content.node.get_breadcrumb(),
        'level_choices': LearningContent.LEVEL_CHOICES,
        'content_type_choices': LearningContent.CONTENT_TYPE_CHOICES,
        'element_type_choices': InteractiveElement.ELEMENT_TYPE_CHOICES,
        'question_type_choices': Assessment.QUESTION_TYPE_CHOICES,
        'schedule_type_choices': Assessment.SCHEDULE_TYPE_CHOICES,
    }
    
    return render(request, 'exams/edit_learning_content.html', context)


@login_required
@require_role(['teacher', 'admin'])
@require_http_methods(["DELETE"])
def delete_learning_content(request, content_id):
    """Delete learning content"""
    content = get_object_or_404(LearningContent, id=content_id)
    
    # Check permissions
    if request.user.role != 'admin' and content.created_by != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        content_title = content.title
        node_title = content.node.title
        content.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Content "{content_title}" deleted from "{node_title}"'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_role(['teacher', 'admin'])
def content_analytics(request, content_id):
    """View analytics for learning content"""
    content = get_object_or_404(LearningContent, id=content_id)
    
    # Check permissions
    if request.user.role != 'admin' and content.created_by != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get or create analytics
    analytics, created = LearningAnalytics.objects.get_or_create(content=content)
    
    # Get student progress data
    student_progress = StudentLearningProgress.objects.filter(content=content)
    
    # Calculate real-time statistics
    total_students = student_progress.count()
    completed_students = student_progress.filter(status='completed').count()
    completion_rate = (completed_students / total_students * 100) if total_students > 0 else 0
    
    avg_time_spent = student_progress.aggregate(
        avg_time=Avg('time_spent')
    )['avg_time'] or 0
    
    avg_understanding = student_progress.aggregate(
        avg_score=Avg('understanding_score')
    )['avg_score'] or 0
    
    # Status distribution
    status_distribution = dict(
        student_progress.values('status').annotate(count=Count('id'))
        .values_list('status', 'count')
    )
    
    # Difficulty ratings from students
    difficulty_ratings = student_progress.exclude(
        difficulty_rating__isnull=True
    ).values_list('difficulty_rating', flat=True)
    
    avg_difficulty = sum(difficulty_ratings) / len(difficulty_ratings) if difficulty_ratings else 0
    
    context = {
        'content': content,
        'analytics': analytics,
        'stats': {
            'total_students': total_students,
            'completed_students': completed_students,
            'completion_rate': round(completion_rate, 1),
            'avg_time_spent': round(avg_time_spent, 1),
            'avg_understanding': round(avg_understanding, 1),
            'avg_difficulty': round(avg_difficulty, 1),
            'status_distribution': status_distribution,
        },
        'recent_progress': student_progress.order_by('-last_accessed_at')[:10]
    }
    
    return render(request, 'exams/content_analytics.html', context)


@login_required
@require_role(['teacher', 'admin'])
def lms_dashboard(request):
    """Main LMS Dashboard - Central hub for all learning management features"""
    
    # Get comprehensive statistics
    total_nodes = SyllabusNode.objects.filter(
        is_active=True,
        node_type='concept'
    ).count()
    
    nodes_with_content = SyllabusNode.objects.filter(
        is_active=True,
        node_type='concept',
        learning_content__isnull=False
    ).distinct().count()
    
    # Teacher's content statistics
    teacher_content = LearningContent.objects.filter(
        created_by=request.user,
        is_ai_generated=False
    )
    
    teacher_content_count = teacher_content.count()
    
    # Recent teacher content
    recent_teacher_content = teacher_content.select_related('node').order_by('-created_at')[:5]
    
    # Content by level breakdown
    content_by_level = {
        'basic': teacher_content.filter(level='basic').count(),
        'intermediate': teacher_content.filter(level='intermediate').count(),
        'advanced': teacher_content.filter(level='advanced').count(),
        'expert': teacher_content.filter(level='expert').count(),
    }
    
    # Available exams with syllabus
    exams_with_syllabus = Exam.objects.filter(
        syllabus__isnull=False,
        is_active=True
    ).distinct().count()
    
    # Analytics overview - top performing content
    top_performing_content = []
    if teacher_content_count > 0:
        # Get content with analytics data
        for content in teacher_content.select_related('node')[:3]:
            analytics, created = LearningAnalytics.objects.get_or_create(content=content)
            
            # Calculate engagement score
            student_progress = StudentLearningProgress.objects.filter(content=content)
            total_students = student_progress.count()
            completed_students = student_progress.filter(status='completed').count()
            completion_rate = (completed_students / total_students * 100) if total_students > 0 else 0
            
            top_performing_content.append({
                'content': content,
                'total_students': total_students,
                'completion_rate': completion_rate,
                'avg_time_spent': analytics.avg_time_spent,
                'engagement_score': analytics.engagement_score
            })
    
    # Concepts needing content
    concepts_needing_content = SyllabusNode.objects.filter(
        is_active=True,
        node_type='concept',
        learning_content__isnull=True
    ).select_related('syllabus__exam').order_by('syllabus__exam__name', 'title')[:10]
    
    # System-wide statistics
    total_learning_content = LearningContent.objects.count()
    ai_generated_content = LearningContent.objects.filter(is_ai_generated=True).count()
    teacher_generated_content = LearningContent.objects.filter(is_ai_generated=False).count()
    
    total_interactive_elements = InteractiveElement.objects.count()
    total_assessments = Assessment.objects.count()
    
    context = {
        # Main statistics
        'total_nodes': total_nodes,
        'nodes_with_content': nodes_with_content,
        'coverage_percentage': round((nodes_with_content / total_nodes * 100) if total_nodes > 0 else 0, 1),
        'teacher_content_count': teacher_content_count,
        'exams_with_syllabus': exams_with_syllabus,
        
        # Teacher's content data
        'recent_teacher_content': recent_teacher_content,
        'content_by_level': content_by_level,
        'top_performing_content': top_performing_content,
        
        # Content opportunities
        'concepts_needing_content': concepts_needing_content,
        
        # System statistics
        'total_learning_content': total_learning_content,
        'ai_generated_content': ai_generated_content,
        'teacher_generated_content': teacher_generated_content,
        'total_interactive_elements': total_interactive_elements,
        'total_assessments': total_assessments,
        
        # Quick access data
        'has_recent_content': recent_teacher_content.exists(),
        'needs_content_attention': concepts_needing_content.exists(),
    }
    
    return render(request, 'exams/lms_dashboard.html', context)
