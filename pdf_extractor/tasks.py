import logging
import time
import json
from typing import Dict, Any, Optional
from django.utils import timezone
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from .models import PDFDocument, ProcessingJob, ExtractedQuestion, ProcessingStatistics
from .processors import PDFTextExtractor, QuestionAnswerDetector
from .security import PDFSecurityValidator
from .error_handling import (
    error_handler, ProcessingLogger, with_error_handling,
    PDFProcessingError, FileSecurityError, OCRProcessingError,
    TextExtractionError, QuestionDetectionError, ProcessingTimeoutError
)

logger = logging.getLogger(__name__)


class PDFProcessingTask:
    """
    Background task processor for PDF Q&A extraction
    """
    
    def __init__(self):
        self.text_extractor = PDFTextExtractor()
        self.qa_detector = QuestionAnswerDetector()
        self.security_validator = PDFSecurityValidator()
        self.processing_logger = None  # Will be initialized per job
        
        # Processing steps with estimated time weights
        self.processing_steps = [
            {
                'step': 'upload_validation',
                'display': 'Validating uploaded file',
                'weight': 0.05,
                'method': self._validate_upload
            },
            {
                'step': 'text_detection',
                'display': 'Analyzing document structure',
                'weight': 0.10,
                'method': self._detect_text_type
            },
            {
                'step': 'ocr_processing',
                'display': 'Processing with OCR (if needed)',
                'weight': 0.30,
                'method': self._process_ocr_if_needed
            },
            {
                'step': 'layout_analysis',
                'display': 'Analyzing document layout',
                'weight': 0.15,
                'method': self._analyze_layout
            },
            {
                'step': 'text_extraction',
                'display': 'Extracting text content',
                'weight': 0.20,
                'method': self._extract_text
            },
            {
                'step': 'qa_detection',
                'display': 'Detecting questions and answers',
                'weight': 0.15,
                'method': self._detect_qa_pairs
            },
            {
                'step': 'answer_extraction',
                'display': 'Extracting answer options',
                'weight': 0.03,
                'method': self._extract_answers
            },
            {
                'step': 'confidence_scoring',
                'display': 'Calculating confidence scores',
                'weight': 0.02,
                'method': self._calculate_confidence
            },
            {
                'step': 'finalization',
                'display': 'Finalizing extraction results',
                'weight': 0.05,
                'method': self._finalize_processing
            }
        ]
    
    def process_pdf_document(self, document_id: int) -> Dict[str, Any]:
        """
        Main method to process a PDF document with real-time progress updates
        """
        start_time = time.time()
        job = None
        
        try:
            # Get document and create processing job
            document = PDFDocument.objects.get(id=document_id)
            job = ProcessingJob.objects.create(
                pdf_document=document,
                status='in_progress',
                current_step='upload_validation',
                progress_percentage=0
            )
            
            # Initialize processing logger
            self.processing_logger = ProcessingLogger(
                job_id=str(job.id),
                document_id=str(document_id)
            )
            
            # Log processing start
            self.processing_logger.log_step_start('document_processing', {
                'filename': document.filename,
                'file_size': document.file_size,
                'page_count': document.page_count
            })
            
            # Initialize processing context
            context = {
                'document': document,
                'job': job,
                'text_content': None,
                'qa_pairs': [],
                'statistics': {},
                'errors': []
            }
            
            logger.info(f"Starting PDF processing for document {document_id}")
            
            # Execute processing steps
            total_weight = sum(step['weight'] for step in self.processing_steps)
            cumulative_progress = 0
            
            for step_info in self.processing_steps:
                step_start_time = time.time()
                
                try:
                    # Log step start
                    self.processing_logger.log_step_start(step_info['step'], {
                        'display_name': step_info['display']
                    })
                    
                    # Update job status
                    self._update_job_progress(
                        job, 
                        step_info['step'], 
                        step_info['display'],
                        cumulative_progress
                    )
                    
                    # Execute step with timeout check
                    max_step_time = 300  # 5 minutes max per step
                    step_result = step_info['method'](context)
                    
                    if time.time() - step_start_time > max_step_time:
                        raise ProcessingTimeoutError(
                            f"Step {step_info['step']} exceeded time limit",
                            details={'elapsed_time': time.time() - step_start_time}
                        )
                    
                    if not step_result.get('success', True):
                        raise PDFProcessingError(
                            f"Step {step_info['step']} failed: {step_result.get('error', 'Unknown error')}",
                            error_code=f"STEP_{step_info['step'].upper()}_FAILED",
                            details=step_result
                        )
                    
                    # Log step completion
                    step_duration = time.time() - step_start_time
                    self.processing_logger.log_step_complete(
                        step_info['step'], 
                        step_duration,
                        step_result
                    )
                    
                    # Update progress
                    cumulative_progress += int((step_info['weight'] / total_weight) * 100)
                    
                    # Small delay to make progress visible (remove in production)
                    time.sleep(0.1)
                    
                except Exception as e:
                    # Handle error using error handler
                    error_handler.handle_processing_error(e, job, step_info['step'])
                    
                    # Log the error
                    logger.error(f"Error in step {step_info['step']}: {str(e)}")
                    context['errors'].append(f"{step_info['step']}: {str(e)}")
                    
                    return {
                        'success': False,
                        'error': str(e),
                        'step': step_info['step']
                    }
            
            # Mark job as completed
            job.status = 'completed'
            job.progress_percentage = 100
            job.current_step = 'completed'
            job.current_step_display = 'Processing complete'
            job.completed_at = timezone.now()
            job.save()
            
            # Update document status
            document.status = 'completed'
            document.save()
            
            logger.info(f"Successfully processed document {document_id}")
            
            return {
                'success': True,
                'document_id': document_id,
                'questions_found': len(context['qa_pairs']),
                'statistics': context['statistics']
            }
            
        except Exception as e:
            logger.error(f"Fatal error processing document {document_id}: {str(e)}")
            
            # Mark document as failed
            if 'document' in locals():
                document.status = 'failed'
                document.save()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_job_progress(self, job: ProcessingJob, step: str, display: str, progress: int):
        """
        Update job progress in database
        """
        job.current_step = step
        job.current_step_display = display
        job.progress_percentage = min(progress, 100)
        job.save(update_fields=['current_step', 'current_step_display', 'progress_percentage'])
    
    def _validate_upload(self, context: Dict) -> Dict[str, Any]:
        """
        Validate uploaded PDF file
        """
        document = context['document']
        
        try:
            # Re-open the file for processing
            with document.file.open('rb') as pdf_file:
                # Read all content into memory for validation
                file_content = pdf_file.read()
                
                # Create a BytesIO object that mimics UploadedFile
                from io import BytesIO
                temp_buffer = BytesIO(file_content)
                temp_buffer.name = document.filename
                temp_buffer.size = document.file_size
                
                # Validate security
                validation_result = self.security_validator.validate_pdf_file(temp_buffer)
                
                if not validation_result['is_valid']:
                    error_messages = '; '.join(validation_result.get('errors', ['Unknown validation error']))
                    raise FileSecurityError(
                        f"Security validation failed: {error_messages}",
                        details=validation_result
                    )
                
                # Update document with validation info
                document.page_count = validation_result.get('page_count', 0)
                document.save()
                
                return {'success': True, 'validation_result': validation_result}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _detect_text_type(self, context: Dict) -> Dict[str, Any]:
        """
        Detect if PDF contains searchable text or needs OCR
        """
        document = context['document']
        
        try:
            with document.file.open('rb') as pdf_file:
                # Read all content into memory for analysis
                file_content = pdf_file.read()
                
                # Create a BytesIO object that mimics UploadedFile
                from io import BytesIO
                temp_buffer = BytesIO(file_content)
                temp_buffer.name = document.filename
                temp_buffer.size = document.file_size
                
                # Analyze text content
                text_analysis = self.text_extractor.text_detector.analyze_pdf_text_content(temp_buffer)
                
                # Store analysis results
                context['text_analysis'] = text_analysis
                
                return {'success': True, 'text_analysis': text_analysis}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _process_ocr_if_needed(self, context: Dict) -> Dict[str, Any]:
        """
        Process with OCR if needed based on text analysis
        """
        text_analysis = context.get('text_analysis', {})
        
        if text_analysis.get('is_searchable', False):
            # Skip OCR processing
            return {'success': True, 'skipped': True, 'reason': 'Text is searchable'}
        
        # OCR would be processed during text extraction step
        return {'success': True, 'ocr_needed': True}
    
    def _analyze_layout(self, context: Dict) -> Dict[str, Any]:
        """
        Analyze document layout
        """
        try:
            # Layout analysis happens during text extraction
            # This step is for progress indication
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_text(self, context: Dict) -> Dict[str, Any]:
        """
        Extract text content from PDF
        """
        document = context['document']
        
        try:
            with document.file.open('rb') as pdf_file:
                # Read all content into memory for processing
                file_content = pdf_file.read()
                
                # Create a BytesIO object that mimics UploadedFile
                from io import BytesIO
                temp_buffer = BytesIO(file_content)
                temp_buffer.name = document.filename
                temp_buffer.size = document.file_size
                
                # Extract text with layout information
                text_content = self.text_extractor.extract_text_with_layout(temp_buffer)
                
                if not text_content.get('success', False):
                    raise Exception("Text extraction failed")
                
                context['text_content'] = text_content
                
                # Track processing methods used
                context['processing_method'] = text_content.get('processing_method', 'standard')
                context['layout_analysis_used'] = text_content.get('layout_analysis_used', False)
                context['ocr_used'] = text_content.get('ocr_used', False)
                
                return {'success': True, 'pages_processed': text_content.get('total_pages', 0)}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _detect_qa_pairs(self, context: Dict) -> Dict[str, Any]:
        """
        Detect question-answer pairs
        """
        text_content = context.get('text_content')
        
        if not text_content:
            return {'success': False, 'error': 'No text content available'}
        
        try:
            # Detect Q&A pairs
            qa_pairs = self.qa_detector.detect_qa_pairs(text_content)
            
            context['qa_pairs'] = qa_pairs
            
            return {'success': True, 'questions_found': len(qa_pairs)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_answers(self, context: Dict) -> Dict[str, Any]:
        """
        Extract and enhance answer options
        """
        qa_pairs = context.get('qa_pairs', [])
        
        try:
            # Answers are already extracted during Q&A detection
            # This step is for any additional answer processing
            
            enhanced_pairs = []
            for qa_pair in qa_pairs:
                # Additional answer enhancement could go here
                enhanced_pairs.append(qa_pair)
            
            context['qa_pairs'] = enhanced_pairs
            
            return {'success': True, 'pairs_processed': len(enhanced_pairs)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _calculate_confidence(self, context: Dict) -> Dict[str, Any]:
        """
        Calculate confidence scores for extracted Q&A pairs
        """
        qa_pairs = context.get('qa_pairs', [])
        text_content = context.get('text_content')
        
        try:
            # Confidence scores are already calculated during detection
            # This step could do additional confidence refinement
            
            high_confidence = sum(1 for qa in qa_pairs if qa.get('confidence_level') == 'high')
            medium_confidence = sum(1 for qa in qa_pairs if qa.get('confidence_level') == 'medium')
            low_confidence = sum(1 for qa in qa_pairs if qa.get('confidence_level') == 'low')
            
            context['statistics'] = {
                'total_questions': len(qa_pairs),
                'high_confidence': high_confidence,
                'medium_confidence': medium_confidence,
                'low_confidence': low_confidence,
                'needs_review': low_confidence
            }
            
            return {'success': True, 'statistics': context['statistics']}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _finalize_processing(self, context: Dict) -> Dict[str, Any]:
        """
        Finalize processing and save results to database
        """
        document = context['document']
        qa_pairs = context.get('qa_pairs', [])
        statistics = context.get('statistics', {})
        
        try:
            with transaction.atomic():
                # Get the processing job for this document
                job = context['job']
                
                # Save extracted questions
                for qa_pair in qa_pairs:
                    ExtractedQuestion.objects.create(
                        pdf_document=document,
                        processing_job=job,
                        question_text=qa_pair.get('question_text', ''),
                        question_type=qa_pair.get('question_type', 'unknown'),
                        page_number=qa_pair.get('page_number', 1),
                        confidence_score=qa_pair.get('confidence_score', 0.5),
                        confidence_level=qa_pair.get('confidence_level', 'medium'),
                        answer_options=qa_pair.get('answer_options', []),
                        correct_answers=qa_pair.get('correct_answers', []),
                        extraction_method=qa_pair.get('extraction_method', 'unknown'),
                        metadata={
                            'position_on_page': qa_pair.get('position_on_page', {}),
                            'confidence_factors': qa_pair.get('confidence_factors', {}),
                            'format_type': qa_pair.get('format_type', ''),
                        }
                    )
                
                # Save processing statistics
                ProcessingStatistics.objects.create(
                    pdf_document=document,
                    total_questions_found=statistics.get('total_questions', 0),
                    high_confidence_questions=statistics.get('high_confidence', 0),
                    medium_confidence_questions=statistics.get('medium_confidence', 0),
                    low_confidence_questions=statistics.get('low_confidence', 0),
                    questions_requiring_review=statistics.get('needs_review', 0),
                    questions_by_confidence={
                        'high': statistics.get('high_confidence', 0),
                        'medium': statistics.get('medium_confidence', 0),
                        'low': statistics.get('low_confidence', 0)
                    },
                    average_confidence_score=sum(qa.get('confidence_score', 0) for qa in qa_pairs) / len(qa_pairs) if qa_pairs else 0,
                    processing_method=context.get('processing_method', 'standard'),
                    layout_analysis_used=context.get('layout_analysis_used', False),
                    ocr_used=context.get('ocr_used', False)
                )
                
                # Update document confidence
                if qa_pairs:
                    avg_confidence = sum(qa.get('confidence_score', 0) for qa in qa_pairs) / len(qa_pairs)
                    document.confidence_score = avg_confidence * 100  # Convert to percentage
                    document.save()
            
            return {'success': True, 'saved_questions': len(qa_pairs)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Task runner function for background processing
def process_pdf_document_task(document_id: int) -> Dict[str, Any]:
    """
    Entry point for background PDF processing
    """
    processor = PDFProcessingTask()
    return processor.process_pdf_document(document_id)