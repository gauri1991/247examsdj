from rest_framework import serializers
from .models import GlobalSubject, GlobalTopic, TopicTemplate, SyllabusTopicMapping, TopicImportTemplate


class GlobalSubjectSerializer(serializers.ModelSerializer):
    """Serializer for GlobalSubject model"""
    
    topic_count = serializers.ReadOnlyField(source='get_topic_count')
    usage_count = serializers.ReadOnlyField(source='get_usage_count')
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = GlobalSubject
        fields = [
            'id', 'name', 'code', 'description', 'category', 'level',
            'icon', 'color_code', 'is_active', 'is_featured', 'popularity_score',
            'reference_standards', 'external_links', 'topic_count', 'usage_count',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'popularity_score']


class GlobalTopicListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for topic lists"""
    
    subject_name = serializers.ReadOnlyField(source='subject.name')
    subject_code = serializers.ReadOnlyField(source='subject.code')
    parent_title = serializers.ReadOnlyField(source='parent.title')
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GlobalTopic
        fields = [
            'id', 'title', 'description', 'topic_type', 'difficulty', 'priority',
            'depth_level', 'order', 'estimated_hours', 'usage_count',
            'subject_name', 'subject_code', 'parent_title', 'children_count',
            'is_active', 'is_template', 'is_approved', 'created_at'
        ]
        
    def get_children_count(self, obj):
        return obj.children.filter(is_active=True).count()


class GlobalTopicDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual topics"""
    
    subject = GlobalSubjectSerializer(read_only=True)
    subject_id = serializers.UUIDField(write_only=True, required=False)
    parent = GlobalTopicListSerializer(read_only=True)
    parent_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    children = GlobalTopicListSerializer(many=True, read_only=True)
    breadcrumb = serializers.SerializerMethodField()
    prerequisites = GlobalTopicListSerializer(many=True, read_only=True)
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    approved_by_username = serializers.ReadOnlyField(source='approved_by.username')
    
    class Meta:
        model = GlobalTopic
        fields = [
            'id', 'subject', 'subject_id', 'parent', 'parent_id', 'children',
            'title', 'description', 'topic_type', 'depth_level', 'order', 'path',
            'difficulty', 'priority', 'estimated_hours', 'learning_objectives',
            'prerequisites', 'keywords', 'reference_materials', 'usage_count',
            'is_active', 'is_template', 'is_approved', 'approval_notes',
            'breadcrumb', 'created_by', 'created_by_username', 
            'approved_by', 'approved_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'depth_level', 'path', 'usage_count', 'created_at', 'updated_at']
        
    def get_breadcrumb(self, obj):
        """Get hierarchical breadcrumb"""
        breadcrumb = obj.get_breadcrumb()
        return [{'id': str(topic.id), 'title': topic.title} for topic in breadcrumb]
        
    def create(self, validated_data):
        """Create topic with proper subject and parent assignment"""
        subject_id = validated_data.pop('subject_id', None)
        parent_id = validated_data.pop('parent_id', None)
        
        if subject_id:
            validated_data['subject'] = GlobalSubject.objects.get(id=subject_id)
        if parent_id:
            validated_data['parent'] = GlobalTopic.objects.get(id=parent_id)
            
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        """Update topic with proper relationships"""
        subject_id = validated_data.pop('subject_id', None)
        parent_id = validated_data.pop('parent_id', None)
        
        if subject_id:
            validated_data['subject'] = GlobalSubject.objects.get(id=subject_id)
        if parent_id:
            validated_data['parent'] = GlobalTopic.objects.get(id=parent_id)
        elif 'parent_id' in validated_data:  # Explicitly set to None
            validated_data['parent'] = None
            
        return super().update(instance, validated_data)


class TopicHierarchySerializer(serializers.ModelSerializer):
    """Serializer for hierarchical topic representation"""
    
    children = serializers.SerializerMethodField()
    subject_name = serializers.ReadOnlyField(source='subject.name')
    
    class Meta:
        model = GlobalTopic
        fields = [
            'id', 'title', 'description', 'topic_type', 'difficulty', 'priority',
            'depth_level', 'order', 'estimated_hours', 'is_active', 'is_approved',
            'subject_name', 'children'
        ]
        
    def get_children(self, obj):
        """Recursively get children for tree structure"""
        children = obj.get_children()
        return TopicHierarchySerializer(children, many=True, context=self.context).data


class TopicTemplateSerializer(serializers.ModelSerializer):
    """Serializer for TopicTemplate model"""
    
    subject = GlobalSubjectSerializer(read_only=True)
    root_topics = GlobalTopicListSerializer(many=True, read_only=True)
    topic_count = serializers.ReadOnlyField(source='get_topic_count')
    
    class Meta:
        model = TopicTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'subject', 
            'root_topics', 'structure', 'topic_count', 'is_active', 
            'is_public', 'usage_count', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class SyllabusTopicMappingSerializer(serializers.ModelSerializer):
    """Serializer for mapping global topics to syllabus"""
    
    global_topic = GlobalTopicListSerializer(read_only=True)
    effective_title = serializers.ReadOnlyField(source='get_effective_title')
    effective_description = serializers.ReadOnlyField(source='get_effective_description')
    
    class Meta:
        model = SyllabusTopicMapping
        fields = [
            'id', 'global_topic', 'syllabus_id', 'syllabus_node_id',
            'custom_title', 'custom_description', 'custom_weightage', 
            'custom_estimated_hours', 'effective_title', 'effective_description',
            'is_mandatory', 'is_modified', 'modification_notes',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TopicImportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for TopicImportTemplate model"""
    
    source_subject = GlobalSubjectSerializer(read_only=True)
    root_topics = GlobalTopicListSerializer(many=True, read_only=True)
    
    class Meta:
        model = TopicImportTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'source_subject',
            'root_topics', 'include_prerequisites', 'include_subtopics',
            'max_depth_level', 'filter_by_difficulty', 'usage_count',
            'is_active', 'is_public', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class TopicSearchSerializer(serializers.Serializer):
    """Serializer for topic search parameters"""
    
    query = serializers.CharField(required=False, allow_blank=True)
    subject_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    levels = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    topic_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    difficulties = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    priorities = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    is_approved = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    min_hours = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    max_hours = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    depth_level = serializers.IntegerField(required=False)
    ordering = serializers.CharField(required=False, default='title')


class TopicBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on topics"""
    
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('delete', 'Delete'),
        ('update_difficulty', 'Update Difficulty'),
        ('update_priority', 'Update Priority'),
    ]
    
    topic_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    
    # Optional parameters for specific actions
    difficulty = serializers.CharField(required=False)
    priority = serializers.CharField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class TopicStatsSerializer(serializers.Serializer):
    """Serializer for topic statistics"""
    
    total_subjects = serializers.IntegerField()
    total_topics = serializers.IntegerField()
    approved_topics = serializers.IntegerField()
    pending_topics = serializers.IntegerField()
    topics_by_category = serializers.DictField()
    topics_by_level = serializers.DictField()
    topics_by_difficulty = serializers.DictField()
    topics_by_type = serializers.DictField()
    avg_hours_per_topic = serializers.DecimalField(max_digits=6, decimal_places=2)
    popular_subjects = serializers.ListField()
    recent_activity = serializers.ListField()


class TopicRecommendationSerializer(serializers.Serializer):
    """Serializer for topic recommendations"""
    
    topic = GlobalTopicListSerializer()
    score = serializers.FloatField()
    reasons = serializers.ListField(child=serializers.CharField())
    subject_match = serializers.BooleanField()
    difficulty_match = serializers.BooleanField()
    prerequisite_satisfied = serializers.BooleanField()