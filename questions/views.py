from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
import pandas as pd
import csv
import json

from rest_framework import generics, status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import QuestionBank, Question, QuestionOption, TestQuestion, UserAnswer
from exams.models import TestAttempt
from .serializers import (
    QuestionBankSerializer, QuestionSerializer, 
    TestQuestionSerializer, UserAnswerSerializer,
    QuestionImportSerializer
)
from core.decorators import (
    api_rate_limit, require_role, security_check, 
    log_user_action, cache_control
)
from core.security import (
    sanitize_user_input, validate_question_content,
    validate_file_upload, log_security_event
)


# Template Views
@login_required
@require_role(['admin', 'teacher'])
@cache_control(max_age=300, private=True)
@log_user_action('view_question_banks')
def question_bank_list(request):
    """List question banks"""
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    # Get all question banks and filter based on permissions
    all_question_banks = QuestionBank.objects.all().annotate(
        questions_count=Count('questions')
    )
    
    # Filter based on new permission system
    if request.user.role == 'admin':
        question_banks = all_question_banks
    else:
        # For teachers, show banks they own, public banks, or banks they have permission to access
        accessible_bank_ids = []
        for bank in all_question_banks:
            if bank.user_can_access(request.user, 'view'):
                accessible_bank_ids.append(bank.id)
        
        question_banks = all_question_banks.filter(id__in=accessible_bank_ids)
    
    # Search with input sanitization
    search = sanitize_user_input(request.GET.get('search', ''))
    if search:
        question_banks = question_banks.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    # Add ordering to prevent pagination warnings
    question_banks = question_banks.order_by('-created_at')
    
    # Calculate statistics before pagination
    all_banks = question_banks  # Keep reference to queryset before pagination
    total_questions = sum(bank.questions_count for bank in all_banks)
    private_banks_count = all_banks.filter(is_public=False).count()
    public_banks_count = all_banks.filter(is_public=True).count()
    
    paginator = Paginator(question_banks, 12)
    page = request.GET.get('page')
    question_banks = paginator.get_page(page)
    
    context = {
        'question_banks': question_banks,
        'search': search,
        'total_questions': total_questions,
        'private_banks_count': private_banks_count,
        'public_banks_count': public_banks_count,
    }
    return render(request, 'questions/question_bank_list.html', context)


@login_required
@require_role(['admin', 'teacher'])
@security_check
@log_user_action('create_question_bank')
def create_question_bank(request):
    """Create new question bank"""
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
        organization = sanitize_user_input(request.POST.get('organization', ''))
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
        
        # Question Types
        question_types_str = request.POST.get('question_types_included', '')
        question_types = [qt.strip() for qt in question_types_str.split(',') if qt.strip()] if question_types_str else []
        
        # Settings
        is_public = request.POST.get('is_public') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        
        # Default Question Settings
        default_difficulty = request.POST.get('default_difficulty', 'intermediate')
        default_marks = float(request.POST.get('default_marks', 1.0))
        default_time_per_question = request.POST.get('default_time_per_question', '')
        
        # Custom fields
        custom_fields = {}
        for key, value in request.POST.items():
            if key.startswith('custom_'):
                field_name = key.replace('custom_', '')
                if value.strip():
                    custom_fields[field_name] = sanitize_user_input(value)
        
        if not name:
            messages.error(request, "Question bank name is required.")
        else:
            # Parse year
            year_int = None
            if year and year.isdigit():
                year_int = int(year)
            
            # Parse default time
            default_time_int = None
            if default_time_per_question and default_time_per_question.isdigit():
                default_time_int = int(default_time_per_question)
            
            question_bank = QuestionBank.objects.create(
                name=name,
                description=description,
                category=category,
                exam_type=exam_type,
                organization=organization,
                year=year_int,
                subject=subject,
                topic=topic,
                subtopic=subtopic,
                difficulty_level=difficulty_level,
                target_audience=target_audience,
                language=language,
                state_specific=state_specific,
                tags=tags,
                question_types_included=question_types,
                custom_fields=custom_fields,
                is_public=is_public,
                is_featured=is_featured,
                default_difficulty=default_difficulty,
                default_marks=default_marks,
                default_time_per_question=default_time_int,
                created_by=request.user
            )
            messages.success(request, f"Question bank '{name}' created successfully.")
            return redirect('question-bank-detail', bank_id=question_bank.id)
    
    return render(request, 'questions/create_question_bank.html')


