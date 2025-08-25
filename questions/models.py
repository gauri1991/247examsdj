from django.db import models
from django.conf import settings
import uuid


class QuestionBank(models.Model):
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
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True)
    
    # Indian Exam Specific Fields
    exam_type = models.CharField(max_length=50, choices=EXAM_TYPE_CHOICES, blank=True)
    organization = models.CharField(max_length=200, blank=True, help_text="Conducting organization (e.g., UPSC, SSC)")
    year = models.IntegerField(null=True, blank=True, help_text="Year of exam or creation")
    
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
    
    # Question Type Distribution (for analytics)
    question_types_included = models.JSONField(default=list, blank=True, help_text="Types of questions in this bank")
    
    # Settings
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='question_banks')
    is_public = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False, help_text="Featured question banks appear first")
    
    # Default Question Settings
    default_difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVEL_CHOICES, default='intermediate')
    default_marks = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    default_time_per_question = models.IntegerField(null=True, blank=True, help_text="Default time in seconds")
    
    # Statistics
    total_questions = models.IntegerField(default=0)
    avg_difficulty = models.CharField(max_length=20, blank=True)
    usage_count = models.IntegerField(default=0, help_text="Number of times used in tests")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'question_banks'
    
    def __str__(self):
        return self.name
    
    def user_can_access(self, user, permission_type='view'):
        """
        Check if user can access this question bank
        
        Args:
            user: User instance
            permission_type: 'view', 'edit', 'copy', or 'full'
        
        Returns:
            bool: True if user can access with specified permission
        """
        # Admin can access everything
        if user.role == 'admin':
            return True
        
        # Owner can access their own banks
        if self.created_by == user:
            return True
        
        # Public banks can be viewed by everyone
        if self.is_public and permission_type == 'view':
            return True
        
        # Check explicit permissions
        try:
            permission = self.permissions.get(user=user, is_active=True)
            if permission.is_expired:
                return False
            
            if permission_type == 'view':
                return permission.can_view()
            elif permission_type == 'edit':
                return permission.can_edit()
            elif permission_type == 'copy':
                return permission.can_copy()
            elif permission_type == 'full':
                return permission.permission_type == 'full'
        except QuestionBankPermission.DoesNotExist:
            pass
        
        return False


class QuestionBankPermission(models.Model):
    """
    Granular permission system for question banks
    Allows admins to grant specific permissions to teachers for accessing question banks
    """
    PERMISSION_TYPES = [
        ('view', 'View Only'),
        ('edit', 'View & Edit'),
        ('copy', 'View & Copy Questions'),
        ('full', 'Full Access (View, Edit, Copy)'),
    ]
    
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='permissions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='question_bank_permissions')
    permission_type = models.CharField(max_length=10, choices=PERMISSION_TYPES, default='view')
    
    # Permission details
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Leave blank for permanent access")
    
    # Notes
    notes = models.TextField(blank=True, help_text="Admin notes about this permission")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'question_bank_permissions'
        unique_together = ['question_bank', 'user']  # One permission per user per bank
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['question_bank', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} -> {self.question_bank.name} ({self.permission_type})"
    
    @property
    def is_expired(self):
        """Check if permission has expired"""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def can_view(self):
        """Can user view this question bank"""
        return self.is_active and not self.is_expired
    
    def can_edit(self):
        """Can user edit this question bank"""
        return self.can_view() and self.permission_type in ['edit', 'full']
    
    def can_copy(self):
        """Can user copy questions from this bank"""
        return self.can_view() and self.permission_type in ['copy', 'full']


