from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.http import JsonResponse
from django.db.models import Q

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserSerializer, UserProfileSerializer, CustomTokenObtainPairSerializer
from core.decorators import login_rate_limit, security_check
from core.security import sanitize_user_input, log_security_event

User = get_user_model()


# Django Template Views
def login_view(request):
    """Login view for templates"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = sanitize_user_input(request.POST.get('email', ''))
        password = request.POST.get('password', '')  # Don't sanitize password
        
        if email and password:
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'users/login.html')


def register_view(request):
    """Registration view for templates"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Get form data with sanitization
        first_name = sanitize_user_input(request.POST.get('first_name', ''))
        last_name = sanitize_user_input(request.POST.get('last_name', ''))
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role', 'student')
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        
        # Debug logging
        print(f"Registration attempt - Username: {username}, Email: {email}")
        
        # Validation
        errors = []
        
        if not all([first_name, last_name, username, email, password, password2]):
            errors.append('All required fields must be filled.')
        
        if password != password2:
            errors.append('Passwords do not match.')
        
        try:
            validate_password(password)
        except ValidationError as e:
            errors.extend(e.messages)
        
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        if not errors:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role=role
                )
                print(f"User created successfully: {user.username} ({user.email})")
                login(request, user)
                messages.success(request, 'Account created successfully! Welcome to ExamPortal.')
                return redirect('dashboard')
            except Exception as e:
                print(f"Error creating user: {str(e)}")
                errors.append('An error occurred while creating your account.')
        
        for error in errors:
            messages.error(request, error)
    
    return render(request, 'users/register.html')


@login_required
def profile_view(request):
    """User profile view"""
    user = request.user
    
    if request.method == 'POST':
        # Update profile
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.phone = request.POST.get('phone', '').strip()
        
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    
    return render(request, 'users/profile.html', {'user': user})


@login_required
def settings_view(request):
    """User settings view"""
    from users.models import UserPreferences
    
    # Get or create user preferences
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    # Apply theme from preferences
    request.session['theme'] = preferences.theme
    
    context = {
        'preferences': preferences,
        'theme_choices': UserPreferences.THEME_CHOICES,
        'language_choices': UserPreferences.LANGUAGE_CHOICES,
        'timezone_choices': UserPreferences.TIMEZONE_CHOICES,
        'date_format_choices': UserPreferences.DATE_FORMAT_CHOICES,
        'font_size_choices': UserPreferences.FONT_SIZE_CHOICES,
    }
    
    return render(request, 'users/settings.html', context)


