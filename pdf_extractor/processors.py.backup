import io
import re
import json
import PyPDF2
import pdfplumber
from typing import Dict, List, Tuple, Any, Optional
from django.core.files.uploadedfile import UploadedFile
import logging
from .models import PDFDocument, ProcessingJob, ExtractedQuestion
from .ocr_processors import OCRManager
from .layout_analysis import AdvancedLayoutAnalyzer, MultiColumnTextProcessor
from .question_classifier import QuestionTypeClassifier, QuestionDifficultyEstimator, TopicExtractor
from .pdf_to_image import PDFToImageConverter, ImagePreprocessor
from .region_extractor import RegionExtractor, RegionCorrector, Region
from dataclasses import dataclass

# Get logger
logger = logging.getLogger(__name__)


class PDFTextDetector:
    """
    Detects whether PDF contains searchable text or requires OCR
    """
    
    @staticmethod
    def analyze_pdf_text_content(pdf_file: UploadedFile) -> Dict[str, Any]:
        """
        Analyze PDF to determine if it contains searchable text
        """
        analysis_result = {
            'is_searchable': False,
            'needs_ocr': True,
            'text_coverage': 0.0,
            'sample_text': '',
            'page_analysis': [],
            'confidence': 0.0
        }
        
        try:
            # Reset file pointer
            pdf_file.seek(0)
            
            # Use pdfplumber for better text extraction analysis
            with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
                total_pages = len(pdf.pages)
                text_pages = 0
                total_characters = 0
                
                # Analyze up to first 10 pages for performance
                pages_to_check = min(10, total_pages)
                
                for i, page in enumerate(pdf.pages[:pages_to_check]):
                    page_text = page.extract_text()
                    
                    page_analysis = {
                        'page_number': i + 1,
                        'has_text': bool(page_text and len(page_text.strip()) > 10),
                        'character_count': len(page_text) if page_text else 0,
                        'word_count': len(page_text.split()) if page_text else 0
                    }
                    
                    analysis_result['page_analysis'].append(page_analysis)
                    
                    if page_analysis['has_text']:
                        text_pages += 1
                        total_characters += page_analysis['character_count']
                        
                        # Store sample text from first text page
                        if not analysis_result['sample_text'] and page_text:
                            analysis_result['sample_text'] = page_text[:500]
                
                # Calculate metrics
                analysis_result['text_coverage'] = text_pages / pages_to_check if pages_to_check > 0 else 0.0
                analysis_result['is_searchable'] = analysis_result['text_coverage'] > 0.7  # 70% threshold
                analysis_result['needs_ocr'] = not analysis_result['is_searchable']
                
                # Confidence calculation
                if analysis_result['text_coverage'] > 0.9:
                    analysis_result['confidence'] = 0.95
                elif analysis_result['text_coverage'] > 0.7:
                    analysis_result['confidence'] = 0.85
                elif analysis_result['text_coverage'] > 0.3:
                    analysis_result['confidence'] = 0.6
                else:
                    analysis_result['confidence'] = 0.3
        
        except Exception as e:
            analysis_result['error'] = str(e)
            analysis_result['confidence'] = 0.0
        
        finally:
            pdf_file.seek(0)
        
        return analysis_result