@login_required
def edit_question_bank(request, bank_id):
    """Edit existing question bank"""
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    # Check permissions
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    if not question_bank.user_can_access(request.user, 'edit'):
        messages.error(request, "You don't have permission to edit this question bank.")
        return redirect('question-bank-detail', bank_id=bank_id)
    
    if request.method == 'POST':
        # Basic Information
        name = sanitize_user_input(request.POST.get('name', ''))
        description = sanitize_user_input(request.POST.get('description', ''))
        category = sanitize_user_input(request.POST.get('category', ''))
        
        # Exam Specific
        exam_type = sanitize_user_input(request.POST.get('exam_type', ''))
        organization = sanitize_user_input(request.POST.get('organization', ''))
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
        
        # Question Types
        question_types_str = request.POST.get('question_types_included', '')
        question_types = [qt.strip() for qt in question_types_str.split(',') if qt.strip()] if question_types_str else []
        
        # Settings
        is_public = request.POST.get('is_public') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        
        # Default Question Settings
        default_difficulty = request.POST.get('default_difficulty', 'intermediate')
        default_marks = float(request.POST.get('default_marks', 1.0))
        default_time_per_question = request.POST.get('default_time_per_question', '')
        
        # Custom fields
        custom_fields = {}
        for key, value in request.POST.items():
            if key.startswith('custom_'):
                field_name = key.replace('custom_', '')
                if value.strip():
                    custom_fields[field_name] = sanitize_user_input(value)
        
        if not name:
            messages.error(request, "Question bank name is required.")
        else:
            # Parse year
            year_int = None
            if year and year.isdigit():
                year_int = int(year)
            
            # Parse default time
            default_time_int = None
            if default_time_per_question and default_time_per_question.isdigit():
                default_time_int = int(default_time_per_question)
            
            # Update question bank
            question_bank.name = name
            question_bank.description = description
            question_bank.category = category
            question_bank.exam_type = exam_type
            question_bank.organization = organization
            question_bank.year = year_int
            question_bank.subject = subject
            question_bank.topic = topic
            question_bank.subtopic = subtopic
            question_bank.difficulty_level = difficulty_level
            question_bank.target_audience = target_audience
            question_bank.language = language
            question_bank.state_specific = state_specific
            question_bank.tags = tags
            question_bank.question_types_included = question_types
            question_bank.custom_fields = custom_fields
            question_bank.is_public = is_public
            question_bank.is_featured = is_featured
            question_bank.default_difficulty = default_difficulty
            question_bank.default_marks = default_marks
            question_bank.default_time_per_question = default_time_int
            question_bank.save()
            
            messages.success(request, f"Question bank '{name}' updated successfully.")
            return redirect('question-bank-detail', bank_id=question_bank.id)
    
    context = {
        'question_bank': question_bank,
        'edit_mode': True
    }
    return render(request, 'questions/edit_question_bank.html', context)


@login_required
def question_bank_detail(request, bank_id):
    """Question bank detail with questions"""
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    # Check permissions using new permission system
    if not question_bank.user_can_access(request.user, 'view'):
        messages.error(request, "Access denied. You don't have permission to view this question bank.")
        return redirect('question-bank-list')
    
    questions = question_bank.questions.all().prefetch_related('options')
    
    # Filters
    question_type = request.GET.get('type', '')
    difficulty = request.GET.get('difficulty', '')
    topic = request.GET.get('topic', '')
    search = request.GET.get('search', '')
    
    if question_type:
        questions = questions.filter(question_type=question_type)
    if difficulty:
        questions = questions.filter(difficulty=difficulty)
    if topic:
        questions = questions.filter(topic__icontains=topic)
    if search:
        questions = questions.filter(question_text__icontains=search)
    
    # Get unique topics for filter
    topics = question_bank.questions.exclude(topic='').values_list('topic', flat=True).distinct()
    
    paginator = Paginator(questions, 20)
    page = request.GET.get('page')
    questions = paginator.get_page(page)
    
    context = {
        'question_bank': question_bank,
        'questions': questions,
        'topics': topics,
        'filters': {
            'type': question_type,
            'difficulty': difficulty,
            'topic': topic,
            'search': search,
        },
        'question_types': Question.QUESTION_TYPES,
        'difficulty_levels': Question.DIFFICULTY_LEVELS,
    }
    return render(request, 'questions/question_bank_detail.html', context)


