from django.db import models
from django.conf import settings
from questions.models import QuestionBank, Question
import uuid


class PDFDocument(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    LAYOUT_TYPES = [
        ('single_column', 'Single Column'),
        ('multi_column', 'Multi Column'),
        ('mixed', 'Mixed Layout'),
        ('unknown', 'Unknown'),
    ]
    
    EXAM_TYPE_CHOICES = [
        ('upsc', 'UPSC (Civil Services)'),
        ('ssc', 'SSC (Staff Selection Commission)'),
        ('banking', 'Banking Exams (SBI, IBPS, RBI)'),
        ('railway', 'Railway Exams (RRB)'),
        ('defense', 'Defense Exams (NDA, CDS, AFCAT)'),
        ('state_psc', 'State PSC'),
        ('teaching', 'Teaching Exams (CTET, TET, NET)'),
        ('engineering', 'Engineering Entrance (JEE, GATE)'),
        ('medical', 'Medical Entrance (NEET, AIIMS)'),
        ('management', 'Management Entrance (CAT, MAT, XAT)'),
        ('law', 'Law Entrance (CLAT, LSAT)'),
        ('judiciary', 'Judicial Services'),
        ('police', 'Police & Para-military'),
        ('insurance', 'Insurance Exams (LIC, GIC)'),
        ('academic', 'Academic/School Level'),
        ('other', 'Other'),
    ]
    
    SOURCE_TYPE_CHOICES = [
        ('previous_year', 'Previous Year Paper'),
        ('mock_test', 'Mock Test'),
        ('sample_paper', 'Sample Paper'),
        ('practice_set', 'Practice Set'),
        ('study_material', 'Study Material'),
        ('question_bank', 'Question Bank'),
        ('textbook', 'Textbook'),
        ('notes', 'Study Notes'),
        ('reference_book', 'Reference Book'),
        ('online_resource', 'Online Resource'),
        ('coaching_material', 'Coaching Material'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='pdf_documents/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_pdfs')
    
    # Document metadata
    title = models.CharField(max_length=255, blank=True, help_text="Document title")
    description = models.TextField(blank=True, help_text="Brief description of the document content")
    
    # Exam information
    exam_type = models.CharField(max_length=50, choices=EXAM_TYPE_CHOICES, blank=True, help_text="Type of exam")
    exam_name = models.CharField(max_length=200, blank=True, help_text="Specific exam name (e.g., UPSC CSE Prelims)")
    organization = models.CharField(max_length=200, blank=True, help_text="Conducting organization")
    year = models.IntegerField(null=True, blank=True, help_text="Year of exam")
    
    # Subject and categorization
    subject = models.CharField(max_length=100, blank=True, help_text="Main subject (e.g., General Studies, Mathematics)")
    topic = models.CharField(max_length=100, blank=True, help_text="Specific topic")
    subtopic = models.CharField(max_length=100, blank=True, help_text="Subtopic if applicable")
    
    # Tags and metadata
    tags = models.JSONField(default=list, blank=True, help_text="List of tags for easy search")
    custom_fields = models.JSONField(default=dict, blank=True, help_text="Additional custom metadata")
    
    # Source information
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES, blank=True, help_text="Type of document source")
    source_url = models.URLField(blank=True, help_text="Source URL if available")
    
    # Processing metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    page_count = models.PositiveIntegerField(null=True, blank=True)
    
    # Analysis results
    is_searchable = models.BooleanField(null=True, blank=True, help_text="True if PDF contains searchable text")
    layout_type = models.CharField(max_length=20, choices=LAYOUT_TYPES, default='unknown')
    confidence_score = models.FloatField(null=True, blank=True, help_text="Overall confidence in extraction")
    
    # Processing details
    processing_time_seconds = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    extraction_notes = models.TextField(blank=True)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'pdf_documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['exam_type']),
            models.Index(fields=['organization']),
            models.Index(fields=['year']),
            models.Index(fields=['subject']),
        ]

