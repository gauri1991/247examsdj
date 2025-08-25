from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
import json
import time
import logging

# Initialize logger
logger = logging.getLogger('pdf_extractor')

from .models import PDFDocument, ProcessingJob, ExtractedQuestion, ProcessingStatistics, RegionCorrection, RegionReviewSession, PageReviewStatus, SavedRegion, MetadataTemplate
from .forms import PDFUploadForm, QuestionReviewForm, QuestionConversionForm, BulkConversionForm, EnhancedQuestionReviewForm
from .bulk_forms import BulkMetadataEditForm, MetadataTemplateForm
from .processors import PDFTextDetector, PDFTextExtractor, QuestionAnswerDetector
from .security import PDFSecurityValidator
from .tasks import process_pdf_document_task
import threading
from questions.models import QuestionBank, Question
from .region_management_apis import delete_saved_region_api, update_saved_region_api, delete_document_api


def get_user_documents_queryset(request):
    """
    Get documents queryset based on user permissions.
    Admin users can see all documents, regular users only see their own.
    """
    if request.user.is_superuser:
        return PDFDocument.objects.all()
    else:
        return PDFDocument.objects.filter(uploaded_by=request.user)


def get_user_document_or_404(request, document_id):
    """
    Get document with permission check.
    Admin users can access any document, regular users only their own.
    """
    if request.user.is_superuser:
        return get_object_or_404(PDFDocument, id=document_id)
    else:
        return get_object_or_404(PDFDocument, id=document_id, uploaded_by=request.user)


def get_user_job_or_404(request, job_id):
    """
    Get processing job with permission check.
    Admin users can access any job, regular users only their own.
    """
    if request.user.is_superuser:
        return get_object_or_404(ProcessingJob, id=job_id)
    else:
        return get_object_or_404(ProcessingJob, id=job_id, pdf_document__uploaded_by=request.user)


def get_user_questions_queryset(request):
    """
    Get extracted questions queryset based on user permissions.
    Admin users can see all questions, regular users only see their own.
    """
    if request.user.is_superuser:
        return ExtractedQuestion.objects.all()
    else:
        return ExtractedQuestion.objects.filter(pdf_document__uploaded_by=request.user)


def get_user_question_or_404(request, question_id):
    """
    Get extracted question with permission check.
    Admin users can access any question, regular users only their own.
    """
    if request.user.is_superuser:
        return get_object_or_404(ExtractedQuestion, id=question_id)
    else:
        return get_object_or_404(ExtractedQuestion, id=question_id, pdf_document__uploaded_by=request.user)


def _parse_question_and_options(ocr_text: str) -> dict:
    """
    Enhanced parser to extract question and options, supporting multiple options per line
    
    Handles formats like:
    '(a) 30     (b) 35'
    '(c) 40     (d) 45'
    
    Or traditional single-option lines:
    '(a) Option A text'
    '(b) Option B text'
    """
    import re
    
    if not ocr_text.strip():
        return {
            'question_text': '',
            'options': [],
            'has_options': False,
            'option_count': 0
        }
    
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    
    question_lines = []
    options = []
    
    for line in lines:
        # Check if this line contains any options
        line_has_options = False
        
        # Enhanced pattern to find multiple options in a single line
        # Matches: (a), (b), (c), (d) OR a), b), c), d)
        multi_option_patterns = [
            r'\(([a-d])\)\s*([^()]+?)(?=\s*\([a-d]\)|$)',  # (a) text (b) text
            r'(?:^|\s)([a-d])\)\s*([^()]+?)(?=\s*[a-d]\)|$)'  # a) text b) text
        ]
        
        for pattern in multi_option_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                line_has_options = True
                for match in matches:
                    option_letter = match[0].lower()
                    option_text = match[1].strip()
                    
                    # Clean up option text (remove extra spaces, trailing punctuation)
                    option_text = re.sub(r'\s+', ' ', option_text).strip()
                    option_text = option_text.rstrip(',').strip()
                    
                    if option_text:  # Only add if there's actual text
                        options.append({
                            'letter': option_letter,
                            'text': option_text,
                            'full_text': f'({option_letter}) {option_text}'
                        })
                break  # Found options with this pattern, no need to try others
        
        # If no options found in this line, it's part of the question
        if not line_has_options:
            question_lines.append(line)
    
    # Join question lines
    question_text = ' '.join(question_lines).strip()
    
    # Sort options by letter to ensure correct order
    options.sort(key=lambda x: x['letter'])
    
    # Enhanced result with additional metadata
    return {
        'question_text': question_text,
        'options': options,
        'has_options': len(options) > 0,
        'option_count': len(options),
        'raw_text': ocr_text,
        'parsing_method': 'enhanced_multiline'
    }


@login_required
def pdf_extraction_home(request):
    """
    Main PDF extraction interface
    """
    # Get user's recent documents
    recent_documents = get_user_documents_queryset(request).order_by('-uploaded_at')[:5]
    
    # Get processing statistics
    total_documents = get_user_documents_queryset(request).count()
    if request.user.is_superuser:
        total_questions = ExtractedQuestion.objects.count()
    else:
        total_questions = ExtractedQuestion.objects.filter(
            pdf_document__uploaded_by=request.user
        ).count()
    
    context = {
        'recent_documents': recent_documents,
        'total_documents': total_documents,
        'total_questions': total_questions,
        'upload_form': PDFUploadForm(user=request.user)
    }
    
    return render(request, 'pdf_extractor/home.html', context)