@login_required
def create_question(request, bank_id=None):
    """Create new question"""
    if request.user.role == 'student':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    question_bank = None
    if bank_id:
        question_bank = get_object_or_404(QuestionBank, id=bank_id)
        # Check permissions
        if request.user.role == 'teacher' and question_bank.created_by != request.user:
            messages.error(request, "Access denied.")
            return redirect('question-bank-list')
    
    if request.method == 'POST':
        return handle_create_question(request, question_bank)
    
    # Get user's question banks for selection
    user_banks = QuestionBank.objects.filter(created_by=request.user)
    
    context = {
        'question_bank': question_bank,
        'user_banks': user_banks,
        'question_types': Question.QUESTION_TYPES,
        'difficulty_levels': Question.DIFFICULTY_LEVELS,
    }
    return render(request, 'questions/create_question.html', context)


def handle_create_question(request, question_bank):
    """Handle question creation POST request"""
    try:
        # Get basic form data
        question_text = sanitize_user_input(request.POST.get('question_text', ''))
        question_type = request.POST.get('question_type', 'mcq')
        difficulty = request.POST.get('difficulty', 'medium')
        marks = float(request.POST.get('marks', 1))
        negative_marks = float(request.POST.get('negative_marks', 0))
        topic = sanitize_user_input(request.POST.get('topic', ''))
        subtopic = sanitize_user_input(request.POST.get('subtopic', ''))
        explanation = sanitize_user_input(request.POST.get('explanation', ''))
        time_limit = request.POST.get('time_limit') or None
        
        if not question_bank:
            bank_id = request.POST.get('question_bank')
            if bank_id:
                question_bank = get_object_or_404(QuestionBank, id=bank_id, created_by=request.user)
        
        if not question_text:
            messages.error(request, "Question text is required.")
            return redirect(request.path)
        
        # Create base question
        question_data = {
            'question_bank': question_bank,
            'question_text': question_text,
            'question_type': question_type,
            'difficulty': difficulty,
            'marks': marks,
            'negative_marks': negative_marks,
            'topic': topic,
            'subtopic': subtopic,
            'explanation': explanation,
            'created_by': request.user
        }
        
        if time_limit:
            question_data['time_limit'] = int(time_limit)
        
        # Handle question type specific fields
        if question_type == 'fill_blank':
            correct_answers_str = request.POST.get('correct_answers', '').strip()
            if correct_answers_str:
                correct_answers = [answer.strip() for answer in correct_answers_str.split('\n') if answer.strip()]
                question_data['correct_answers'] = correct_answers
            question_data['case_sensitive'] = request.POST.get('case_sensitive') == 'on'
            
        elif question_type == 'essay':
            min_words = request.POST.get('min_words')
            max_words = request.POST.get('max_words')
            if min_words:
                question_data['min_words'] = int(min_words)
            if max_words:
                question_data['max_words'] = int(max_words)
        
        # Create question
        question = Question.objects.create(**question_data)
        
        # Handle image upload
        if request.FILES.get('image'):
            question.image = request.FILES['image']
            question.save()
        
        # Create options for MCQ/Multi-select/True-False
        if question_type in ['mcq', 'multi_select', 'true_false']:
            options_data = []
            
            if question_type == 'true_false':
                # Auto-create True/False options
                correct_answer = request.POST.get('correct_answer', 'true')
                options_data = [
                    {'text': 'True', 'is_correct': correct_answer == 'true'},
                    {'text': 'False', 'is_correct': correct_answer == 'false'},
                ]
            else:
                # Get options from form
                option_texts = request.POST.getlist('option_text')
                correct_options = request.POST.getlist('correct_options')
                
                for i, option_text in enumerate(option_texts):
                    if option_text.strip():
                        options_data.append({
                            'text': sanitize_user_input(option_text.strip()),
                            'is_correct': str(i) in correct_options
                        })
            
            # Validate at least one correct answer for MCQ
            if question_type == 'mcq':
                if not any(option['is_correct'] for option in options_data):
                    messages.error(request, "Please select the correct answer for the MCQ question.")
                    question.delete()
                    return redirect(request.path)
            
            # Create option objects
            for i, option_data in enumerate(options_data):
                QuestionOption.objects.create(
                    question=question,
                    option_text=option_data['text'],
                    is_correct=option_data['is_correct'],
                    order=i + 1
                )
        
        messages.success(request, "Question created successfully.")
        
        if question_bank:
            return redirect('question-bank-detail', bank_id=question_bank.id)
        else:
            return redirect('question-bank-list')
            
    except Exception as e:
        messages.error(request, f"Error creating question: {str(e)}")
        return redirect(request.path)