class MetadataTemplate(models.Model):
    """
    Predefined metadata templates for quick application to documents
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Template name")
    description = models.TextField(blank=True, help_text="Template description")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='metadata_templates')
    
    # Template metadata fields
    exam_type = models.CharField(max_length=50, choices=PDFDocument.EXAM_TYPE_CHOICES, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    topic = models.CharField(max_length=100, blank=True)
    source_type = models.CharField(max_length=50, choices=PDFDocument.SOURCE_TYPE_CHOICES, blank=True)
    year = models.IntegerField(null=True, blank=True)
    
    # Template tags and custom fields
    default_tags = models.JSONField(default=list, blank=True, help_text="Default tags to apply")
    custom_fields = models.JSONField(default=dict, blank=True, help_text="Default custom fields")
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0, help_text="Number of times template has been used")
    is_public = models.BooleanField(default=False, help_text="Allow other users to use this template")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'metadata_templates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_by', 'exam_type']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_exam_type_display() or 'General'})"
    
    def apply_to_document(self, document):
        """
        Apply this template's metadata to a document
        """
        if self.exam_type and not document.exam_type:
            document.exam_type = self.exam_type
        if self.organization and not document.organization:
            document.organization = self.organization
        if self.subject and not document.subject:
            document.subject = self.subject
        if self.topic and not document.topic:
            document.topic = self.topic
        if self.source_type and not document.source_type:
            document.source_type = self.source_type
        if self.year and not document.year:
            document.year = self.year
        
        # Merge tags
        if self.default_tags:
            existing_tags = document.tags or []
            new_tags = list(set(existing_tags + self.default_tags))
            document.tags = new_tags
        
        # Merge custom fields
        if self.custom_fields:
            existing_custom = document.custom_fields or {}
            for key, value in self.custom_fields.items():
                if key not in existing_custom:
                    existing_custom[key] = value
            document.custom_fields = existing_custom
        
        # Increment usage count
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
        
        return document


# Add methods to PDFDocument class (they should be part of the class above)
PDFDocument.add_to_class('__str__', lambda self: f"{self.title} ({self.status})" if self.title else f"{self.filename} ({self.status})")
PDFDocument.add_to_class('get_display_name', lambda self: self.title if self.title else (f"{self.exam_name} - {self.year}" if self.exam_name and self.year else self.filename))
PDFDocument.add_to_class('get_tag_list', lambda self: ', '.join(self.tags) if self.tags else '')


class ProcessingJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    PROCESSING_STEPS = [
        ('upload_validation', 'Upload Validation'),
        ('text_detection', 'Text Detection'),
        ('ocr_processing', 'OCR Processing'),
        ('layout_analysis', 'Layout Analysis'),
        ('text_extraction', 'Text Extraction'),
        ('qa_detection', 'Q&A Detection'),
        ('answer_extraction', 'Answer Extraction'),
        ('confidence_scoring', 'Confidence Scoring'),
        ('finalization', 'Finalization'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdf_document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name='processing_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_step = models.CharField(max_length=30, choices=PROCESSING_STEPS, blank=True)
    current_step_display = models.CharField(max_length=100, blank=True, help_text="Human-readable current step description")
    progress_percentage = models.PositiveIntegerField(default=0)
    
    # Step tracking
    step_details = models.JSONField(default=dict, blank=True, help_text="Details for each processing step")
    error_details = models.JSONField(default=dict, blank=True, help_text="Error details if processing fails")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'processing_jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.id} - {self.pdf_document.filename} ({self.status})"


class ExtractedQuestion(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('multi_select', 'Multiple Select'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('essay', 'Essay/Descriptive'),
        ('unknown', 'Unknown'),
    ]
    
    CONFIDENCE_LEVELS = [
        ('high', 'High (>80%)'),
        ('medium', 'Medium (60-80%)'),
        ('low', 'Low (<60%)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdf_document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name='extracted_questions')
    processing_job = models.ForeignKey(ProcessingJob, on_delete=models.CASCADE, related_name='extracted_questions')
    
    # Question content
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='unknown')
    page_number = models.PositiveIntegerField()
    position_on_page = models.JSONField(default=dict, help_text="Bounding box coordinates")
    
    # Answer content
    answer_options = models.JSONField(default=list, blank=True, help_text="List of answer options for MCQ")
    correct_answers = models.JSONField(default=list, blank=True, help_text="List of correct answers")
    explanation = models.TextField(blank=True)
    
    # Extraction metadata
    confidence_score = models.FloatField(help_text="Confidence score 0-100")
    confidence_level = models.CharField(max_length=10, choices=CONFIDENCE_LEVELS)
    extraction_method = models.CharField(max_length=50, help_text="Method used for extraction")
    
    # Auto-detected metadata
    estimated_difficulty = models.CharField(max_length=10, blank=True, help_text="Auto-detected difficulty")
    estimated_topic = models.CharField(max_length=100, blank=True)
    estimated_marks = models.FloatField(null=True, blank=True)
    
    # Processing flags
    requires_review = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False, help_text="True if manually rejected during review")
    is_converted = models.BooleanField(default=False, help_text="True if converted to Question model")
    
    # Additional metadata for review and processing
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata from processing and review")
    
    # Question Bank integration
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.SET_NULL, null=True, blank=True)
    converted_question = models.OneToOneField(Question, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_extraction')
    
    # Timestamps
    extracted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'extracted_questions'
        ordering = ['page_number', 'id']

    def __str__(self):
        return f"Q{self.page_number}: {self.question_text[:50]}..."

    @property
    def confidence_percentage(self):
        return round(self.confidence_score, 1)

    def set_confidence_level(self):
        if self.confidence_score >= 80:
            self.confidence_level = 'high'
        elif self.confidence_score >= 60:
            self.confidence_level = 'medium'
        else:
            self.confidence_level = 'low'


class ProcessingStatistics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdf_document = models.OneToOneField(PDFDocument, on_delete=models.CASCADE, related_name='statistics')
    
    # Extraction statistics
    total_questions_found = models.PositiveIntegerField(default=0)
    questions_by_type = models.JSONField(default=dict, help_text="Count of questions by type")
    questions_by_confidence = models.JSONField(default=dict, help_text="Count of questions by confidence level")
    
    # Processing performance
    pages_processed = models.PositiveIntegerField(default=0)
    text_extraction_time = models.FloatField(null=True, blank=True)
    qa_detection_time = models.FloatField(null=True, blank=True)
    total_processing_time = models.FloatField(null=True, blank=True)
    
    # Quality metrics
    average_confidence_score = models.FloatField(null=True, blank=True)
    high_confidence_questions = models.PositiveIntegerField(default=0)
    medium_confidence_questions = models.PositiveIntegerField(default=0)
    low_confidence_questions = models.PositiveIntegerField(default=0)
    questions_requiring_review = models.PositiveIntegerField(default=0)
    
    # Processing method tracking
    processing_method = models.CharField(max_length=50, default='standard', help_text="Method used for processing")
    layout_analysis_used = models.BooleanField(default=False, help_text="Whether layout analysis was used")
    ocr_used = models.BooleanField(default=False, help_text="Whether OCR was used")
    
    # Integration metrics
    questions_converted = models.PositiveIntegerField(default=0)
    questions_approved = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'processing_statistics'

    def __str__(self):
        return f"Stats for {self.pdf_document.filename}"


class ExtractionTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('regex', 'Regular Expression'),
        ('pattern', 'Pattern-based'),
        ('ml_model', 'Machine Learning'),
        ('hybrid', 'Hybrid Approach'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    
    # Template configuration
    pattern_config = models.JSONField(default=dict, help_text="Configuration for extraction patterns")
    question_patterns = models.JSONField(default=list, help_text="Patterns for question detection")
    answer_patterns = models.JSONField(default=list, help_text="Patterns for answer detection")
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    success_rate = models.FloatField("Success rate in %", null=True, blank=True)
    
    # Template status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='extraction_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'extraction_templates'
        ordering = ['-success_rate', 'name']

    def __str__(self):
        return f"{self.name} ({self.template_type})"


class RegionCorrection(models.Model):
    """
    Tracks manual corrections made to detected regions
    """
    CORRECTION_TYPES = [
        ('resize', 'Resize Region'),
        ('move', 'Move Region'),
        ('split', 'Split Region'),
        ('merge', 'Merge Regions'),
        ('delete', 'Delete Region'),
        ('create', 'Create Region'),
        ('retype', 'Change Region Type'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdf_document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name='region_corrections')
    page_number = models.PositiveIntegerField()
    
    # Original region data (JSON)
    original_coordinates = models.JSONField(help_text="Original region coordinates and properties")
    
    # Corrected region data (JSON)
    corrected_coordinates = models.JSONField(help_text="Corrected region coordinates and properties")
    
    # Correction details
    correction_type = models.CharField(max_length=20, choices=CORRECTION_TYPES)
    correction_reason = models.TextField(blank=True, help_text="Optional reason for the correction")
    
    # User tracking
    corrected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='region_corrections')
    correction_timestamp = models.DateTimeField(auto_now_add=True)
    
    # Review status
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_corrections'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Quality metrics
    confidence_before = models.FloatField(null=True, blank=True, help_text="Confidence score before correction")
    confidence_after = models.FloatField(null=True, blank=True, help_text="Confidence score after correction")
    
    class Meta:
        db_table = 'region_corrections'
        ordering = ['-correction_timestamp']
        indexes = [
            models.Index(fields=['pdf_document', 'page_number']),
            models.Index(fields=['correction_type']),
            models.Index(fields=['corrected_by']),
        ]

    def __str__(self):
        return f"{self.correction_type} on {self.pdf_document.filename} page {self.page_number}"


class RegionReviewSession(models.Model):
    """
    Tracks review sessions for document regions
    """
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdf_document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name='review_sessions')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_sessions')
    
    # Session details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    current_page = models.PositiveIntegerField(default=1)
    total_pages = models.PositiveIntegerField()
    
    # Progress tracking
    pages_reviewed = models.PositiveIntegerField(default=0)
    regions_corrected = models.PositiveIntegerField(default=0)
    regions_approved = models.PositiveIntegerField(default=0)
    regions_rejected = models.PositiveIntegerField(default=0)
    
    # Session timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Session metadata
    session_notes = models.TextField(blank=True)
    estimated_completion_time = models.PositiveIntegerField(null=True, blank=True, help_text="Estimated time in minutes")
    
    class Meta:
        db_table = 'region_review_sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f"Review session for {self.pdf_document.filename} by {self.reviewer.username}"
    
    @property
    def progress_percentage(self) -> float:
        if self.total_pages == 0:
            return 0.0
        return (self.pages_reviewed / self.total_pages) * 100
    
    @property
    def is_active(self) -> bool:
        return self.status == 'in_progress'


class PageReviewStatus(models.Model):
    """
    Track the review status of individual pages in a PDF document
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('no_questions', 'No Questions'),
        ('pending_unsupported', 'Pending - Unsupported Type'),
        ('skipped', 'Skipped'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdf_document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name='page_statuses')
    page_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Track questions found
    questions_found = models.PositiveIntegerField(default=0)
    questions_extracted = models.PositiveIntegerField(default=0)
    
    # Review metadata
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_pages'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes for skipped/no questions pages
    notes = models.TextField(blank=True)
    
    # Processing time
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'page_review_status'
        unique_together = ['pdf_document', 'page_number']
        ordering = ['page_number']
    
    def __str__(self):
        return f"Page {self.page_number} of {self.pdf_document.filename} - {self.status}"


