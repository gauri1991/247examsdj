from django import forms
from django.core.exceptions import ValidationError
from .models import PDFDocument, ExtractedQuestion
from .security import pdf_file_validator, PDFSecurityValidator
from questions.models import QuestionBank, Question


class PDFUploadForm(forms.ModelForm):
    """
    Form for uploading PDF documents with comprehensive validation
    """
    
    class Meta:
        model = PDFDocument
        fields = [
            'file', 'title', 'description', 'exam_type', 'exam_name', 
            'organization', 'year', 'subject', 'topic', 'subtopic', 
            'source_type', 'source_url'
        ]
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': '.pdf',
                'id': 'pdf-file-input'
            }),
            'title': forms.TextInput(attrs={'class': 'enhanced-input'}),
            'description': forms.Textarea(attrs={'class': 'enhanced-textarea', 'rows': 3}),
            'exam_type': forms.Select(attrs={'class': 'enhanced-select'}),
            'exam_name': forms.TextInput(attrs={'class': 'enhanced-input'}),
            'organization': forms.TextInput(attrs={'class': 'enhanced-input'}),
            'year': forms.NumberInput(attrs={'class': 'enhanced-input', 'min': '1990', 'max': '2030'}),
            'subject': forms.TextInput(attrs={'class': 'enhanced-input'}),
            'topic': forms.TextInput(attrs={'class': 'enhanced-input'}),
            'subtopic': forms.TextInput(attrs={'class': 'enhanced-input'}),
            'source_type': forms.Select(attrs={'class': 'enhanced-select'}),
            'source_url': forms.URLInput(attrs={'class': 'enhanced-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add custom validation
        self.fields['file'].validators.append(pdf_file_validator)
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if not file:
            raise ValidationError("Please select a PDF file to upload.")
        
        # Security validation
        validator = PDFSecurityValidator()
        validation_result = validator.validate_pdf_file(file)
        
        if not validation_result['is_valid']:
            error_msg = '; '.join(validation_result['errors'])
            raise ValidationError(f"Invalid PDF file: {error_msg}")
        
        # Store validation results for later use
        self._validation_result = validation_result
        
        return file
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.uploaded_by = self.user
        
        # Set filename and file size from validation
        if hasattr(self, '_validation_result'):
            instance.filename = PDFSecurityValidator.sanitize_filename(
                self.cleaned_data['file'].name
            )
            instance.file_size = self._validation_result['file_size']
            instance.page_count = self._validation_result.get('page_count', 0)
            instance.is_searchable = not self._validation_result.get('needs_ocr', True)
        
        # Initialize title with filename if title is empty (new upload)
        if not instance.title and instance.filename:
            # Remove .pdf extension and make it more readable
            title = instance.filename.replace('.pdf', '').replace('_', ' ')
            instance.title = title
        
        if commit:
            instance.save()
        
        return instance


class QuestionReviewForm(forms.ModelForm):
    """
    Form for reviewing and editing extracted questions
    """
    
    class Meta:
        model = ExtractedQuestion
        fields = [
            'question_text', 'question_type', 'answer_options', 
            'correct_answers', 'explanation', 'estimated_difficulty',
            'estimated_topic', 'estimated_marks', 'is_approved'
        ]
        widgets = {
            'question_text': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4
            }),
            'question_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
            'estimated_difficulty': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'estimated_topic': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'estimated_marks': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.5',
                'min': '0'
            }),
            'is_approved': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamic field setup based on question type
        if self.instance and self.instance.question_type:
            self._setup_dynamic_fields()
    
    def _setup_dynamic_fields(self):
        """Setup fields based on question type"""
        question_type = self.instance.question_type
        
        if question_type in ['mcq', 'multi_select']:
            # Add option management for MCQ
            self.fields['answer_options'].widget = forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 6,
                'placeholder': 'Enter options, one per line'
            })
        
        elif question_type == 'true_false':
            # Limit options for True/False
            self.fields['correct_answers'].widget = forms.Select(
                choices=[('True', 'True'), ('False', 'False')],
                attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}
            )