@login_required
def edit_question(request, question_id):
    """Edit existing question"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check permissions
    if request.user != question.created_by and request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('question-bank-list')
    
    if request.method == 'POST':
        return handle_edit_question(request, question)
    
    context = {
        'question': question,
        'question_types': Question.QUESTION_TYPES,
        'difficulty_levels': Question.DIFFICULTY_LEVELS,
    }
    return render(request, 'questions/edit_question.html', context)


def handle_edit_question(request, question):
    """Handle question edit POST request"""
    try:
        # Update basic fields
        question.question_text = request.POST.get('question_text', '').strip()
        question.question_type = request.POST.get('question_type', 'mcq')
        question.difficulty = request.POST.get('difficulty', 'medium')
        question.marks = int(request.POST.get('marks', 1))
        question.negative_marks = float(request.POST.get('negative_marks', 0))
        question.topic = request.POST.get('topic', '').strip()
        question.subtopic = request.POST.get('subtopic', '').strip()
        question.explanation = request.POST.get('explanation', '').strip()
        
        # Handle image upload
        if request.FILES.get('image'):
            question.image = request.FILES['image']
        
        question.save()
        
        # Update options if it's an option-based question
        if question.question_type in ['mcq', 'multi_select', 'true_false']:
            # Delete existing options
            question.options.all().delete()
            
            if question.question_type == 'true_false':
                correct_answer = request.POST.get('correct_answer', 'true')
                QuestionOption.objects.create(
                    question=question,
                    option_text='True',
                    is_correct=correct_answer == 'true',
                    order=1
                )
                QuestionOption.objects.create(
                    question=question,
                    option_text='False',
                    is_correct=correct_answer == 'false',
                    order=2
                )
            else:
                option_texts = request.POST.getlist('option_text')
                correct_options = request.POST.getlist('correct_options')
                
                for i, option_text in enumerate(option_texts):
                    if option_text.strip():
                        QuestionOption.objects.create(
                            question=question,
                            option_text=option_text.strip(),
                            is_correct=str(i) in correct_options,
                            order=i + 1
                        )
        
        # Update expected answer for text-based questions
        elif question.question_type in ['fill_blank', 'essay']:
            question.expected_answer = request.POST.get('expected_answer', '').strip()
            question.save()
        
        messages.success(request, "Question updated successfully.")
        
        if question.question_bank:
            return redirect('question-bank-detail', bank_id=question.question_bank.id)
        else:
            return redirect('question-bank-list')
            
    except Exception as e:
        messages.error(request, f"Error updating question: {str(e)}")
        return redirect('edit-question', question_id=question.id)


@login_required
@require_http_methods(["POST"])
def delete_question(request, question_id):
    """Delete question"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check permissions
    if request.user != question.created_by and request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    bank_id = question.question_bank.id if question.question_bank else None
    question.delete()
    
    messages.success(request, "Question deleted successfully.")
    
    if request.headers.get('HX-Request'):
        return JsonResponse({'success': True})
    
    if bank_id:
        return redirect('question-bank-detail', bank_id=bank_id)
    else:
        return redirect('question-bank-list')