@login_required
@require_http_methods(["POST"])
def change_password_api(request):
    """API to change user password"""
    try:
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not all([current_password, new_password, confirm_password]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        if new_password != confirm_password:
            return JsonResponse({'error': 'New passwords do not match'}, status=400)
        
        if not request.user.check_password(current_password):
            return JsonResponse({'error': 'Current password is incorrect'}, status=400)
        
        try:
            validate_password(new_password, user=request.user)
        except ValidationError as e:
            return JsonResponse({'error': e.messages[0]}, status=400)
        
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session to prevent logout
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while changing password'}, status=500)


@login_required
@require_http_methods(["POST"])
def update_privacy_settings_api(request):
    """API to update privacy and notification settings"""
    try:
        from users.models import UserPreferences
        
        # Get or create user preferences
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        
        # Update privacy settings
        preferences.email_notifications = request.POST.get('email_notifications') == 'true'
        preferences.push_notifications = request.POST.get('push_notifications', 'true') == 'true'
        preferences.profile_visibility = request.POST.get('profile_visibility', 'public')
        preferences.show_online_status = request.POST.get('show_online_status', 'true') == 'true'
        preferences.show_activity = request.POST.get('show_activity', 'true') == 'true'
        preferences.allow_messages = request.POST.get('allow_messages', 'everyone')
        
        preferences.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Privacy settings updated successfully',
            'settings': {
                'email_notifications': preferences.email_notifications,
                'push_notifications': preferences.push_notifications,
                'profile_visibility': preferences.profile_visibility,
                'show_online_status': preferences.show_online_status,
                'show_activity': preferences.show_activity,
                'allow_messages': preferences.allow_messages
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred while updating privacy settings: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def update_exam_preferences_api(request):
    """API to update exam preferences"""
    try:
        from users.models import UserPreferences
        
        # Get or create user preferences
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        
        # Update exam preferences
        preferences.auto_save = request.POST.get('auto_save') == 'true'
        preferences.auto_save_interval = int(request.POST.get('auto_save_interval', '30'))
        preferences.show_timer = request.POST.get('timer_display', 'always') == 'always'
        preferences.confirm_navigation = request.POST.get('navigation_enabled') == 'true'
        preferences.keyboard_shortcuts = request.POST.get('keyboard_shortcuts', 'true') == 'true'
        preferences.show_question_palette = request.POST.get('show_question_palette', 'true') == 'true'
        preferences.enable_calculator = request.POST.get('enable_calculator', 'true') == 'true'
        preferences.enable_rough_sheet = request.POST.get('enable_rough_sheet', 'true') == 'true'
        preferences.mark_review_enabled = request.POST.get('mark_review_enabled', 'true') == 'true'
        
        preferences.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Exam preferences updated successfully',
            'preferences': {
                'auto_save': preferences.auto_save,
                'auto_save_interval': preferences.auto_save_interval,
                'show_timer': preferences.show_timer,
                'confirm_navigation': preferences.confirm_navigation,
                'keyboard_shortcuts': preferences.keyboard_shortcuts,
                'show_question_palette': preferences.show_question_palette,
                'enable_calculator': preferences.enable_calculator,
                'enable_rough_sheet': preferences.enable_rough_sheet,
                'mark_review_enabled': preferences.mark_review_enabled
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred while updating exam preferences: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def update_system_settings_api(request):
    """API to update system settings"""
    try:
        from users.models import UserPreferences
        
        # Get or create user preferences
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        
        # Update system settings
        preferences.theme = request.POST.get('theme', 'light')
        preferences.language = request.POST.get('language', 'en')
        preferences.timezone = request.POST.get('timezone', 'Asia/Kolkata')
        preferences.date_format = request.POST.get('date_format', 'DD/MM/YYYY')
        preferences.time_format_24h = request.POST.get('time_format_24h', 'false') == 'true'
        preferences.font_size = request.POST.get('font_size', 'medium')
        preferences.high_contrast = request.POST.get('high_contrast', 'false') == 'true'
        preferences.reduce_animations = request.POST.get('reduce_animations', 'false') == 'true'
        
        preferences.save()
        
        # Set theme in session for immediate effect
        request.session['theme'] = preferences.theme
        
        return JsonResponse({
            'success': True,
            'message': 'System settings updated successfully',
            'settings': {
                'theme': preferences.theme,
                'language': preferences.language,
                'timezone': preferences.timezone,
                'date_format': preferences.date_format,
                'time_format_24h': preferences.time_format_24h,
                'font_size': preferences.font_size,
                'high_contrast': preferences.high_contrast,
                'reduce_animations': preferences.reduce_animations
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred while updating system settings: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_account_api(request):
    """API to delete user account"""
    try:
        password = request.POST.get('password', '')
        confirmation = request.POST.get('confirmation', '')
        
        if not password:
            return JsonResponse({'error': 'Password is required'}, status=400)
        
        if confirmation != 'DELETE':
            return JsonResponse({'error': 'Please type DELETE to confirm'}, status=400)
        
        if not request.user.check_password(password):
            return JsonResponse({'error': 'Password is incorrect'}, status=400)
        
        # Store user info before deletion
        user_email = request.user.email
        
        # Delete the user
        request.user.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Account deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while deleting account'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_user_preferences_api(request):
    """API to get current user preferences"""
    try:
        from users.models import UserPreferences
        
        # Get or create user preferences
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        
        return JsonResponse({
            'success': True,
            'preferences': {
                # Privacy settings
                'email_notifications': preferences.email_notifications,
                'push_notifications': preferences.push_notifications,
                'profile_visibility': preferences.profile_visibility,
                'show_online_status': preferences.show_online_status,
                'show_activity': preferences.show_activity,
                'allow_messages': preferences.allow_messages,
                
                # Exam preferences
                'auto_save': preferences.auto_save,
                'auto_save_interval': preferences.auto_save_interval,
                'show_timer': preferences.show_timer,
                'confirm_navigation': preferences.confirm_navigation,
                'keyboard_shortcuts': preferences.keyboard_shortcuts,
                'show_question_palette': preferences.show_question_palette,
                'enable_calculator': preferences.enable_calculator,
                'enable_rough_sheet': preferences.enable_rough_sheet,
                'mark_review_enabled': preferences.mark_review_enabled,
                
                # System settings
                'theme': preferences.theme,
                'language': preferences.language,
                'timezone': preferences.timezone,
                'date_format': preferences.date_format,
                'time_format_24h': preferences.time_format_24h,
                'font_size': preferences.font_size,
                'high_contrast': preferences.high_contrast,
                'reduce_animations': preferences.reduce_animations,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred while fetching preferences: {str(e)}'}, status=500)


@login_required
def admin_management(request):
    """Admin management dashboard"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    # Get statistics
    from django.db.models import Count, Avg, Sum
    from exams.models import Exam, Test, TestAttempt
    from questions.models import Question, QuestionBank
    from payments.models import SubscriptionPlan, UserSubscription, Payment
    from knowledge.models import GlobalSubject, GlobalTopic, TopicImportTemplate
    
    stats = {
        'total_users': User.objects.count(),
        'students': User.objects.filter(role='student').count(),
        'teachers': User.objects.filter(role='teacher').count(),
        'admins': User.objects.filter(role='admin').count(),
        'total_exams': Exam.objects.count(),
        'total_tests': Test.objects.count(),
        'total_attempts': TestAttempt.objects.count(),
        'total_questions': Question.objects.count(),
        'total_question_banks': QuestionBank.objects.count(),
        # Payment and subscription stats
        'active_subscriptions': UserSubscription.objects.filter(status='active').count(),
        'total_revenue': Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0,
        'pending_payments': Payment.objects.filter(status='pending').count(),
        'subscription_plans': SubscriptionPlan.objects.filter(is_active=True).count(),
    }
    
    # Global Taxonomy Statistics
    taxonomy_stats = {
        'total_subjects': GlobalSubject.objects.filter(is_active=True).count(),
        'total_topics': GlobalTopic.objects.filter(is_active=True).count(),
        'total_templates': TopicImportTemplate.objects.filter(is_active=True).count(),
        'pending_approval': GlobalTopic.objects.filter(is_active=True, is_approved=False).count(),
    }
    
    # Recent activities
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_exams = Exam.objects.order_by('-created_at')[:5]
    recent_attempts = TestAttempt.objects.select_related('user', 'test').order_by('-start_time')[:10]
    
    # Get subscription and payment data
    recent_subscriptions = UserSubscription.objects.select_related('user', 'plan').order_by('-created_at')[:3]
    recent_payments = Payment.objects.select_related('user', 'plan').order_by('-created_at')[:5]
    subscription_plans = SubscriptionPlan.objects.filter(is_active=True)
    
    # Get discount data for the modals
    from payments.models import Discount
    from django.utils import timezone
    
    # Get active discounts
    active_discounts = Discount.objects.filter(
        is_active=True,
        valid_until__gte=timezone.now()
    ).order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'taxonomy_stats': taxonomy_stats,
        'recent_users': recent_users,
        'recent_exams': recent_exams,
        'recent_attempts': recent_attempts,
        'recent_subscriptions': recent_subscriptions,
        'recent_payments': recent_payments,
        'subscription_plans': subscription_plans,
        'active_discounts': active_discounts,
    }
    
    return render(request, 'users/admin_management.html', context)


# API Views (keep existing ones for API access)
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class LoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset


# Custom Admin Views
@login_required
def admin_users_list(request):
    """Custom admin user management list view"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    # Get users with search and filter functionality
    users = User.objects.all().order_by('-date_joined')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Role filter
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(users, 25)
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'search': search,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'user_roles': User._meta.get_field('role').choices,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
    }
    
    return render(request, 'users/admin_users_list.html', context)


@login_required
def admin_user_create(request):
    """Custom admin user creation view"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Get form data with sanitization
        first_name = sanitize_user_input(request.POST.get('first_name', ''))
        last_name = sanitize_user_input(request.POST.get('last_name', ''))
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role', 'student')
        password = request.POST.get('password', '')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        errors = []
        
        if not all([first_name, last_name, username, email, password]):
            errors.append('All required fields must be filled.')
        
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(password)
        except ValidationError as e:
            errors.extend(e.messages)
        
        if not errors:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role=role,
                    is_active=is_active
                )
                messages.success(request, f'User "{user.get_full_name()}" created successfully.')
                return redirect('admin-users-list')
            except Exception as e:
                errors.append('An error occurred while creating the user.')
        
        for error in errors:
            messages.error(request, error)
    
    context = {
        'user_roles': User._meta.get_field('role').choices,
    }
    
    return render(request, 'users/admin_user_create.html', context)


@login_required
def admin_user_edit(request, user_id):
    """Custom admin user edit view"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    edit_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Get form data with sanitization
        edit_user.first_name = sanitize_user_input(request.POST.get('first_name', ''))
        edit_user.last_name = sanitize_user_input(request.POST.get('last_name', ''))
        edit_user.username = request.POST.get('username', '').strip()
        edit_user.email = request.POST.get('email', '').strip()
        edit_user.phone = request.POST.get('phone', '').strip()
        edit_user.role = request.POST.get('role', 'student')
        edit_user.is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        errors = []
        
        if not all([edit_user.first_name, edit_user.last_name, edit_user.username, edit_user.email]):
            errors.append('All required fields must be filled.')
        
        # Check for duplicate username (excluding current user)
        if User.objects.filter(username=edit_user.username).exclude(id=user_id).exists():
            errors.append('Username already exists.')
        
        # Check for duplicate email (excluding current user)
        if User.objects.filter(email=edit_user.email).exclude(id=user_id).exists():
            errors.append('Email already registered.')
        
        # Handle password change if provided
        new_password = request.POST.get('password', '')
        if new_password:
            try:
                from django.contrib.auth.password_validation import validate_password
                validate_password(new_password)
                edit_user.set_password(new_password)
            except ValidationError as e:
                errors.extend(e.messages)
        
        if not errors:
            try:
                edit_user.save()
                messages.success(request, f'User "{edit_user.get_full_name()}" updated successfully.')
                return redirect('admin-users-list')
            except Exception as e:
                errors.append('An error occurred while updating the user.')
        
        for error in errors:
            messages.error(request, error)
    
    context = {
        'edit_user': edit_user,
        'user_roles': User._meta.get_field('role').choices,
    }
    
    return render(request, 'users/admin_user_edit.html', context)


@login_required
@require_http_methods(["POST"])
def admin_user_delete(request, user_id):
    """Custom admin user delete view"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    delete_user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deletion
    if delete_user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('admin-users-list')
    
    try:
        username = delete_user.get_full_name() or delete_user.username
        delete_user.delete()
        messages.success(request, f'User "{username}" deleted successfully.')
    except Exception as e:
        messages.error(request, 'An error occurred while deleting the user.')
    
    return redirect('admin-users-list')


@login_required
@require_http_methods(["POST"])
def admin_user_toggle_status(request, user_id):
    """Toggle user active status"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    toggle_user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deactivation
    if toggle_user == request.user:
        return JsonResponse({'error': 'You cannot deactivate your own account'}, status=400)
    
    try:
        toggle_user.is_active = not toggle_user.is_active
        toggle_user.save()
        
        status = 'activated' if toggle_user.is_active else 'deactivated'
        return JsonResponse({
            'success': True,
            'message': f'User {status} successfully',
            'is_active': toggle_user.is_active
        })
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while updating user status'}, status=500)


@login_required
def admin_exams_list(request):
    """Custom admin exam management list view"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    from exams.models import Exam, Organization
    from django.db.models import Count
    
    # Get exams with related data
    exams = Exam.objects.select_related('organization', 'created_by').annotate(
        tests_count=Count('tests'),
        active_tests_count=Count('tests', filter=Q(tests__is_published=True))
    ).order_by('-created_at')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        exams = exams.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__icontains=search) |
            Q(organization__name__icontains=search)
        )
    
    # Organization filter
    org_filter = request.GET.get('organization', '')
    if org_filter:
        exams = exams.filter(organization_id=org_filter)
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        exams = exams.filter(is_active=True)
    elif status_filter == 'inactive':
        exams = exams.filter(is_active=False)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(exams, 25)
    page = request.GET.get('page')
    exams = paginator.get_page(page)
    
    context = {
        'exams': exams,
        'search': search,
        'org_filter': org_filter,
        'status_filter': status_filter,
        'organizations': Organization.objects.filter(is_active=True).order_by('name'),
        'total_exams': Exam.objects.count(),
        'active_exams': Exam.objects.filter(is_active=True).count(),
        'inactive_exams': Exam.objects.filter(is_active=False).count(),
    }
    
    return render(request, 'users/admin_exams_list.html', context)


@login_required
def admin_exam_edit(request, exam_id):
    """Custom admin exam edit view"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    from exams.models import Exam, Organization
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        # Get form data with sanitization
        exam.name = sanitize_user_input(request.POST.get('name', ''))
        exam.description = sanitize_user_input(request.POST.get('description', ''))
        exam.category = sanitize_user_input(request.POST.get('category', ''))
        exam.year = request.POST.get('year', '') or None
        exam.is_active = request.POST.get('is_active') == 'on'
        
        organization_id = request.POST.get('organization', '')
        if organization_id:
            exam.organization_id = organization_id
        else:
            exam.organization = None
        
        # Validation
        errors = []
        
        if not exam.name:
            errors.append('Exam name is required.')
        
        if not errors:
            try:
                exam.save()
                messages.success(request, f'Exam "{exam.name}" updated successfully.')
                return redirect('admin-exams-list')
            except Exception as e:
                errors.append('An error occurred while updating the exam.')
        
        for error in errors:
            messages.error(request, error)
    
    context = {
        'exam': exam,
        'organizations': Organization.objects.filter(is_active=True).order_by('name'),
    }
    
    return render(request, 'users/admin_exam_edit.html', context)


@login_required
@require_http_methods(["POST"])
def admin_exam_toggle_status(request, exam_id):
    """Toggle exam active status"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    from exams.models import Exam
    
    exam = get_object_or_404(Exam, id=exam_id)
    
    try:
        exam.is_active = not exam.is_active
        exam.save()
        
        status = 'activated' if exam.is_active else 'deactivated'
        return JsonResponse({
            'success': True,
            'message': f'Exam {status} successfully',
            'is_active': exam.is_active
        })
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while updating exam status'}, status=500)


@login_required
def admin_questions_list(request):
    """Custom admin question management list view"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    from questions.models import Question, QuestionBank
    
    # Get questions with related data
    questions = Question.objects.select_related('created_by', 'question_bank').order_by('-created_at')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        questions = questions.filter(
            Q(question_text__icontains=search) |
            Q(question_bank__category__icontains=search) |
            Q(question_bank__name__icontains=search) |
            Q(topic__icontains=search) |
            Q(subtopic__icontains=search) |
            Q(tags__icontains=search) |
            Q(explanation__icontains=search)
        )
    
    # Question bank filter
    bank_filter = request.GET.get('question_bank', '')
    if bank_filter:
        questions = questions.filter(question_bank_id=bank_filter)
    
    # Type filter
    type_filter = request.GET.get('question_type', '')
    if type_filter:
        questions = questions.filter(question_type=type_filter)
    
    # Difficulty filter
    difficulty_filter = request.GET.get('difficulty', '')
    if difficulty_filter:
        questions = questions.filter(difficulty=difficulty_filter)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(questions, 25)
    page = request.GET.get('page')
    questions = paginator.get_page(page)
    
    # Get question types and difficulty levels from the model
    question_types = Question.QUESTION_TYPES if hasattr(Question, 'QUESTION_TYPES') else []
    difficulty_levels = [
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'), 
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    # Handle JSON requests (for manual selection interface)
    if request.headers.get('Accept') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        
        questions_data = []
        for question in questions:
            questions_data.append({
                'id': str(question.id),
                'question_text': question.question_text,
                'subject': question.subject,
                'topic': question.topic,
                'subtopic': question.subtopic,
                'difficulty': question.difficulty,
                'question_type': question.question_type,
                'question_bank_name': question.question_bank.name if question.question_bank else None,
                'question_bank_id': str(question.question_bank.id) if question.question_bank else None,
                'created_at': question.created_at.isoformat() if question.created_at else None,
            })
        
        return JsonResponse({
            'success': True,
            'questions': questions_data,
            'results': questions_data,  # Alternative key name
            'count': questions.paginator.count if hasattr(questions, 'paginator') else len(questions_data),
            'total': questions.paginator.count if hasattr(questions, 'paginator') else len(questions_data),
            'page': questions.number if hasattr(questions, 'number') else 1,
            'page_size': 25,
            'start_index': questions.start_index() if hasattr(questions, 'start_index') else 1,
            'end_index': questions.end_index() if hasattr(questions, 'end_index') else len(questions_data),
        })
    
    context = {
        'questions': questions,
        'search': search,
        'bank_filter': bank_filter,
        'type_filter': type_filter,
        'difficulty_filter': difficulty_filter,
        'question_banks': QuestionBank.objects.all().order_by('name'),
        'question_types': question_types,
        'difficulty_levels': difficulty_levels,
        'total_questions': Question.objects.count(),
    }
    
    return render(request, 'users/admin_questions_list.html', context)


@login_required
def admin_email_settings(request):
    """Custom admin email settings view"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # This would typically update email settings in the database or settings file
        # For now, just show a success message
        messages.success(request, 'Email settings updated successfully.')
        return redirect('admin-management')
    
    # Get current email settings (placeholder)
    context = {
        'email_settings': {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'from_email': 'noreply@examportal.com',
        }
    }
    
    return render(request, 'users/admin_email_settings.html', context)


@login_required
@require_http_methods(["POST"])
def admin_bulk_activate_users(request):
    """Bulk activate users"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    import json
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return JsonResponse({'error': 'No users selected'}, status=400)
        
        # Prevent self-modification
        if str(request.user.id) in user_ids:
            user_ids.remove(str(request.user.id))
        
        users_updated = User.objects.filter(id__in=user_ids).update(is_active=True)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully activated {users_updated} user(s)',
            'users_updated': users_updated
        })
    except Exception as e:
        return JsonResponse({'error': 'An error occurred during bulk activation'}, status=500)


@login_required  
@require_http_methods(["POST"])
def admin_bulk_deactivate_users(request):
    """Bulk deactivate users"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    import json
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return JsonResponse({'error': 'No users selected'}, status=400)
        
        # Prevent self-modification
        if str(request.user.id) in user_ids:
            user_ids.remove(str(request.user.id))
        
        users_updated = User.objects.filter(id__in=user_ids).update(is_active=False)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deactivated {users_updated} user(s)',
            'users_updated': users_updated
        })
    except Exception as e:
        return JsonResponse({'error': 'An error occurred during bulk deactivation'}, status=500)


@login_required
def admin_export_users(request):
    """Export user data to CSV"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write CSV header
    writer.writerow([
        'ID', 'Username', 'Email', 'First Name', 'Last Name', 
        'Phone', 'Role', 'Is Active', 'Date Joined', 'Last Login'
    ])
    
    # Write user data
    users = User.objects.all().order_by('-date_joined')
    for user in users:
        writer.writerow([
            str(user.id),
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            user.phone or '',
            user.get_role_display(),
            'Yes' if user.is_active else 'No',
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'
        ])
    
    return response


@login_required
def admin_user_groups(request):
    """Custom admin user groups management"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    from django.contrib.auth.models import Group, Permission
    
    groups = Group.objects.all().prefetch_related('permissions')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_group':
            group_name = sanitize_user_input(request.POST.get('group_name', ''))
            if group_name:
                try:
                    group, created = Group.objects.get_or_create(name=group_name)
                    if created:
                        messages.success(request, f'Group "{group_name}" created successfully.')
                    else:
                        messages.warning(request, f'Group "{group_name}" already exists.')
                except Exception as e:
                    messages.error(request, 'An error occurred while creating the group.')
        
        elif action == 'delete_group':
            group_id = request.POST.get('group_id')
            try:
                group = Group.objects.get(id=group_id)
                group_name = group.name
                group.delete()
                messages.success(request, f'Group "{group_name}" deleted successfully.')
            except Group.DoesNotExist:
                messages.error(request, 'Group not found.')
            except Exception as e:
                messages.error(request, 'An error occurred while deleting the group.')
        
        return redirect('admin-user-groups')
    
    context = {
        'groups': groups,
        'total_groups': groups.count(),
    }
    
    return render(request, 'users/admin_user_groups.html', context)


@login_required
def admin_permissions(request):
    """Custom admin permissions management"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
    
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Get permissions grouped by content type
    permissions = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename')
    
    # Group permissions by content type
    grouped_permissions = {}
    for permission in permissions:
        app_label = permission.content_type.app_label.replace('_', ' ').title()
        model_name = permission.content_type.model.replace('_', ' ').title()
        app_model = f"{app_label} - {model_name}"
        if app_model not in grouped_permissions:
            grouped_permissions[app_model] = []
        grouped_permissions[app_model].append(permission)
    
    context = {
        'grouped_permissions': grouped_permissions,
        'total_permissions': permissions.count(),
    }
    
    return render(request, 'users/admin_permissions.html', context)


# Question Bank Permission Management APIs
@login_required
def question_bank_permissions_api(request):
    """API to manage question bank permissions"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    from questions.models import QuestionBank, QuestionBankPermission
    
    if request.method == 'GET':
        # Get all question banks with their permissions
        banks = QuestionBank.objects.select_related('created_by').prefetch_related(
            'permissions__user', 'permissions__granted_by'
        ).all()
        
        data = []
        for bank in banks:
            permissions_data = []
            for perm in bank.permissions.filter(is_active=True):
                permissions_data.append({
                    'id': perm.id,
                    'user_id': perm.user.id,
                    'user_name': perm.user.get_full_name() or perm.user.username,
                    'user_email': perm.user.email,
                    'permission_type': perm.permission_type,
                    'permission_display': perm.get_permission_type_display(),
                    'granted_by': perm.granted_by.get_full_name() or perm.granted_by.username,
                    'granted_at': perm.granted_at.isoformat(),
                    'expires_at': perm.expires_at.isoformat() if perm.expires_at else None,
                    'is_expired': perm.is_expired,
                    'notes': perm.notes,
                })
            
            data.append({
                'id': str(bank.id),
                'name': bank.name,
                'description': bank.description,
                'category': bank.category,
                'is_public': bank.is_public,
                'created_by': bank.created_by.get_full_name() or bank.created_by.username,
                'created_by_id': bank.created_by.id,
                'total_questions': bank.total_questions,
                'permissions': permissions_data,
                'permission_count': len(permissions_data),
            })
        
        return JsonResponse({'question_banks': data})
    
    elif request.method == 'POST':
        # Grant permission to a user
        try:
            bank_id = request.POST.get('question_bank_id')
            user_id = request.POST.get('user_id')
            permission_type = request.POST.get('permission_type', 'view')
            expires_at = request.POST.get('expires_at')
            notes = request.POST.get('notes', '')
            
            if not bank_id or not user_id:
                return JsonResponse({'error': 'Question bank and user are required'}, status=400)
            
            bank = get_object_or_404(QuestionBank, id=bank_id)
            user = get_object_or_404(User, id=user_id)
            
            # Parse expiration date
            expires_at_obj = None
            if expires_at:
                from datetime import datetime
                try:
                    expires_at_obj = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                except ValueError:
                    return JsonResponse({'error': 'Invalid expiration date format'}, status=400)
            
            # Create or update permission
            permission, created = QuestionBankPermission.objects.update_or_create(
                question_bank=bank,
                user=user,
                defaults={
                    'permission_type': permission_type,
                    'granted_by': request.user,
                    'expires_at': expires_at_obj,
                    'notes': notes,
                    'is_active': True,
                }
            )

            action = 'granted' if created else 'updated'

            return JsonResponse({
                'success': True,
                'message': f'Permission {action} successfully',
                'permission': {
                    'id': permission.id,
                    'user_name': user.get_full_name() or user.username,
                    'permission_type': permission.permission_type,
                    'permission_display': permission.get_permission_type_display(),
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    elif request.method == 'DELETE':
        # Revoke permission
        try:
            permission_id = request.GET.get('permission_id')
            if not permission_id:
                return JsonResponse({'error': 'Permission ID required'}, status=400)
            
            permission = get_object_or_404(QuestionBankPermission, id=permission_id)
            user_name = permission.user.get_full_name() or permission.user.username
            bank_name = permission.question_bank.name

            permission.delete()

            return JsonResponse({
                'success': True,
                'message': 'Permission revoked successfully'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required 
def get_teachers_for_permissions(request):
    """Get all teachers for permission assignment"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    teachers = User.objects.filter(role='teacher').values(
        'id', 'username', 'email', 'first_name', 'last_name'
    )
    
    teachers_data = []
    for teacher in teachers:
        full_name = f"{teacher['first_name']} {teacher['last_name']}".strip()
        teachers_data.append({
            'id': teacher['id'],
            'username': teacher['username'],
            'email': teacher['email'],
            'full_name': full_name or teacher['username'],
            'display_name': f"{full_name or teacher['username']} ({teacher['email']})"
        })
    
    return JsonResponse({'teachers': teachers_data})


@login_required
def bulk_permission_management(request):
    """Bulk grant/revoke permissions"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Admin access required'}, status=403)

    if request.method == 'POST':
        try:
            action = request.POST.get('action')  # 'grant' or 'revoke'
            bank_ids = request.POST.getlist('bank_ids[]')
            user_ids = request.POST.getlist('user_ids[]')
            permission_type = request.POST.get('permission_type', 'view')

            if action not in ['grant', 'revoke']:
                return JsonResponse({'error': 'Invalid action'}, status=400)

            if not bank_ids or not user_ids:
                return JsonResponse({'error': 'Banks and users are required'}, status=400)

            from questions.models import QuestionBank, QuestionBankPermission

            banks = QuestionBank.objects.filter(id__in=bank_ids)
            users = User.objects.filter(id__in=user_ids, role='teacher')

            success_count = 0
            error_count = 0

            for bank in banks:
                for user in users:
                    try:
                        if action == 'grant':
                            permission, created = QuestionBankPermission.objects.update_or_create(
                                question_bank=bank,
                                user=user,
                                defaults={
                                    'permission_type': permission_type,
                                    'granted_by': request.user,
                                    'is_active': True,
                                }
                            )
                            success_count += 1
                        elif action == 'revoke':
                            QuestionBankPermission.objects.filter(
                                question_bank=bank,
                                user=user
                            ).delete()
                            success_count += 1
                    except Exception:
                        error_count += 1

            return JsonResponse({
                'success': True,
                'message': f'Bulk {action}: {success_count} successful, {error_count} errors',
                'success_count': success_count,
                'error_count': error_count,
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Test Attempts Management APIs
@login_required
def test_attempts_list_api(request):
    """API to list all tests with their max_attempts setting"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Admin access required'}, status=403)

    from exams.models import Test, Exam
    from django.db.models import Count

    # Get all tests with related exam and attempt counts
    tests = Test.objects.select_related('exam').annotate(
        attempt_count=Count('attempts')
    ).order_by('-created_at')

    # Search functionality
    search = request.GET.get('search', '')
    if search:
        tests = tests.filter(
            Q(title__icontains=search) |
            Q(exam__name__icontains=search) |
            Q(description__icontains=search)
        )

    tests_data = []
    for test in tests:
        tests_data.append({
            'id': str(test.id),
            'title': test.title,
            'exam_name': test.exam.name if test.exam else 'N/A',
            'exam_id': str(test.exam.id) if test.exam else None,
            'max_attempts': test.max_attempts,
            'total_attempts': test.attempt_count,
            'duration_minutes': test.duration_minutes,
            'total_marks': test.total_marks,
            'is_published': test.is_published,
            'created_at': test.created_at.isoformat() if hasattr(test, 'created_at') else None,
        })

    return JsonResponse({
        'success': True,
        'tests': tests_data,
        'count': len(tests_data)
    })


@login_required
@require_http_methods(["POST"])
def update_test_max_attempts_api(request):
    """API to update max_attempts for a specific test"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Admin access required'}, status=403)

    try:
        import json
        data = json.loads(request.body) if request.body else {}

        test_id = data.get('test_id') or request.POST.get('test_id')
        max_attempts = data.get('max_attempts') or request.POST.get('max_attempts')

        if not test_id:
            return JsonResponse({'error': 'Test ID is required'}, status=400)

        if not max_attempts:
            return JsonResponse({'error': 'Max attempts value is required'}, status=400)

        try:
            max_attempts = int(max_attempts)
            if max_attempts < 1:
                return JsonResponse({'error': 'Max attempts must be at least 1'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Max attempts must be a valid number'}, status=400)

        from exams.models import Test
        test = get_object_or_404(Test, id=test_id)

        old_max_attempts = test.max_attempts
        test.max_attempts = max_attempts
        test.save()

        return JsonResponse({
            'success': True,
            'message': f'Max attempts updated successfully to {max_attempts}',
            'test_id': str(test.id),
            'test_title': test.title,
            'old_max_attempts': old_max_attempts,
            'new_max_attempts': max_attempts
        })

    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def bulk_update_test_attempts_api(request):
    """API to bulk update max_attempts for multiple tests"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Admin access required'}, status=403)

    try:
        import json
        data = json.loads(request.body) if request.body else {}

        test_ids = data.get('test_ids', [])
        max_attempts = data.get('max_attempts')

        if not test_ids:
            return JsonResponse({'error': 'No tests selected'}, status=400)

        if not max_attempts:
            return JsonResponse({'error': 'Max attempts value is required'}, status=400)

        try:
            max_attempts = int(max_attempts)
            if max_attempts < 1:
                return JsonResponse({'error': 'Max attempts must be at least 1'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Max attempts must be a valid number'}, status=400)

        from exams.models import Test

        tests_updated = Test.objects.filter(id__in=test_ids).update(max_attempts=max_attempts)

        return JsonResponse({
            'success': True,
            'message': f'Successfully updated {tests_updated} test(s) to {max_attempts} max attempts',
            'tests_updated': tests_updated,
            'max_attempts': max_attempts
        })

    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