class Question(models.Model):
    QUESTION_TYPES = [
        # Basic Types
        ('mcq', 'Multiple Choice (Single Answer)'),
        ('multi_select', 'Multiple Select (Multiple Answers)'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('essay', 'Essay/Descriptive'),
        
        # Indian Exam Specific Types
        ('statement_reason', 'Statement & Reason'),
        ('assertion_reason', 'Assertion & Reason'),
        ('match_following', 'Match the Following'),
        ('arrangement', 'Arrangement/Sequencing'),
        ('coding_decoding', 'Coding-Decoding'),
        ('analogy', 'Analogy'),
        ('classification', 'Classification/Odd One Out'),
        ('series_completion', 'Series Completion'),
        ('direction_sense', 'Direction Sense'),
        ('blood_relations', 'Blood Relations'),
        ('ranking_arrangement', 'Ranking & Arrangement'),
        ('syllogism', 'Syllogism'),
        ('data_sufficiency', 'Data Sufficiency'),
        ('reading_comprehension', 'Reading Comprehension'),
        ('cloze_test', 'Cloze Test'),
        ('para_jumbles', 'Para Jumbles'),
        ('error_spotting', 'Error Spotting'),
        ('sentence_improvement', 'Sentence Improvement'),
        ('idioms_phrases', 'Idioms & Phrases'),
        ('synonyms_antonyms', 'Synonyms & Antonyms'),
        ('one_word_substitution', 'One Word Substitution'),
        ('mathematical_calculation', 'Mathematical Calculation'),
        ('data_interpretation', 'Data Interpretation'),
        ('puzzle', 'Puzzles'),
        ('seating_arrangement', 'Seating Arrangement'),
        ('calendar', 'Calendar Problems'),
        ('clock', 'Clock Problems'),
        ('number_system', 'Number System'),
        ('percentage', 'Percentage'),
        ('profit_loss', 'Profit & Loss'),
        ('simple_compound_interest', 'Simple & Compound Interest'),
        ('time_work', 'Time & Work'),
        ('speed_distance_time', 'Speed, Distance & Time'),
        ('geometry', 'Geometry'),
        ('mensuration', 'Mensuration'),
        ('probability', 'Probability'),
        ('permutation_combination', 'Permutation & Combination'),
        ('set_theory', 'Set Theory'),
        ('venn_diagram', 'Venn Diagram'),
        ('pie_chart', 'Pie Chart'),
        ('bar_graph', 'Bar Graph'),
        ('line_graph', 'Line Graph'),
        ('table_chart', 'Table Chart'),
        ('case_study', 'Case Study'),
        ('situation_based', 'Situation Based'),
        ('current_affairs', 'Current Affairs'),
        ('static_gk', 'Static General Knowledge'),
        ('other', 'Other'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('basic', '🟢 Basic'),
        ('intermediate', '🟡 Intermediate'),
        ('advanced', '🟠 Advanced'),
        ('expert', '🔴 Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='intermediate')
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    negative_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Time settings
    time_limit = models.IntegerField(null=True, blank=True, help_text="Time limit in seconds")
    
    # For fill in the blank questions
    correct_answers = models.JSONField(default=list, blank=True, help_text="List of acceptable answers")
    case_sensitive = models.BooleanField(default=False)
    
    # For essay questions
    expected_answer = models.TextField(blank=True)
    min_words = models.IntegerField(null=True, blank=True)
    max_words = models.IntegerField(null=True, blank=True)
    
    # Metadata
    topic = models.CharField(max_length=100, blank=True)
    subtopic = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    explanation = models.TextField(blank=True)
    
    # Media
    image = models.ImageField(upload_to='questions/', blank=True, null=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_questions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'questions'


class QuestionOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'question_options'
        ordering = ['order']


class TestQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey('exams.Test', on_delete=models.CASCADE, related_name='test_questions')
    section = models.ForeignKey('exams.TestSection', on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    marks = models.IntegerField()
    
    class Meta:
        db_table = 'test_questions'
        ordering = ['order']
        unique_together = ['test', 'question']


class UserAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_attempt = models.ForeignKey('exams.TestAttempt', on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    # For MCQ/Multi-select
    selected_options = models.ManyToManyField(QuestionOption, blank=True)
    
    # For text answers (fill blank, essay)
    text_answer = models.TextField(blank=True)
    
    # For true/false
    boolean_answer = models.BooleanField(null=True, blank=True)
    
    is_marked_for_review = models.BooleanField(default=False)
    time_spent_seconds = models.IntegerField(default=0)
    
    # Evaluation
    is_correct = models.BooleanField(null=True, blank=True)
    marks_obtained = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    answered_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_answers'
        unique_together = ['test_attempt', 'question']