@login_required
@require_role(['admin', 'teacher'])
@security_check
@log_user_action('import_questions')
def import_questions(request, bank_id):
    """Import questions from CSV/Excel"""
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    # Check permissions
    if request.user != question_bank.created_by and request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('question-bank-list')
    
    if request.method == 'POST':
        return handle_import_questions(request, question_bank)
    
    context = {'question_bank': question_bank}
    return render(request, 'questions/import_questions.html', context)


def handle_import_questions(request, question_bank):
    """Handle question import POST request"""
    try:
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, "Please select a file to import.")
            return redirect('import-questions', bank_id=question_bank.id)
        
        # Validate file upload for security
        try:
            validate_file_upload(uploaded_file)
        except ValidationError as e:
            messages.error(request, str(e))
            log_security_event(request, 'INVALID_FILE_UPLOAD', f'File: {uploaded_file.name}')
            return redirect('import-questions', bank_id=question_bank.id)
        
        # Save uploaded file temporarily
        file_path = default_storage.save(f'temp/{uploaded_file.name}', uploaded_file)
        full_path = default_storage.path(file_path)
        
        questions_created = 0
        errors = []
        
        try:
            # Read file based on extension
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(full_path)
            else:
                df = pd.read_excel(full_path)
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Validate and sanitize question data
                    raw_question_data = {
                        'question_text': row.get('question_text', ''),
                        'question_type': row.get('question_type', 'mcq'),
                        'difficulty': row.get('difficulty', 'medium'),
                        'marks': row.get('marks', 1),
                        'negative_marks': row.get('negative_marks', 0),
                        'topic': row.get('topic', ''),
                        'subtopic': row.get('subtopic', ''),
                        'explanation': row.get('explanation', ''),
                    }
                    
                    sanitized_data = validate_question_content(raw_question_data)
                    
                    # Create question
                    question = Question.objects.create(
                        question_bank=question_bank,
                        created_by=request.user,
                        **sanitized_data
                    )
                    
                    # Create options for MCQ questions
                    if question.question_type in ['mcq', 'multi_select']:
                        for i in range(1, 5):  # Up to 4 options
                            option_text = row.get(f'option_{i}')
                            if pd.notna(option_text) and option_text.strip():
                                QuestionOption.objects.create(
                                    question=question,
                                    option_text=option_text.strip(),
                                    is_correct=bool(row.get(f'is_correct_{i}', False)),
                                    order=i
                                )
                    
                    questions_created += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    continue
            
            # Clean up temporary file
            default_storage.delete(file_path)
            
            if questions_created > 0:
                messages.success(request, f"Successfully imported {questions_created} questions.")
            
            if errors:
                error_msg = f"Encountered {len(errors)} errors:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n... and {len(errors) - 5} more errors."
                messages.warning(request, error_msg)
            
        except Exception as e:
            default_storage.delete(file_path)
            messages.error(request, f"Error processing file: {str(e)}")
        
        return redirect('question-bank-detail', bank_id=question_bank.id)
        
    except Exception as e:
        messages.error(request, f"Error importing questions: {str(e)}")
        return redirect('import-questions', bank_id=question_bank.id)


@login_required
def export_questions(request, bank_id):
    """Export questions to CSV"""
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    # Check permissions
    if request.user.role == 'teacher' and not question_bank.is_public and question_bank.created_by != request.user:
        messages.error(request, "Access denied.")
        return redirect('question-bank-list')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{question_bank.name}_questions.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'question_text', 'question_type', 'difficulty', 'marks', 'negative_marks',
        'topic', 'subtopic', 'explanation',
        'option_1', 'is_correct_1', 'option_2', 'is_correct_2',
        'option_3', 'is_correct_3', 'option_4', 'is_correct_4'
    ])
    
    # Write questions
    for question in question_bank.questions.all().prefetch_related('options'):
        row = [
            question.question_text,
            question.question_type,
            question.difficulty,
            question.marks,
            question.negative_marks,
            question.topic,
            question.subtopic,
            question.explanation,
        ]
        
        # Add options (up to 4)
        options = list(question.options.all().order_by('order'))
        for i in range(4):
            if i < len(options):
                row.extend([options[i].option_text, options[i].is_correct])
            else:
                row.extend(['', False])
        
        writer.writerow(row)
    
    return response


