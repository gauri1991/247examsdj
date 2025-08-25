from django import forms
from .models import PDFDocument, MetadataTemplate

class BulkMetadataEditForm(forms.Form):
    """
    Form for bulk editing metadata across multiple documents
    """
    
    # Basic Information
    title_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
            ('append', 'Append to existing'),
            ('prepend', 'Prepend to existing'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    title_value = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'enhanced-input', 'placeholder': 'New title value'})
    )
    
    description_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
            ('append', 'Append to existing'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    description_value = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={'class': 'enhanced-textarea', 'rows': 3, 'placeholder': 'New description'})
    )
    
    # Exam Information
    exam_type_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    exam_type_value = forms.ChoiceField(
        choices=[('', 'Select exam type')] + list(PDFDocument.EXAM_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    
    exam_name_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    exam_name_value = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'enhanced-input', 'placeholder': 'Exam name'})
    )
    
    organization_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    organization_value = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'enhanced-input', 'placeholder': 'Organization name'})
    )
    
    year_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    year_value = forms.IntegerField(
        required=False,
        min_value=1990,
        max_value=2030,
        widget=forms.NumberInput(attrs={'class': 'enhanced-input', 'placeholder': '2024'})
    )
    
    # Subject & Classification
    subject_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    subject_value = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'enhanced-input', 'placeholder': 'Subject'})
    )
    
    topic_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    topic_value = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'enhanced-input', 'placeholder': 'Topic'})
    )
    
    subtopic_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    subtopic_value = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'enhanced-input', 'placeholder': 'Subtopic'})
    )
    
    # Additional Information
    source_type_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    source_type_value = forms.ChoiceField(
        choices=[('', 'Select source type')] + list(PDFDocument.SOURCE_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    
    source_url_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    source_url_value = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'enhanced-input', 'placeholder': 'https://example.com'})
    )
    
    # Tags
    tags_action = forms.ChoiceField(
        choices=[
            ('keep', 'Keep existing'),
            ('replace', 'Replace with'),
            ('add', 'Add to existing'),
            ('remove', 'Remove from existing'),
        ],
        initial='keep',
        widget=forms.Select(attrs={'class': 'enhanced-select'})
    )
    tags_value = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'enhanced-input', 'placeholder': 'tag1, tag2, tag3'})
    )
    
    def __init__(self, *args, **kwargs):
        self.selected_documents = kwargs.pop('selected_documents', [])
        super().__init__(*args, **kwargs)
    
    def apply_bulk_changes(self):
        """
        Apply the bulk changes to selected documents
        """
        updated_count = 0
        
        for document in self.selected_documents:
            changed = False
            
            # Apply changes based on form data
            for field_name in ['title', 'description', 'exam_type', 'exam_name', 'organization', 
                             'year', 'subject', 'topic', 'subtopic', 'source_type', 'source_url']:
                action = self.cleaned_data.get(f'{field_name}_action')
                value = self.cleaned_data.get(f'{field_name}_value')
                
                if action == 'replace' and value:
                    setattr(document, field_name, value)
                    changed = True
                elif action == 'append' and value and hasattr(document, field_name):
                    current_value = getattr(document, field_name) or ''
                    setattr(document, field_name, f"{current_value} {value}".strip())
                    changed = True
                elif action == 'prepend' and value and hasattr(document, field_name):
                    current_value = getattr(document, field_name) or ''
                    setattr(document, field_name, f"{value} {current_value}".strip())
                    changed = True
            
            # Handle tags separately
            tags_action = self.cleaned_data.get('tags_action')
            tags_value = self.cleaned_data.get('tags_value')
            
            if tags_action and tags_value:
                new_tags = [tag.strip() for tag in tags_value.split(',') if tag.strip()]
                current_tags = document.tags or []
                
                if tags_action == 'replace':
                    document.tags = new_tags
                    changed = True
                elif tags_action == 'add':
                    # Add new tags, avoiding duplicates
                    combined_tags = list(set(current_tags + new_tags))
                    document.tags = combined_tags
                    changed = True
                elif tags_action == 'remove':
                    # Remove specified tags
                    document.tags = [tag for tag in current_tags if tag not in new_tags]
                    changed = True
            
            if changed:
                document.save()
                updated_count += 1
        
        return updated_count

class MetadataTemplateForm(forms.ModelForm):
    """
    Form for creating reusable metadata templates
    """
    default_tags = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'enhanced-input', 
            'placeholder': 'tag1, tag2, tag3'
        }),
        help_text="Comma-separated tags to apply by default"
    )
    
    custom_fields = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'enhanced-textarea', 
            'rows': 4,
            'placeholder': '{"difficulty": "medium", "pattern": "prelims"}'
        }),
        help_text="JSON object with custom field names and values"
    )
    
    class Meta:
        model = MetadataTemplate
        fields = [
            'name', 'description', 'exam_type', 'organization', 'year',
            'subject', 'topic', 'source_type', 'is_public'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'enhanced-input',
                'placeholder': 'Template name (e.g., UPSC Prelims 2024)',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'enhanced-textarea',
                'rows': 3,
                'placeholder': 'Brief description of when to use this template...'
            }),
            'exam_type': forms.Select(attrs={'class': 'enhanced-select'}),
            'organization': forms.TextInput(attrs={
                'class': 'enhanced-input',
                'placeholder': 'e.g., UPSC, SSC, IBPS'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'enhanced-input',
                'min': '1990',
                'max': '2030',
                'placeholder': '2024'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'enhanced-input',
                'placeholder': 'e.g., General Studies, Mathematics'
            }),
            'topic': forms.TextInput(attrs={
                'class': 'enhanced-input',
                'placeholder': 'Specific topic or chapter'
            }),
            'source_type': forms.Select(attrs={'class': 'enhanced-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'enhanced-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add empty choice to dropdowns
        self.fields['exam_type'].choices = [('', 'Select exam type')] + list(self.fields['exam_type'].choices)
        self.fields['source_type'].choices = [('', 'Select source type')] + list(self.fields['source_type'].choices)
        
        # Pre-populate fields if editing
        if self.instance and self.instance.pk:
            if self.instance.default_tags:
                self.fields['default_tags'].initial = ', '.join(self.instance.default_tags)
            if self.instance.custom_fields:
                import json
                self.fields['custom_fields'].initial = json.dumps(self.instance.custom_fields, indent=2)
    
    def clean_default_tags(self):
        """Convert comma-separated tags to list"""
        tags_str = self.cleaned_data.get('default_tags', '')
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            return tags
        return []
    
    def clean_custom_fields(self):
        """Parse and validate JSON custom fields"""
        custom_fields_str = self.cleaned_data.get('custom_fields', '').strip()
        if custom_fields_str:
            try:
                import json
                custom_fields = json.loads(custom_fields_str)
                if not isinstance(custom_fields, dict):
                    raise forms.ValidationError("Custom fields must be a JSON object (dictionary)")
                return custom_fields
            except json.JSONDecodeError as e:
                raise forms.ValidationError(f"Invalid JSON format: {str(e)}")
        return {}
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set default tags and custom fields from cleaned data
        instance.default_tags = self.cleaned_data.get('default_tags', [])
        instance.custom_fields = self.cleaned_data.get('custom_fields', {})
        
        if commit:
            instance.save()
        
        return instance