class QuestionConversionForm(forms.Form):
    """
    Form for converting extracted questions to question bank
    """
    question_bank = forms.ModelChoiceField(
        queryset=QuestionBank.objects.none(),
        required=False,  # Make it not required, we'll validate in clean()
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        help_text="Select the question bank to add this question to"
    )
    
    create_new_bank = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        }),
        help_text="Check to create a new question bank"
    )
    
    new_bank_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter new question bank name'
        })
    )
    
    new_bank_category = forms.ChoiceField(
        choices=QuestionBank.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Show user's question banks
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(
                created_by=user
            ).order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        create_new = cleaned_data.get('create_new_bank')
        new_name = cleaned_data.get('new_bank_name')
        question_bank = cleaned_data.get('question_bank')
        
        if create_new and not new_name:
            raise ValidationError("Please provide a name for the new question bank.")
        
        if not create_new and not question_bank:
            raise ValidationError("Please select a question bank or choose to create a new one.")
        
        return cleaned_data


class BulkConversionForm(forms.Form):
    """
    Form for bulk conversion of extracted questions
    """
    CONFIDENCE_CHOICES = [
        ('all', 'All Questions'),
        ('high', 'High Confidence Only (>80%)'),
        ('medium_high', 'Medium-High Confidence (>60%)'),
    ]
    
    question_bank = forms.ModelChoiceField(
        queryset=QuestionBank.objects.none(),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    confidence_filter = forms.ChoiceField(
        choices=CONFIDENCE_CHOICES,
        initial='high',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    approved_only = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        }),
        help_text="Only convert manually approved questions"
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(
                created_by=user
            ).order_by('name')


class ExtractionTemplateForm(forms.Form):
    """
    Form for selecting extraction templates
    """
    template = forms.ChoiceField(
        choices=[
            ('default', 'Default Pattern Recognition'),
            ('academic', 'Academic Exam Format'),
            ('competitive', 'Competitive Exam Format'),
            ('textbook', 'Textbook Q&A Format'),
            ('custom', 'Custom Template'),
        ],
        initial='default',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    enable_ocr = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        }),
        help_text="Enable OCR for scanned PDFs"
    )
    
    auto_detect_layout = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        }),
        help_text="Automatically detect single/multi-column layout"
    )


