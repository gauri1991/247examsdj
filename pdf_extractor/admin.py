from django.contrib import admin
from .models import PDFDocument, ProcessingJob, ExtractedQuestion, ProcessingStatistics, ExtractionTemplate, RegionCorrection, RegionReviewSession


@admin.register(PDFDocument)
class PDFDocumentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'status', 'uploaded_by', 'page_count', 'confidence_score', 'uploaded_at']
    list_filter = ['status', 'layout_type', 'is_searchable', 'uploaded_at']
    search_fields = ['filename', 'uploaded_by__username']
    readonly_fields = ['id', 'file_size', 'uploaded_at', 'processing_started_at', 'processing_completed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('filename', 'file', 'uploaded_by', 'status')
        }),
        ('Processing Results', {
            'fields': ('is_searchable', 'layout_type', 'page_count', 'confidence_score')
        }),
        ('Processing Details', {
            'fields': ('processing_time_seconds', 'error_message', 'extraction_notes')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'processing_started_at', 'processing_completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ['pdf_document', 'status', 'current_step', 'progress_percentage', 'created_at']
    list_filter = ['status', 'current_step', 'created_at']
    search_fields = ['pdf_document__filename']
    readonly_fields = ['id', 'created_at', 'started_at', 'completed_at']


@admin.register(ExtractedQuestion)
class ExtractedQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'question_type', 'confidence_level', 'page_number', 'requires_review', 'is_converted']
    list_filter = ['question_type', 'confidence_level', 'requires_review', 'is_approved', 'is_converted']
    search_fields = ['question_text', 'estimated_topic']
    readonly_fields = ['id', 'extracted_at', 'reviewed_at', 'converted_at']
    
    def question_text_short(self, obj):
        return obj.question_text[:80] + "..." if len(obj.question_text) > 80 else obj.question_text
    question_text_short.short_description = 'Question Text'
    
    fieldsets = (
        ('Question Content', {
            'fields': ('question_text', 'question_type', 'answer_options', 'correct_answers', 'explanation')
        }),
        ('Extraction Details', {
            'fields': ('pdf_document', 'processing_job', 'page_number', 'position_on_page')
        }),
        ('Quality Metrics', {
            'fields': ('confidence_score', 'confidence_level', 'extraction_method')
        }),
        ('Auto-Detection', {
            'fields': ('estimated_difficulty', 'estimated_topic', 'estimated_marks')
        }),
        ('Processing Status', {
            'fields': ('requires_review', 'is_approved', 'is_converted')
        }),
        ('Integration', {
            'fields': ('question_bank', 'converted_question')
        }),
    )


@admin.register(ProcessingStatistics)
class ProcessingStatisticsAdmin(admin.ModelAdmin):
    list_display = ['pdf_document', 'total_questions_found', 'average_confidence_score', 'questions_converted']
    search_fields = ['pdf_document__filename']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ExtractionTemplate)
class ExtractionTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'success_rate', 'usage_count', 'is_active', 'is_default']
    list_filter = ['template_type', 'is_active', 'is_default']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'usage_count', 'created_at', 'updated_at']


@admin.register(RegionCorrection)
class RegionCorrectionAdmin(admin.ModelAdmin):
    list_display = ['pdf_document', 'page_number', 'correction_type', 'corrected_by', 'is_approved', 'correction_timestamp']
    list_filter = ['correction_type', 'is_approved', 'correction_timestamp']
    search_fields = ['pdf_document__filename', 'corrected_by__username', 'correction_reason']
    readonly_fields = ['id', 'correction_timestamp', 'approved_at']
    
    fieldsets = (
        ('Correction Details', {
            'fields': ('pdf_document', 'page_number', 'correction_type', 'correction_reason')
        }),
        ('Region Data', {
            'fields': ('original_coordinates', 'corrected_coordinates')
        }),
        ('User Tracking', {
            'fields': ('corrected_by', 'correction_timestamp')
        }),
        ('Review Status', {
            'fields': ('is_approved', 'approved_by', 'approved_at')
        }),
        ('Quality Metrics', {
            'fields': ('confidence_before', 'confidence_after')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pdf_document', 'corrected_by', 'approved_by')


@admin.register(RegionReviewSession)
class RegionReviewSessionAdmin(admin.ModelAdmin):
    list_display = ['pdf_document', 'reviewer', 'status', 'progress_percentage_display', 'regions_corrected', 'started_at']
    list_filter = ['status', 'started_at', 'completed_at']
    search_fields = ['pdf_document__filename', 'reviewer__username']
    readonly_fields = ['id', 'started_at', 'last_activity', 'completed_at', 'progress_percentage']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('pdf_document', 'reviewer', 'status')
        }),
        ('Progress', {
            'fields': ('current_page', 'total_pages', 'pages_reviewed', 'progress_percentage')
        }),
        ('Statistics', {
            'fields': ('regions_corrected', 'regions_approved', 'regions_rejected')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'last_activity', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('session_notes', 'estimated_completion_time')
        }),
    )
    
    def progress_percentage_display(self, obj):
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage_display.short_description = 'Progress'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pdf_document', 'reviewer')
