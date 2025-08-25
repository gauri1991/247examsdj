from django.contrib import admin
from .models import Exam, Test, TestSection, TestAttempt


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_by', 'is_active', 'test_count', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def test_count(self, obj):
        return obj.tests.count()
    test_count.short_description = 'Tests'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['title', 'exam', 'duration_minutes', 'total_marks', 'is_published', 'question_count', 'created_at']
    list_filter = ['is_published', 'exam', 'created_at']
    search_fields = ['title', 'description', 'exam__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('exam', 'title', 'description')
        }),
        ('Test Configuration', {
            'fields': ('duration_minutes', 'total_marks', 'pass_percentage')
        }),
        ('Settings', {
            'fields': ('is_published', 'randomize_questions', 'show_result_immediately', 'allow_review', 'max_attempts')
        }),
        ('Scheduling', {
            'fields': ('start_time', 'end_time'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def question_count(self, obj):
        return obj.test_questions.count()
    question_count.short_description = 'Questions'


@admin.register(TestSection)
class TestSectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'test', 'order', 'question_count']
    list_filter = ['test']
    search_fields = ['name', 'test__title']
    ordering = ['test', 'order']
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'test_title', 'status', 'percentage', 'marks_obtained', 'start_time']
    list_filter = ['status', 'test', 'start_time']
    search_fields = ['user__username', 'test__title']
    readonly_fields = ['start_time', 'end_time']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('test', 'user', 'status')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'time_spent_seconds')
        }),
        ('Results', {
            'fields': ('total_questions', 'attempted_questions', 'correct_answers', 'marks_obtained', 'percentage')
        })
    )
    
    def test_title(self, obj):
        return obj.test.title
    test_title.short_description = 'Test'
