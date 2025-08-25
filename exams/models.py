from django.db import models
from django.conf import settings
import uuid


class Exam(models.Model):
    CATEGORY_CHOICES = [
        # Core Academic Subjects
        ('mathematics', '📊 Mathematics'),
        ('physics', '⚡ Physics'),
        ('chemistry', '🧪 Chemistry'),
        ('biology', '🧬 Biology'),
        ('english', '📚 English Language'),
        ('hindi', '🇮🇳 Hindi'),
        ('history', '🏛️ History'),
        ('geography', '🌍 Geography'),
        ('economics', '💰 Economics'),
        ('political_science', '🏛️ Political Science'),
        ('sociology', '👥 Sociology'),
        ('psychology', '🧠 Psychology'),
        ('philosophy', '🤔 Philosophy'),
        
        # Professional & Technical
        ('computer_science', '💻 Computer Science'),
        ('engineering', '⚙️ Engineering'),
        ('medical', '🏥 Medical'),
        ('law', '⚖️ Law'),
        ('commerce', '📈 Commerce'),
        ('accountancy', '📋 Accountancy'),
        ('business_studies', '💼 Business Studies'),
        
        # Government Exam Specific
        ('general_knowledge', '🎯 General Knowledge'),
        ('current_affairs', '📰 Current Affairs'),
        ('reasoning', '🧩 Logical Reasoning'),
        ('quantitative_aptitude', '🔢 Quantitative Aptitude'),
        ('data_interpretation', '📊 Data Interpretation'),
        ('english_comprehension', '📖 English Comprehension'),
        ('general_science', '🔬 General Science'),
        ('indian_polity', '🏛️ Indian Polity'),
        ('indian_economy', '💹 Indian Economy'),
        ('indian_geography', '🗺️ Indian Geography'),
        ('indian_history', '📜 Indian History'),
        ('environment_ecology', '🌱 Environment & Ecology'),
        
        # Language & Literature
        ('sanskrit', '📿 Sanskrit'),
        ('literature', '📚 Literature'),
        ('linguistics', '🗣️ Linguistics'),
        
        # Specialized
        ('statistics', '📈 Statistics'),
        ('agriculture', '🌾 Agriculture'),
        ('home_science', '🏠 Home Science'),
        ('physical_education', '🏃 Physical Education'),
        ('fine_arts', '🎨 Fine Arts'),
        ('music', '🎵 Music'),
        
        ('other', '📋 Other'),
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
    
    DIFFICULTY_LEVEL_CHOICES = [
        ('basic', '🟢 Basic'),
        ('intermediate', '🟡 Intermediate'), 
        ('advanced', '🟠 Advanced'),
        ('expert', '🔴 Expert'),
        ('mixed', '🔵 Mixed Level'),
    ]
    
    TARGET_AUDIENCE_CHOICES = [
        ('beginners', 'Beginners'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('competitive_exam', 'Competitive Exam Aspirants'),
        ('school_students', 'School Students'),
        ('college_students', 'College Students'),
        ('professionals', 'Working Professionals'),
        ('general', 'General Audience'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Enhanced organization and classification
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='exams', null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True)
    exam_type = models.CharField(max_length=50, choices=EXAM_TYPE_CHOICES, blank=True)
    
    # Enhanced Organization
    subject = models.CharField(max_length=100, blank=True, help_text="Specific subject")
    topic = models.CharField(max_length=100, blank=True, help_text="Main topic")
    subtopic = models.CharField(max_length=100, blank=True, help_text="Subtopic")
    
    # Difficulty and Target
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVEL_CHOICES, default='intermediate')
    target_audience = models.CharField(max_length=50, choices=TARGET_AUDIENCE_CHOICES, default='general')
    
    # Language and Location
    language = models.CharField(max_length=50, default='english', help_text="Primary language")
    state_specific = models.CharField(max_length=100, blank=True, help_text="State-specific content (if any)")
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True, help_text="Custom fields for specific needs")
    
    # Settings
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_exams')
    year = models.IntegerField(null=True, blank=True, help_text="Year of exam or creation")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Featured exams appear first")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exams'
        ordering = ['-created_at']
    
    @property
    def published_tests_count(self):
        """Return count of published tests for this exam"""
        return self.tests.filter(is_published=True).count()


class TestSelectionRule(models.Model):
    """Model to store question selection rules for tests"""
    SELECTION_MODES = [
        ('random', 'Random Selection'),
        ('rule_based', 'Rule-Based Selection'),
        ('manual', 'Manual Selection'),
        ('hybrid', 'Hybrid Selection')
    ]
    
    test = models.OneToOneField('Test', on_delete=models.CASCADE, related_name='selection_rule')
    
    # Selection mode
    selection_mode = models.CharField(max_length=20, choices=SELECTION_MODES, default='random')
    
    # Total questions to select
    total_questions = models.IntegerField(default=50)
    
    # Distribution rules (JSON)
    difficulty_distribution = models.JSONField(default=dict, help_text='{"basic": 30, "intermediate": 50, "advanced": 20}')
    category_distribution = models.JSONField(default=dict, help_text='{"mathematics": 25, "physics": 25, ...}')
    question_type_distribution = models.JSONField(default=dict, help_text='{"mcq": 70, "essay": 30}')
    
    # Filters
    year_range = models.JSONField(default=dict, help_text='{"start": 2020, "end": 2024}')
    included_topics = models.JSONField(default=list)
    excluded_topics = models.JSONField(default=list)
    included_banks = models.JSONField(default=list, help_text='List of question bank IDs')
    excluded_questions = models.JSONField(default=list, help_text='Already used question IDs')
    
    # Advanced rules
    ensure_topic_coverage = models.BooleanField(default=True)
    avoid_duplicates_from_attempts = models.BooleanField(default=True)
    priority_new_questions = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_selection_rules'
    
    def __str__(self):
        return f"Selection Rule for {self.test.title}"


class SelectionRuleTemplate(models.Model):
    """Reusable templates for question selection rules"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='selection_templates')
    
    # Copy all rule fields from TestSelectionRule
    selection_mode = models.CharField(max_length=20, choices=TestSelectionRule.SELECTION_MODES, default='random')
    total_questions = models.IntegerField(default=50)
    difficulty_distribution = models.JSONField(default=dict)
    category_distribution = models.JSONField(default=dict)
    question_type_distribution = models.JSONField(default=dict)
    year_range = models.JSONField(default=dict)
    included_topics = models.JSONField(default=list)
    excluded_topics = models.JSONField(default=list)
    ensure_topic_coverage = models.BooleanField(default=True)
    avoid_duplicates_from_attempts = models.BooleanField(default=True)
    priority_new_questions = models.BooleanField(default=False)
    
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'selection_rule_templates'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Test(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_minutes = models.IntegerField()
    total_marks = models.IntegerField()
    pass_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=40.00)
    
    # Test settings
    is_published = models.BooleanField(default=False)
    randomize_questions = models.BooleanField(default=False)
    show_result_immediately = models.BooleanField(default=True)
    allow_review = models.BooleanField(default=True)
    max_attempts = models.IntegerField(default=1)
    
    # Scheduling
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tests'
        ordering = ['-created_at']


class TestSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'test_sections'
        ordering = ['order']


class TestAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='test_attempts')
    attempt_number = models.IntegerField(default=1)  # Track which attempt this is
    
    status = models.CharField(max_length=20, choices=[
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('evaluated', 'Evaluated'),
        ('expired', 'Expired')
    ], default='in_progress')
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)
    
    total_questions = models.IntegerField(default=0)
    attempted_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    marks_obtained = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'test_attempts'
        # Removed unique_together to allow multiple attempts per user per test


class Organization(models.Model):
    ORGANIZATION_TYPES = [
        ('government', 'Government'),
        ('private', 'Private'),
        ('university', 'University'),
        ('board', 'Education Board'),
        ('psu', 'Public Sector Undertaking'),
        ('other', 'Other')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    short_name = models.CharField(max_length=50, blank=True)
    organization_type = models.CharField(max_length=20, choices=ORGANIZATION_TYPES, default='government')
    logo = models.ImageField(upload_to='organization_logos/', null=True, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    
    # Contact Information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Meta Information
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_organizations')
    
    class Meta:
        db_table = 'organizations'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ExamMetadata(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='metadata')
    
    # Important Dates
    notification_date = models.DateField(null=True, blank=True)
    form_start_date = models.DateTimeField(null=True, blank=True)
    form_end_date = models.DateTimeField(null=True, blank=True)
    form_extended_date = models.DateTimeField(null=True, blank=True)
    fee_payment_last_date = models.DateTimeField(null=True, blank=True)
    correction_window_start = models.DateTimeField(null=True, blank=True)
    correction_window_end = models.DateTimeField(null=True, blank=True)
    admit_card_date = models.DateField(null=True, blank=True)
    exam_start_date = models.DateField(null=True, blank=True)
    exam_end_date = models.DateField(null=True, blank=True)
    result_date = models.DateField(null=True, blank=True)
    
    # Eligibility & Fees
    min_age = models.IntegerField(null=True, blank=True)
    max_age = models.IntegerField(null=True, blank=True)
    eligibility_criteria = models.TextField(blank=True)
    
    # Fee Structure (stored as JSON for flexibility)
    fee_structure = models.JSONField(default=dict, blank=True)
    # Example: {"general": 1000, "obc": 750, "sc_st": 500, "female": 500}
    
    # Links
    official_notification_url = models.URLField(blank=True)
    syllabus_url = models.URLField(blank=True)
    apply_online_url = models.URLField(blank=True)
    
    # Additional flexible data
    custom_fields = models.JSONField(default=dict, blank=True)
    
    # Tags for better organization
    tags = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exam_metadata'


class Syllabus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='syllabus')
    description = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to='syllabus_pdfs/', null=True, blank=True)
    total_marks = models.IntegerField(null=True, blank=True)
    exam_pattern = models.TextField(blank=True)
    
    # Enhanced fields for syllabus tracking
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    total_topics = models.IntegerField(default=0)
    estimated_hours = models.IntegerField(default=0, help_text="Total estimated study hours")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_syllabi')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'syllabi'
        verbose_name_plural = 'Syllabi'
    
    def __str__(self):
        return f"Syllabus for {self.exam.name}"
    
    def calculate_total_topics(self):
        """Calculate total number of topics in the syllabus"""
        return self.nodes.count()
    
    def get_root_nodes(self):
        """Get all root level nodes (topics without parent)"""
        return self.nodes.filter(parent=None).order_by('order')


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    weightage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    topics = models.JSONField(default=list, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'subjects'
        ordering = ['order', 'name']


class SyllabusNode(models.Model):
    """Hierarchical structure for syllabus topics and subtopics"""
    NODE_TYPE_CHOICES = [
        ('unit', 'Unit'),
        ('chapter', 'Chapter'),
        ('topic', 'Topic'),
        ('subtopic', 'Subtopic'),
        ('concept', 'Concept'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name='nodes')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    node_type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES, default='topic')
    
    order = models.IntegerField(default=0, help_text="Order within parent level")
    depth_level = models.IntegerField(default=0, help_text="0 for root, increments for children")
    
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    weightage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, 
        help_text="Weightage in exam (percentage)"
    )
    
    is_optional = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    reference_materials = models.JSONField(default=list, blank=True, help_text="List of reference links/books")
    tags = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'syllabus_nodes'
        ordering = ['depth_level', 'order', 'title']
        indexes = [
            models.Index(fields=['syllabus', 'parent', 'order']),
            models.Index(fields=['syllabus', 'depth_level']),
        ]
        
    def __str__(self):
        return f"{'  ' * self.depth_level}{self.title}"
    
    def save(self, *args, **kwargs):
        if self.parent:
            self.depth_level = self.parent.depth_level + 1
            self.syllabus = self.parent.syllabus
        else:
            self.depth_level = 0
        super().save(*args, **kwargs)
    
    def get_children(self):
        """Get immediate children ordered"""
        return self.children.filter(is_active=True).order_by('order')
    
    def get_all_descendants(self):
        """Get all descendants recursively"""
        descendants = []
        for child in self.get_children():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def get_breadcrumb(self):
        """Get breadcrumb path from root to this node"""
        breadcrumb = []
        node = self
        while node:
            breadcrumb.insert(0, node)
            node = node.parent
        return breadcrumb


class StudentSyllabusProgress(models.Model):
    """Track individual student's progress on syllabus nodes"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('revision', 'Revision'),
        ('skipped', 'Skipped'),
    ]
    
    CONFIDENCE_CHOICES = [
        (1, 'Very Low'),
        (2, 'Low'),
        (3, 'Medium'),
        (4, 'High'),
        (5, 'Very High'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='syllabus_progress')
    node = models.ForeignKey(SyllabusNode, on_delete=models.CASCADE, related_name='student_progress')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    progress_percentage = models.IntegerField(default=0)
    confidence_level = models.IntegerField(choices=CONFIDENCE_CHOICES, default=3)
    
    study_hours = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    revision_count = models.IntegerField(default=0)
    
    notes = models.TextField(blank=True)
    bookmarks = models.JSONField(default=list, blank=True, help_text="Personal bookmarks/resources")
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_revised_at = models.DateTimeField(null=True, blank=True)
    
    test_ready = models.BooleanField(default=False, help_text="Ready to take test on this topic")
    test_scores = models.JSONField(default=list, blank=True, help_text="List of test scores for this topic")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_syllabus_progress'
        unique_together = ['student', 'node']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['student', 'node', 'status']),
        ]
        
    def __str__(self):
        return f"{self.student.username} - {self.node.title} ({self.progress_percentage}%)"
    
    def mark_completed(self):
        """Mark the node as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.progress_percentage = 100
        self.completed_at = timezone.now()
        if self.confidence_level >= 4:
            self.test_ready = True
        self.save()
    
    def mark_revision(self):
        """Mark for revision"""
        from django.utils import timezone
        self.status = 'revision'
        self.revision_count += 1
        self.last_revised_at = timezone.now()
        self.save()
    
    def update_progress(self, percentage):
        """Update progress percentage and status accordingly"""
        from django.utils import timezone
        self.progress_percentage = percentage
        if percentage == 0:
            self.status = 'not_started'
        elif percentage == 100:
            self.status = 'completed'
            self.completed_at = timezone.now()
        else:
            self.status = 'in_progress'
            if not self.started_at:
                self.started_at = timezone.now()
        self.save()
    
    def calculate_readiness_score(self):
        """Calculate test readiness score based on multiple factors"""
        score = 0
        score += self.progress_percentage * 0.4  # 40% weight to progress
        score += self.confidence_level * 20 * 0.3  # 30% weight to confidence
        score += min(self.revision_count * 10, 30)  # 30% weight to revisions (max 3 revisions)
        return round(score, 1)


class LearningContent(models.Model):
    """Enterprise-grade learning content management system"""
    LEVEL_CHOICES = [
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'), 
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('theory', 'Theory'),
        ('example', 'Example'),
        ('exercise', 'Exercise'),
        ('simulation', 'Interactive Simulation'),
        ('code', 'Code Playground'),
        ('assessment', 'Assessment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node = models.ForeignKey(SyllabusNode, on_delete=models.CASCADE, related_name='learning_content')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="Rich HTML content with LaTeX support")
    interactive_data = models.JSONField(default=dict, blank=True, help_text="Configuration for interactive elements")
    
    # Content metadata
    estimated_read_time = models.IntegerField(default=5, help_text="Minutes to complete")
    order = models.IntegerField(default=0)
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Authoring
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_ai_generated = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    avg_completion_time = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    difficulty_rating = models.DecimalField(max_digits=3, decimal_places=2, default=3.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_content'
        ordering = ['level', 'order']
        indexes = [
            models.Index(fields=['node', 'level', 'order']),
            models.Index(fields=['content_type', 'is_approved']),
        ]
        
    def __str__(self):
        return f"{self.node.title} - {self.level} - {self.title}"


class InteractiveElement(models.Model):
    """Interactive learning components - simulations, visualizations, code playgrounds"""
    ELEMENT_TYPE_CHOICES = [
        ('graph', 'Interactive Graph'),
        ('simulation', 'Physics/Math Simulation'),
        ('code_editor', 'Code Playground'),
        ('formula_builder', 'Formula Constructor'),
        ('drag_drop', 'Drag & Drop Exercise'),
        ('slider_demo', 'Parameter Slider Demo'),
        ('animation', 'Step-by-Step Animation'),
        ('quiz_interactive', 'Interactive Quiz'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(LearningContent, on_delete=models.CASCADE, related_name='interactive_elements')
    
    element_type = models.CharField(max_length=20, choices=ELEMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Configuration data for different interactive types
    config_data = models.JSONField(default=dict, help_text="Element-specific configuration")
    # Example: {"x_range": [-10, 10], "y_range": [-5, 5], "functions": ["sin(x)", "cos(x)"]}
    
    # Code for interactive elements
    javascript_code = models.TextField(blank=True, help_text="Custom JavaScript for interactivity")
    python_code = models.TextField(blank=True, help_text="Python code for code playground")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'interactive_elements'
        
    def __str__(self):
        return f"{self.title} ({self.element_type})"


class Assessment(models.Model):
    """Advanced assessment system with spaced repetition"""
    QUESTION_TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('numerical', 'Numerical Answer'),
        ('short_answer', 'Short Answer'),
        ('code_completion', 'Code Completion'),
        ('drag_drop', 'Drag & Drop'),
        ('formula_input', 'Formula Input'),
    ]
    
    SCHEDULE_TYPE_CHOICES = [
        ('immediate', 'Immediate (After Content)'),
        ('spaced_1d', '1 Day Later'),
        ('spaced_3d', '3 Days Later'),
        ('spaced_1w', '1 Week Later'),
        ('spaced_1m', '1 Month Later'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(LearningContent, on_delete=models.CASCADE, related_name='assessments')
    
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES)
    
    question_text = models.TextField()
    question_data = models.JSONField(default=dict, help_text="Question-specific data (options, correct_answer, etc.)")
    
    # Scoring
    max_points = models.IntegerField(default=1)
    difficulty_weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    
    # Analytics
    total_attempts = models.IntegerField(default=0)
    correct_attempts = models.IntegerField(default=0)
    avg_time_taken = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assessments'
        
    @property
    def success_rate(self):
        if self.total_attempts == 0:
            return 0
        return round((self.correct_attempts / self.total_attempts) * 100, 1)
        
    def __str__(self):
        return f"Assessment: {self.question_text[:50]}..."


class StudentLearningProgress(models.Model):
    """Track detailed student progress through learning content"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('mastered', 'Mastered'),
        ('needs_review', 'Needs Review'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_progress')
    content = models.ForeignKey(LearningContent, on_delete=models.CASCADE, related_name='student_progress')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    progress_percentage = models.IntegerField(default=0)
    
    # Time tracking
    time_spent = models.DecimalField(max_digits=6, decimal_places=1, default=0, help_text="Minutes spent")
    session_count = models.IntegerField(default=0)
    
    # Performance metrics
    understanding_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="0-100 based on assessments")
    retention_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Spaced repetition performance")
    
    # Learning behavior
    notes = models.TextField(blank=True)
    bookmarks = models.JSONField(default=list, blank=True)
    difficulty_rating = models.IntegerField(null=True, blank=True, help_text="Student's difficulty rating 1-5")
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_learning_progress'
        unique_together = ['student', 'content']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['content', 'status']),
        ]
        
    def __str__(self):
        return f"{self.student.username} - {self.content.title} ({self.progress_percentage}%)"