@login_required
@require_http_methods(["POST"])
def pdf_upload(request):
    """
    Handle PDF file upload with metadata and redirect directly to interactive review
    """
    form = PDFUploadForm(request.POST, request.FILES, user=request.user)
    
    if form.is_valid():
        try:
            # Save the document
            pdf_document = form.save()
            
            # Handle tags (from JSON string)
            tags_json = request.POST.get('tags')
            if tags_json:
                try:
                    tags = json.loads(tags_json)
                    pdf_document.tags = tags
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Handle custom fields (from JSON string)
            custom_fields_json = request.POST.get('custom_fields')
            if custom_fields_json:
                try:
                    custom_fields = json.loads(custom_fields_json)
                    pdf_document.custom_fields = custom_fields
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Set document status to completed (ready for interactive review)
            pdf_document.status = 'completed' 
            pdf_document.save()
            
            messages.success(request, f'PDF "{pdf_document.filename}" uploaded successfully with metadata! Opening interactive review...')
            return JsonResponse({
                'success': True,
                'document_id': str(pdf_document.id),
                'redirect_url': f'/pdf-extractor/interactive-review/{pdf_document.id}/'
            })
        
        except Exception as e:
            messages.error(request, f'Upload failed: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    else:
        errors = []
        for field, field_errors in form.errors.items():
            errors.extend(field_errors)
        
        return JsonResponse({
            'success': False,
            'errors': errors
        }, status=400)


@login_required
def edit_metadata(request, document_id):
    """
    Edit document metadata
    """
    document = get_user_document_or_404(request, document_id)
    
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, instance=document, user=request.user)
        
        if form.is_valid():
            # Update the document with new metadata
            updated_document = form.save()
            
            # Handle tags (from JSON string)
            tags_json = request.POST.get('tags')
            if tags_json:
                try:
                    tags = json.loads(tags_json)
                    updated_document.tags = tags
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Handle custom fields (from JSON string)
            custom_fields_json = request.POST.get('custom_fields')
            if custom_fields_json:
                try:
                    custom_fields = json.loads(custom_fields_json)
                    updated_document.custom_fields = custom_fields
                except (json.JSONDecodeError, TypeError):
                    pass
            
            updated_document.save()
            
            messages.success(request, f'Metadata for "{document.filename}" updated successfully!')
            return redirect('pdf_extractor:document_detail', document_id=document.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-populate form with existing document data
        form = PDFUploadForm(instance=document, user=request.user)
    
    context = {
        'form': form,
        'document': document
    }
    
    return render(request, 'pdf_extractor/edit_metadata.html', context)


@login_required
def bulk_edit_metadata(request):
    """
    Bulk edit metadata for multiple documents
    """
    if request.method == 'POST':
        document_ids = request.POST.getlist('document_ids')
        
        if not document_ids:
            messages.error(request, 'No documents selected for bulk editing.')
            return redirect('pdf_extractor:document_list')
        
        # Get selected documents
        documents = PDFDocument.objects.filter(
            id__in=document_ids,
            uploaded_by=request.user
        )
        
        if not documents.exists():
            messages.error(request, 'No valid documents found for editing.')
            return redirect('pdf_extractor:document_list')
        
        # Process bulk edit form
        if 'apply_changes' in request.POST:
            form = BulkMetadataEditForm(request.POST, selected_documents=documents)
            if form.is_valid():
                updated_count = form.apply_bulk_changes()
                messages.success(request, f'Successfully updated metadata for {updated_count} documents.')
                return redirect('pdf_extractor:document_list')
        else:
            form = BulkMetadataEditForm(selected_documents=documents)
        
        context = {
            'form': form,
            'selected_documents': documents,
            'document_count': documents.count()
        }
        
        return render(request, 'pdf_extractor/bulk_edit_metadata.html', context)
    
    return redirect('pdf_extractor:document_list')


@login_required 
def export_metadata(request):
    """
    Export metadata for selected documents
    """
    import csv
    import io
    from django.http import HttpResponse
    
    document_ids = request.GET.getlist('document_ids')
    
    if not document_ids:
        messages.error(request, 'No documents selected for export.')
        return redirect('pdf_extractor:document_list')
    
    documents = PDFDocument.objects.filter(
        id__in=document_ids,
        uploaded_by=request.user
    )
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="document_metadata.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Filename', 'Title', 'Description', 'Exam Type', 'Exam Name', 
        'Organization', 'Year', 'Subject', 'Topic', 'Subtopic',
        'Source Type', 'Source URL', 'Tags', 'Custom Fields', 'Uploaded At'
    ])
    
    # Write document data
    for doc in documents:
        tags_str = ', '.join(doc.tags) if doc.tags else ''
        custom_fields_str = json.dumps(doc.custom_fields) if doc.custom_fields else ''
        
        writer.writerow([
            doc.filename,
            doc.title or '',
            doc.description or '',
            doc.get_exam_type_display() if doc.exam_type else '',
            doc.exam_name or '',
            doc.organization or '',
            doc.year or '',
            doc.subject or '',
            doc.topic or '',
            doc.subtopic or '',
            doc.get_source_type_display() if doc.source_type else '',
            doc.source_url or '',
            tags_str,
            custom_fields_str,
            doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


@login_required
@require_http_methods(["POST"])
def import_metadata(request):
    """
    Import metadata from CSV/JSON file
    """
    import csv
    import io
    
    if 'metadata_file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'})
    
    file = request.FILES['metadata_file']
    
    try:
        if file.name.endswith('.csv'):
            # Handle CSV import
            file_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            updated_count = 0
            
            for row in csv_reader:
                # Find document by filename
                try:
                    document = PDFDocument.objects.get(
                        filename=row.get('Filename', '').strip(),
                        uploaded_by=request.user
                    )
                    
                    # Update fields if provided
                    if row.get('Title'):
                        document.title = row['Title'].strip()
                    if row.get('Description'):
                        document.description = row['Description'].strip()
                    if row.get('Exam Type'):
                        # Map display name back to choice value
                        exam_type_map = {display: value for value, display in PDFDocument.EXAM_TYPE_CHOICES}
                        if row['Exam Type'] in exam_type_map:
                            document.exam_type = exam_type_map[row['Exam Type']]
                    if row.get('Organization'):
                        document.organization = row['Organization'].strip()
                    if row.get('Year') and row['Year'].strip():
                        try:
                            document.year = int(row['Year'])
                        except ValueError:
                            pass
                    if row.get('Subject'):
                        document.subject = row['Subject'].strip()
                    if row.get('Topic'):
                        document.topic = row['Topic'].strip()
                    if row.get('Subtopic'):
                        document.subtopic = row['Subtopic'].strip()
                    if row.get('Tags'):
                        tags = [tag.strip() for tag in row['Tags'].split(',') if tag.strip()]
                        document.tags = tags
                    
                    document.save()
                    updated_count += 1
                    
                except PDFDocument.DoesNotExist:
                    continue  # Skip non-existent documents
            
            return JsonResponse({
                'success': True, 
                'updated_count': updated_count,
                'message': f'Successfully updated {updated_count} documents'
            })
            
        elif file.name.endswith('.json'):
            # Handle JSON import
            file_content = file.read().decode('utf-8')
            data = json.loads(file_content)
            
            updated_count = 0
            
            for item in data:
                try:
                    document = PDFDocument.objects.get(
                        filename=item.get('filename', ''),
                        uploaded_by=request.user
                    )
                    
                    # Update document fields from JSON
                    for field in ['title', 'description', 'exam_type', 'exam_name', 
                                'organization', 'year', 'subject', 'topic', 'subtopic',
                                'source_type', 'source_url']:
                        if field in item and item[field]:
                            setattr(document, field, item[field])
                    
                    if 'tags' in item and isinstance(item['tags'], list):
                        document.tags = item['tags']
                    
                    if 'custom_fields' in item and isinstance(item['custom_fields'], dict):
                        document.custom_fields = item['custom_fields']
                    
                    document.save()
                    updated_count += 1
                    
                except PDFDocument.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'updated_count': updated_count,
                'message': f'Successfully updated {updated_count} documents'
            })
        
        else:
            return JsonResponse({'success': False, 'error': 'Unsupported file format'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def processing_status(request, job_id):
    """
    Display processing status page
    """
    job = get_user_job_or_404(request, job_id)
    
    context = {
        'job': job,
        'document': job.pdf_document,
        'progress_percentage': job.progress_percentage,
        'current_step': job.get_current_step_display(),
        'step_details': job.step_details
    }
    
    return render(request, 'pdf_extractor/processing_status.html', context)


@login_required
def interactive_review(request, document_id):
    """
    Interactive PDF review interface for manual region selection and OCR
    """
    document = get_user_document_or_404(request, document_id)
    
    # Get or create review session
    # First try to get the most recent active session
    try:
        review_session = RegionReviewSession.objects.filter(
            pdf_document=document,
            reviewer=request.user,
            status__in=['in_progress', 'active']
        ).order_by('-started_at').first()
        
        if not review_session:
            # No active session, create a new one
            review_session = RegionReviewSession.objects.create(
                pdf_document=document,
                reviewer=request.user,
                current_page=1,
                status='in_progress',
                total_pages=document.page_count or 1
            )
    except Exception as e:
        # If there's any issue, create a new session
        review_session = RegionReviewSession.objects.create(
            pdf_document=document,
            reviewer=request.user,
            current_page=1,
            status='in_progress',
            total_pages=document.page_count or 1
        )
    
    # Get current page from request or session
    current_page = int(request.GET.get('page', review_session.current_page))
    
    # Update session current page
    if current_page != review_session.current_page:
        review_session.current_page = current_page
        review_session.save()
    
    # Get processed images for the PDF
    from .pdf_to_image import PDFToImageConverter
    converter = PDFToImageConverter()
    
    try:
        with document.file.open('rb') as pdf_file:
            file_content = pdf_file.read()
            from io import BytesIO
            temp_buffer = BytesIO(file_content)
            temp_buffer.name = document.filename
            temp_buffer.size = document.file_size
            
            conversion_result = converter.convert_pdf_to_images(temp_buffer)
    except Exception as e:
        return render(request, 'pdf_extractor/error.html', {
            'error': f'Failed to convert PDF to images: {str(e)}'
        })
    
    if not conversion_result.get('success'):
        return render(request, 'pdf_extractor/error.html', {
            'error': 'Failed to convert PDF to images for review'
        })
    
    # Get current page image info
    images = conversion_result.get('images', [])
    current_image = None
    current_image_url = None
    
    if images and current_page <= len(images):
        current_image = images[current_page - 1]
        # Generate URL from image path
        if current_image and 'path' in current_image:
            import os
            from django.conf import settings
            # Convert absolute path to relative media URL
            image_path = str(current_image['path'])  # Convert to string
            media_root = str(settings.MEDIA_ROOT)   # Convert to string
            
            if image_path.startswith(media_root):
                relative_path = os.path.relpath(image_path, media_root)
                current_image_url = settings.MEDIA_URL + relative_path.replace('\\', '/')
            else:
                # Fallback: try to construct URL
                filename = os.path.basename(image_path)
                current_image_url = f"{settings.MEDIA_URL}pdf_image_cache/{filename}"
    
    # Get existing regions/corrections for current page
    existing_corrections = RegionCorrection.objects.filter(
        pdf_document=document,
        page_number=current_page
    ).order_by('id')
    
    # Get extracted questions for this page if they exist
    page_questions = ExtractedQuestion.objects.filter(
        pdf_document=document,
        page_number=current_page
    ).order_by('id')
    
    context = {
        'document': document,
        'review_session': review_session,
        'current_page': current_page,
        'total_pages': document.page_count or len(images),
        'current_image': current_image,
        'current_image_url': current_image_url,
        'existing_corrections': existing_corrections,
        'page_questions': page_questions,
        'has_previous': current_page > 1,
        'has_next': current_page < (document.page_count or len(images)),
        'previous_page': current_page - 1 if current_page > 1 else None,
        'next_page': current_page + 1 if current_page < (document.page_count or len(images)) else None,
    }
    
    return render(request, 'pdf_extractor/interactive_review.html', context)


@login_required
def auto_detect_regions_api(request, document_id):
    """
    API endpoint for automatic region detection
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        page_number = data.get('page_number', 1)
        
        # Import region detection components
        from .region_extractor import RegionExtractor
        from .pdf_to_image import PDFToImageConverter
        
        # Convert current page to image
        converter = PDFToImageConverter()
        with document.file.open('rb') as pdf_file:
            file_content = pdf_file.read()
            from io import BytesIO
            temp_buffer = BytesIO(file_content)
            temp_buffer.name = document.filename
            temp_buffer.size = document.file_size
            
            conversion_result = converter.convert_pdf_to_images(temp_buffer)
        
        if not conversion_result.get('success'):
            return JsonResponse({
                'success': False,
                'error': 'Failed to convert PDF page to image'
            })
        
        # Get the specific page image
        images = conversion_result.get('images', [])
        if page_number > len(images):
            return JsonResponse({
                'success': False,
                'error': f'Page {page_number} not found'
            })
        
        page_image_info = images[page_number - 1]
        
        # Load the actual image from path
        from PIL import Image
        actual_image = Image.open(page_image_info['path'])
        
        # Extract regions from the image
        region_extractor = RegionExtractor()
        detected_regions = region_extractor.extract_regions_from_image(actual_image, page_number)
        
        # Convert regions to API format
        regions_data = []
        for i, region in enumerate(detected_regions):
            regions_data.append({
                'id': f'auto_region_{page_number}_{i}',
                'region_type': region.region_type,  # Keep both for compatibility
                'type': region.region_type,
                'coordinates': {
                    'x': region.x,
                    'y': region.y,
                    'width': region.width,
                    'height': region.height
                },
                'confidence': region.confidence,
                'text_preview': region.text[:100] if region.text else '',
                'needs_review': region.confidence < 0.8,
                'metadata': region.metadata  # Include enhanced metadata
            })
        
        return JsonResponse({
            'success': True,
            'page_number': page_number,
            'regions': regions_data,
            'total_regions': len(regions_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def process_selected_regions_api(request, document_id):
    """
    API endpoint to process and OCR selected regions
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        page_number = data.get('page_number', 1)
        selected_regions = data.get('selected_regions', [])
        
        if not selected_regions:
            return JsonResponse({
                'success': False,
                'error': 'No regions selected'
            })
        
        # Import OCR components
        from .ocr_processors import OCRManager
        from .pdf_to_image import PDFToImageConverter
        from PIL import Image
        
        # Convert current page to image
        converter = PDFToImageConverter()
        with document.file.open('rb') as pdf_file:
            file_content = pdf_file.read()
            from io import BytesIO
            temp_buffer = BytesIO(file_content)
            temp_buffer.name = document.filename
            temp_buffer.size = document.file_size
            
            conversion_result = converter.convert_pdf_to_images(temp_buffer)
        
        if not conversion_result.get('success'):
            return JsonResponse({
                'success': False,
                'error': 'Failed to convert PDF page to image'
            })
        
        # Get the specific page image
        images = conversion_result.get('images', [])
        if page_number > len(images):
            return JsonResponse({
                'success': False,
                'error': f'Page {page_number} not found'
            })
        
        page_image_info = images[page_number - 1]
        
        # Load the actual image from path
        full_image = Image.open(page_image_info['path'])
        
        ocr_manager = OCRManager()
        processed_regions = []
        
        # Process each selected region with OCR
        for region_data in selected_regions:
            try:
                coords = region_data['coordinates']
                
                # Crop the region from the full page image
                region_image = full_image.crop((
                    coords['x'],
                    coords['y'], 
                    coords['x'] + coords['width'],
                    coords['y'] + coords['height']
                ))
                
                # Debug: Save cropped region for inspection (optional)
                # region_image.save(f'/tmp/debug_region_{region_data["id"]}.png')
                
                # PHASE 1 ENHANCED OCR: Use production-grade OCR processing
                print(f"Processing region {region_data['id']} with coordinates: {coords} [ENHANCED OCR]")
                
                # Use enhanced OCR processing
                ocr_result = ocr_manager.process_image_with_ocr(region_image)
                
                # Enhanced logging with performance metrics
                ocr_text = ocr_result.get('text', '')
                enhanced_mode = ocr_result.get('enhanced_ocr', False)
                processing_time = ocr_result.get('processing_time', 0)
                method = ocr_result.get('method', 'unknown')
                preprocessing = ocr_result.get('preprocessing_applied', [])
                
                # PARSE QUESTION AND OPTIONS from OCR text
                parsed_question = _parse_question_and_options(ocr_text)
                
                print(f"OCR result for region {region_data['id']}:")
                print(f"  Mode: {'ENHANCED' if enhanced_mode else 'LEGACY'}")
                print(f"  Method: {method}")
                print(f"  Processing time: {processing_time:.2f}s")
                print(f"  Preprocessing: {preprocessing}")
                print(f"  Success: {ocr_result.get('success', False)}")
                print(f"  Confidence: {ocr_result.get('confidence', 0):.1f}%")
                print(f"  Text length: {len(ocr_text)}")
                print(f"  Line count: {len(ocr_text.splitlines())}")
                print(f"  Raw text with line breaks:")
                for i, line in enumerate(ocr_text.splitlines()):
                    print(f"    Line {i}: '{line}'")
                
                # Show parsed question results
                print(f"  PARSED QUESTION DATA:")
                print(f"    Question: '{parsed_question['question_text']}'")
                print(f"    Has options: {parsed_question['has_options']}")
                print(f"    Option count: {parsed_question['option_count']}")
                if parsed_question['options']:
                    for opt in parsed_question['options']:
                        print(f"      ({opt['letter']}) {opt['text']}")
                
                processed_region = {
                    'region_id': region_data['id'],
                    'region_type': region_data.get('type', 'unknown'),
                    'coordinates': coords,
                    'ocr_success': ocr_result.get('success', False),
                    'text': ocr_text,
                    'confidence': ocr_result.get('confidence', 0),
                    'word_count': len(ocr_text.split()),
                    'error': ocr_result.get('error') if not ocr_result.get('success') else None,
                    # Enhanced OCR metadata
                    'enhanced_ocr': enhanced_mode,
                    'ocr_engine': method,
                    'processing_time': processing_time,
                    'preprocessing_applied': preprocessing,
                    # PARSED QUESTION DATA
                    'parsed_question': parsed_question
                }
                
                processed_regions.append(processed_region)
                
            except Exception as e:
                processed_regions.append({
                    'region_id': region_data.get('id', 'unknown'),
                    'region_type': region_data.get('type', 'unknown'),
                    'coordinates': region_data.get('coordinates', {}),
                    'ocr_success': False,
                    'text': '',
                    'confidence': 0,
                    'error': str(e)
                })
        
        return JsonResponse({
            'success': True,
            'page_number': page_number,
            'processed_regions': processed_regions,
            'total_processed': len(processed_regions),
            'successful_ocr': sum(1 for r in processed_regions if r['ocr_success'])
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def save_extracted_questions_api_legacy(request, document_id):
    """
    Legacy API endpoint to save manually reviewed questions and answers
    """
    import logging
    logger = logging.getLogger('pdf_extractor')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        page_number = data.get('page_number', 1)
        questions_data = data.get('questions', [])
        
        logger.info(f"Saving questions for document {document_id}, page {page_number}")
        logger.info(f"Number of questions received: {len(questions_data)}")
        
        if not questions_data:
            return JsonResponse({
                'success': False,
                'error': 'No questions provided'
            })
        
        saved_questions = []
        
        # Get or create processing job for this session
        processing_job = ProcessingJob.objects.filter(
            pdf_document=document
        ).order_by('-created_at').first()
        
        if not processing_job:
            processing_job = ProcessingJob.objects.create(
                pdf_document=document,
                status='completed',
                current_step='manual_review',
                progress_percentage=100
            )
        
        # Save each question
        for question_data in questions_data:
            try:
                # Convert confidence to percentage if needed
                confidence = float(question_data.get('confidence', 0.8))
                if confidence <= 1.0:
                    confidence = confidence * 100
                
                extracted_question = ExtractedQuestion.objects.create(
                    pdf_document=document,
                    processing_job=processing_job,
                    question_text=question_data.get('question_text', ''),
                    question_type=question_data.get('question_type', 'mcq'),
                    page_number=page_number,
                    confidence_score=confidence,
                    answer_options=question_data.get('answer_options', []),
                    correct_answers=question_data.get('correct_answers', []),
                    extraction_method='manual_review',
                    metadata={
                        'manually_reviewed': True,
                        'review_timestamp': timezone.now().isoformat(),
                        'reviewer_id': str(request.user.id),  # Convert UUID to string
                        'region_coordinates': question_data.get('region_coordinates', {})
                    }
                )
                
                # Set confidence level based on score
                extracted_question.set_confidence_level()
                extracted_question.save()
                
                saved_questions.append({
                    'id': str(extracted_question.id),
                    'question_text': extracted_question.question_text,
                    'question_type': extracted_question.question_type,
                    'confidence_score': extracted_question.confidence_score
                })
                
                logger.info(f"Successfully saved question: {extracted_question.id}")
                
            except Exception as e:
                logger.error(f"Failed to save question: {str(e)}")
                logger.error(f"Question data: {question_data}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue  # Skip problematic questions
        
        # Update document status
        if saved_questions:
            document.status = 'completed'
            document.save()
            
            # Update page review status
            from .models import PageReviewStatus
            page_status, created = PageReviewStatus.objects.get_or_create(
                pdf_document=document,
                page_number=page_number,
                defaults={
                    'status': 'completed',
                    'reviewed_by': request.user,
                    'reviewed_at': timezone.now()
                }
            )
            
            if not created:
                page_status.status = 'completed'
                page_status.reviewed_by = request.user
                page_status.reviewed_at = timezone.now()
            
            page_status.questions_found = len(saved_questions)
            page_status.questions_extracted = len(saved_questions)
            page_status.save()
        
        logger.info(f"Total questions saved: {len(saved_questions)}")
        
        return JsonResponse({
            'success': True,
            'page_number': page_number,
            'saved_questions': saved_questions,
            'total_saved': len(saved_questions)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def finish_review_api(request, document_id):
    """
    API endpoint to finish and complete the interactive review session
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        current_page = data.get('current_page', 1)
        status = data.get('status', 'completed')
        
        # Update or complete the review session
        try:
            # Get the most recent active session
            review_session = RegionReviewSession.objects.filter(
                pdf_document=document,
                reviewer=request.user,
                status__in=['in_progress', 'active']
            ).order_by('-started_at').first()
            
            if not review_session:
                return JsonResponse({
                    'success': False,
                    'error': 'No active review session found'
                })
            
            review_session.status = status
            review_session.current_page = current_page
            review_session.completed_at = timezone.now()
            review_session.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Review session completed successfully',
                'session_id': str(review_session.id),
                'status': review_session.status
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to update session: {str(e)}'
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def mark_page_no_questions_api(request, document_id):
    """
    API endpoint to mark a page as having no questions
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        page_number = data.get('page_number', 1)
        notes = data.get('notes', '')
        
        # Import the PageReviewStatus model
        from .models import PageReviewStatus
        
        # Get or create the page status
        page_status, created = PageReviewStatus.objects.get_or_create(
            pdf_document=document,
            page_number=page_number,
            defaults={
                'status': 'no_questions',
                'notes': notes,
                'reviewed_by': request.user,
                'reviewed_at': timezone.now(),
                'questions_found': 0,
                'questions_extracted': 0
            }
        )
        
        if not created:
            # Update existing page status
            page_status.status = 'no_questions'
            page_status.notes = notes
            page_status.reviewed_by = request.user
            page_status.reviewed_at = timezone.now()
            page_status.questions_found = 0
            page_status.questions_extracted = 0
            page_status.save()
        
        # Update review session if exists
        review_session = RegionReviewSession.objects.filter(
            pdf_document=document,
            reviewer=request.user,
            status__in=['in_progress', 'active']
        ).order_by('-started_at').first()
        
        if review_session:
            # Update pages reviewed count
            if page_number > review_session.pages_reviewed:
                review_session.pages_reviewed = page_number
            review_session.current_page = page_number
            review_session.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Page {page_number} marked as having no questions',
            'page_status': {
                'page_number': page_number,
                'status': 'no_questions',
                'notes': notes
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def mark_page_for_later_api(request, document_id):
    """
    API endpoint to mark a page for later review with unsupported question type
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        page_number = data.get('page_number', 1)
        notes = data.get('notes', '')
        
        if not notes:
            return JsonResponse({
                'success': False,
                'error': 'Please provide a description of the unsupported question type'
            })
        
        # Import the PageReviewStatus model
        from .models import PageReviewStatus
        
        # Get or create the page status
        page_status, created = PageReviewStatus.objects.get_or_create(
            pdf_document=document,
            page_number=page_number,
            defaults={
                'status': 'pending_unsupported',
                'notes': notes,
                'reviewed_by': request.user,
                'reviewed_at': timezone.now(),
                'questions_found': 0,  # Unknown number of questions
                'questions_extracted': 0
            }
        )
        
        if not created:
            # Update existing page status
            page_status.status = 'pending_unsupported'
            page_status.notes = notes
            page_status.reviewed_by = request.user
            page_status.reviewed_at = timezone.now()
            # Don't reset questions_found as there might be questions detected
            page_status.save()
        
        # Update review session if exists
        review_session = RegionReviewSession.objects.filter(
            pdf_document=document,
            reviewer=request.user,
            status__in=['in_progress', 'active']
        ).order_by('-started_at').first()
        
        if review_session:
            # Update current page but don't mark as fully reviewed
            review_session.current_page = page_number
            review_session.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Page {page_number} marked for later review',
            'page_status': {
                'page_number': page_number,
                'status': 'pending_unsupported',
                'notes': notes
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def processing_progress_api(request, job_id):
    """
    API endpoint for real-time processing progress updates
    """
    job = get_user_job_or_404(request, job_id)
    
    response_data = {
        'status': job.status,
        'progress_percentage': job.progress_percentage,
        'current_step': job.current_step,
        'current_step_display': job.get_current_step_display(),
        'step_details': job.step_details,
        'error_details': job.error_details
    }
    
    # If completed, include summary
    if job.status == 'completed':
        try:
            stats = job.pdf_document.statistics
            response_data['results'] = {
                'total_questions': stats.total_questions_found,
                'high_confidence': stats.high_confidence_questions,
                'needs_review': stats.questions_requiring_review
            }
        except ProcessingStatistics.DoesNotExist:
            response_data['results'] = {'total_questions': 0}
    
    return JsonResponse(response_data)


@login_required
def document_detail(request, document_id):
    """
    Display document details and processing results
    """
    document = get_user_document_or_404(request, document_id)
    
    # Get extracted questions
    questions = ExtractedQuestion.objects.filter(
        pdf_document=document
    ).order_by('page_number', 'id')
    
    # Pagination
    paginator = Paginator(questions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    try:
        stats = document.statistics
    except ProcessingStatistics.DoesNotExist:
        stats = None
    
    # Get page review status
    from .models import PageReviewStatus
    page_statuses = PageReviewStatus.objects.filter(
        pdf_document=document
    ).order_by('page_number')
    
    # Create page statuses if they don't exist
    if document.page_count and page_statuses.count() < document.page_count:
        # Create missing page statuses
        existing_pages = set(page_statuses.values_list('page_number', flat=True))
        for page_num in range(1, document.page_count + 1):
            if page_num not in existing_pages:
                PageReviewStatus.objects.create(
                    pdf_document=document,
                    page_number=page_num,
                    status='pending'
                )
        # Re-fetch page statuses
        page_statuses = PageReviewStatus.objects.filter(
            pdf_document=document
        ).order_by('page_number')
    
    # Calculate progress
    total_pages = document.page_count or 0
    pages_reviewed = page_statuses.filter(
        status__in=['completed', 'no_questions', 'skipped']
    ).count()
    pages_pending_unsupported = page_statuses.filter(
        status='pending_unsupported'
    ).count()
    # For progress calculation, count pending_unsupported as partially reviewed (0.5)
    progress_percentage = ((pages_reviewed + (pages_pending_unsupported * 0.5)) / total_pages * 100) if total_pages > 0 else 0
    
    # Generate page range for empty state
    page_range = range(1, (document.page_count or 0) + 1)
    
    # Get pages with unsupported types for display
    unsupported_pages = page_statuses.filter(
        status='pending_unsupported'
    ).select_related('reviewed_by')
    
    context = {
        'document': document,
        'questions': page_obj,
        'stats': stats,
        'total_questions': questions.count(),
        'page_statuses': page_statuses,
        'pages_reviewed': pages_reviewed,
        'progress_percentage': progress_percentage,
        'page_range': page_range,
        'unsupported_pages': unsupported_pages,
        'pages_pending_unsupported': pages_pending_unsupported
    }
    
    return render(request, 'pdf_extractor/document_detail.html', context)


@login_required
def extracted_questions(request, document_id):
    """
    Display and manage extracted questions with advanced filtering and search
    """
    document = get_user_document_or_404(request, document_id)
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    confidence_filter = request.GET.get('confidence', 'all')
    question_type_filter = request.GET.get('type', 'all')
    review_filter = request.GET.get('review', 'all')
    difficulty_filter = request.GET.get('difficulty', 'all')
    topic_filter = request.GET.get('topic', 'all')
    page_filter = request.GET.get('page_range', 'all')
    sort_by = request.GET.get('sort', 'page_number')
    
    # Base query
    questions = ExtractedQuestion.objects.filter(pdf_document=document)
    
    # Search functionality
    if search_query:
        questions = questions.filter(
            Q(question_text__icontains=search_query) |
            Q(explanation__icontains=search_query) |
            Q(estimated_topic__icontains=search_query)
        )
    
    # Confidence filter
    if confidence_filter != 'all':
        questions = questions.filter(confidence_level=confidence_filter)
    
    # Question type filter
    if question_type_filter != 'all':
        questions = questions.filter(question_type=question_type_filter)
    
    # Review status filter
    if review_filter == 'needs_review':
        questions = questions.filter(requires_review=True)
    elif review_filter == 'approved':
        questions = questions.filter(is_approved=True)
    elif review_filter == 'rejected':
        questions = questions.filter(is_rejected=True)
    elif review_filter == 'converted':
        questions = questions.filter(is_converted=True)
    elif review_filter == 'pending':
        questions = questions.filter(
            requires_review=False, 
            is_approved=False, 
            is_rejected=False
        )
    
    # Difficulty filter
    if difficulty_filter != 'all':
        questions = questions.filter(estimated_difficulty=difficulty_filter)
    
    # Topic filter
    if topic_filter != 'all':
        questions = questions.filter(estimated_topic__icontains=topic_filter)
    
    # Page range filter
    if page_filter != 'all':
        if '-' in page_filter:
            try:
                start_page, end_page = map(int, page_filter.split('-'))
                questions = questions.filter(
                    page_number__gte=start_page, 
                    page_number__lte=end_page
                )
            except ValueError:
                pass
        else:
            try:
                specific_page = int(page_filter)
                questions = questions.filter(page_number=specific_page)
            except ValueError:
                pass
    
    # Sorting
    sort_options = {
        'page_number': 'page_number',
        'confidence_desc': '-confidence_score',
        'confidence_asc': 'confidence_score',
        'date_desc': '-extracted_at',
        'date_asc': 'extracted_at',
        'difficulty': 'estimated_difficulty',
        'topic': 'estimated_topic'
    }
    
    if sort_by in sort_options:
        questions = questions.order_by(sort_options[sort_by], 'id')
    else:
        questions = questions.order_by('page_number', 'id')
    
    # Get statistics for the filtered questions
    stats = {
        'total': questions.count(),
        'by_confidence': {
            'high': questions.filter(confidence_level='high').count(),
            'medium': questions.filter(confidence_level='medium').count(),
            'low': questions.filter(confidence_level='low').count(),
        },
        'by_type': {},
        'by_status': {
            'needs_review': questions.filter(requires_review=True).count(),
            'approved': questions.filter(is_approved=True).count(),
            'rejected': questions.filter(is_rejected=True).count(),
            'converted': questions.filter(is_converted=True).count(),
        }
    }
    
    # Get question type statistics
    for choice in ExtractedQuestion.QUESTION_TYPES:
        type_code, type_name = choice
        stats['by_type'][type_code] = questions.filter(question_type=type_code).count()
    
    # Get unique topics for filter dropdown
    unique_topics = ExtractedQuestion.objects.filter(
        pdf_document=document,
        estimated_topic__isnull=False
    ).exclude(estimated_topic='').values_list(
        'estimated_topic', flat=True
    ).distinct().order_by('estimated_topic')
    
    # Pagination
    per_page = int(request.GET.get('per_page', 15))
    per_page = min(per_page, 100)  # Limit to 100 items per page
    
    paginator = Paginator(questions, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'document': document,
        'questions': page_obj,
        'stats': stats,
        'filters': {
            'search_query': search_query,
            'confidence_filter': confidence_filter,
            'question_type_filter': question_type_filter,
            'review_filter': review_filter,
            'difficulty_filter': difficulty_filter,
            'topic_filter': topic_filter,
            'page_filter': page_filter,
            'sort_by': sort_by,
            'per_page': per_page,
        },
        'unique_topics': unique_topics,
        'question_types': ExtractedQuestion.QUESTION_TYPES,
        'total_questions': questions.count()
    }
    
    return render(request, 'pdf_extractor/extracted_questions.html', context)


@login_required
def review_question(request, question_id):
    """
    Review and edit extracted question with enhanced functionality
    """
    question = get_user_question_or_404(request, question_id)
    
    if request.method == 'POST':
        form = EnhancedQuestionReviewForm(request.POST, instance=question, user=request.user)
        
        if form.is_valid():
            action = request.POST.get('action', 'save')
            
            try:
                if action == 'save':
                    # Save changes to the extracted question
                    updated_question = form.save()
                    messages.success(request, 'Question updated successfully.')
                    return redirect('pdf_extractor:document_detail', document_id=question.pdf_document.id)
                
                elif action == 'convert':
                    # Save changes and convert to question bank
                    updated_question = form.save()
                    
                    # Convert to question bank
                    converted_question = form.convert_to_question_bank()
                    
                    messages.success(
                        request, 
                        f'Question saved and converted to question bank "{converted_question.question_bank.name}" successfully.'
                    )
                    return redirect('pdf_extractor:document_detail', document_id=question.pdf_document.id)
                
                elif action == 'reject':
                    # Mark question as rejected
                    question.is_approved = False
                    question.requires_review = False
                    question.is_rejected = True
                    if not question.metadata:
                        question.metadata = {}
                    question.metadata.update({
                        'rejected_at': timezone.now().isoformat(),
                        'rejected_by': str(request.user.id),  # Convert UUID to string
                        'rejection_reason': 'Manual review rejection'
                    })
                    question.save()
                    
                    messages.info(request, 'Question has been rejected.')
                    return redirect('pdf_extractor:document_detail', document_id=question.pdf_document.id)
                
            except Exception as e:
                messages.error(request, f'Action failed: {str(e)}')
                
    else:
        form = EnhancedQuestionReviewForm(instance=question, user=request.user)
    
    # Add question bank conversion form for the template
    conversion_form = QuestionConversionForm(user=request.user)
    
    context = {
        'question': question,
        'form': form,
        'conversion_form': conversion_form,
        'document': question.pdf_document
    }
    
    return render(request, 'pdf_extractor/question_review.html', context)


@login_required
def convert_to_question_bank(request, question_id):
    """
    Convert extracted question to question bank
    """
    extracted_question = get_user_question_or_404(request, question_id)
    
    if extracted_question.is_converted:
        messages.warning(request, 'This question has already been converted.')
        return redirect('pdf_extractor:extracted_questions', document_id=extracted_question.pdf_document.id)
    
    if request.method == 'POST':
        form = QuestionConversionForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                question_bank = _get_or_create_question_bank(form, request.user)
                
                # Create Question object
                question = Question.objects.create(
                    question_bank=question_bank,
                    question_text=extracted_question.question_text,
                    question_type=extracted_question.question_type,
                    difficulty=extracted_question.estimated_difficulty or 'medium',
                    marks=extracted_question.estimated_marks or 1.0,
                    topic=extracted_question.estimated_topic,
                    explanation=extracted_question.explanation,
                    created_by=request.user
                )
                
                # Create options for MCQ questions
                if extracted_question.question_type in ['mcq', 'multi_select']:
                    _create_question_options(question, extracted_question)
                
                # Update extracted question
                extracted_question.is_converted = True
                extracted_question.converted_question = question
                extracted_question.question_bank = question_bank
                extracted_question.converted_at = timezone.now()
                extracted_question.save()
                
                messages.success(request, f'Question converted to "{question_bank.name}" successfully.')
                return redirect('pdf_extractor:extracted_questions', document_id=extracted_question.pdf_document.id)
            
            except Exception as e:
                messages.error(request, f'Conversion failed: {str(e)}')
    else:
        form = QuestionConversionForm(user=request.user)
    
    context = {
        'extracted_question': extracted_question,
        'form': form
    }
    
    return render(request, 'pdf_extractor/convert_question.html', context)


@login_required
def convert_all_questions(request, document_id):
    """
    Bulk convert extracted questions to question bank
    """
    document = get_user_document_or_404(request, document_id)
    
    if request.method == 'POST':
        form = BulkConversionForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                question_bank = form.cleaned_data['question_bank']
                confidence_filter = form.cleaned_data['confidence_filter']
                approved_only = form.cleaned_data['approved_only']
                
                # Build query for questions to convert
                questions_query = ExtractedQuestion.objects.filter(
                    pdf_document=document,
                    is_converted=False
                )
                
                if approved_only:
                    questions_query = questions_query.filter(is_approved=True)
                
                if confidence_filter == 'high':
                    questions_query = questions_query.filter(confidence_level='high')
                elif confidence_filter == 'medium_high':
                    questions_query = questions_query.filter(confidence_level__in=['high', 'medium'])
                
                questions_to_convert = list(questions_query)
                converted_count = 0
                
                for extracted_question in questions_to_convert:
                    try:
                        # Create Question object
                        question = Question.objects.create(
                            question_bank=question_bank,
                            question_text=extracted_question.question_text,
                            question_type=extracted_question.question_type,
                            difficulty=extracted_question.estimated_difficulty or 'medium',
                            marks=extracted_question.estimated_marks or 1.0,
                            topic=extracted_question.estimated_topic,
                            explanation=extracted_question.explanation,
                            created_by=request.user
                        )
                        
                        # Create options for MCQ questions
                        if extracted_question.question_type in ['mcq', 'multi_select']:
                            _create_question_options(question, extracted_question)
                        
                        # Update extracted question
                        extracted_question.is_converted = True
                        extracted_question.converted_question = question
                        extracted_question.question_bank = question_bank
                        extracted_question.converted_at = timezone.now()
                        extracted_question.save()
                        
                        converted_count += 1
                    
                    except Exception as e:
                        continue  # Skip problematic questions
                
                messages.success(request, f'Successfully converted {converted_count} questions to "{question_bank.name}".')
                return redirect('pdf_extractor:document_detail', document_id=document.id)
            
            except Exception as e:
                messages.error(request, f'Bulk conversion failed: {str(e)}')
    else:
        form = BulkConversionForm(user=request.user)
    
    # Get conversion candidates
    questions = ExtractedQuestion.objects.filter(
        pdf_document=document,
        is_converted=False
    ).order_by('-confidence_score')
    
    # Get questions by type
    from django.db.models import Count
    questions_by_type = {}
    type_counts = questions.values('question_type').annotate(count=Count('id'))
    for item in type_counts:
        questions_by_type[item['question_type']] = item['count']
    
    # Get confidence level counts
    confidence_counts = {
        'high': questions.filter(confidence_level='high').count(),
        'medium': questions.filter(confidence_level='medium').count(),
        'low': questions.filter(confidence_level='low').count(),
    }
    
    context = {
        'document': document,
        'form': form,
        'questions': questions,
        'candidates': questions,  # Keep for backward compatibility
        'total_candidates': questions.count(),
        'questions_by_type': questions_by_type,
        'confidence_counts': confidence_counts,
    }
    
    return render(request, 'pdf_extractor/convert_all_questions.html', context)


@login_required
def export_questions(request, document_id, format):
    """
    Export extracted questions in various formats
    """
    document = get_user_document_or_404(request, document_id)
    questions = ExtractedQuestion.objects.filter(pdf_document=document).order_by('page_number')
    
    if format == 'json':
        return _export_as_json(questions, document)
    elif format == 'csv':
        return _export_as_csv(questions, document)
    else:
        messages.error(request, 'Invalid export format.')
        return redirect('pdf_extractor:document_detail', document_id=document.id)


@login_required
def document_list(request):
    """
    List all user's PDF documents with real processing status and metadata filters
    """
    documents = get_user_documents_queryset(request).order_by('-uploaded_at')
    
    # Search functionality - enhanced to include metadata fields
    search_query = request.GET.get('search', '')
    if search_query:
        documents = documents.filter(
            Q(filename__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(extraction_notes__icontains=search_query) |
            Q(exam_name__icontains=search_query) |
            Q(organization__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(topic__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        documents = documents.filter(status=status_filter)
    
    # Filter by exam type
    exam_type_filter = request.GET.get('exam_type', '')
    if exam_type_filter:
        documents = documents.filter(exam_type=exam_type_filter)
    
    # Filter by organization
    organization_filter = request.GET.get('organization', '')
    if organization_filter:
        documents = documents.filter(organization__icontains=organization_filter)
    
    # Filter by subject
    subject_filter = request.GET.get('subject', '')
    if subject_filter:
        documents = documents.filter(subject__icontains=subject_filter)
    
    # Filter by year
    year_filter = request.GET.get('year', '')
    if year_filter:
        try:
            year = int(year_filter)
            documents = documents.filter(year=year)
        except ValueError:
            pass
    
    # Filter by source type
    source_type_filter = request.GET.get('source_type', '')
    if source_type_filter:
        documents = documents.filter(source_type=source_type_filter)
    
    # Filter by tags
    tags_filter = request.GET.get('tags', '')
    if tags_filter:
        # Support multiple tags separated by commas
        tag_list = [tag.strip() for tag in tags_filter.split(',') if tag.strip()]
        for tag in tag_list:
            documents = documents.filter(tags__icontains=tag)
    
    # Filter by user (superuser only)
    user_filter = request.GET.get('user', '')
    if user_filter and request.user.is_superuser:
        documents = documents.filter(uploaded_by__username__icontains=user_filter)
    
    # Filter by upload date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        try:
            from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            documents = documents.filter(uploaded_at__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            documents = documents.filter(uploaded_at__date__lte=to_date)
        except ValueError:
            pass
    
    # Filter by file size range
    size_filter = request.GET.get('size_range', '')
    if size_filter:
        if size_filter == 'small':  # < 5MB
            documents = documents.filter(file_size__lt=5*1024*1024)
        elif size_filter == 'medium':  # 5-20MB
            documents = documents.filter(file_size__gte=5*1024*1024, file_size__lt=20*1024*1024)
        elif size_filter == 'large':  # > 20MB
            documents = documents.filter(file_size__gte=20*1024*1024)
    
    # Sort options
    sort_by = request.GET.get('sort_by', '-uploaded_at')
    valid_sorts = ['-uploaded_at', 'uploaded_at', 'filename', '-filename', 'title', '-title', 'year', '-year']
    if sort_by in valid_sorts:
        documents = documents.order_by(sort_by)
    else:
        documents = documents.order_by('-uploaded_at')
    
    # Calculate real processing status for each document
    documents_with_status = []
    for document in documents:
        # Get page review statuses for this document
        page_statuses = PageReviewStatus.objects.filter(pdf_document=document)
        
        # Calculate real processing status
        processing_status = _calculate_document_processing_status(document, page_statuses)
        
        # Add processing status to document object
        document.processing_status = processing_status
        documents_with_status.append(document)
    
    # Pagination
    paginator = Paginator(documents_with_status, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'documents': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'exam_type_filter': exam_type_filter,
        'organization_filter': organization_filter,
        'subject_filter': subject_filter,
        'year_filter': year_filter,
        'source_type_filter': source_type_filter,
        'tags_filter': tags_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'size_filter': size_filter,
        'sort_by': sort_by,
        'exam_type_choices': PDFDocument.EXAM_TYPE_CHOICES,
        'source_type_choices': PDFDocument.SOURCE_TYPE_CHOICES,
    }
    
    return render(request, 'pdf_extractor/document_list.html', context)


@login_required
def metadata_templates(request):
    """
    Manage metadata templates
    """
    templates = MetadataTemplate.objects.filter(
        Q(created_by=request.user) | Q(is_public=True)
    ).order_by('-usage_count', '-created_at')
    
    context = {
        'templates': templates,
        'user_templates': templates.filter(created_by=request.user),
        'public_templates': templates.filter(is_public=True).exclude(created_by=request.user),
    }
    
    return render(request, 'pdf_extractor/metadata_templates.html', context)


@login_required
@require_http_methods(["GET", "POST"]) 
def create_metadata_template(request):
    """
    Create a new metadata template
    """
    if request.method == 'POST':
        form = MetadataTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            
            messages.success(request, f'Metadata template "{template.name}" created successfully!')
            return redirect('pdf_extractor:metadata_templates')
    else:
        form = MetadataTemplateForm()
    
    context = {
        'form': form,
        'page_title': 'Create Metadata Template'
    }
    return render(request, 'pdf_extractor/create_metadata_template.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def edit_metadata_template(request, template_id):
    """
    Edit an existing metadata template
    """
    template = get_object_or_404(MetadataTemplate, id=template_id, created_by=request.user)
    
    if request.method == 'POST':
        form = MetadataTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'Template "{template.name}" updated successfully!')
            return redirect('pdf_extractor:metadata_templates')
    else:
        form = MetadataTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'page_title': f'Edit Template: {template.name}'
    }
    return render(request, 'pdf_extractor/create_metadata_template.html', context)


@login_required
@require_http_methods(["POST"])
def delete_metadata_template(request, template_id):
    """
    Delete a metadata template
    """
    template = get_object_or_404(MetadataTemplate, id=template_id, created_by=request.user)
    template_name = template.name
    template.delete()
    
    messages.success(request, f'Template "{template_name}" deleted successfully!')
    return redirect('pdf_extractor:metadata_templates')


@login_required
@require_http_methods(["POST"])
def apply_metadata_template(request):
    """
    Apply a metadata template to selected documents
    """
    template_id = request.POST.get('template_id')
    document_ids = request.POST.getlist('document_ids')
    
    if not template_id or not document_ids:
        return JsonResponse({'success': False, 'error': 'Missing template or document selection'})
    
    try:
        template = MetadataTemplate.objects.get(
            Q(id=template_id) & (Q(created_by=request.user) | Q(is_public=True))
        )
        
        documents = PDFDocument.objects.filter(
            id__in=document_ids,
            uploaded_by=request.user
        )
        
        updated_count = 0
        for document in documents:
            template.apply_to_document(document)
            document.save()
            updated_count += 1
        
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'template_name': template.name
        })
        
    except MetadataTemplate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Template not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def extraction_templates(request):
    """
    Redirect to metadata templates for consistency
    """
    return redirect('pdf_extractor:metadata_templates')


# Helper functions

def _calculate_document_processing_status(document, page_statuses):
    """
    Calculate the real processing status based on page review statuses
    """
    if not page_statuses.exists():
        # No pages have been reviewed yet
        return {
            'status': 'pending_review',
            'display': 'Pending Review',
            'color': 'gray',
            'description': 'Not started yet',
            'pages_completed': 0,
            'total_pages': document.page_count or 0,
            'progress_percentage': 0
        }
    
    # Count different status types
    status_counts = {}
    for status in page_statuses:
        status_counts[status.status] = status_counts.get(status.status, 0) + 1
    
    total_pages = document.page_count or page_statuses.count()
    pages_reviewed = page_statuses.count()
    
    # Determine overall status based on page statuses
    if status_counts.get('pending_unsupported', 0) > 0:
        # Has unsupported questions
        unsupported_count = status_counts.get('pending_unsupported', 0)
        completed_count = status_counts.get('completed', 0)
        return {
            'status': 'has_unsupported',
            'display': 'Has Unsupported Questions',
            'color': 'orange',
            'description': f'{unsupported_count} page(s) with unsupported questions, {completed_count} completed',
            'pages_completed': completed_count,
            'total_pages': total_pages,
            'progress_percentage': int((completed_count / total_pages) * 100) if total_pages > 0 else 0,
            'unsupported_pages': unsupported_count
        }
    
    elif status_counts.get('completed', 0) == total_pages:
        # All pages completed
        return {
            'status': 'fully_complete',
            'display': 'Fully Complete',
            'color': 'green',
            'description': f'All {total_pages} pages completed',
            'pages_completed': total_pages,
            'total_pages': total_pages,
            'progress_percentage': 100
        }
    
    elif status_counts.get('in_progress', 0) > 0 or status_counts.get('completed', 0) > 0:
        # Some pages in progress or completed
        completed_count = status_counts.get('completed', 0)
        in_progress_count = status_counts.get('in_progress', 0)
        return {
            'status': 'in_progress',
            'display': 'In Progress',
            'color': 'blue',
            'description': f'{completed_count} completed, {in_progress_count} in progress',
            'pages_completed': completed_count,
            'total_pages': total_pages,
            'progress_percentage': int((completed_count / total_pages) * 100) if total_pages > 0 else 0
        }
    
    else:
        # Other statuses (no_questions, error, etc.)
        no_questions_count = status_counts.get('no_questions', 0)
        return {
            'status': 'partial_review',
            'display': 'Partial Review',
            'color': 'yellow',
            'description': f'{pages_reviewed} of {total_pages} pages reviewed',
            'pages_completed': 0,
            'total_pages': total_pages,
            'progress_percentage': int((pages_reviewed / total_pages) * 100) if total_pages > 0 else 0
        }


def _start_pdf_processing(pdf_document, processing_job):
    """
    Start PDF processing pipeline using background task processor
    """
    # Update job status to indicate processing has started
    processing_job.status = 'in_progress'
    processing_job.started_at = timezone.now()
    processing_job.save()
    
    # Start background processing
    def run_processing():
        try:
            # Process the document using the enhanced task processor
            result = process_pdf_document_task(pdf_document.id)
            
            if not result.get('success', False):
                # Handle processing failure
                processing_job.status = 'failed'
                processing_job.error_details = {
                    'error': result.get('error', 'Unknown error'),
                    'step': result.get('step', 'unknown')
                }
                processing_job.save()
                
                pdf_document.status = 'failed'
                pdf_document.error_message = result.get('error', 'Processing failed')
                pdf_document.save()
            
        except Exception as e:
            # Handle unexpected errors
            processing_job.status = 'failed'
            processing_job.error_details = {'error': str(e), 'step': 'background_processing'}
            processing_job.save()
            
            pdf_document.status = 'failed'
            pdf_document.error_message = str(e)
            pdf_document.save()
    
    # Start processing in a separate thread
    # In production, this would be replaced with a proper task queue like Celery
    processing_thread = threading.Thread(target=run_processing)
    processing_thread.daemon = True
    processing_thread.start()


def _get_or_create_question_bank(form, user):
    """
    Get existing or create new question bank based on form data
    """
    if form.cleaned_data['create_new_bank']:
        question_bank = QuestionBank.objects.create(
            name=form.cleaned_data['new_bank_name'],
            category=form.cleaned_data['new_bank_category'],
            created_by=user
        )
    else:
        question_bank = form.cleaned_data['question_bank']
    
    return question_bank


def _create_question_options(question, extracted_question):
    """
    Create question options for MCQ questions
    """
    from questions.models import QuestionOption
    
    options = extracted_question.answer_options
    correct_answers = extracted_question.correct_answers
    
    for i, option in enumerate(options):
        is_correct = option.get('letter', '') in correct_answers or option.get('text', '') in correct_answers
        
        QuestionOption.objects.create(
            question=question,
            option_text=option.get('text', ''),
            is_correct=is_correct,
            order=i
        )


def _export_as_json(questions, document):
    """
    Export questions as JSON
    """
    questions_data = []
    for q in questions:
        questions_data.append({
            'question_text': q.question_text,
            'question_type': q.question_type,
            'page_number': q.page_number,
            'answer_options': q.answer_options,
            'correct_answers': q.correct_answers,
            'explanation': q.explanation,
            'confidence_score': q.confidence_score,
            'estimated_difficulty': q.estimated_difficulty,
            'estimated_topic': q.estimated_topic
        })
    
    response = HttpResponse(
        json.dumps(questions_data, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{document.filename}_questions.json"'
    return response


def _export_as_csv(questions, document):
    """
    Export questions as CSV
    """
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Question Text', 'Question Type', 'Page Number', 'Answer Options',
        'Correct Answers', 'Explanation', 'Confidence Score', 'Difficulty', 'Topic'
    ])
    
    # Data rows
    for q in questions:
        writer.writerow([
            q.question_text,
            q.get_question_type_display(),
            q.page_number,
            '; '.join([opt.get('text', '') for opt in q.answer_options]),
            '; '.join(q.correct_answers),
            q.explanation,
            q.confidence_score,
            q.estimated_difficulty,
            q.estimated_topic
        ])
    
    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{document.filename}_questions.csv"'
    return response


# New Interactive Region Review Views

@login_required
def region_review_interface(request, document_id):
    """
    Main interface for reviewing and correcting extracted regions
    """
    document = get_user_document_or_404(request, document_id)
    
    # Get or create review session
    session, created = RegionReviewSession.objects.get_or_create(
        pdf_document=document,
        reviewer=request.user,
        status='in_progress',
        defaults={
            'total_pages': document.page_count or 1,
            'current_page': 1
        }
    )
    
    # Get page data with regions
    page_number = int(request.GET.get('page', session.current_page))
    page_data = _get_page_data_with_regions(document, page_number)
    
    context = {
        'document': document,
        'session': session,
        'page_data': page_data,
        'current_page': page_number,
        'total_pages': document.page_count or 1,
        'corrections_made': RegionCorrection.objects.filter(
            pdf_document=document,
            corrected_by=request.user
        ).count()
    }
    
    return render(request, 'pdf_extractor/region_review_interface.html', context)


@login_required
def get_page_regions_api(request, document_id, page_number):
    """
    API endpoint to get regions for a specific page
    """
    document = get_user_document_or_404(request, document_id)
    page_data = _get_page_data_with_regions(document, page_number)
    
    return JsonResponse({
        'success': True,
        'page_number': page_number,
        'regions': page_data.get('regions', []),
        'image_url': page_data.get('image_url', ''),
        'image_dimensions': page_data.get('image_dimensions', {}),
        'metadata': page_data.get('metadata', {})
    })


@login_required
def save_region_correction(request, document_id):
    """
    Save a region correction made by the user
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        
        # Create region correction record
        correction = RegionCorrection.objects.create(
            pdf_document=document,
            page_number=data['page_number'],
            original_coordinates=data['original_coordinates'],
            corrected_coordinates=data['corrected_coordinates'],
            correction_type=data['correction_type'],
            correction_reason=data.get('reason', ''),
            corrected_by=request.user,
            confidence_before=data.get('confidence_before'),
            confidence_after=data.get('confidence_after')
        )
        
        # Update session statistics
        session = RegionReviewSession.objects.filter(
            pdf_document=document,
            reviewer=request.user,
            status='in_progress'
        ).first()
        
        if session:
            session.regions_corrected += 1
            session.save()
        
        return JsonResponse({
            'success': True,
            'correction_id': str(correction.id),
            'message': 'Region correction saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def batch_approve_regions(request, document_id):
    """
    Batch approve multiple regions on a page
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        page_number = data['page_number']
        region_ids = data['region_ids']
        action = data.get('action', 'approve')  # approve, reject, auto_fix
        
        # Update session
        session = RegionReviewSession.objects.filter(
            pdf_document=document,
            reviewer=request.user,
            status='in_progress'
        ).first()
        
        if session:
            if action == 'approve':
                session.regions_approved += len(region_ids)
            elif action == 'reject':
                session.regions_rejected += len(region_ids)
            
            # Mark page as reviewed if not already
            if page_number > session.pages_reviewed:
                session.pages_reviewed = page_number
            
            session.save()
        
        return JsonResponse({
            'success': True,
            'processed_count': len(region_ids),
            'action': action
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def complete_review_session(request, document_id):
    """
    Complete the current review session
    """
    document = get_user_document_or_404(request, document_id)
    
    session = RegionReviewSession.objects.filter(
        pdf_document=document,
        reviewer=request.user,
        status='in_progress'
    ).first()
    
    if session:
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()
        
        messages.success(request, f'Review session completed! You reviewed {session.pages_reviewed} pages and made {session.regions_corrected} corrections.')
    
    return redirect('pdf_extractor:document_detail', document_id=document_id)


@login_required
def region_visualization(request, document_id, page_number):
    """
    Generate region visualization for debugging
    """
    document = get_user_document_or_404(request, document_id)
    
    # This would generate a visualization of detected regions
    # For now, return the page data
    page_data = _get_page_data_with_regions(document, page_number)
    
    return JsonResponse({
        'success': True,
        'visualization_url': f'/media/visualizations/{document_id}_page_{page_number}.png',
        'regions_count': len(page_data.get('regions', [])),
        'page_data': page_data
    })


def _get_page_data_with_regions(document, page_number):
    """
    Helper function to get page data with detected regions
    """
    # Try to get from processing results first
    processing_jobs = document.processing_jobs.filter(status='completed').order_by('-completed_at')
    
    page_data = {
        'page_number': page_number,
        'regions': [],
        'image_url': '',
        'image_dimensions': {'width': 0, 'height': 0},
        'metadata': {}
    }
    
    # Load actual extracted questions from processing results
    regions = []
    
    # Get extracted questions for this page
    from .models import ExtractedQuestion, SavedRegion
    extracted_questions = ExtractedQuestion.objects.filter(
        pdf_document=document,
        page_number=page_number
    ).order_by('id')
    
    # Also get saved regions for this page
    saved_regions = SavedRegion.objects.filter(
        pdf_document=document,
        page_number=page_number
    ).order_by('processed_at')
    
    if extracted_questions.exists():
        # Convert extracted questions to region format
        for i, question in enumerate(extracted_questions):
            # Create question region
            question_region = {
                'id': f'question_{question.id}',
                'type': 'question',
                'confidence': min(question.confidence_score / 100, 1.0),  # Normalize confidence to 0-1
                'text': question.question_text,
                'needs_review': question.requires_review,
                'metadata': {
                    'question_type': question.question_type,
                    'extraction_method': question.extraction_method,
                    'estimated_difficulty': question.estimated_difficulty
                }
            }
            
            # Use position if available, otherwise create estimated positions
            if question.position_on_page and question.position_on_page.get('x') is not None:
                question_region['coordinates'] = question.position_on_page
            else:
                # Create estimated positions based on question order
                y_offset = 100 + (i * 200)  # Space questions vertically
                question_region['coordinates'] = {
                    'x': 50, 
                    'y': y_offset, 
                    'width': 500, 
                    'height': 80
                }
            
            regions.append(question_region)
            
            # Create answer options region if available
            if question.answer_options:
                answer_text = '\n'.join([f"{opt['letter']}) {opt['text']}" for opt in question.answer_options])
                answer_region = {
                    'id': f'answers_{question.id}',
                    'type': 'answer_options',
                    'coordinates': {
                        'x': question_region['coordinates']['x'] + 20,
                        'y': question_region['coordinates']['y'] + 90,
                        'width': 450,
                        'height': min(30 * len(question.answer_options), 120)
                    },
                    'confidence': question_region['confidence'] * 0.9,  # Slightly lower confidence for options
                    'text': answer_text,
                    'needs_review': len(question.answer_options) < 2,  # Review if fewer than 2 options
                    'metadata': {
                        'question_id': str(question.id),
                        'option_count': len(question.answer_options)
                    }
                }
                regions.append(answer_region)
    
    # Add saved regions to the regions list
    if saved_regions.exists():
        for saved_region in saved_regions:
            region_data = {
                'id': f'saved_{saved_region.id}',
                'type': saved_region.region_type,
                'coordinates': saved_region.coordinates,
                'confidence': saved_region.confidence_score,
                'text': saved_region.extracted_text or f'{saved_region.get_status_display()} region',
                'needs_review': saved_region.status in ['detected', 'error'],
                'status': saved_region.status,
                'status_display': saved_region.get_status_display(),
                'notes': saved_region.notes,
                'metadata': {
                    'saved_region_id': str(saved_region.id),
                    'processed_by': saved_region.processed_by.username if saved_region.processed_by else None,
                    'processed_at': saved_region.processed_at.isoformat() if saved_region.processed_at else None,
                    'status_color': saved_region.status_color
                }
            }
            regions.append(region_data)
    
    if not regions:
        # Fallback to mock data if no questions found
        regions = [
            {
                'id': f'mock_region_{page_number}_1',
                'type': 'question',
                'coordinates': {'x': 50, 'y': 100, 'width': 500, 'height': 80},
                'confidence': 0.85,
                'text': f'No extracted questions found for page {page_number}. This is mock data.',
                'needs_review': True,
                'metadata': {'is_mock': True}
            }
        ]
    
    page_data['regions'] = regions
    
    if processing_jobs.exists():
        # Look for cached regions in processing job results
        # This would typically come from the enhanced processing pipeline
        pass  # TODO: Load actual regions when processing is complete
        
    # Try to find the converted image
    try:
        import os
        from django.conf import settings
        
        # Look for cached PDF images
        cache_dir = os.path.join(settings.MEDIA_ROOT, 'pdf_image_cache')
        if os.path.exists(cache_dir):
            # Look for images with various naming patterns
            possible_patterns = [
                f'page_{page_number}.png',
                f'{document.id}_p{page_number}_dpi150.png',
                f'*_p{page_number}_*.png'
            ]
            
            import glob
            for pattern in possible_patterns:
                matches = glob.glob(os.path.join(cache_dir, pattern))
                if matches:
                    # Use the first match found
                    image_path = matches[0]
                    relative_path = os.path.relpath(image_path, settings.MEDIA_ROOT)
                    page_data['image_url'] = f'/media/{relative_path}'
                    page_data['image_dimensions'] = {'width': 800, 'height': 1000}
                    break
            else:
                # No cached image found, provide a placeholder
                page_data['image_url'] = ''
                page_data['image_dimensions'] = {'width': 800, 'height': 1000}
        else:
            # Cache directory doesn't exist
            page_data['image_url'] = ''
            page_data['image_dimensions'] = {'width': 800, 'height': 1000}
    except Exception as e:
        # Fallback for any errors
        page_data['image_url'] = ''
        page_data['image_dimensions'] = {'width': 800, 'height': 1000}
    
    return page_data


@login_required 
def mark_regions_unsupported_api(request, document_id):
    """
    API endpoint to mark selected regions as unsupported question type
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        page_number = data.get('page_number', 1)
        regions = data.get('regions', [])
        notes = data.get('notes', '')
        
        if not regions:
            return JsonResponse({'success': False, 'error': 'No regions provided'})
        
        from .models import SavedRegion, PageReviewStatus
        
        saved_regions = []
        for region_data in regions:
            # Save each region with unsupported status
            saved_region = SavedRegion.objects.create(
                pdf_document=document,
                page_number=page_number,
                coordinates=region_data.get('coordinates', {}),
                region_type=region_data.get('type', 'unknown'),
                extracted_text=region_data.get('text_preview', region_data.get('text', '')),
                confidence_score=region_data.get('confidence', 0.0),
                status='unsupported',
                notes=notes,
                processed_by=request.user
            )
            saved_regions.append(saved_region)
        
        # Update page status if needed
        page_status, created = PageReviewStatus.objects.get_or_create(
            pdf_document=document,
            page_number=page_number,
            defaults={
                'status': 'pending_unsupported',
                'notes': notes,
                'reviewed_by': request.user,
                'reviewed_at': timezone.now()
            }
        )
        
        # Update page status to reflect unsupported regions
        if not created:
            # If page already exists, update it to pending_unsupported status
            page_status.status = 'pending_unsupported'
            page_status.notes = f"{page_status.notes}\n{notes}".strip()
            page_status.reviewed_by = request.user
            page_status.reviewed_at = timezone.now()
            page_status.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{len(saved_regions)} regions marked as unsupported',
            'regions_saved': len(saved_regions)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def delete_saved_region_api(request, document_id, region_id):
    """
    API endpoint to delete a saved region
    """
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'DELETE required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        from .models import SavedRegion, PageReviewStatus
        
        saved_region = get_object_or_404(SavedRegion, id=region_id, pdf_document=document)
        page_number = saved_region.page_number
        
        # Delete the region
        saved_region.delete()
        
        # Check if there are any remaining unsupported regions on this page
        remaining_unsupported = SavedRegion.objects.filter(
            pdf_document=document,
            page_number=page_number,
            status='unsupported'
        ).count()
        
        # Update page status if no more unsupported regions
        if remaining_unsupported == 0:
            try:
                page_status = PageReviewStatus.objects.get(
                    pdf_document=document,
                    page_number=page_number
                )
                
                # Check if there are any completed regions
                completed_regions = SavedRegion.objects.filter(
                    pdf_document=document,
                    page_number=page_number,
                    status='completed'
                ).count()
                
                if completed_regions > 0:
                    page_status.status = 'completed'
                else:
                    page_status.status = 'pending'
                    
                page_status.save()
                
            except PageReviewStatus.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Region deleted successfully',
            'remaining_unsupported': remaining_unsupported
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def update_saved_region_api(request, document_id, region_id):
    """
    API endpoint to update a saved region's properties
    """
    if request.method != 'PUT':
        return JsonResponse({'success': False, 'error': 'PUT required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        from .models import SavedRegion
        
        saved_region = get_object_or_404(SavedRegion, id=region_id, pdf_document=document)
        
        # Update allowed fields
        if 'coordinates' in data:
            saved_region.coordinates = data['coordinates']
        if 'status' in data:
            saved_region.status = data['status']
        if 'notes' in data:
            saved_region.notes = data['notes']
        if 'region_type' in data:
            saved_region.region_type = data['region_type']
            
        saved_region.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Region updated successfully',
            'region': {
                'id': str(saved_region.id),
                'coordinates': saved_region.coordinates,
                'status': saved_region.status,
                'notes': saved_region.notes,
                'region_type': saved_region.region_type,
                'status_color': saved_region.status_color
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def mark_page_complete_api(request, document_id):
    """
    API endpoint to mark a page as complete after processing all supported questions
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        page_number = data.get('page_number', 1)
        
        from .models import PageReviewStatus, SavedRegion
        
        # Check if there are any unsupported regions on this page
        unsupported_regions = SavedRegion.objects.filter(
            pdf_document=document,
            page_number=page_number,
            status='unsupported'
        ).count()
        
        # Determine appropriate status
        if unsupported_regions > 0:
            # Mixed content: some completed, some unsupported
            status = 'pending_unsupported'
            message = f'Page {page_number} marked as complete with {unsupported_regions} unsupported regions'
        else:
            # Fully completed
            status = 'completed'
            message = f'Page {page_number} marked as complete'
        
        # Update page status
        page_status, created = PageReviewStatus.objects.get_or_create(
            pdf_document=document,
            page_number=page_number,
            defaults={
                'status': status,
                'reviewed_by': request.user,
                'reviewed_at': timezone.now(),
                'processing_completed_at': timezone.now()
            }
        )
        
        if not created:
            page_status.status = status
            page_status.reviewed_by = request.user
            page_status.reviewed_at = timezone.now()
            page_status.processing_completed_at = timezone.now()
            page_status.save()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'page_status': status,
            'unsupported_regions': unsupported_regions
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def delete_saved_region_api(request, document_id, region_id):
    """
    API endpoint to delete a saved region
    """
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'DELETE required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        from .models import SavedRegion, PageReviewStatus
        
        saved_region = get_object_or_404(SavedRegion, id=region_id, pdf_document=document)
        page_number = saved_region.page_number
        
        # Delete the region
        saved_region.delete()
        
        # Check if there are any remaining unsupported regions on this page
        remaining_unsupported = SavedRegion.objects.filter(
            pdf_document=document,
            page_number=page_number,
            status='unsupported'
        ).count()
        
        # Update page status if no more unsupported regions
        if remaining_unsupported == 0:
            try:
                page_status = PageReviewStatus.objects.get(
                    pdf_document=document,
                    page_number=page_number
                )
                
                # Check if there are any completed regions
                completed_regions = SavedRegion.objects.filter(
                    pdf_document=document,
                    page_number=page_number,
                    status='completed'
                ).count()
                
                if completed_regions > 0:
                    page_status.status = 'completed'
                else:
                    page_status.status = 'pending'
                    
                page_status.save()
                
            except PageReviewStatus.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Region deleted successfully',
            'remaining_unsupported': remaining_unsupported
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def update_saved_region_api(request, document_id, region_id):
    """
    API endpoint to update a saved region's properties
    """
    if request.method != 'PUT':
        return JsonResponse({'success': False, 'error': 'PUT required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        from .models import SavedRegion
        
        saved_region = get_object_or_404(SavedRegion, id=region_id, pdf_document=document)
        
        # Update allowed fields
        if 'coordinates' in data:
            saved_region.coordinates = data['coordinates']
        if 'status' in data:
            saved_region.status = data['status']
        if 'notes' in data:
            saved_region.notes = data['notes']
        if 'region_type' in data:
            saved_region.region_type = data['region_type']
            
        saved_region.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Region updated successfully',
            'region': {
                'id': str(saved_region.id),
                'coordinates': saved_region.coordinates,
                'status': saved_region.status,
                'notes': saved_region.notes,
                'region_type': saved_region.region_type,
                'status_color': saved_region.status_color
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def saved_regions_api(request, document_id, page_number):
    """
    API endpoint to get saved regions for a specific page
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'GET required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        from .models import SavedRegion
        
        saved_regions = SavedRegion.objects.filter(
            pdf_document=document,
            page_number=page_number
        ).order_by('processed_at')
        
        regions_data = []
        for region in saved_regions:
            regions_data.append({
                'id': str(region.id),
                'coordinates': region.coordinates,
                'region_type': region.region_type,
                'extracted_text': region.extracted_text,
                'confidence_score': region.confidence_score,
                'status': region.status,
                'status_display': region.get_status_display(),
                'notes': region.notes,
                'processed_at': region.processed_at.isoformat(),
                'status_color': region.status_color
            })
        
        return JsonResponse({
            'success': True,
            'regions': regions_data,
            'count': len(regions_data)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def delete_saved_region_api(request, document_id, region_id):
    """
    API endpoint to delete a saved region
    """
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'DELETE required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        from .models import SavedRegion, PageReviewStatus
        
        saved_region = get_object_or_404(SavedRegion, id=region_id, pdf_document=document)
        page_number = saved_region.page_number
        
        # Delete the region
        saved_region.delete()
        
        # Check if there are any remaining unsupported regions on this page
        remaining_unsupported = SavedRegion.objects.filter(
            pdf_document=document,
            page_number=page_number,
            status='unsupported'
        ).count()
        
        # Update page status if no more unsupported regions
        if remaining_unsupported == 0:
            try:
                page_status = PageReviewStatus.objects.get(
                    pdf_document=document,
                    page_number=page_number
                )
                
                # Check if there are any completed regions
                completed_regions = SavedRegion.objects.filter(
                    pdf_document=document,
                    page_number=page_number,
                    status='completed'
                ).count()
                
                if completed_regions > 0:
                    page_status.status = 'completed'
                else:
                    page_status.status = 'pending'
                    
                page_status.save()
                
            except PageReviewStatus.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Region deleted successfully',
            'remaining_unsupported': remaining_unsupported
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def update_saved_region_api(request, document_id, region_id):
    """
    API endpoint to update a saved region's properties
    """
    if request.method != 'PUT':
        return JsonResponse({'success': False, 'error': 'PUT required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        from .models import SavedRegion
        
        saved_region = get_object_or_404(SavedRegion, id=region_id, pdf_document=document)
        
        # Update allowed fields
        if 'coordinates' in data:
            saved_region.coordinates = data['coordinates']
        if 'status' in data:
            saved_region.status = data['status']
        if 'notes' in data:
            saved_region.notes = data['notes']
        if 'region_type' in data:
            saved_region.region_type = data['region_type']
            
        saved_region.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Region updated successfully',
            'region': {
                'id': str(saved_region.id),
                'coordinates': saved_region.coordinates,
                'status': saved_region.status,
                'notes': saved_region.notes,
                'region_type': saved_region.region_type,
                'status_color': saved_region.status_color
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def save_extracted_questions_api(request, document_id):
    """
    Enhanced API endpoint to save extracted questions and create saved regions
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        page_number = data.get('page_number', 1)
        questions_data = data.get('questions', [])
        
        if not questions_data:
            return JsonResponse({'success': False, 'error': 'No questions provided'})
        
        from .models import SavedRegion, PageReviewStatus
        
        # Get or create a processing job
        processing_job = document.processing_jobs.first()
        if not processing_job:
            processing_job = ProcessingJob.objects.create(
                pdf_document=document,
                status='in_progress'
            )
        
        saved_questions = []
        saved_regions = []
        
        for q_data in questions_data:
            # Create ExtractedQuestion
            extracted_question = ExtractedQuestion.objects.create(
                pdf_document=document,
                processing_job=processing_job,
                question_text=q_data.get('question_text', ''),
                question_type=q_data.get('question_type', 'unknown'),
                page_number=page_number,
                position_on_page=q_data.get('position', {}),
                answer_options=q_data.get('answer_options', []),
                correct_answers=q_data.get('correct_answers', []),
                confidence_score=q_data.get('confidence', 80.0),  # Already in 0-100 range from frontend
                confidence_level='medium',
                extraction_method='interactive_review'
            )
            extracted_question.set_confidence_level()
            extracted_question.save()
            
            # Create corresponding SavedRegion
            saved_region = SavedRegion.objects.create(
                pdf_document=document,
                page_number=page_number,
                coordinates=q_data.get('position', {}),
                region_type='question',
                extracted_text=q_data.get('question_text', ''),
                confidence_score=q_data.get('confidence', 0.0),
                status='completed',
                processed_by=request.user,
                extracted_question=extracted_question
            )
            
            saved_questions.append(extracted_question)
            saved_regions.append(saved_region)
        
        # Smart page status logic - check for unsupported regions first
        unsupported_regions_count = SavedRegion.objects.filter(
            pdf_document=document,
            page_number=page_number,
            status='unsupported'
        ).count()
        
        completed_regions_count = SavedRegion.objects.filter(
            pdf_document=document,
            page_number=page_number,
            status='completed'
        ).count()
        
        # Determine appropriate status based on region mix
        # NOTE: Only explicit "Mark Page as Complete" button should make pages green
        if unsupported_regions_count > 0:
            # Page has unsupported regions - should stay orange
            page_status_value = 'pending_unsupported'
        elif completed_regions_count > 0:
            # Page has some completed regions but user hasn't explicitly marked as complete
            # Stay in progress until user clicks "Mark Page as Complete"
            page_status_value = 'in_progress'
        else:
            # Page has no completed or unsupported regions - stay pending
            page_status_value = 'pending'
        
        # Update page status
        page_status, created = PageReviewStatus.objects.get_or_create(
            pdf_document=document,
            page_number=page_number,
            defaults={
                'status': page_status_value,
                'questions_found': len(saved_questions),
                'questions_extracted': len(saved_questions),
                'reviewed_by': request.user,
                'reviewed_at': timezone.now(),
                'processing_completed_at': None  # Only set when explicitly marked complete
            }
        )
        
        if not created:
            page_status.questions_extracted += len(saved_questions)
            page_status.status = page_status_value
            page_status.reviewed_by = request.user 
            page_status.reviewed_at = timezone.now()
            # Don't set processing_completed_at until explicitly marked complete
            if page_status_value != 'completed':
                page_status.processing_completed_at = None
            page_status.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{len(saved_questions)} questions saved successfully',
            'questions_saved': len(saved_questions),
            'regions_saved': len(saved_regions)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def delete_saved_region_api(request, document_id, region_id):
    """
    API endpoint to delete a saved region
    """
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'DELETE required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        from .models import SavedRegion, PageReviewStatus
        
        saved_region = get_object_or_404(SavedRegion, id=region_id, pdf_document=document)
        page_number = saved_region.page_number
        
        # Delete the region
        saved_region.delete()
        
        # Check if there are any remaining unsupported regions on this page
        remaining_unsupported = SavedRegion.objects.filter(
            pdf_document=document,
            page_number=page_number,
            status='unsupported'
        ).count()
        
        # Update page status if no more unsupported regions
        if remaining_unsupported == 0:
            try:
                page_status = PageReviewStatus.objects.get(
                    pdf_document=document,
                    page_number=page_number
                )
                
                # Check if there are any completed regions
                completed_regions = SavedRegion.objects.filter(
                    pdf_document=document,
                    page_number=page_number,
                    status='completed'
                ).count()
                
                if completed_regions > 0:
                    page_status.status = 'completed'
                else:
                    page_status.status = 'pending'
                    
                page_status.save()
                
            except PageReviewStatus.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Region deleted successfully',
            'remaining_unsupported': remaining_unsupported
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def update_saved_region_api(request, document_id, region_id):
    """
    API endpoint to update a saved region's properties
    """
    if request.method != 'PUT':
        return JsonResponse({'success': False, 'error': 'PUT required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        from .models import SavedRegion
        
        saved_region = get_object_or_404(SavedRegion, id=region_id, pdf_document=document)
        
        # Update allowed fields
        if 'coordinates' in data:
            saved_region.coordinates = data['coordinates']
        if 'status' in data:
            saved_region.status = data['status']
        if 'notes' in data:
            saved_region.notes = data['notes']
        if 'region_type' in data:
            saved_region.region_type = data['region_type']
            
        saved_region.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Region updated successfully',
            'region': {
                'id': str(saved_region.id),
                'coordinates': saved_region.coordinates,
                'status': saved_region.status,
                'notes': saved_region.notes,
                'region_type': saved_region.region_type,
                'status_color': saved_region.status_color
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@login_required
def search_questions_api(request, document_id):
    """
    API endpoint to search all questions for a document (regardless of pagination)
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "error": "GET required"})
    
    document = get_user_document_or_404(request, document_id)
    
    # Get search parameters
    text_search = request.GET.get("text", "").strip()
    page_search = request.GET.get("page", "").strip()
    
    # Start with all questions for this document
    questions = ExtractedQuestion.objects.filter(pdf_document=document)
    
    # Apply text search filter
    if text_search:
        from django.db import models
        questions = questions.filter(
            models.Q(question_text__icontains=text_search) |
            models.Q(answer_options__icontains=text_search) |
            models.Q(correct_answers__icontains=text_search) |
            models.Q(question_type__icontains=text_search)
        )
    
    # Apply page number filter
    if page_search and page_search.isdigit():
        questions = questions.filter(page_number=int(page_search))
    
    # Order and limit results
    questions = questions.order_by("page_number", "id")[:100]  # Limit to 100 results
    
    # Format the results
    results = []
    for question in questions:
        results.append({
            "id": str(question.id),
            "question_text": question.question_text,
            "question_type": question.get_question_type_display(),
            "page_number": question.page_number,
            "confidence_level": question.get_confidence_level_display(),
            "answer_options": question.answer_options,
            "correct_answers": question.correct_answers,
            "is_converted": question.is_converted,
        })
    
    return JsonResponse({
        "success": True,
        "questions": results,
        "total_found": len(results)
    })


# Admin Document Management API Views
@login_required
@require_http_methods(["GET"])
def admin_documents_api(request):
    """Get all documents for admin management"""
    if not request.user.is_superuser:
        return JsonResponse({
            'error': 'Permission denied', 
            'user': request.user.username,
            'is_superuser': request.user.is_superuser,
            'is_staff': request.user.is_staff
        }, status=403)
    
    try:
        documents = PDFDocument.objects.select_related('uploaded_by').all()
        
        documents_data = []
        for doc in documents:
            documents_data.append({
                'id': str(doc.id),
                'title': doc.title or doc.filename,
                'filename': doc.filename,
                'user': doc.uploaded_by.username if doc.uploaded_by else 'Unknown',
                'status': doc.status,
                'question_count': doc.extracted_questions.count(),
                'uploaded_at': doc.uploaded_at.isoformat(),
            })
        
        return JsonResponse(documents_data, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def admin_document_stats_api(request):
    """Get document statistics for admin dashboard"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        from django.db.models import Count, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        # Basic counts
        total_documents = PDFDocument.objects.count()
        processed_documents = PDFDocument.objects.filter(status='completed').count()
        in_progress_documents = PDFDocument.objects.filter(status='processing').count()
        total_questions = ExtractedQuestion.objects.count()
        
        # Calculate average processing time (mock data for now)
        avg_processing_time = 5.2  # minutes
        
        # Calculate success rate
        success_rate = (processed_documents / total_documents * 100) if total_documents > 0 else 0
        
        return JsonResponse({
            'total': total_documents,
            'processed': processed_documents,
            'in_progress': in_progress_documents,
            'questions': total_questions,
            'avg_time': round(avg_processing_time, 1),
            'success_rate': round(success_rate, 1),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def admin_processing_status_api(request):
    """Get processing status information"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:        
        total_docs = PDFDocument.objects.count()
        in_progress = PDFDocument.objects.filter(status='processing').count()
        completed = PDFDocument.objects.filter(status='completed').count()
        
        success_rate = (completed / total_docs * 100) if total_docs > 0 else 0
        avg_time = 4.8  # Mock average processing time in minutes
        
        return JsonResponse({
            'in_progress': in_progress,
            'success_rate': round(success_rate, 1),
            'avg_time': avg_time,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def admin_recent_activity_api(request):
    """Get recent document activity"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Get recent documents (last 7 days)
        recent_docs = PDFDocument.objects.filter(
            uploaded_at__gte=timezone.now() - timedelta(days=7)
        ).select_related('uploaded_by').order_by('-uploaded_at')[:10]
        
        activities = []
        for doc in recent_docs:
            activities.append({
                'description': f'"{doc.title or doc.filename}" uploaded by {doc.uploaded_by.username if doc.uploaded_by else "Unknown"}',
                'timestamp': doc.uploaded_at.strftime('%Y-%m-%d %H:%M'),
            })
        
        return JsonResponse({'activities': activities})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def admin_analytics_api(request):
    """Get document analytics data"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        
        # Current month uploads
        current_month = timezone.now().replace(day=1)
        uploads_this_month = PDFDocument.objects.filter(
            uploaded_at__gte=current_month
        ).count()
        
        # Success rate
        total_docs = PDFDocument.objects.count()
        completed_docs = PDFDocument.objects.filter(status='completed').count()
        success_rate = (completed_docs / total_docs * 100) if total_docs > 0 else 0
        
        # Popular exam types
        exam_type_counts = PDFDocument.objects.values('exam_type').annotate(
            count=Count('exam_type')
        ).filter(exam_type__isnull=False).order_by('-count')[:5]
        
        popular_exam_types = [
            {'name': item['exam_type'], 'count': item['count']}
            for item in exam_type_counts
        ]
        
        # Active users (users who uploaded in last week)
        week_ago = timezone.now() - timedelta(days=7)
        active_users = PDFDocument.objects.filter(
            uploaded_at__gte=week_ago
        ).values('uploaded_by').distinct().count()
        
        return JsonResponse({
            'uploads_this_month': uploads_this_month,
            'success_rate': round(success_rate, 1),
            'popular_exam_types': popular_exam_types,
            'active_users': active_users,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@login_required
@require_http_methods(["POST"])
def delete_question_api(request, question_id):
    """Delete a specific extracted question"""
    try:
        # Get the question and ensure user has permission
        question = get_object_or_404(ExtractedQuestion, id=question_id)
        
        # Check permissions - user must own the document or be superuser
        if question.pdf_document.uploaded_by != request.user and not request.user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Delete the question
        question.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Question deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to delete question: {str(e)}'
        }, status=500)

