"""
Global Knowledge Taxonomy Models
Centralized subject and topic management system
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class GlobalSubject(models.Model):
    """Master subject database - reusable across all exams and content"""
    
    CATEGORY_CHOICES = [
        ('science', 'Science'),
        ('mathematics', 'Mathematics'),
        ('language', 'Language'),
        ('social_science', 'Social Science'),
        ('engineering', 'Engineering'),
        ('medical', 'Medical'),
        ('commerce', 'Commerce'),
        ('arts', 'Arts'),
        ('computer_science', 'Computer Science'),
        ('general_knowledge', 'General Knowledge'),
    ]
    
    LEVEL_CHOICES = [
        ('elementary', 'Elementary (1-5)'),
        ('middle', 'Middle School (6-8)'),
        ('high_school', 'High School (9-12)'),
        ('undergraduate', 'Undergraduate'),
        ('postgraduate', 'Postgraduate'),
        ('competitive', 'Competitive Exams'),
        ('professional', 'Professional'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code like MATH, PHYS, ENG")
    description = models.TextField()
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    
    # Visual and organizational
    icon = models.CharField(max_length=50, blank=True, help_text="Emoji or icon class")
    color_code = models.CharField(max_length=7, default="#3B82F6", help_text="Hex color code")
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    popularity_score = models.IntegerField(default=0, help_text="Usage count across exams")
    
    # Relationships
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_global_subjects'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_global_subjects'
    )
    
    # References and standards
    reference_standards = models.JSONField(
        default=list, 
        blank=True, 
        help_text="Educational standards this subject aligns with"
    )
    external_links = models.JSONField(
        default=list, 
        blank=True, 
        help_text="Reference links for subject information"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'global_subjects'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'level']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['popularity_score']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_topic_count(self):
        """Get total number of topics under this subject"""
        return self.global_topics.filter(is_active=True).count()
    
    def get_usage_count(self):
        """Get number of exams using this subject"""
        return self.exam_subjects.count()
    
    def increment_popularity(self):
        """Increment popularity score when used"""
        self.popularity_score += 1
        self.save(update_fields=['popularity_score'])


class GlobalTopic(models.Model):
    """Master topic templates - reusable topic structures"""
    
    TOPIC_TYPE_CHOICES = [
        ('unit', 'Unit'),
        ('chapter', 'Chapter'), 
        ('topic', 'Topic'),
        ('subtopic', 'Subtopic'),
        ('concept', 'Concept'),
        ('skill', 'Skill'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('easy', 'Easy'),
        ('medium', 'Medium'), 
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(GlobalSubject, on_delete=models.CASCADE, related_name='global_topics')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    # Basic Information
    title = models.CharField(max_length=255)
    description = models.TextField()
    topic_type = models.CharField(max_length=20, choices=TOPIC_TYPE_CHOICES, default='topic')
    
    # Hierarchy
    depth_level = models.IntegerField(default=0, help_text="0 for root topics")
    order = models.IntegerField(default=0, help_text="Order within same level")
    path = models.CharField(max_length=500, blank=True, help_text="Hierarchical path like /math/algebra/linear-equations")
    
    # Characteristics
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Content and Resources
    learning_objectives = models.JSONField(
        default=list, 
        blank=True, 
        help_text="List of learning objectives"
    )
    prerequisites = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        related_name='dependent_topics',
        help_text="Topics that should be learned before this one"
    )
    keywords = models.JSONField(
        default=list, 
        blank=True, 
        help_text="Search keywords and tags"
    )
    reference_materials = models.JSONField(
        default=list, 
        blank=True, 
        help_text="Books, links, videos, etc."
    )
    
    # Usage tracking
    is_active = models.BooleanField(default=True)
    is_template = models.BooleanField(default=True, help_text="Can be used as template for exam syllabi")
    usage_count = models.IntegerField(default=0, help_text="Number of times used in syllabi")
    
    # Quality control
    is_approved = models.BooleanField(default=False)
    approval_notes = models.TextField(blank=True)
    
    # Relationships
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_global_topics'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_global_topics'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'global_topics'
        ordering = ['subject', 'depth_level', 'order', 'title']
        unique_together = ['subject', 'parent', 'title']
        indexes = [
            models.Index(fields=['subject', 'parent', 'order']),
            models.Index(fields=['subject', 'depth_level']),
            models.Index(fields=['is_active', 'is_template', 'is_approved']),
            models.Index(fields=['difficulty', 'priority']),
            models.Index(fields=['usage_count']),
        ]
    
    def __str__(self):
        indent = "  " * self.depth_level
        return f"{indent}{self.title} ({self.subject.code})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate depth level and path
        if self.parent:
            self.depth_level = self.parent.depth_level + 1
            self.subject = self.parent.subject
            parent_path = self.parent.path or f"/{self.parent.subject.code.lower()}"
            self.path = f"{parent_path}/{self.title.lower().replace(' ', '-')}"
        else:
            self.depth_level = 0
            self.path = f"/{self.subject.code.lower()}/{self.title.lower().replace(' ', '-')}"
        
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
        """Get breadcrumb path from root to this topic"""
        breadcrumb = []
        topic = self
        while topic:
            breadcrumb.insert(0, topic)
            topic = topic.parent
        return breadcrumb
    
    def increment_usage(self):
        """Increment usage count when used in syllabus"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
        # Also increment subject popularity
        self.subject.increment_popularity()
    
    def get_suggested_duration(self):
        """Get suggested study duration based on difficulty and content"""
        base_hours = float(self.estimated_hours)
        difficulty_multiplier = {
            'beginner': 0.8,
            'easy': 1.0,
            'medium': 1.2,
            'hard': 1.5,
            'expert': 2.0
        }
        return base_hours * difficulty_multiplier.get(self.difficulty, 1.0)