class AssessmentAttempt(models.Model):
    """Track individual assessment attempts with spaced repetition"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessment_attempts')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    
    student_answer = models.JSONField(help_text="Student's answer data")
    is_correct = models.BooleanField()
    points_earned = models.DecimalField(max_digits=5, decimal_places=2)
    time_taken = models.DecimalField(max_digits=5, decimal_places=1, help_text="Seconds")
    
    # Spaced repetition scheduling
    scheduled_for = models.DateTimeField(help_text="When this assessment is scheduled")
    next_review_date = models.DateTimeField(null=True, blank=True)
    review_interval = models.IntegerField(default=1, help_text="Days until next review")
    ease_factor = models.DecimalField(max_digits=3, decimal_places=2, default=2.5, help_text="Spaced repetition ease")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assessment_attempts'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.student.username} - {self.assessment} - {'✓' if self.is_correct else '✗'}"


class LearningAnalytics(models.Model):
    """Advanced analytics for learning content performance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.OneToOneField(LearningContent, on_delete=models.CASCADE, related_name='analytics')
    
    # Engagement metrics
    total_views = models.IntegerField(default=0)
    unique_viewers = models.IntegerField(default=0)
    avg_time_spent = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Learning effectiveness
    avg_understanding_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_difficulty_rating = models.DecimalField(max_digits=3, decimal_places=2, default=3.0)
    improvement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Content quality indicators
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="% who leave without interaction")
    engagement_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_analytics'
        
    def __str__(self):
        return f"Analytics: {self.content.title}"