class SavedRegion(models.Model):
    """
    Store selected/detected regions with their processing status
    """
    REGION_STATUS_CHOICES = [
        ('detected', 'Detected'),
        ('completed', 'Questions Extracted'),
        ('unsupported', 'Unsupported Type'),
        ('no_questions', 'No Questions'),
        ('error', 'Processing Error'),
    ]
    
    REGION_TYPE_CHOICES = [
        ('question', 'Question'),
        ('answer_options', 'Answer Options'),
        ('passage', 'Passage/Context'),
        ('diagram', 'Diagram'),
        ('table', 'Table'),
        ('mixed', 'Mixed Content'),
        ('unknown', 'Unknown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pdf_document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name='saved_regions')
    page_number = models.PositiveIntegerField()
    
    # Region data
    coordinates = models.JSONField(help_text="Region coordinates {x, y, width, height}")
    region_type = models.CharField(max_length=20, choices=REGION_TYPE_CHOICES, default='unknown')
    extracted_text = models.TextField(blank=True, help_text="OCR extracted text from region")
    confidence_score = models.FloatField(default=0.0, help_text="Detection/OCR confidence 0-1")
    
    # Processing status
    status = models.CharField(max_length=20, choices=REGION_STATUS_CHOICES, default='detected')
    notes = models.TextField(blank=True, help_text="User notes about this region")
    
    # Metadata
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='processed_regions'
    )
    processed_at = models.DateTimeField(auto_now_add=True)
    
    # Optional link to extracted question if successfully processed
    extracted_question = models.ForeignKey(
        'ExtractedQuestion', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='source_regions'
    )
    
    class Meta:
        db_table = 'saved_regions'
        indexes = [
            models.Index(fields=['pdf_document', 'page_number']),
            models.Index(fields=['status']),
            models.Index(fields=['region_type']),
        ]
        ordering = ['page_number', 'coordinates']
    
    def __str__(self):
        return f"Region on page {self.page_number} - {self.status}"
    
    @property
    def status_color(self):
        """Return CSS color class for this region's status"""
        color_map = {
            'detected': 'border-blue-500 bg-blue-100',
            'completed': 'border-green-500 bg-green-100', 
            'unsupported': 'border-orange-500 bg-orange-100',
            'no_questions': 'border-gray-500 bg-gray-100',
            'error': 'border-red-500 bg-red-100',
        }
        return color_map.get(self.status, 'border-gray-500 bg-gray-100')
