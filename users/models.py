from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student')
    ], default='student')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'


class UserPreferences(models.Model):
    """Store user preferences and settings"""
    
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto (System)')
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('ta', 'Tamil'),
        ('te', 'Telugu'),
        ('mr', 'Marathi'),
        ('gu', 'Gujarati'),
        ('bn', 'Bengali'),
        ('kn', 'Kannada'),
        ('ml', 'Malayalam'),
        ('pa', 'Punjabi')
    ]
    
    TIMEZONE_CHOICES = [
        ('Asia/Kolkata', 'India Standard Time (IST)'),
        ('Asia/Dubai', 'Gulf Standard Time (GST)'),
        ('Asia/Singapore', 'Singapore Time (SGT)'),
        ('Europe/London', 'British Time (GMT/BST)'),
        ('America/New_York', 'Eastern Time (EST/EDT)'),
        ('America/Los_Angeles', 'Pacific Time (PST/PDT)')
    ]
    
    DATE_FORMAT_CHOICES = [
        ('DD/MM/YYYY', 'DD/MM/YYYY'),
        ('MM/DD/YYYY', 'MM/DD/YYYY'),
        ('YYYY-MM-DD', 'YYYY-MM-DD'),
        ('DD-MM-YYYY', 'DD-MM-YYYY')
    ]
    
    FONT_SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('extra_large', 'Extra Large')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Privacy Settings
    email_notifications = models.BooleanField(default=True, help_text="Receive email notifications")
    push_notifications = models.BooleanField(default=True, help_text="Receive push notifications")
    profile_visibility = models.CharField(max_length=20, default='public', choices=[
        ('public', 'Public'),
        ('private', 'Private'),
        ('friends', 'Friends Only')
    ])
    show_online_status = models.BooleanField(default=True)
    show_activity = models.BooleanField(default=True)
    allow_messages = models.CharField(max_length=20, default='everyone', choices=[
        ('everyone', 'Everyone'),
        ('friends', 'Friends Only'),
        ('none', 'No One')
    ])
    
    # Exam Preferences
    auto_save = models.BooleanField(default=True, help_text="Auto-save answers during exam")
    auto_save_interval = models.IntegerField(default=30, help_text="Auto-save interval in seconds")
    show_timer = models.BooleanField(default=True, help_text="Show timer during exam")
    confirm_navigation = models.BooleanField(default=True, help_text="Confirm before navigating away")
    keyboard_shortcuts = models.BooleanField(default=True, help_text="Enable keyboard shortcuts")
    show_question_palette = models.BooleanField(default=True, help_text="Show question navigation palette")
    enable_calculator = models.BooleanField(default=True, help_text="Enable calculator in exams")
    enable_rough_sheet = models.BooleanField(default=True, help_text="Enable rough sheet/notepad")
    mark_review_enabled = models.BooleanField(default=True, help_text="Enable mark for review feature")
    
    # System Settings
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='Asia/Kolkata')
    date_format = models.CharField(max_length=20, choices=DATE_FORMAT_CHOICES, default='DD/MM/YYYY')
    time_format_24h = models.BooleanField(default=False, help_text="Use 24-hour time format")
    
    # Display Preferences
    results_per_page = models.IntegerField(default=10, choices=[
        (10, '10'),
        (25, '25'),
        (50, '50'),
        (100, '100')
    ])
    default_view = models.CharField(max_length=20, default='grid', choices=[
        ('grid', 'Grid View'),
        ('list', 'List View'),
        ('compact', 'Compact View')
    ])
    sidebar_collapsed = models.BooleanField(default=False)
    show_recent_activity = models.BooleanField(default=True)
    
    # Accessibility Settings
    high_contrast = models.BooleanField(default=False, help_text="Enable high contrast mode")
    font_size = models.CharField(max_length=20, choices=FONT_SIZE_CHOICES, default='medium')
    screen_reader_mode = models.BooleanField(default=False, help_text="Optimize for screen readers")
    reduce_animations = models.BooleanField(default=False, help_text="Reduce UI animations")
    
    # Notification Preferences (stored as JSON)
    notification_settings = models.JSONField(default=dict, blank=True, help_text="Detailed notification preferences")
    
    # Custom Settings (for future extensibility)
    custom_settings = models.JSONField(default=dict, blank=True, help_text="Additional custom settings")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'
    
    def __str__(self):
        return f"{self.user.username}'s preferences"
    
    def get_notification_setting(self, key, default=True):
        """Get specific notification setting"""
        return self.notification_settings.get(key, default)
    
    def set_notification_setting(self, key, value):
        """Set specific notification setting"""
        if not self.notification_settings:
            self.notification_settings = {}
        self.notification_settings[key] = value
        self.save(update_fields=['notification_settings'])
    
    def get_custom_setting(self, key, default=None):
        """Get specific custom setting"""
        return self.custom_settings.get(key, default)
    
    def set_custom_setting(self, key, value):
        """Set specific custom setting"""
        if not self.custom_settings:
            self.custom_settings = {}
        self.custom_settings[key] = value
        self.save(update_fields=['custom_settings'])


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Automatically create UserPreferences when a new user is created"""
    if created:
        UserPreferences.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_preferences(sender, instance, **kwargs):
    """Save UserPreferences when user is saved"""
    if hasattr(instance, 'preferences'):
        instance.preferences.save()