@login_required
@require_http_methods(["GET"])
def question_preview_api(request, question_id):
    """Simple question preview API using session authentication"""
    try:
        question = get_object_or_404(Question, id=question_id)
        
        # Check permissions
        if request.user.role == 'student':
            # Students can only view questions from public banks
            if not question.question_bank.is_public:
                return JsonResponse({'error': 'Access denied'}, status=403)
        elif request.user.role == 'teacher':
            # Teachers can view questions from their own banks or public banks
            if (question.question_bank.created_by != request.user and 
                not question.question_bank.is_public):
                return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Serialize question data
        question_data = {
            'id': str(question.id),
            'question_text': question.question_text,
            'question_type': question.question_type,
            'difficulty': question.difficulty,
            'marks': question.marks,
            'negative_marks': question.negative_marks,
            'topic': question.topic,
            'subtopic': question.subtopic,
            'explanation': question.explanation,
            'expected_answer': question.expected_answer,
            'time_limit': question.time_limit,
            'image': question.image.url if question.image else None,
            'topics': [question.topic] if question.topic else [],
            'options': []
        }
        
        # Add options for MCQ/multi-select/true-false questions
        for option in question.options.all().order_by('order'):
            question_data['options'].append({
                'id': str(option.id),
                'option_text': option.option_text,
                'is_correct': option.is_correct,
                'order': option.order
            })
        
        return JsonResponse(question_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class QuestionBankViewSet(viewsets.ModelViewSet):
    queryset = QuestionBank.objects.all()
    serializer_class = QuestionBankSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 'student':
            queryset = queryset.filter(is_public=True)
        elif self.request.user.role == 'teacher':
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(is_public=True)
            )
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by question bank
        bank_id = self.request.query_params.get('question_bank')
        if bank_id:
            queryset = queryset.filter(question_bank_id=bank_id)
        
        # Filter by question type
        q_type = self.request.query_params.get('type')
        if q_type:
            queryset = queryset.filter(question_type=q_type)
        
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Filter by topic
        topic = self.request.query_params.get('topic')
        if topic:
            queryset = queryset.filter(topic__icontains=topic)
        
        # Search in question text
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(question_text__icontains=search)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'], serializer_class=QuestionImportSerializer)
    def import_questions(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file = serializer.validated_data['file']
        question_bank_id = serializer.validated_data.get('question_bank')
        
        try:
            # Read Excel file
            df = pd.read_excel(file)
            questions_created = 0
            
            for _, row in df.iterrows():
                # Create question
                question_data = {
                    'question_text': row['question_text'],
                    'question_type': row.get('question_type', 'mcq'),
                    'difficulty': row.get('difficulty', 'medium'),
                    'marks': row.get('marks', 1),
                    'negative_marks': row.get('negative_marks', 0),
                    'topic': row.get('topic', ''),
                    'subtopic': row.get('subtopic', ''),
                    'explanation': row.get('explanation', ''),
                    'created_by': request.user,
                }
                
                if question_bank_id:
                    question_data['question_bank_id'] = question_bank_id
                
                question = Question.objects.create(**question_data)
                
                # Create options for MCQ questions
                if question.question_type in ['mcq', 'multi_select']:
                    for i in range(1, 5):  # Assume 4 options
                        option_text = row.get(f'option_{i}')
                        if option_text:
                            QuestionOption.objects.create(
                                question=question,
                                option_text=option_text,
                                is_correct=row.get(f'is_correct_{i}', False),
                                order=i
                            )
                
                questions_created += 1
            
            return Response({
                'message': f'{questions_created} questions imported successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to import questions: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserAnswerViewSet(viewsets.ModelViewSet):
    queryset = UserAnswer.objects.all()
    serializer_class = UserAnswerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        attempt_id = self.request.query_params.get('test_attempt')
        if attempt_id:
            queryset = queryset.filter(test_attempt_id=attempt_id)
        return queryset.filter(test_attempt__user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        # Validate that the test attempt belongs to the user and is in progress
        attempt_id = request.data.get('test_attempt')
        try:
            attempt = TestAttempt.objects.get(
                id=attempt_id,
                user=request.user,
                status='in_progress'
            )
        except TestAttempt.DoesNotExist:
            return Response(
                {'error': 'Invalid or inactive test attempt'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)