class PDFTextExtractor:
    """
    Extracts text from PDF files with spatial awareness
    """
    
    def __init__(self):
        self.text_detector = PDFTextDetector()
        self.ocr_manager = OCRManager()
        self.layout_analyzer = AdvancedLayoutAnalyzer()
        self.multi_column_processor = MultiColumnTextProcessor()
        self.pdf_to_image = PDFToImageConverter()
        self.image_preprocessor = ImagePreprocessor()
        self.region_extractor = RegionExtractor()
    
    def extract_text_with_layout(self, pdf_file: UploadedFile) -> Dict[str, Any]:
        """
        Extract text while preserving spatial relationships and layout information
        """
        extraction_result = {
            'success': False,
            'pages': [],
            'total_pages': 0,
            'extraction_method': 'unknown',
            'layout_info': {},
            'errors': []
        }
        
        # First, detect if text extraction is possible
        text_analysis = self.text_detector.analyze_pdf_text_content(pdf_file)
        
        try:
            pdf_file.seek(0)
            
            logger.info(f"PDF analysis: is_searchable={text_analysis['is_searchable']}")
            
            if text_analysis['is_searchable']:
                # Use direct text extraction
                logger.info("Using direct text extraction for searchable PDF")
                extraction_result = self._extract_searchable_text(pdf_file)
                extraction_result['extraction_method'] = 'direct_text'
                extraction_result['processing_method'] = 'standard'
                extraction_result['layout_analysis_used'] = True
                extraction_result['ocr_used'] = False
            else:
                # Convert to images for better processing
                logger.info("PDF is not searchable, using image-based extraction")
                image_result = self.pdf_to_image.convert_for_region_detection(pdf_file)
                
                logger.info(f"Image conversion result: success={image_result['success']}, images={len(image_result.get('images', []))}")
                
                if image_result['success']:
                    # Use image-based extraction with OCR
                    logger.info("Using image-based extraction with OCR")
                    extraction_result = self._extract_from_images(pdf_file, image_result)
                    extraction_result['extraction_method'] = 'image_based_ocr'
                    extraction_result['processing_method'] = 'advanced'
                    extraction_result['layout_analysis_used'] = True
                    extraction_result['ocr_used'] = True
                else:
                    # Fallback to standard OCR
                    logger.info("Image conversion failed, falling back to standard OCR")
                    extraction_result = self.ocr_manager.process_pdf_with_best_ocr(pdf_file)
                    extraction_result['extraction_method'] = 'ocr'
                    extraction_result['processing_method'] = 'standard'
                    extraction_result['layout_analysis_used'] = False
                    extraction_result['ocr_used'] = True
        
        except Exception as e:
            extraction_result['errors'].append(f"Text extraction failed: {str(e)}")
        
        logger.info(f"Final extraction result: success={extraction_result.get('success')}, pages={len(extraction_result.get('pages', []))}, errors={len(extraction_result.get('errors', []))}")
        if extraction_result.get('errors'):
            logger.error(f"Extraction errors found: {extraction_result['errors']}")
        
        return extraction_result
    
    def _extract_searchable_text(self, pdf_file: UploadedFile) -> Dict[str, Any]:
        """
        Extract text from searchable PDF using pdfplumber
        """
        result = {
            'success': False,
            'pages': [],
            'total_pages': 0,
            'layout_info': {'detected_columns': 1, 'layout_type': 'single_column'},
            'errors': []
        }
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
                result['total_pages'] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_data = self._extract_page_with_layout(page, page_num)
                    
                    # Enhance with advanced layout analysis
                    if hasattr(page, 'to_image'):
                        try:
                            page_image = page.to_image(resolution=150)
                            advanced_layout = self.layout_analyzer.analyze_page_layout(page_image.original, page_num)
                            
                            # Enhance layout with text data
                            advanced_layout = self.layout_analyzer.enhance_layout_with_text_data(
                                advanced_layout, page_data
                            )
                            
                            page_data['advanced_layout'] = advanced_layout
                            
                            # Process multi-column text if detected
                            if len(advanced_layout.get('columns', [])) > 1:
                                multi_column_result = self.multi_column_processor.process_multi_column_text(
                                    page_data, advanced_layout
                                )
                                page_data['multi_column_text'] = multi_column_result
                        
                        except Exception as e:
                            page_data['layout_analysis_error'] = str(e)
                    
                    result['pages'].append(page_data)
                
                # Analyze overall layout
                result['layout_info'] = self._analyze_document_layout(result['pages'])
                result['success'] = True
        
        except Exception as e:
            result['errors'].append(f"Searchable text extraction failed: {str(e)}")
        
        return result
    
    def _extract_page_with_layout(self, page, page_number: int) -> Dict[str, Any]:
        """
        Extract text from a single page with layout information
        """
        page_data = {
            'page_number': page_number,
            'text': '',
            'words': [],
            'lines': [],
            'paragraphs': [],
            'layout_info': {},
            'bounding_boxes': []
        }
        
        try:
            # Extract raw text
            page_data['text'] = page.extract_text() or ''
            
            # Extract word-level information with coordinates
            words = page.extract_words()
            page_data['words'] = [
                {
                    'text': word['text'],
                    'x0': word['x0'], 'y0': word['y0'],
                    'x1': word['x1'], 'y1': word['y1'],
                    'fontname': word.get('fontname', ''),
                    'size': word.get('size', 0)
                }
                for word in words
            ]
            
            # Group words into lines and paragraphs
            page_data['lines'] = self._group_words_into_lines(page_data['words'])
            page_data['paragraphs'] = self._group_lines_into_paragraphs(page_data['lines'])
            
            # Detect layout structure
            page_data['layout_info'] = self._detect_page_layout(page_data['words'], page.width, page.height)
        
        except Exception as e:
            page_data['error'] = str(e)
        
        return page_data
    
    def _group_words_into_lines(self, words: List[Dict]) -> List[Dict]:
        """
        Group words into lines based on y-coordinates
        """
        if not words:
            return []
        
        # Sort words by y-coordinate (top to bottom) then x-coordinate (left to right)
        sorted_words = sorted(words, key=lambda w: (-w['y1'], w['x0']))
        
        lines = []
        current_line = []
        current_y = None
        tolerance = 5  # Y-coordinate tolerance for same line
        
        for word in sorted_words:
            if current_y is None or abs(word['y1'] - current_y) <= tolerance:
                current_line.append(word)
                current_y = word['y1']
            else:
                if current_line:
                    lines.append({
                        'words': current_line,
                        'text': ' '.join([w['text'] for w in current_line]),
                        'y_position': current_y,
                        'x_start': min([w['x0'] for w in current_line]),
                        'x_end': max([w['x1'] for w in current_line])
                    })
                current_line = [word]
                current_y = word['y1']
        
        # Add the last line
        if current_line:
            lines.append({
                'words': current_line,
                'text': ' '.join([w['text'] for w in current_line]),
                'y_position': current_y,
                'x_start': min([w['x0'] for w in current_line]),
                'x_end': max([w['x1'] for w in current_line])
            })
        
        return lines
    
    def _group_lines_into_paragraphs(self, lines: List[Dict]) -> List[Dict]:
        """
        Group lines into paragraphs based on spacing and alignment
        """
        if not lines:
            return []
        
        paragraphs = []
        current_paragraph = []
        
        for i, line in enumerate(lines):
            if not current_paragraph:
                current_paragraph = [line]
            else:
                # Check if this line should start a new paragraph
                prev_line = lines[i-1]
                y_gap = prev_line['y_position'] - line['y_position']
                
                # Large gap or significant indent change suggests new paragraph
                if y_gap > 20 or abs(line['x_start'] - prev_line['x_start']) > 50:
                    # Finish current paragraph
                    paragraphs.append({
                        'lines': current_paragraph,
                        'text': '\n'.join([l['text'] for l in current_paragraph]),
                        'start_y': current_paragraph[0]['y_position'],
                        'end_y': current_paragraph[-1]['y_position']
                    })
                    current_paragraph = [line]
                else:
                    current_paragraph.append(line)
        
        # Add the last paragraph
        if current_paragraph:
            paragraphs.append({
                'lines': current_paragraph,
                'text': '\n'.join([l['text'] for l in current_paragraph]),
                'start_y': current_paragraph[0]['y_position'],
                'end_y': current_paragraph[-1]['y_position']
            })
        
        return paragraphs
    
    def _detect_page_layout(self, words: List[Dict], page_width: float, page_height: float) -> Dict[str, Any]:
        """
        Detect page layout (single/multi-column, margins, etc.)
        """
        layout_info = {
            'page_width': page_width,
            'page_height': page_height,
            'columns': 1,
            'column_boundaries': [],
            'margins': {'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        }
        
        if not words:
            return layout_info
        
        # Calculate margins
        x_coords = [w['x0'] for w in words] + [w['x1'] for w in words]
        y_coords = [w['y0'] for w in words] + [w['y1'] for w in words]
        
        layout_info['margins'] = {
            'left': min(x_coords),
            'right': page_width - max(x_coords),
            'top': page_height - max(y_coords),
            'bottom': min(y_coords)
        }
        
        # Detect columns by analyzing x-coordinate distribution
        x_starts = [w['x0'] for w in words]
        
        # Simple column detection: look for gaps in x-coordinate distribution
        x_starts_sorted = sorted(set(x_starts))
        
        if len(x_starts_sorted) > 1:
            # Look for significant gaps that might indicate column boundaries
            gaps = []
            for i in range(len(x_starts_sorted) - 1):
                gap = x_starts_sorted[i + 1] - x_starts_sorted[i]
                if gap > 50:  # Significant gap threshold
                    gaps.append((x_starts_sorted[i], x_starts_sorted[i + 1], gap))
            
            if gaps:
                # Sort by gap size and take the largest
                largest_gap = max(gaps, key=lambda x: x[2])
                if largest_gap[2] > page_width * 0.1:  # Gap is > 10% of page width
                    layout_info['columns'] = 2
                    layout_info['column_boundaries'] = [largest_gap[0], largest_gap[1]]
        
        return layout_info
    
    def _analyze_document_layout(self, pages: List[Dict]) -> Dict[str, Any]:
        """
        Analyze overall document layout across all pages
        """
        layout_summary = {
            'detected_columns': 1,
            'layout_type': 'single_column',
            'consistent_layout': True,
            'average_margins': {'left': 0, 'right': 0, 'top': 0, 'bottom': 0},
            'advanced_analysis': {
                'has_advanced_layout': False,
                'multi_column_pages': 0,
                'average_confidence': 0.0,
                'common_layout_types': []
            }
        }
        
        if not pages:
            return layout_summary
        
        # Check for advanced layout analysis
        advanced_layouts = []
        basic_column_counts = []
        
        for page in pages:
            # Check advanced layout first
            if 'advanced_layout' in page:
                advanced_layout = page['advanced_layout']
                advanced_layouts.append(advanced_layout)
                column_count = len(advanced_layout.get('columns', []))
                if column_count == 0:
                    column_count = 1  # Fallback
            else:
                # Fall back to basic layout analysis
                column_count = page.get('layout_info', {}).get('columns', 1)
                # Ensure column_count is an integer
                if not isinstance(column_count, int):
                    column_count = 1
            
            basic_column_counts.append(column_count)
        
        # Update summary with advanced analysis if available
        if advanced_layouts:
            layout_summary['advanced_analysis']['has_advanced_layout'] = True
            layout_summary['advanced_analysis']['multi_column_pages'] = sum(
                1 for layout in advanced_layouts 
                if len(layout.get('columns', [])) > 1
            )
            
            # Calculate average confidence
            confidences = [layout.get('confidence', 0) for layout in advanced_layouts]
            if confidences:
                layout_summary['advanced_analysis']['average_confidence'] = sum(confidences) / len(confidences)
            
            # Collect layout types (ensure they are strings)
            layout_types = []
            for layout in advanced_layouts:
                layout_type = layout.get('layout_type', 'unknown')
                # Convert to string if it's not already a string
                if isinstance(layout_type, (list, dict)):
                    layout_type = str(layout_type)
                layout_types.append(layout_type)
            
            # Use set only with hashable (string) types
            try:
                layout_summary['advanced_analysis']['common_layout_types'] = list(set(layout_types))
            except TypeError:
                # Fallback if any types are still unhashable
                unique_types = []
                for layout_type in layout_types:
                    if layout_type not in unique_types:
                        unique_types.append(layout_type)
                layout_summary['advanced_analysis']['common_layout_types'] = unique_types
            
            # Use advanced column detection for overall summary
            advanced_column_counts = []
            for layout in advanced_layouts:
                columns = layout.get('columns', [])
                if isinstance(columns, list):
                    count = len(columns) or 1
                else:
                    count = 1
                advanced_column_counts.append(count)
            try:
                most_common_columns = max(set(advanced_column_counts), key=advanced_column_counts.count)
            except TypeError:
                # Fallback: find most frequent count manually
                if advanced_column_counts:
                    # Count occurrences manually
                    count_freq = {}
                    for count in advanced_column_counts:
                        if isinstance(count, (int, float)):
                            count_freq[count] = count_freq.get(count, 0) + 1
                    most_common_columns = max(count_freq.keys()) if count_freq else 1
                else:
                    most_common_columns = 1
        else:
            # Use basic column detection
            try:
                most_common_columns = max(set(basic_column_counts), key=basic_column_counts.count)
            except TypeError:
                # Fallback: find most frequent count manually
                if basic_column_counts:
                    # Count occurrences manually
                    count_freq = {}
                    for count in basic_column_counts:
                        if isinstance(count, (int, float)):
                            count_freq[count] = count_freq.get(count, 0) + 1
                    most_common_columns = max(count_freq.keys()) if count_freq else 1
                else:
                    most_common_columns = 1
        
        layout_summary['detected_columns'] = most_common_columns
        
        # Determine overall layout type
        if most_common_columns == 1:
            layout_summary['layout_type'] = 'single_column'
        elif most_common_columns == 2:
            layout_summary['layout_type'] = 'two_column'
        elif most_common_columns >= 3:
            layout_summary['layout_type'] = 'multi_column'
        else:
            layout_summary['layout_type'] = 'mixed'
        
        # Check layout consistency
        column_counts_to_check = advanced_column_counts if advanced_layouts else basic_column_counts
        try:
            layout_summary['consistent_layout'] = len(set(column_counts_to_check)) == 1
        except TypeError:
            # Fallback: check manually if all counts are the same
            if column_counts_to_check:
                first_count = column_counts_to_check[0]
                layout_summary['consistent_layout'] = all(count == first_count for count in column_counts_to_check)
            else:
                layout_summary['consistent_layout'] = True
        
        # Calculate average margins (prefer advanced if available)
        if advanced_layouts:
            margins_list = []
            for layout in advanced_layouts:
                for region in layout.get('text_regions', []):
                    # Convert region positions to margin-like metrics
                    margins_list.append({
                        'left': region.get('x', 0),
                        'top': region.get('y', 0),
                        'right': layout.get('page_width', 0) - (region.get('x', 0) + region.get('width', 0)),
                        'bottom': layout.get('page_height', 0) - (region.get('y', 0) + region.get('height', 0))
                    })
        else:
            margins_list = [page.get('layout_info', {}).get('margins', {}) for page in pages]
        
        if margins_list:
            avg_margins = {}
            for key in ['left', 'right', 'top', 'bottom']:
                values = [m.get(key, 0) for m in margins_list if m.get(key) is not None]
                avg_margins[key] = sum(values) / len(values) if values else 0
            layout_summary['average_margins'] = avg_margins
        
        return layout_summary
    
    def _extract_from_images(self, pdf_file: UploadedFile, image_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract text from PDF using converted images with advanced preprocessing
        
        Args:
            pdf_file: Original PDF file
            image_result: Result from PDF to image conversion
            
        Returns:
            Dict containing extraction results
        """
        result = {
            'success': False,
            'pages': [],
            'total_pages': len(image_result['images']),
            'layout_info': {},
            'errors': []
        }
        
        try:
            for image_info in image_result['images']:
                page_num = image_info['page_number']
                
                # Load image
                from PIL import Image
                image = Image.open(image_info['path'])
                
                # Preprocess image for better OCR
                preprocessed_image = self.image_preprocessor.preprocess_for_ocr(image)
                
                # Detect and correct skew
                corrected_image, skew_angle = self.image_preprocessor.detect_and_correct_skew(preprocessed_image)
                
                # Perform OCR on preprocessed image
                ocr_result = self.ocr_manager.process_image_with_ocr(corrected_image)
                
                # Debug logging
                logger.info(f"Page {page_num} OCR result: success={ocr_result.get('success')}, text_length={len(ocr_result.get('text', ''))}, error={ocr_result.get('error', 'none')}")
                
                if ocr_result['success']:
                    try:
                        # Advanced layout analysis on the original image
                        logger.info(f"Starting layout analysis for page {page_num}")
                        layout_analysis = self.layout_analyzer.analyze_page_layout(image, page_num)
                        logger.info(f"Layout analysis completed for page {page_num}")
                        
                        # Extract regions for interactive review
                        logger.info(f"Starting region extraction for page {page_num}")
                        detected_regions = self.region_extractor.extract_regions_from_image(image, page_num)
                        logger.info(f"Region extraction completed for page {page_num}, regions: {len(detected_regions)}")
                        
                        # Combine OCR results with layout analysis
                        page_data = {
                            'page_number': page_num,
                            'text': ocr_result.get('text', ''),
                            'words': ocr_result.get('words', []),
                            'lines': ocr_result.get('lines', []),
                            'paragraphs': ocr_result.get('paragraphs', []),
                            'layout_info': layout_analysis,
                            'preprocessing_info': {
                                'skew_corrected': abs(skew_angle) > 0.5,
                                'skew_angle': skew_angle,
                                'preprocessing_applied': True
                            },
                            'image_info': {
                                'path': image_info['path'],
                                'width': image_info['width'],
                                'height': image_info['height'],
                                'dpi': image_info['dpi']
                            },
                            'detected_regions': self._safe_serialize_regions(detected_regions)
                        }
                        
                        # Process multi-column text if detected
                        if len(layout_analysis.get('columns', [])) > 1:
                            logger.info(f"Processing multi-column text for page {page_num}")
                            multi_column_result = self.multi_column_processor.process_multi_column_text(
                                page_data, layout_analysis
                            )
                            page_data['multi_column_text'] = multi_column_result
                            
                        result['pages'].append(page_data)
                        logger.info(f"Successfully processed page {page_num}, total pages: {len(result['pages'])}")
                        
                    except Exception as page_error:
                        logger.error(f"Error processing page {page_num} after successful OCR: {str(page_error)}")
                        result['errors'].append(f"Post-OCR processing failed for page {page_num}: {str(page_error)}")
                        # Still add basic page data even if advanced processing fails
                        basic_page_data = {
                            'page_number': page_num,
                            'text': ocr_result.get('text', ''),
                            'words': ocr_result.get('words', []),
                            'lines': ocr_result.get('lines', []),
                            'paragraphs': ocr_result.get('paragraphs', []),
                            'layout_info': {},
                            'detected_regions': []
                        }
                        result['pages'].append(basic_page_data)
                
                else:
                    result['errors'].append(f"OCR failed for page {page_num}: {ocr_result.get('error', 'Unknown error')}")
            
            # Analyze overall document layout
            if result['pages']:
                result['layout_info'] = self._analyze_document_layout(result['pages'])
                # Set success based on pages processed vs errors
                if len(result['errors']) == 0:
                    result['success'] = True
                else:
                    logger.warning(f"Setting success=False due to {len(result['errors'])} errors: {result['errors']}")
                    result['success'] = False
            
        except Exception as e:
            result['errors'].append(f"Image-based extraction failed: {str(e)}")
            
        return result

    def _safe_serialize_regions(self, detected_regions):
        """Safely serialize detected regions, handling unhashable types"""
        safe_regions = []
        
        for region in detected_regions:
            try:
                if hasattr(region, 'to_dict'):
                    # Try to serialize the region
                    region_dict = region.to_dict()
                    
                    # Check for lists in metadata that might cause issues
                    if 'metadata' in region_dict and isinstance(region_dict['metadata'], dict):
                        # Convert any list values to strings to avoid unhashable type errors
                        safe_metadata = {}
                        for key, value in region_dict['metadata'].items():
                            if isinstance(value, list):
                                safe_metadata[key] = str(value)  # Convert list to string
                            elif isinstance(value, dict):
                                safe_metadata[key] = json.dumps(value)  # Convert dict to JSON string
                            else:
                                safe_metadata[key] = value
                        region_dict['metadata'] = safe_metadata
                    
                    safe_regions.append(region_dict)
                else:
                    # Fallback for regions without to_dict method
                    safe_regions.append(str(region))
                    
            except Exception as e:
                # Log the error and add a fallback representation
                logger.warning(f"Failed to serialize region: {e}")
                safe_regions.append(f"Region(error: {str(e)})")
        
        return safe_regions


class QuestionAnswerDetector:
    """
    Detects question and answer patterns in extracted text
    """
    
    def __init__(self):
        # Initialize confidence scorer and format handler
        self.confidence_scorer = ConfidenceScorer()
        self.format_handler = QuestionFormatHandler()
        
        # Initialize classifiers
        self.type_classifier = QuestionTypeClassifier()
        self.difficulty_estimator = QuestionDifficultyEstimator()
        self.topic_extractor = TopicExtractor()
        
        # Common question patterns
        self.question_patterns = [
            # Numbered questions: 1., 2., Q1, Q.1, Question 1
            r'^\s*(?:Q\.?\s*)?(\d+)\.?\s*(.+?)(?=\n|$)',
            # Lettered questions: a), b), (a), (b)
            r'^\s*(?:\(?([a-zA-Z])\)\.?\s*(.+?)(?=\n|$))',
            # Question keywords
            r'^\s*(What|How|Why|When|Where|Which|Who|Explain|Define|Describe|List|State|Calculate)\s+(.+?)(?=\n|$)',
            # Fill in the blank
            r'(.+?)(?:_____+|\.\.\.\.+)(.+?)(?=\n|$)',
        ]
        
        # Answer patterns
        self.answer_patterns = [
            # Multiple choice: A) B) C) D) or (A) (B) (C) (D)
            r'^\s*(?:\(?([A-Da-d])\)\.?\s*(.+?)(?=\n|$))',
            # Answer indicators
            r'^\s*(?:Answer|Ans|Solution|Sol)\.?\s*:?\s*(.+?)(?=\n|$)',
            # True/False
            r'^\s*(True|False|T|F)\s*$',
        ]
    
    def detect_qa_pairs(self, text_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect question-answer pairs in extracted text content using multiple methods
        """
        qa_pairs = []
        
        # Method 1: Use format handler for structured questions
        format_questions = self.format_handler.parse_questions_with_format(text_content)
        
        # Method 2: Use regex patterns for unstructured questions
        regex_questions = []
        for page_data in text_content.get('pages', []):
            page_qa = self._detect_qa_in_page(page_data)
            regex_questions.extend(page_qa)
        
        # Combine and deduplicate questions
        all_questions = self._merge_detection_results(format_questions, regex_questions)
        
        # Enhance questions with answers using the improved detection
        for question in all_questions:
            if question.get('extraction_method') == 'format_handler':
                # Format handler questions need answer detection
                page_data = self._get_page_data_for_question(question, text_content)
                if page_data:
                    answers = self._find_answers_for_question(
                        question, page_data.get('paragraphs', []), 
                        question.get('paragraph_index', 0)
                    )
                    if answers:
                        question['answer_options'] = answers.get('options', [])
                        question['correct_answers'] = answers.get('correct', [])
                        question['answer_detection_confidence'] = answers.get('detection_confidence', 0.0)
        
        qa_pairs.extend(all_questions)
        return qa_pairs
    
    def _merge_detection_results(self, format_questions: List[Dict], 
                               regex_questions: List[Dict]) -> List[Dict[str, Any]]:
        """
        Merge results from different detection methods, avoiding duplicates
        """
        merged_questions = []
        
        # Add format handler questions first (higher priority)
        merged_questions.extend(format_questions)
        
        # Add regex questions that don't overlap with format questions
        for regex_q in regex_questions:
            is_duplicate = False
            
            for format_q in format_questions:
                # Check if they're on the same page and have similar text
                if (regex_q.get('page_number') == format_q.get('page_number') and
                    self._questions_are_similar(regex_q.get('question_text', ''), 
                                              format_q.get('question_text', ''))):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged_questions.append(regex_q)
        
        return merged_questions
    
    def _questions_are_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """
        Check if two question texts are similar (to avoid duplicates)
        """
        if not text1 or not text2:
            return False
        
        # Simple similarity check based on word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold
    
    def _get_page_data_for_question(self, question: Dict, text_content: Dict) -> Optional[Dict]:
        """
        Get the page data for a specific question
        """
        page_number = question.get('page_number', 1)
        
        for page in text_content.get('pages', []):
            if page.get('page_number') == page_number:
                return page
        
        return None
    
    def _detect_qa_in_page(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect Q&A pairs in a single page
        """
        qa_pairs = []
        text = page_data.get('text', '')
        paragraphs = page_data.get('paragraphs', [])
        
        # Process each paragraph
        for para_idx, paragraph in enumerate(paragraphs):
            para_text = paragraph.get('text', '')
            
            # Try to match question patterns
            for pattern in self.question_patterns:
                matches = re.finditer(pattern, para_text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    question_data = self._extract_question_data(
                        match, paragraph, page_data, para_idx
                    )
                    if question_data:
                        qa_pairs.append(question_data)
        
        return qa_pairs
    
    def _extract_question_data(self, match, paragraph: Dict, page_data: Dict, para_idx: int) -> Optional[Dict[str, Any]]:
        """
        Extract detailed question data from a regex match
        """
        question_text = match.group().strip()
        
        if len(question_text) < 10:  # Too short to be a meaningful question
            return None
        
        question_data = {
            'question_text': question_text,
            'page_number': page_data.get('page_number', 1),
            'paragraph_index': para_idx,
            'position_on_page': {
                'start_y': paragraph.get('start_y', 0),
                'end_y': paragraph.get('end_y', 0)
            },
            'question_type': 'unknown',
            'answer_options': [],
            'correct_answers': [],
            'confidence_score': 0.5,
            'extraction_method': 'regex_pattern'
        }
        
        # Determine question type based on content
        question_data['question_type'] = self._classify_question_type(question_text)
        
        # Look for answers in subsequent paragraphs
        answers = self._find_answers_for_question(
            question_data, page_data.get('paragraphs', []), para_idx
        )
        
        if answers:
            question_data['answer_options'] = answers.get('options', [])
            question_data['correct_answers'] = answers.get('correct', [])
            question_data['answer_boundary'] = answers.get('answer_boundary')
            question_data['answer_detection_confidence'] = answers.get('detection_confidence', 0.0)
            
            # Re-classify question type with answer options for better accuracy
            question_data['question_type'] = self._classify_question_type(
                question_text, 
                question_data['answer_options']
            )
            
            # Boost overall confidence based on answer detection quality
            if answers.get('detection_confidence', 0) > 0.7:
                question_data['confidence_score'] = min(question_data['confidence_score'] + 0.4, 1.0)
            elif answers.get('detection_confidence', 0) > 0.5:
                question_data['confidence_score'] = min(question_data['confidence_score'] + 0.3, 1.0)
            else:
                question_data['confidence_score'] = min(question_data['confidence_score'] + 0.2, 1.0)
        
        # Use comprehensive confidence scoring system
        comprehensive_confidence = self.confidence_scorer.calculate_comprehensive_confidence(
            question_data, 
            page_data,
            page_data.get('advanced_layout')
        )
        
        # Update question data with comprehensive confidence information
        question_data['confidence_score'] = comprehensive_confidence['overall_confidence']
        question_data['confidence_level'] = comprehensive_confidence['confidence_level']
        question_data['confidence_factors'] = comprehensive_confidence['factors']
        question_data['confidence_breakdown'] = comprehensive_confidence.get('raw_factors')
        
        # Classify difficulty level
        difficulty_level, difficulty_confidence = self.difficulty_estimator.estimate_difficulty(
            question_text, 
            question_data['question_type'],
            question_data.get('answer_options', [])
        )
        question_data['estimated_difficulty'] = difficulty_level
        question_data['difficulty_confidence'] = difficulty_confidence
        
        # Extract topic
        topic, topic_confidence = self.topic_extractor.extract_topic(question_text)
        question_data['estimated_topic'] = topic
        question_data['topic_confidence'] = topic_confidence
        
        # Extract additional metadata
        question_metadata = self.type_classifier.extract_question_metadata(
            question_text, 
            question_data['question_type']
        )
        question_data['metadata'] = question_metadata
        
        return question_data
    
    def _classify_question_type(self, question_text: str, answer_options: List[Dict] = None) -> str:
        """
        Classify question type using advanced classifier
        """
        question_type, confidence = self.type_classifier.classify_question(question_text, answer_options)
        return question_type
    
    def _find_answers_for_question(self, question_data: Dict, paragraphs: List[Dict], question_para_idx: int) -> Optional[Dict[str, Any]]:
        """
        Find answer options for a question in subsequent paragraphs using advanced boundary detection
        """
        answer_data = {
            'options': [],
            'correct': [],
            'answer_boundary': None,
            'detection_confidence': 0.0
        }
        
        # Look in the next few paragraphs for answer options
        search_range = min(len(paragraphs), question_para_idx + 5)
        
        # Track answer detection patterns and confidence
        detection_methods = []
        
        for para_idx in range(question_para_idx + 1, search_range):
            paragraph = paragraphs[para_idx]
            para_text = paragraph.get('text', '')
            
            # Method 1: Multiple choice options (A, B, C, D)
            mcq_confidence = self._detect_mcq_answers(para_text, answer_data, paragraph, detection_methods)
            
            # Method 2: Numbered list answers (1, 2, 3, 4)
            numbered_confidence = self._detect_numbered_answers(para_text, answer_data, paragraph, detection_methods)
            
            # Method 3: True/False answers
            tf_confidence = self._detect_true_false_answers(para_text, answer_data, paragraph, detection_methods)
            
            # Method 4: Fill-in-the-blank answers
            fill_confidence = self._detect_fill_blank_answers(para_text, answer_data, paragraph, detection_methods)
            
            # Method 5: Answer keywords (Answer:, Solution:, etc.)
            keyword_confidence = self._detect_keyword_answers(para_text, answer_data, paragraph, detection_methods)
            
            # Stop searching if we hit a new question or significant format change
            if self._is_new_question_boundary(para_text):
                break
        
        # Calculate overall detection confidence
        if detection_methods:
            answer_data['detection_confidence'] = max(detection_methods)
            
        return answer_data if answer_data['options'] or answer_data['correct'] else None
    
    def _detect_mcq_answers(self, para_text: str, answer_data: Dict, paragraph: Dict, detection_methods: List) -> float:
        """
        Detect multiple choice answers (A), B), C), D) format
        """
        confidence = 0.0
        
        # Enhanced pattern for multiple choice options
        mcq_patterns = [
            r'^\s*(?:\(?([A-Da-d])\)\.?\s*(.+?)(?=\n|$))',  # (A) or A)
            r'^\s*([A-Da-d])\.\s*(.+?)(?=\n|$)',             # A.
            r'^\s*\(([A-Da-d])\)\s*(.+?)(?=\n|$)',           # (A)
        ]
        
        for pattern in mcq_patterns:
            matches = list(re.finditer(pattern, para_text, re.IGNORECASE | re.MULTILINE))
            
            if matches:
                confidence = 0.8  # High confidence for MCQ pattern
                
                for match in matches:
                    option_letter = match.group(1).upper()
                    option_text = match.group(2).strip()
                    
                    if len(option_text) > 3:  # Filter out very short options
                        answer_data['options'].append({
                            'letter': option_letter,
                            'text': option_text,
                            'paragraph_index': paragraph.get('paragraph_index', 0),
                            'position': {
                                'start_y': paragraph.get('start_y', 0),
                                'end_y': paragraph.get('end_y', 0)
                            },
                            'detection_method': 'mcq_pattern'
                        })
                
                # Check for correct answer indicators
                correct_indicators = ['correct', 'right', 'answer is', 'ans:']
                for indicator in correct_indicators:
                    if indicator.lower() in para_text.lower():
                        confidence += 0.1
                
                break
        
        if confidence > 0:
            detection_methods.append(confidence)
        
        return confidence
    
    def _detect_numbered_answers(self, para_text: str, answer_data: Dict, paragraph: Dict, detection_methods: List) -> float:
        """
        Detect numbered list answers 1), 2), 3), 4) format
        """
        confidence = 0.0
        
        numbered_patterns = [
            r'^\s*(\d+)\)\s*(.+?)(?=\n|$)',     # 1)
            r'^\s*(\d+)\.\s*(.+?)(?=\n|$)',     # 1.
            r'^\s*\((\d+)\)\s*(.+?)(?=\n|$)',   # (1)
        ]
        
        for pattern in numbered_patterns:
            matches = list(re.finditer(pattern, para_text, re.IGNORECASE | re.MULTILINE))
            
            if matches and len(matches) >= 2:  # At least 2 numbered items
                confidence = 0.7  # Good confidence for numbered lists
                
                for match in matches:
                    option_number = match.group(1)
                    option_text = match.group(2).strip()
                    
                    if len(option_text) > 3:
                        answer_data['options'].append({
                            'letter': chr(64 + int(option_number)),  # Convert 1->A, 2->B, etc.
                            'number': option_number,
                            'text': option_text,
                            'paragraph_index': paragraph.get('paragraph_index', 0),
                            'position': {
                                'start_y': paragraph.get('start_y', 0),
                                'end_y': paragraph.get('end_y', 0)
                            },
                            'detection_method': 'numbered_list'
                        })
                
                break
        
        if confidence > 0:
            detection_methods.append(confidence)
        
        return confidence
    
    def _detect_true_false_answers(self, para_text: str, answer_data: Dict, paragraph: Dict, detection_methods: List) -> float:
        """
        Detect True/False type answers
        """
        confidence = 0.0
        
        # Look for True/False indicators
        tf_patterns = [
            r'\b(True|False)\b',
            r'\b(T|F)\b(?:\s|$)',
            r'\b(Correct|Incorrect)\b',
            r'\b(Yes|No)\b'
        ]
        
        tf_matches = []
        for pattern in tf_patterns:
            matches = re.findall(pattern, para_text, re.IGNORECASE)
            tf_matches.extend(matches)
        
        if tf_matches:
            confidence = 0.6
            
            # Create options for True/False
            unique_answers = list(set([match.upper() for match in tf_matches]))
            for answer in unique_answers:
                answer_data['options'].append({
                    'letter': 'T' if answer in ['TRUE', 'T', 'CORRECT', 'YES'] else 'F',
                    'text': answer,
                    'paragraph_index': paragraph.get('paragraph_index', 0),
                    'position': {
                        'start_y': paragraph.get('start_y', 0),
                        'end_y': paragraph.get('end_y', 0)
                    },
                    'detection_method': 'true_false'
                })
        
        if confidence > 0:
            detection_methods.append(confidence)
        
        return confidence
    
    def _detect_fill_blank_answers(self, para_text: str, answer_data: Dict, paragraph: Dict, detection_methods: List) -> float:
        """
        Detect fill-in-the-blank answers
        """
        confidence = 0.0
        
        # Look for answer patterns after blanks
        fill_patterns = [
            r'(?:answer|ans|solution|sol)(?:\s*:)?\s*(.+?)(?=\n|$)',
            r'(?:fill|complete|insert)(?:\s*:)?\s*(.+?)(?=\n|$)',
            r'(?:blank|gap)(?:\s*:)?\s*(.+?)(?=\n|$)'
        ]
        
        for pattern in fill_patterns:
            matches = re.finditer(pattern, para_text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                answer_text = match.group(1).strip()
                
                if len(answer_text) > 1:
                    confidence = 0.5
                    
                    answer_data['correct'].append({
                        'text': answer_text,
                        'paragraph_index': paragraph.get('paragraph_index', 0),
                        'position': {
                            'start_y': paragraph.get('start_y', 0),
                            'end_y': paragraph.get('end_y', 0)
                        },
                        'detection_method': 'fill_blank'
                    })
        
        if confidence > 0:
            detection_methods.append(confidence)
        
        return confidence
    
    def _detect_keyword_answers(self, para_text: str, answer_data: Dict, paragraph: Dict, detection_methods: List) -> float:
        """
        Detect answers marked with keywords (Answer:, Solution:, etc.)
        """
        confidence = 0.0
        
        keyword_patterns = [
            r'(?:answer|ans)(?:\s*:)?\s*(.+?)(?=\n|$)',
            r'(?:solution|sol)(?:\s*:)?\s*(.+?)(?=\n|$)',
            r'(?:correct|right)(?:\s*:)?\s*(.+?)(?=\n|$)',
            r'(?:explanation|explain)(?:\s*:)?\s*(.+?)(?=\n|$)'
        ]
        
        for pattern in keyword_patterns:
            matches = re.finditer(pattern, para_text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                answer_text = match.group(1).strip()
                
                if len(answer_text) > 2:
                    confidence = 0.7
                    
                    answer_data['correct'].append({
                        'text': answer_text,
                        'paragraph_index': paragraph.get('paragraph_index', 0),
                        'position': {
                            'start_y': paragraph.get('start_y', 0),
                            'end_y': paragraph.get('end_y', 0)
                        },
                        'detection_method': 'keyword_answer'
                    })
        
        if confidence > 0:
            detection_methods.append(confidence)
        
        return confidence
    
    def _is_new_question_boundary(self, para_text: str) -> bool:
        """
        Detect if we've hit a new question boundary
        """
        # Look for new question indicators
        new_question_patterns = [
            r'^\s*(?:Q\.?\s*)?(\d+)\.?\s*',  # Q.1, 1., etc.
            r'^\s*(?:Question|Q)\s*\d+',        # Question 1
            r'^\s*(?:What|How|Why|When|Where|Which|Who|Explain|Define|Describe)\s+',  # Question starters
        ]
        
        for pattern in new_question_patterns:
            if re.search(pattern, para_text, re.IGNORECASE | re.MULTILINE):
                return True
        
        return False


class QuestionFormatHandler:
    """
    Handles various question numbering and formatting patterns
    """
    
    def __init__(self):
        # Define format patterns with their priorities and characteristics
        self.format_patterns = {
            'numbered_dot': {
                'pattern': r'^\s*(\d+)\.\s*(.+?)(?=\n|$)',
                'priority': 10,
                'description': 'Numbered with dot (1., 2., 3.)',
                'continuation_pattern': r'^\s*(\d+)\.\s*'
            },
            'numbered_paren': {
                'pattern': r'^\s*(\d+)\)\s*(.+?)(?=\n|$)',
                'priority': 9,
                'description': 'Numbered with parenthesis (1), 2), 3))',
                'continuation_pattern': r'^\s*(\d+)\)\s*'
            },
            'numbered_paren_both': {
                'pattern': r'^\s*\((\d+)\)\s*(.+?)(?=\n|$)',
                'priority': 8,
                'description': 'Numbered with both parentheses ((1), (2), (3))',
                'continuation_pattern': r'^\s*\((\d+)\)\s*'
            },
            'lettered_dot': {
                'pattern': r'^\s*([a-zA-Z])\.\s*(.+?)(?=\n|$)',
                'priority': 7,
                'description': 'Lettered with dot (a., b., c.)',
                'continuation_pattern': r'^\s*([a-zA-Z])\.\s*'
            },
            'lettered_paren': {
                'pattern': r'^\s*([a-zA-Z])\)\s*(.+?)(?=\n|$)',
                'priority': 6,
                'description': 'Lettered with parenthesis (a), b), c))',
                'continuation_pattern': r'^\s*([a-zA-Z])\)\s*'
            },
            'lettered_paren_both': {
                'pattern': r'^\s*\(([a-zA-Z])\)\s*(.+?)(?=\n|$)',
                'priority': 5,
                'description': 'Lettered with both parentheses ((a), (b), (c))',
                'continuation_pattern': r'^\s*\(([a-zA-Z])\)\s*'
            },
            'roman_dot': {
                'pattern': r'^\s*([ivxlcdm]+)\.\s*(.+?)(?=\n|$)',
                'priority': 4,
                'description': 'Roman numerals with dot (i., ii., iii.)',
                'continuation_pattern': r'^\s*([ivxlcdm]+)\.\s*'
            },
            'roman_paren': {
                'pattern': r'^\s*([ivxlcdm]+)\)\s*(.+?)(?=\n|$)',
                'priority': 3,
                'description': 'Roman numerals with parenthesis (i), ii), iii))',
                'continuation_pattern': r'^\s*([ivxlcdm]+)\)\s*'
            },
            'bullet_dash': {
                'pattern': r'^\s*[-–—]\s*(.+?)(?=\n|$)',
                'priority': 2,
                'description': 'Dash bullets (-, –, —)',
                'continuation_pattern': r'^\s*[-–—]\s*'
            },
            'bullet_asterisk': {
                'pattern': r'^\s*\*\s*(.+?)(?=\n|$)',
                'priority': 1,
                'description': 'Asterisk bullets (*)',
                'continuation_pattern': r'^\s*\*\s*'
            }
        }
        
        # Question keywords that can appear before numbering
        self.question_prefixes = [
            r'(?:Question|Q|Prob|Problem)\.?\s*',
        ]
    
    def detect_question_format(self, text_lines: List[str]) -> Dict[str, Any]:
        """
        Detect the question formatting pattern used in the text
        """
        format_scores = {}
        total_lines = len(text_lines)
        
        # Score each format pattern
        for format_name, format_info in self.format_patterns.items():
            pattern = format_info['pattern']
            matches = 0
            consecutive_matches = 0
            max_consecutive = 0
            
            for line in text_lines:
                line = line.strip()
                if re.match(pattern, line, re.IGNORECASE):
                    matches += 1
                    consecutive_matches += 1
                    max_consecutive = max(max_consecutive, consecutive_matches)
                else:
                    consecutive_matches = 0
            
            if matches > 0:
                # Calculate score based on matches, priority, and consecutiveness
                match_ratio = matches / total_lines if total_lines > 0 else 0
                priority_score = format_info['priority'] / 10.0
                consecutive_score = max_consecutive / total_lines if total_lines > 0 else 0
                
                format_scores[format_name] = {
                    'score': (match_ratio * 0.5 + priority_score * 0.3 + consecutive_score * 0.2),
                    'matches': matches,
                    'match_ratio': match_ratio,
                    'max_consecutive': max_consecutive,
                    'pattern_info': format_info
                }
        
        # Find the best format
        if format_scores:
            best_format = max(format_scores, key=lambda x: format_scores[x]['score'])
            return {
                'detected_format': best_format,
                'confidence': format_scores[best_format]['score'],
                'all_scores': format_scores,
                'format_info': format_scores[best_format]['pattern_info']
            }
        
        return {
            'detected_format': None,
            'confidence': 0.0,
            'all_scores': {},
            'format_info': None
        }
    
    def parse_questions_with_format(self, text_content: Dict[str, Any], 
                                   detected_format: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Parse questions using the detected or specified format
        """
        questions = []
        
        if not detected_format:
            # Auto-detect format from all text
            all_text_lines = []
            for page in text_content.get('pages', []):
                for paragraph in page.get('paragraphs', []):
                    lines = paragraph.get('text', '').split('\n')
                    all_text_lines.extend([line.strip() for line in lines if line.strip()])
            
            detected_format = self.detect_question_format(all_text_lines)
        
        if not detected_format.get('detected_format'):
            return questions
        
        format_info = detected_format['format_info']
        main_pattern = format_info['pattern']
        
        # Process each page
        for page_idx, page in enumerate(text_content.get('pages', [])):
            page_questions = self._extract_questions_from_page(
                page, main_pattern, format_info, page_idx + 1
            )
            questions.extend(page_questions)
        
        return questions
    
    def _extract_questions_from_page(self, page_data: Dict, pattern: str, 
                                   format_info: Dict, page_number: int) -> List[Dict[str, Any]]:
        """
        Extract questions from a single page using the specified pattern
        """
        questions = []
        
        for para_idx, paragraph in enumerate(page_data.get('paragraphs', [])):
            para_text = paragraph.get('text', '')
            lines = para_text.split('\n')
            
            current_question = None
            question_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line starts a new question
                match = re.match(pattern, line, re.IGNORECASE | re.MULTILINE)
                
                if match:
                    # Save previous question if exists
                    if current_question and question_lines:
                        current_question['question_text'] = ' '.join(question_lines)
                        questions.append(current_question)
                    
                    # Start new question
                    question_identifier = match.group(1) if match.groups() else ''
                    question_text_part = match.group(2) if len(match.groups()) > 1 else line
                    
                    current_question = {
                        'question_identifier': question_identifier,
                        'question_text': question_text_part,
                        'page_number': page_number,
                        'paragraph_index': para_idx,
                        'position_on_page': {
                            'start_y': paragraph.get('start_y', 0),
                            'end_y': paragraph.get('end_y', 0)
                        },
                        'format_type': format_info['description'],
                        'extraction_method': 'format_handler',
                        'question_type': 'unknown',
                        'confidence_score': 0.7,  # Base confidence for format-detected questions
                        'answer_options': [],
                        'correct_answers': []
                    }
                    question_lines = [question_text_part] if question_text_part else []
                
                elif current_question:
                    # This line continues the current question
                    question_lines.append(line)
                
                else:
                    # This line doesn't match pattern and no current question
                    # Could be a standalone question without numbering
                    if self._looks_like_question(line):
                        question = {
                            'question_identifier': '',
                            'question_text': line,
                            'page_number': page_number,
                            'paragraph_index': para_idx,
                            'position_on_page': {
                                'start_y': paragraph.get('start_y', 0),
                                'end_y': paragraph.get('end_y', 0)
                            },
                            'format_type': 'unformatted',
                            'extraction_method': 'format_handler',
                            'question_type': 'unknown',
                            'confidence_score': 0.5,  # Lower confidence for unformatted
                            'answer_options': [],
                            'correct_answers': []
                        }
                        questions.append(question)
            
            # Don't forget the last question
            if current_question and question_lines:
                current_question['question_text'] = ' '.join(question_lines)
                questions.append(current_question)
        
        return questions
    
    def _looks_like_question(self, text: str) -> bool:
        """
        Determine if a line looks like a question without specific formatting
        """
        if len(text) < 10:  # Too short
            return False
        
        # Check for question indicators
        question_indicators = [
            r'\?$',  # Ends with question mark
            r'^(?:what|how|why|when|where|which|who|explain|define|describe|list|state|calculate)',
            r'(?:true or false|t/f)',
            r'(?:choose|select|identify)',
            r'(?:_____+|\.\.\.\.+)',  # Fill in the blank
        ]
        
        return any(re.search(indicator, text, re.IGNORECASE) for indicator in question_indicators)
    
    def normalize_question_identifier(self, identifier: str, format_type: str) -> str:
        """
        Normalize question identifiers to a standard format
        """
        if not identifier:
            return ''
        
        identifier = identifier.strip()
        
        # Convert roman numerals to numbers
        if 'roman' in format_type.lower():
            identifier = self._roman_to_int(identifier)
        
        # Convert letters to numbers (a=1, b=2, etc.)
        elif identifier.isalpha() and len(identifier) == 1:
            identifier = str(ord(identifier.lower()) - ord('a') + 1)
        
        return str(identifier)
    
    def _roman_to_int(self, roman: str) -> int:
        """
        Convert Roman numerals to integers
        """
        roman_values = {
            'i': 1, 'v': 5, 'x': 10, 'l': 50, 
            'c': 100, 'd': 500, 'm': 1000
        }
        
        roman = roman.lower()
        total = 0
        prev_value = 0
        
        for char in reversed(roman):
            value = roman_values.get(char, 0)
            if value < prev_value:
                total -= value
            else:
                total += value
            prev_value = value
        
        return total
    
    def get_format_statistics(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about the formats found in the questions
        """
        format_counts = {}
        total_questions = len(questions)
        
        for question in questions:
            format_type = question.get('format_type', 'unknown')
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        return {
            'total_questions': total_questions,
            'format_distribution': format_counts,
            'most_common_format': max(format_counts, key=format_counts.get) if format_counts else None,
            'format_consistency': max(format_counts.values()) / total_questions if total_questions > 0 else 0
        }


@dataclass
class ConfidenceFactors:
    """
    Data class to hold various confidence factors for Q&A extraction
    """
    question_structure: float = 0.0  # How well-structured the question appears
    answer_detection: float = 0.0    # Quality of answer option detection
    text_clarity: float = 0.0        # OCR/text extraction clarity
    format_consistency: float = 0.0  # Consistency with expected Q&A formats
    spatial_layout: float = 0.0      # Spatial relationship quality
    linguistic_quality: float = 0.0  # Language/grammar quality
    context_coherence: float = 0.0   # Coherence with surrounding content


class ConfidenceScorer:
    """
    Advanced confidence scoring system for extracted Q&A pairs
    """
    
    def __init__(self):
        # Weight factors for different confidence components
        self.weights = {
            'question_structure': 0.20,
            'answer_detection': 0.25,
            'text_clarity': 0.15,
            'format_consistency': 0.15,
            'spatial_layout': 0.10,
            'linguistic_quality': 0.10,
            'context_coherence': 0.05
        }
        
        # Common question starters for structure assessment
        self.question_starters = [
            'what', 'how', 'why', 'when', 'where', 'which', 'who', 'whom',
            'explain', 'define', 'describe', 'list', 'state', 'calculate',
            'analyze', 'compare', 'contrast', 'evaluate', 'discuss'
        ]
        
        # Answer format indicators
        self.answer_format_patterns = [
            r'^\s*[A-Da-d]\)',  # A), B), C), D)
            r'^\s*\([A-Da-d]\)',  # (A), (B), (C), (D)
            r'^\s*\d+\)',  # 1), 2), 3)
            r'^\s*[A-Da-d]\.',  # A., B., C., D.
            r'^\s*true|false\b',  # True/False
            r'^\s*yes|no\b'  # Yes/No
        ]
    
    def calculate_comprehensive_confidence(self, question_data: Dict[str, Any], 
                                         page_data: Dict[str, Any] = None,
                                         layout_info: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Calculate comprehensive confidence score for a Q&A pair
        """
        factors = ConfidenceFactors()
        
        # 1. Question structure analysis
        factors.question_structure = self._assess_question_structure(
            question_data.get('question_text', '')
        )
        
        # 2. Answer detection quality
        factors.answer_detection = self._assess_answer_detection(
            question_data.get('answer_options', []),
            question_data.get('correct_answers', []),
            question_data.get('answer_detection_confidence', 0.0)
        )
        
        # 3. Text clarity assessment
        factors.text_clarity = self._assess_text_clarity(
            question_data, page_data
        )
        
        # 4. Format consistency
        factors.format_consistency = self._assess_format_consistency(
            question_data.get('question_text', ''),
            question_data.get('answer_options', [])
        )
        
        # 5. Spatial layout quality
        factors.spatial_layout = self._assess_spatial_layout(
            question_data, layout_info
        )
        
        # 6. Linguistic quality
        factors.linguistic_quality = self._assess_linguistic_quality(
            question_data.get('question_text', ''),
            question_data.get('answer_options', [])
        )
        
        # 7. Context coherence
        factors.context_coherence = self._assess_context_coherence(
            question_data, page_data
        )
        
        # Calculate weighted confidence score
        total_confidence = 0.0
        confidence_breakdown = {}
        
        for factor_name, weight in self.weights.items():
            factor_value = getattr(factors, factor_name)
            weighted_value = factor_value * weight
            total_confidence += weighted_value
            confidence_breakdown[factor_name] = {
                'score': factor_value,
                'weight': weight,
                'weighted_score': weighted_value
            }
        
        # Apply question type specific adjustments
        total_confidence = self._apply_question_type_adjustments(
            total_confidence, question_data.get('question_type', 'unknown')
        )
        
        return {
            'overall_confidence': min(max(total_confidence, 0.0), 1.0),
            'confidence_level': self._get_confidence_level(total_confidence),
            'factors': confidence_breakdown,
            'raw_factors': factors
        }
    
    def _assess_question_structure(self, question_text: str) -> float:
        """
        Assess the structural quality of a question
        """
        if not question_text or len(question_text.strip()) < 5:
            return 0.1
        
        confidence = 0.3  # Base confidence
        question_lower = question_text.lower().strip()
        
        # Check for question mark
        if question_text.endswith('?'):
            confidence += 0.2
        
        # Check for question starters
        starts_with_question_word = any(
            question_lower.startswith(starter) 
            for starter in self.question_starters
        )
        if starts_with_question_word:
            confidence += 0.3
        
        # Check length (reasonable questions are not too short or too long)
        word_count = len(question_text.split())
        if 3 <= word_count <= 50:
            confidence += 0.1
        elif word_count > 50:
            confidence -= 0.1
        
        # Check for imperative structures (command-like questions)
        imperative_starters = ['explain', 'define', 'describe', 'list', 'calculate', 'analyze']
        if any(question_lower.startswith(starter) for starter in imperative_starters):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _assess_answer_detection(self, answer_options: List[Dict], 
                               correct_answers: List[Dict],
                               detection_confidence: float) -> float:
        """
        Assess the quality of answer detection
        """
        if not answer_options and not correct_answers:
            return 0.2  # Some questions might not have explicit answers
        
        confidence = detection_confidence  # Start with the detection algorithm's confidence
        
        # Boost confidence for multiple choice questions with good options
        if answer_options:
            option_count = len(answer_options)
            
            # Ideal MCQ has 3-5 options
            if 3 <= option_count <= 5:
                confidence += 0.2
            elif option_count == 2:  # True/False or binary choice
                confidence += 0.1
            elif option_count > 5:
                confidence -= 0.1  # Too many options might indicate noise
            
            # Check option quality
            avg_option_length = sum(len(opt.get('text', '')) for opt in answer_options) / len(answer_options)
            if 10 <= avg_option_length <= 100:  # Reasonable option length
                confidence += 0.1
            
            # Check for format consistency in options
            if self._check_option_format_consistency(answer_options):
                confidence += 0.1
        
        # Boost for correct answers found
        if correct_answers:
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _assess_text_clarity(self, question_data: Dict, page_data: Dict = None) -> float:
        """
        Assess the clarity of extracted text (OCR quality, etc.)
        """
        base_confidence = 0.7  # Assume good quality by default
        
        # If we have OCR confidence information, use it
        if page_data and 'confidence' in page_data:
            ocr_confidence = page_data['confidence'] / 100.0  # Convert percentage to decimal
            base_confidence = min(base_confidence, ocr_confidence)
        
        # Check for OCR artifacts or garbled text
        question_text = question_data.get('question_text', '')
        
        # Common OCR errors
        ocr_error_indicators = ['|||', '~~~', '^^^', '```', 'iii', 'lll']
        error_count = sum(question_text.count(indicator) for indicator in ocr_error_indicators)
        
        if error_count > 0:
            base_confidence -= min(error_count * 0.1, 0.3)
        
        # Check for reasonable character distribution
        if question_text:
            alpha_ratio = sum(c.isalpha() for c in question_text) / len(question_text)
            if alpha_ratio < 0.5:  # Less than 50% alphabetic characters might indicate poor OCR
                base_confidence -= 0.2
        
        return max(base_confidence, 0.1)
    
    def _assess_format_consistency(self, question_text: str, answer_options: List[Dict]) -> float:
        """
        Assess consistency with expected Q&A formats
        """
        confidence = 0.5
        
        # Check if question follows standard academic format
        if question_text:
            # Numbered questions: "1.", "Q1.", "Question 1:"
            if re.match(r'^\s*(?:Q\.?\s*)?\d+\.?\s*', question_text):
                confidence += 0.2
            
            # Proper capitalization
            if question_text[0].isupper():
                confidence += 0.1
        
        # Check answer option format consistency
        if answer_options:
            format_scores = []
            
            for pattern in self.answer_format_patterns:
                matches = sum(1 for opt in answer_options 
                            if re.match(pattern, opt.get('text', ''), re.IGNORECASE))
                if matches > 0:
                    format_scores.append(matches / len(answer_options))
            
            if format_scores:
                consistency_score = max(format_scores)
                confidence += consistency_score * 0.3
        
        return min(confidence, 1.0)
    
    def _assess_spatial_layout(self, question_data: Dict, layout_info: Dict = None) -> float:
        """
        Assess spatial layout quality
        """
        if not layout_info:
            return 0.5  # Neutral score if no layout info
        
        confidence = 0.4
        
        # Check if question and answers are spatially well-separated
        question_pos = question_data.get('position_on_page', {})
        answer_options = question_data.get('answer_options', [])
        
        if question_pos and answer_options:
            # Check if answers appear below the question (typical layout)
            answers_below_question = all(
                opt.get('position', {}).get('start_y', 0) < question_pos.get('start_y', 0)
                for opt in answer_options if opt.get('position')
            )
            
            if answers_below_question:
                confidence += 0.3
        
        # Boost confidence for consistent column detection
        if layout_info.get('confidence', 0) > 0.7:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _assess_linguistic_quality(self, question_text: str, answer_options: List[Dict]) -> float:
        """
        Assess linguistic/grammatical quality
        """
        confidence = 0.6  # Base confidence
        
        if question_text:
            # Check for basic grammar indicators
            word_count = len(question_text.split())
            
            # Check for proper sentence structure
            if word_count >= 3:  # At least subject-verb-object
                confidence += 0.1
            
            # Check for common English question patterns
            english_patterns = [
                r'\b(?:what|how|why|when|where|which|who)\s+(?:is|are|was|were|do|does|did|can|could|will|would|should)\b',
                r'\b(?:explain|describe|define|calculate|analyze)\s+(?:the|how|why|what)\b'
            ]
            
            if any(re.search(pattern, question_text, re.IGNORECASE) for pattern in english_patterns):
                confidence += 0.2
        
        # Assess answer option linguistic quality
        if answer_options:
            valid_options = [opt for opt in answer_options if len(opt.get('text', '').strip()) > 2]
            if len(valid_options) == len(answer_options):
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _assess_context_coherence(self, question_data: Dict, page_data: Dict = None) -> float:
        """
        Assess coherence with surrounding content
        """
        # This is a simplified version - could be enhanced with NLP
        confidence = 0.5
        
        question_text = question_data.get('question_text', '')
        
        # Check if question makes sense in isolation
        if question_text:
            # Questions with context references might need surrounding text
            context_indicators = ['above', 'below', 'following', 'preceding', 'this', 'these', 'that', 'those']
            
            has_context_references = any(
                indicator in question_text.lower() 
                for indicator in context_indicators
            )
            
            if has_context_references:
                confidence -= 0.2  # Might need more context
            else:
                confidence += 0.1  # Self-contained question
        
        return min(confidence, 1.0)
    
    def _check_option_format_consistency(self, answer_options: List[Dict]) -> bool:
        """
        Check if answer options follow a consistent format
        """
        if len(answer_options) < 2:
            return True
        
        # Check if all options start with the same format pattern
        first_option_text = answer_options[0].get('text', '')
        
        for pattern in self.answer_format_patterns:
            if re.match(pattern, first_option_text, re.IGNORECASE):
                # Check if all other options match the same pattern
                return all(
                    re.match(pattern, opt.get('text', ''), re.IGNORECASE)
                    for opt in answer_options[1:]
                )
        
        return False
    
    def _apply_question_type_adjustments(self, confidence: float, question_type: str) -> float:
        """
        Apply question type specific confidence adjustments
        """
        adjustments = {
            'mcq': 0.05,        # MCQ are generally well-structured
            'true_false': 0.03,  # T/F are simple and clear
            'fill_blank': -0.02, # Fill-in-blank can be ambiguous
            'essay': -0.05,      # Essay questions are harder to validate
            'unknown': -0.1      # Unknown type reduces confidence
        }
        
        adjustment = adjustments.get(question_type, 0)
        return confidence + adjustment
    
    def _get_confidence_level(self, confidence_score: float) -> str:
        """
        Convert numerical confidence to categorical level
        """
        if confidence_score >= 0.8:
            return 'high'
        elif confidence_score >= 0.6:
            return 'medium'
        elif confidence_score >= 0.4:
            return 'low'
        else:
            return 'very_low'