class EnhancedQuestionReviewForm(forms.ModelForm):
    """
    Enhanced form for reviewing and editing extracted questions
    """
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'), 
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ]
    
    question_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 4,
            'placeholder': 'Enter the question text...'
        }),
        help_text="Edit the question text to improve clarity and correctness"
    )
    
    question_type = forms.ChoiceField(
        choices=ExtractedQuestion.QUESTION_TYPES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    difficulty_level = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        help_text="Estimate the difficulty level of this question"
    )
    
    # Metadata fields inherited from PDF document
    exam_type = forms.ChoiceField(
        choices=[('', '-- Select Exam Type --')] + PDFDocument.EXAM_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        help_text="Exam type (inherited from document)"
    )
    
    organization = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Conducting organization'
        }),
        help_text="Organization conducting the exam"
    )
    
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'min': '1990',
            'max': '2030'
        }),
        help_text="Year of exam"
    )
    
    subject = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Subject (e.g., General Studies, Mathematics)'
        }),
        help_text="Main subject"
    )
    
    topic = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Topic'
        }),
        help_text="Specific topic"
    )
    
    subtopic = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Subtopic'
        }),
        help_text="Subtopic if applicable"
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Tags (comma-separated)'
        }),
        help_text="Tags for easy search (comma-separated)"
    )
    
    review_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Add notes about changes made or issues identified...'
        }),
        help_text="Document any changes or observations during review"
    )
    
    # Question bank selection for conversion
    question_bank = forms.ModelChoiceField(
        queryset=QuestionBank.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        help_text="Select question bank for conversion (required for convert action)"
    )
    
    create_new_bank = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        }),
        help_text="Create a new question bank"
    )
    
    new_bank_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter new question bank name'
        }),
        help_text="Name for the new question bank (required if creating new)"
    )
    
    new_bank_category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter category (e.g., Mathematics, Science)'
        }),
        help_text="Category for the new question bank"
    )
    
    class Meta:
        model = ExtractedQuestion
        fields = ['question_text', 'question_type']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(
                created_by=self.user
            ).order_by('name')
        
        # Pre-populate fields with existing data
        if self.instance and self.instance.pk:
            # Get metadata from the question
            metadata = self.instance.metadata or {}
            self.fields['difficulty_level'].initial = metadata.get('difficulty_level', 'medium')
            self.fields['review_notes'].initial = metadata.get('review_notes', '')
            
            # Auto-populate metadata from PDF document if not already set
            pdf_doc = self.instance.pdf_document
            if pdf_doc:
                # Use metadata value if exists, otherwise inherit from PDF document
                self.fields['exam_type'].initial = metadata.get('exam_type', pdf_doc.exam_type)
                self.fields['organization'].initial = metadata.get('organization', pdf_doc.organization)
                self.fields['year'].initial = metadata.get('year', pdf_doc.year)
                self.fields['subject'].initial = metadata.get('subject', pdf_doc.subject)
                self.fields['topic'].initial = metadata.get('topic', pdf_doc.topic)
                self.fields['subtopic'].initial = metadata.get('subtopic', pdf_doc.subtopic)
                
                # Convert tags list to comma-separated string
                tags = metadata.get('tags', pdf_doc.tags)
                if isinstance(tags, list):
                    self.fields['tags'].initial = ', '.join(tags)
                else:
                    self.fields['tags'].initial = tags or ''
    
    def clean_tags(self):
        """Convert comma-separated tags to a list"""
        tags = self.cleaned_data.get('tags', '')
        if tags:
            # Split by comma, strip whitespace, and remove empty strings
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            return tag_list
        return []
    
    def clean(self):
        cleaned_data = super().clean()
        create_new_bank = cleaned_data.get('create_new_bank')
        new_bank_name = cleaned_data.get('new_bank_name')
        question_bank = cleaned_data.get('question_bank')
        
        # Validate question bank selection for conversion
        action = self.data.get('action')
        if action == 'convert':
            if create_new_bank:
                if not new_bank_name:
                    self.add_error('new_bank_name', 'Bank name is required when creating a new question bank')
            elif not question_bank:
                self.add_error('question_bank', 'Please select a question bank or choose to create a new one')
        
        return cleaned_data
    
    def get_answer_options_data(self):
        """
        Extract answer options data from form
        """
        options = []
        correct_answers = []
        
        # Process answer options from form data
        option_index = 0
        while f'option_{option_index}' in self.data:
            option_text = self.data.get(f'option_{option_index}', '').strip()
            is_correct = f'correct_{option_index}' in self.data
            
            if option_text:
                option_letter = chr(65 + option_index)  # A, B, C, D...
                options.append({
                    'letter': option_letter,
                    'text': option_text
                })
                
                if is_correct:
                    correct_answers.append(option_letter)
            
            option_index += 1
        
        return options, correct_answers
    
    def save(self, commit=True):
        from django.utils import timezone
        
        instance = super().save(commit=False)
        
        # Update metadata
        if not instance.metadata:
            instance.metadata = {}
        
        instance.metadata.update({
            'difficulty_level': self.cleaned_data.get('difficulty_level'),
            'review_notes': self.cleaned_data.get('review_notes'),
            'last_reviewed_at': timezone.now().isoformat(),
            'reviewed_by': str(self.user.id) if self.user else None,
            # Store document metadata
            'exam_type': self.cleaned_data.get('exam_type'),
            'organization': self.cleaned_data.get('organization'),
            'year': self.cleaned_data.get('year'),
            'subject': self.cleaned_data.get('subject'),
            'topic': self.cleaned_data.get('topic'),
            'subtopic': self.cleaned_data.get('subtopic'),
            'tags': self.cleaned_data.get('tags', [])
        })
        
        # Update answer options
        options, correct_answers = self.get_answer_options_data()
        instance.answer_options = options
        instance.correct_answers = correct_answers
        
        # Mark as reviewed
        instance.requires_review = False
        instance.is_approved = True
        
        if commit:
            instance.save()
        
        return instance
    
    def convert_to_question_bank(self):
        """
        Convert the extracted question to the question bank
        """
        from questions.models import Question, QuestionOption
        
        if self.cleaned_data.get('create_new_bank'):
            question_bank = QuestionBank.objects.create(
                name=self.cleaned_data['new_bank_name'],
                category=self.cleaned_data.get('new_bank_category', ''),
                created_by=self.user
            )
        else:
            question_bank = self.cleaned_data['question_bank']
        
        # Create the question
        question = Question.objects.create(
            question_bank=question_bank,
            question_text=self.cleaned_data['question_text'],
            question_type=self.cleaned_data['question_type'],
            difficulty_level=self.cleaned_data.get('difficulty_level', 'medium'),
            points=1,  # Default points
            created_by=self.user
        )
        
        # Create answer options for MCQ questions
        options, correct_answers = self.get_answer_options_data()
        for option in options:
            is_correct = option['letter'] in correct_answers
            QuestionOption.objects.create(
                question=question,
                option_text=option['text'],
                is_correct=is_correct
            )
        
        # Mark the extracted question as converted
        instance = self.instance
        instance.is_converted = True
        instance.converted_question = question
        instance.save()
        
        return question