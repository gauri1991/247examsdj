from django.contrib import admin
from .models import QuestionBank, Question, QuestionOption, TestQuestion, UserAnswer


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0
    ordering = ['order']


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_by', 'is_public', 'question_count', 'created_at']
    list_filter = ['category', 'is_public', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'question_type', 'difficulty', 'marks', 'topic', 'question_bank', 'created_at']
    list_filter = ['question_type', 'difficulty', 'question_bank', 'topic', 'created_at']
    search_fields = ['question_text', 'topic', 'subtopic']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [QuestionOptionInline]
    
    fieldsets = (
        ('Question Content', {
            'fields': ('question_bank', 'question_text', 'question_type', 'image')
        }),
        ('Settings', {
            'fields': ('difficulty', 'marks', 'negative_marks', 'time_limit')
        }),
        ('Classification', {
            'fields': ('topic', 'subtopic', 'tags')
        }),
        ('Answer Configuration', {
            'fields': ('correct_answers', 'case_sensitive', 'expected_answer', 'min_words', 'max_words'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('explanation', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def question_text_short(self, obj):
        return obj.question_text[:60] + "..." if len(obj.question_text) > 60 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['option_text_short', 'question_short', 'is_correct', 'order']
    list_filter = ['is_correct', 'question__question_type']
    search_fields = ['option_text', 'question__question_text']
    
    def option_text_short(self, obj):
        return obj.option_text[:40] + "..." if len(obj.option_text) > 40 else obj.option_text
    option_text_short.short_description = 'Option'
    
    def question_short(self, obj):
        return obj.question.question_text[:30] + "..." if len(obj.question.question_text) > 30 else obj.question.question_text
    question_short.short_description = 'Question'


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ['test', 'question_short', 'order', 'marks']
    list_filter = ['test', 'question__difficulty', 'question__question_type']
    search_fields = ['test__title', 'question__question_text']
    ordering = ['test', 'order']
    
    def question_short(self, obj):
        return obj.question.question_text[:50] + "..." if len(obj.question.question_text) > 50 else obj.question.question_text
    question_short.short_description = 'Question'


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['test_attempt', 'question_short', 'is_correct', 'marks_obtained', 'answered_at']
    list_filter = ['is_correct', 'test_attempt__test', 'answered_at']
    search_fields = ['test_attempt__user__username', 'question__question_text']
    readonly_fields = ['answered_at']
    
    def question_short(self, obj):
        return obj.question.question_text[:40] + "..." if len(obj.question.question_text) > 40 else obj.question.question_text
    question_short.short_description = 'Question'
