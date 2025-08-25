from django.contrib import admin
from django.utils.html import format_html
from .models import GlobalSubject, GlobalTopic, TopicTemplate, SubjectExpertise, TopicUsageLog, SyllabusTopicMapping, TopicImportTemplate


@admin.register(GlobalSubject)
class GlobalSubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'level', 'get_topic_count', 'popularity_score', 'is_active', 'is_featured']
    list_filter = ['category', 'level', 'is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['popularity_score', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'code', 'description', 'category', 'level']
        }),
        ('Visual & Organization', {
            'fields': ['icon', 'color_code', 'is_active', 'is_featured']
        }),
        ('References & Standards', {
            'fields': ['reference_standards', 'external_links'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['popularity_score', 'created_by', 'approved_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_topic_count(self, obj):
        count = obj.get_topic_count()
        return format_html('<span style="font-weight: bold; color: #10b981;">{}</span>', count)
    get_topic_count.short_description = 'Topics'


@admin.register(GlobalTopic)
class GlobalTopicAdmin(admin.ModelAdmin):
    list_display = ['get_indented_title', 'subject', 'topic_type', 'difficulty', 'priority', 'usage_count', 'is_active', 'is_approved']
    list_filter = ['subject', 'topic_type', 'difficulty', 'priority', 'is_active', 'is_approved', 'is_template']
    search_fields = ['title', 'description', 'keywords']
    readonly_fields = ['depth_level', 'path', 'usage_count', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['subject', 'parent', 'title', 'description', 'topic_type']
        }),
        ('Hierarchy & Order', {
            'fields': ['depth_level', 'order', 'path'],
            'classes': ['collapse']
        }),
        ('Characteristics', {
            'fields': ['difficulty', 'priority', 'estimated_hours']
        }),
        ('Content & Resources', {
            'fields': ['learning_objectives', 'prerequisites', 'keywords', 'reference_materials'],
            'classes': ['collapse']
        }),
        ('Usage & Quality', {
            'fields': ['is_active', 'is_template', 'is_approved', 'approval_notes', 'usage_count']
        }),
        ('Metadata', {
            'fields': ['created_by', 'approved_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_indented_title(self, obj):
        indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * obj.depth_level
        status_color = "#10b981" if obj.is_approved else "#fbbf24" if obj.is_active else "#ef4444"
        return format_html(
            '{}<span style="font-weight: bold; color: {};">{}</span>',
            indent, status_color, obj.title
        )
    get_indented_title.short_description = 'Title (Hierarchy)'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subject', 'parent')


@admin.register(TopicTemplate)
class TopicTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'template_type', 'get_topic_count', 'usage_count', 'is_active', 'is_public']
    list_filter = ['template_type', 'is_active', 'is_public', 'subject__category']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Template Information', {
            'fields': ['name', 'description', 'template_type', 'subject']
        }),
        ('Topic Structure', {
            'fields': ['root_topics', 'structure']
        }),
        ('Settings', {
            'fields': ['is_active', 'is_public', 'usage_count']
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_topic_count(self, obj):
        count = obj.get_topic_count()
        return format_html('<span style="font-weight: bold; color: #667eea;">{}</span>', count)
    get_topic_count.short_description = 'Topics'


@admin.register(SubjectExpertise)
class SubjectExpertiseAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'expertise_level', 'verified', 'topics_created', 'topics_approved', 'content_contributions']
    list_filter = ['expertise_level', 'verified', 'subject__category']
    search_fields = ['user__username', 'user__email', 'subject__name', 'credentials']
    readonly_fields = ['topics_created', 'topics_approved', 'content_contributions', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Expertise Information', {
            'fields': ['user', 'subject', 'expertise_level', 'credentials', 'verified']
        }),
        ('Contribution Stats', {
            'fields': ['topics_created', 'topics_approved', 'content_contributions'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]


@admin.register(TopicUsageLog)
class TopicUsageLogAdmin(admin.ModelAdmin):
    list_display = ['global_topic', 'exam_id', 'used_by', 'has_customizations', 'created_at']
    list_filter = ['created_at', 'global_topic__subject']
    search_fields = ['global_topic__title', 'exam_id', 'used_by__username']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Usage Information', {
            'fields': ['global_topic', 'exam_id', 'used_by']
        }),
        ('Customizations', {
            'fields': ['customizations']
        }),
        ('Metadata', {
            'fields': ['created_at'],
            'classes': ['collapse']
        })
    ]
    
    def has_customizations(self, obj):
        has_custom = bool(obj.customizations)
        color = "#10b981" if has_custom else "#94a3b8"
        text = "Yes" if has_custom else "No"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, text)
    has_customizations.short_description = 'Customized'


@admin.register(SyllabusTopicMapping)
class SyllabusTopicMappingAdmin(admin.ModelAdmin):
    list_display = ['global_topic', 'syllabus_id', 'is_mandatory', 'is_modified', 'created_by', 'created_at']
    list_filter = ['is_mandatory', 'is_modified', 'created_at']
    search_fields = ['global_topic__title', 'syllabus_id', 'custom_title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Mapping Information', {
            'fields': ['global_topic', 'syllabus_id', 'syllabus_node_id']
        }),
        ('Customizations', {
            'fields': ['custom_title', 'custom_description', 'custom_weightage', 'custom_estimated_hours']
        }),
        ('Settings', {
            'fields': ['is_mandatory', 'is_modified', 'modification_notes']
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('global_topic', 'created_by')


@admin.register(TopicImportTemplate)  
class TopicImportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_subject', 'template_type', 'usage_count', 'is_active', 'is_public', 'created_by']
    list_filter = ['template_type', 'is_active', 'is_public', 'source_subject__category']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Template Information', {
            'fields': ['name', 'description', 'template_type', 'source_subject']
        }),
        ('Import Configuration', {
            'fields': ['root_topics', 'include_prerequisites', 'include_subtopics', 'max_depth_level', 'filter_by_difficulty']
        }),
        ('Settings', {
            'fields': ['is_active', 'is_public', 'usage_count']
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('source_subject', 'created_by')