class TopicTemplate(models.Model):
    """Predefined topic structures for common subjects"""
    
    TEMPLATE_TYPE_CHOICES = [
        ('standard', 'Standard Curriculum'),
        ('competitive', 'Competitive Exam'),
        ('custom', 'Custom Template'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    
    subject = models.ForeignKey(GlobalSubject, on_delete=models.CASCADE, related_name='templates')
    root_topics = models.ManyToManyField(GlobalTopic, related_name='templates', blank=True)
    
    # Template structure (JSON representation of topic hierarchy)
    structure = models.JSONField(
        default=dict, 
        help_text="JSON structure defining the complete topic hierarchy"
    )
    
    # Usage and quality
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'topic_templates'
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.subject.name})"
    
    def get_topic_count(self):
        """Count total topics in template"""
        return len(self._flatten_structure(self.structure))
    
    def _flatten_structure(self, structure, count=0):
        """Recursively count topics in structure"""
        topics = []
        if isinstance(structure, dict):
            topics.append(structure)
            for child in structure.get('children', []):
                topics.extend(self._flatten_structure(child))
        elif isinstance(structure, list):
            for item in structure:
                topics.extend(self._flatten_structure(item))
        return topics


class SubjectExpertise(models.Model):
    """Track user expertise in subjects for content quality"""
    
    EXPERTISE_LEVEL_CHOICES = [
        (1, 'Beginner'),
        (2, 'Basic'),
        (3, 'Intermediate'),
        (4, 'Advanced'),
        (5, 'Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey(GlobalSubject, on_delete=models.CASCADE)
    
    expertise_level = models.IntegerField(choices=EXPERTISE_LEVEL_CHOICES)
    credentials = models.TextField(blank=True, help_text="Qualifications, experience, etc.")
    verified = models.BooleanField(default=False)
    
    # Contribution tracking
    topics_created = models.IntegerField(default=0)
    topics_approved = models.IntegerField(default=0)
    content_contributions = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subject_expertise'
        unique_together = ['user', 'subject']
    
    def __str__(self):
        return f"{self.user.username} - {self.subject.name} (Level {self.expertise_level})"


class TopicUsageLog(models.Model):
    """Log topic usage across exams for analytics"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    global_topic = models.ForeignKey(GlobalTopic, on_delete=models.CASCADE)
    exam_id = models.UUIDField()  # Reference to exam without direct FK
    used_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    customizations = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Custom modifications made to the topic"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'topic_usage_logs'
        indexes = [
            models.Index(fields=['global_topic', 'exam_id']),
            models.Index(fields=['created_at']),
        ]


# Integration models for connecting with existing syllabus system

class SyllabusTopicMapping(models.Model):
    """Maps global topics to specific syllabus nodes for exam customization"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Using string references to avoid circular imports
    # syllabus = models.ForeignKey('exams.Syllabus', on_delete=models.CASCADE, related_name='global_topic_mappings')
    # syllabus_node = models.ForeignKey('exams.SyllabusNode', on_delete=models.CASCADE, related_name='global_topic_mapping')
    global_topic = models.ForeignKey(GlobalTopic, on_delete=models.CASCADE, related_name='syllabus_mappings')
    
    # Reference IDs to avoid circular imports
    syllabus_id = models.UUIDField()
    syllabus_node_id = models.UUIDField()
    
    # Exam-specific customizations
    custom_title = models.CharField(max_length=255, blank=True, help_text="Override title if needed")
    custom_description = models.TextField(blank=True, help_text="Exam-specific description")
    custom_weightage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    custom_estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Integration metadata
    is_mandatory = models.BooleanField(default=True, help_text="Required for this exam")
    is_modified = models.BooleanField(default=False, help_text="Has exam-specific modifications")
    modification_notes = models.TextField(blank=True, help_text="Notes about modifications made")
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'syllabus_topic_mappings'
        unique_together = ['syllabus_node_id', 'global_topic']
        indexes = [
            models.Index(fields=['syllabus_id', 'global_topic']),
            models.Index(fields=['is_mandatory', 'is_modified']),
        ]
    
    def __str__(self):
        return f"Mapping: {self.global_topic.title} → Syllabus {self.syllabus_id}"
    
    def get_effective_title(self):
        """Get title to display - custom or original"""
        return self.custom_title if self.custom_title else self.global_topic.title
    
    def get_effective_description(self):
        """Get description to display - custom or original"""
        return self.custom_description if self.custom_description else self.global_topic.description


class TopicImportTemplate(models.Model):
    """Templates for importing topic hierarchies from global taxonomy"""
    
    TEMPLATE_TYPE_CHOICES = [
        ('full', 'Complete Topic Hierarchy'),
        ('selective', 'Selected Topics Only'),
        ('condensed', 'Condensed Version'),
        ('extended', 'Extended with Prerequisites'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    
    # Source configuration
    source_subject = models.ForeignKey(GlobalSubject, on_delete=models.CASCADE, related_name='import_templates')
    root_topics = models.ManyToManyField(GlobalTopic, related_name='import_templates', blank=True)
    
    # Import rules
    include_prerequisites = models.BooleanField(default=False)
    include_subtopics = models.BooleanField(default=True)
    max_depth_level = models.IntegerField(default=5, help_text="Maximum depth to import")
    filter_by_difficulty = models.JSONField(default=list, blank=True, help_text="Difficulty levels to include")
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'topic_import_templates'
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.source_subject.name})"