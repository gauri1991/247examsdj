import io
import os
import tempfile
import logging
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import pytesseract
import pdf2image
from django.core.files.uploadedfile import UploadedFile
from .security import ProcessingSecurityManager

logger = logging.getLogger(__name__)

# Import the enhanced OCR system
try:
    from .enhanced_ocr import enhanced_ocr, extract_text_enhanced, OCRResult
    ENHANCED_OCR_AVAILABLE = True
    logger.info("Enhanced OCR system loaded successfully")
except ImportError as e:
    ENHANCED_OCR_AVAILABLE = False
    logger.warning(f"Enhanced OCR system not available: {e}")


class OCRProcessor:
    """
    Handles OCR processing for scanned PDF documents
    """
    
    def __init__(self):
        self.dpi = 300  # High DPI for better OCR accuracy
        # HIGH QUALITY Tesseract configuration for exam papers
        self.tesseract_configs = {
            'high_quality': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'exam_paper': '--oem 3 --psm 4 -c preserve_interword_spaces=1 -c chop_enable=1',
            'questions_with_options': '--oem 3 --psm 6 -c preserve_interword_spaces=1 -c textord_tabfind_find_tables=1'
        }
        
        # Use high quality as default
        self.tesseract_config = self.tesseract_configs['high_quality']
        
        # Try to detect Tesseract installation
        try:
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            self.tesseract_available = False
    
    def process_pdf_with_ocr(self, pdf_file: UploadedFile) -> Dict[str, Any]:
        """
        Process a PDF file using OCR to extract text
        """
        if not self.tesseract_available:
            return {
                'success': False,
                'error': 'OCR engine (Tesseract) is not available',
                'pages': [],
                'total_pages': 0
            }
        
        result = {
            'success': False,
            'pages': [],
            'total_pages': 0,
            'extraction_method': 'ocr',
            'processing_time': 0,
            'errors': []
        }
        
        temp_dir = None
        try:
            # Create secure temporary directory
            temp_dir = ProcessingSecurityManager.create_secure_temp_directory()
            
            # Convert PDF to images
            pdf_file.seek(0)
            images = pdf2image.convert_from_bytes(
                pdf_file.read(),
                dpi=self.dpi,
                output_folder=temp_dir,
                fmt='PNG'
            )
            
            result['total_pages'] = len(images)
            
            # Process each page with OCR
            for page_num, image in enumerate(images, 1):
                try:
                    page_data = self._process_page_with_ocr(image, page_num)
                    result['pages'].append(page_data)
                except Exception as e:
                    logger.error(f"Error processing page {page_num}: {e}")
                    result['errors'].append(f"Page {page_num}: {str(e)}")
                    
                    # Add empty page data to maintain page order
                    result['pages'].append({
                        'page_number': page_num,
                        'text': '',
                        'words': [],
                        'lines': [],
                        'paragraphs': [],
                        'confidence': 0.0,
                        'error': str(e)
                    })
            
            result['success'] = len(result['pages']) > 0
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            result['error'] = str(e)
            result['errors'].append(str(e))
        
        finally:
            # Clean up temporary directory
            if temp_dir:
                ProcessingSecurityManager.cleanup_temp_directory(temp_dir)
            pdf_file.seek(0)
        
        return result
    
    def process_image_with_ocr(self, image: Image.Image) -> Dict[str, Any]:
        """
        Process a single image with OCR
        
        Args:
            image: PIL Image to process
            
        Returns:
            Dict containing OCR results
        """
        if not self.tesseract_available:
            return {
                'success': False,
                'error': 'Tesseract OCR not available',
                'text': '',
                'words': [],
                'lines': [],
                'paragraphs': []
            }
        
        try:
            # Use the existing method
            return self._process_page_with_ocr(image, 1)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'words': [],
                'lines': [],
                'paragraphs': []
            }
    
    def _process_page_with_ocr(self, image: Image.Image, page_number: int) -> Dict[str, Any]:
        """
        Process a single page image with OCR
        """
        page_data = {
            'page_number': page_number,
            'text': '',
            'words': [],
            'lines': [],
            'paragraphs': [],
            'confidence': 0.0,
            'layout_info': {}
        }
        
        try:
            # Get detailed OCR data with coordinates
            ocr_data = pytesseract.image_to_data(
                image, 
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            page_data['text'] = pytesseract.image_to_string(
                image, 
                config=self.tesseract_config
            )
            
            # Process OCR data to extract words with coordinates
            words = []
            confidences = []
            
            for i in range(len(ocr_data['text'])):
                word_text = ocr_data['text'][i].strip()
                if word_text:  # Skip empty words
                    word_data = {
                        'text': word_text,
                        'x0': ocr_data['left'][i],
                        'y0': ocr_data['top'][i],
                        'x1': ocr_data['left'][i] + ocr_data['width'][i],
                        'y1': ocr_data['top'][i] + ocr_data['height'][i],
                        'confidence': float(ocr_data['conf'][i]),
                        'fontname': 'unknown',  # OCR doesn't provide font info
                        'size': 0  # OCR doesn't provide font size
                    }
                    words.append(word_data)
                    confidences.append(float(ocr_data['conf'][i]))
            
            page_data['words'] = words
            
            # Calculate average confidence
            if confidences:
                page_data['confidence'] = sum(confidences) / len(confidences)
            
            # Group words into lines and paragraphs
            page_data['lines'] = self._group_words_into_lines(words)
            page_data['paragraphs'] = self._group_lines_into_paragraphs(page_data['lines'])
            
            # Analyze layout
            page_data['layout_info'] = self._analyze_ocr_layout(
                words, image.width, image.height
            )
            
            # Mark as successful
            page_data['success'] = True
            
        except Exception as e:
            logger.error(f"OCR processing failed for page {page_number}: {e}")
            page_data['error'] = str(e)
            page_data['success'] = False
        
        return page_data
    
    def _group_words_into_lines(self, words: List[Dict]) -> List[Dict]:
        """
        Group OCR words into lines based on y-coordinates
        """
        if not words:
            return []
        
        # Sort words by y-coordinate then x-coordinate
        sorted_words = sorted(words, key=lambda w: (-w['y1'], w['x0']))
        
        lines = []
        current_line = []
        current_y = None
        tolerance = 10  # Y-coordinate tolerance for same line
        
        for word in sorted_words:
            if current_y is None or abs(word['y1'] - current_y) <= tolerance:
                current_line.append(word)
                current_y = word['y1']
            else:
                if current_line:
                    # Sort current line by x-coordinate
                    current_line.sort(key=lambda w: w['x0'])
                    lines.append({
                        'words': current_line,
                        'text': ' '.join([w['text'] for w in current_line]),
                        'y_position': current_y,
                        'x_start': min([w['x0'] for w in current_line]),
                        'x_end': max([w['x1'] for w in current_line]),
                        'confidence': sum([w['confidence'] for w in current_line]) / len(current_line)
                    })
                current_line = [word]
                current_y = word['y1']
        
        # Add the last line
        if current_line:
            current_line.sort(key=lambda w: w['x0'])
            lines.append({
                'words': current_line,
                'text': ' '.join([w['text'] for w in current_line]),
                'y_position': current_y,
                'x_start': min([w['x0'] for w in current_line]),
                'x_end': max([w['x1'] for w in current_line]),
                'confidence': sum([w['confidence'] for w in current_line]) / len(current_line)
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
                prev_line = lines[i-1]
                
                # Calculate vertical gap between lines
                y_gap = prev_line['y_position'] - line['y_position']
                
                # Calculate horizontal alignment difference
                alignment_diff = abs(line['x_start'] - prev_line['x_start'])
                
                # Start new paragraph if large gap or significant alignment change
                if y_gap > 30 or alignment_diff > 100:
                    # Finish current paragraph
                    paragraphs.append({
                        'lines': current_paragraph,
                        'text': '\n'.join([l['text'] for l in current_paragraph]),
                        'start_y': current_paragraph[0]['y_position'],
                        'end_y': current_paragraph[-1]['y_position'],
                        'confidence': sum([l['confidence'] for l in current_paragraph]) / len(current_paragraph)
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
                'end_y': current_paragraph[-1]['y_position'],
                'confidence': sum([l['confidence'] for l in current_paragraph]) / len(current_paragraph)
            })
        
        return paragraphs
    
    def _analyze_ocr_layout(self, words: List[Dict], page_width: int, page_height: int) -> Dict[str, Any]:
        """
        Analyze page layout from OCR word positions
        """
        layout_info = {
            'page_width': page_width,
            'page_height': page_height,
            'columns': 1,
            'column_boundaries': [],
            'margins': {'left': 0, 'right': 0, 'top': 0, 'bottom': 0},
            'text_regions': []
        }
        
        if not words:
            return layout_info
        
        # Calculate margins
        x_coords = [w['x0'] for w in words] + [w['x1'] for w in words]
        y_coords = [w['y0'] for w in words] + [w['y1'] for w in words]
        
        if x_coords and y_coords:
            layout_info['margins'] = {
                'left': min(x_coords),
                'right': page_width - max(x_coords),
                'top': min(y_coords),
                'bottom': page_height - max(y_coords)
            }
        
        # Simple column detection based on x-coordinate clustering
        x_starts = [w['x0'] for w in words]
        if x_starts:
            # Find potential column boundaries by looking for gaps in x-coordinates
            x_starts_sorted = sorted(set(x_starts))
            
            # Look for significant gaps that might indicate column boundaries
            gaps = []
            for i in range(len(x_starts_sorted) - 1):
                gap_size = x_starts_sorted[i + 1] - x_starts_sorted[i]
                if gap_size > page_width * 0.1:  # Gap > 10% of page width
                    gaps.append({
                        'start': x_starts_sorted[i],
                        'end': x_starts_sorted[i + 1],
                        'size': gap_size
                    })
            
            if gaps:
                # Take the largest gap as potential column separator
                largest_gap = max(gaps, key=lambda g: g['size'])
                if largest_gap['size'] > page_width * 0.15:  # Significant gap
                    layout_info['columns'] = 2
                    layout_info['column_boundaries'] = [largest_gap['start'], largest_gap['end']]
        
        return layout_info
    
    def enhance_ocr_quality(self, image: Image.Image) -> Image.Image:
        """
        Apply HIGH QUALITY image preprocessing to improve OCR accuracy
        """
        try:
            from PIL import ImageEnhance, ImageFilter, ImageOps
            
            # Convert to grayscale if needed
            if image.mode != 'L':
                image = image.convert('L')
            
            # Upscale if image is too small (improves OCR accuracy significantly)
            width, height = image.size
            if width < 500 or height < 200:
                scale_factor = max(500 / width, 200 / height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Upscaled image from {width}x{height} to {new_size[0]}x{new_size[1]} (factor: {scale_factor:.2f})")
            
            # Enhance contrast (critical for OCR)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)  # Increased contrast
            
            # Enhance sharpness (helps with character recognition)
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)  # More sharpening
            
            # Auto-level the image (normalize brightness)
            image = ImageOps.autocontrast(image)
            
            # Apply unsharp mask for better character definition
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            
            # Slight noise reduction
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image
    
    def get_optimal_tesseract_config(self, image_analysis: Dict[str, Any] = None) -> str:
        """
        Get optimal Tesseract configuration based on image analysis
        
        Args:
            image_analysis: Analysis of the image content
            
        Returns:
            Optimal Tesseract configuration string
        """
        if not image_analysis:
            return self.tesseract_configs['exam_paper']
        
        # Analyze image properties to choose best config
        layout_type = image_analysis.get('layout_type', 'mixed')
        text_density = image_analysis.get('text_density', 'medium')
        
        if layout_type == 'single_column' and text_density == 'high':
            return self.tesseract_configs['single_column']
        elif text_density == 'sparse':
            return self.tesseract_configs['sparse_text']
        elif image_analysis.get('contains_numbers_only', False):
            return self.tesseract_configs['numbers_only']
        elif image_analysis.get('high_quality', False):
            return self.tesseract_configs['high_quality']
        else:
            return self.tesseract_configs['exam_paper']
    
    def get_ocr_languages(self) -> List[str]:
        """
        Get available OCR languages
        """
        try:
            if self.tesseract_available:
                return pytesseract.get_languages()
            return []
        except Exception:
            return ['eng']  # Default to English
    
    def estimate_ocr_confidence(self, text: str, confidence_scores: List[float]) -> float:
        """
        Estimate overall OCR confidence for extracted text
        """
        if not confidence_scores:
            return 0.0
        
        # Filter out very low confidence scores (likely noise)
        valid_scores = [score for score in confidence_scores if score > 10]
        
        if not valid_scores:
            return 0.0
        
        # Calculate weighted confidence based on text length and scores
        avg_confidence = sum(valid_scores) / len(valid_scores)
        
        # Adjust based on text characteristics
        if len(text.strip()) < 50:  # Very short text is less reliable
            avg_confidence *= 0.8
        
        # Check for common OCR errors
        error_indicators = ['||', '|', '~', '^', '`']
        error_count = sum(text.count(indicator) for indicator in error_indicators)
        
        if error_count > len(text) * 0.05:  # More than 5% error characters
            avg_confidence *= 0.7
        
        return min(avg_confidence, 100.0)


class EasyOCRProcessor:
    """
    Alternative OCR processor using EasyOCR (more accurate for some documents)
    """
    
    def __init__(self):
        self.reader = None
        self.available = False
        
        try:
            import easyocr
            self.reader = easyocr.Reader(['en'], gpu=False)  # Use CPU
            self.available = True
        except ImportError:
            logger.warning("EasyOCR not available")
        except Exception as e:
            logger.warning(f"EasyOCR initialization failed: {e}")
    
    def process_image_with_easyocr(self, image: Image.Image, page_number: int) -> Dict[str, Any]:
        """
        Process image using EasyOCR
        """
        if not self.available:
            return {
                'success': False,
                'page_number': page_number,
                'text': '',
                'words': [],
                'confidence': 0.0,
                'error': 'EasyOCR not available'
            }
        
        try:
            # Convert PIL Image to numpy array
            import numpy as np
            image_array = np.array(image)
            
            # Process with EasyOCR
            results = self.reader.readtext(image_array, detail=1)
            
            # Extract text and word data
            text_parts = []
            words = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                if text.strip():
                    text_parts.append(text)
                    
                    # Convert bounding box to our format
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    
                    word_data = {
                        'text': text,
                        'x0': min(x_coords),
                        'y0': min(y_coords),
                        'x1': max(x_coords),
                        'y1': max(y_coords),
                        'confidence': confidence * 100,  # Convert to percentage
                        'fontname': 'unknown',
                        'size': 0
                    }
                    words.append(word_data)
                    confidences.append(confidence * 100)
            
            return {
                'success': True,
                'page_number': page_number,
                'text': ' '.join(text_parts),
                'words': words,
                'confidence': sum(confidences) / len(confidences) if confidences else 0.0,
                'method': 'easyocr'
            }
            
        except Exception as e:
            logger.error(f"EasyOCR processing failed: {e}")
            return {
                'success': False,
                'page_number': page_number,
                'text': '',
                'words': [],
                'confidence': 0.0,
                'error': str(e)
            }


class OCRManager:
    """
    Manages multiple OCR processors and selects the best results
    Production OCR upgrade with enhanced processing pipeline
    """
    
    def __init__(self):
        self.tesseract_processor = OCRProcessor()
        self.easyocr_processor = EasyOCRProcessor()
        
        # Enhanced OCR integration
        self.enhanced_ocr_available = ENHANCED_OCR_AVAILABLE
        if self.enhanced_ocr_available:
            logger.info("Enhanced OCR pipeline active - Production mode enabled")
        else:
            logger.info("Using legacy OCR processors only")
    
    def process_image_with_ocr(self, image: Image.Image) -> Dict[str, Any]:
        """
        Process a single image with SIMPLE, WORKING OCR
        """
        logger.info("Using SIMPLE OCR - no more complexity!")
        
        # Use high-quality Tesseract with image preprocessing
        if self.tesseract_processor.tesseract_available:
            # Apply high-quality image enhancement for better OCR
            enhanced_image = self.tesseract_processor.enhance_ocr_quality(image)
            
            # Choose best Tesseract configuration based on image size
            width, height = enhanced_image.size
            if height > 300:  # Multi-line text (exam questions)
                self.tesseract_processor.tesseract_config = self.tesseract_processor.tesseract_configs['exam_paper']
                logger.info("Using exam_paper config for multi-line text")
            else:  # Single line or small text
                self.tesseract_processor.tesseract_config = self.tesseract_processor.tesseract_configs['questions_with_options']
                logger.info("Using questions_with_options config for compact text")
            
            result = self.tesseract_processor.process_image_with_ocr(enhanced_image)
            if result['success']:
                # Simple post-processing to improve spacing
                text = result.get('text', '')
                # Fix common OCR spacing issues
                text = text.replace('  ', ' ')  # Multiple spaces to single space
                text = text.replace('\n\n', '\n')  # Multiple newlines to single newline
                text = text.strip()
                
                result['text'] = text
                result['enhanced_ocr'] = False
                result['method'] = 'simple_tesseract'
                logger.info(f"Simple OCR successful: confidence={result.get('confidence', 0):.1f}%, text_length={len(text)}")
                return result
        
        # Try EasyOCR as simple fallback
        if self.easyocr_processor.available:
            try:
                result = self.easyocr_processor.process_image_with_easyocr(image, 1)
                if result['success']:
                    # Simple post-processing for EasyOCR too
                    text = result.get('text', '')
                    text = text.replace('  ', ' ')  # Fix spacing
                    text = text.strip()
                    
                    result['text'] = text
                    result['enhanced_ocr'] = False
                    result['method'] = 'simple_easyocr'
                    logger.info(f"Simple EasyOCR successful: confidence={result.get('confidence', 0):.1f}%, text_length={len(text)}")
                    return result
            except Exception as e:
                logger.warning(f"EasyOCR processing failed: {e}")
        
        # No OCR available
        return {
            'success': False,
            'error': 'No OCR processors available or all failed',
            'text': '',
            'words': [],
            'lines': [],
            'paragraphs': [],
            'enhanced_ocr': False
        }
    
    def process_pdf_with_best_ocr(self, pdf_file: UploadedFile) -> Dict[str, Any]:
        """
        Process PDF using the best available OCR method
        """
        results = []
        
        # Try Tesseract first (faster)
        if self.tesseract_processor.tesseract_available:
            tesseract_result = self.tesseract_processor.process_pdf_with_ocr(pdf_file)
            if tesseract_result['success']:
                results.append(('tesseract', tesseract_result))
        
        # Try EasyOCR if Tesseract fails or for comparison
        if self.easyocr_processor.available and (not results or self._should_try_easyocr(results[0][1])):
            # For now, skip EasyOCR to avoid long processing times
            # easyocr_result = self._process_with_easyocr(pdf_file)
            # if easyocr_result['success']:
            #     results.append(('easyocr', easyocr_result))
            pass
        
        if not results:
            return {
                'success': False,
                'error': 'No OCR processors available',
                'pages': [],
                'total_pages': 0
            }
        
        # Return the best result (for now, just return the first successful one)
        return results[0][1]
    
    def process_region_with_enhanced_ocr(self, image_path: str, region_coords: Dict) -> Dict[str, Any]:
        """
        Process a specific region using enhanced OCR pipeline
        
        Args:
            image_path: Path to the image file
            region_coords: Dictionary with 'x', 'y', 'width', 'height' keys
            
        Returns:
            Dictionary with enhanced OCR results
        """
        if not self.enhanced_ocr_available:
            # Fallback to legacy region processing
            return self._process_region_legacy(image_path, region_coords)
        
        try:
            from .enhanced_ocr import extract_text_from_region_enhanced
            
            # Use enhanced OCR for region processing
            result = extract_text_from_region_enhanced(image_path, region_coords)
            
            # Add performance metrics
            if result.get('success'):
                logger.info(f"Enhanced region OCR successful: "
                          f"engine={result.get('engine', 'unknown')}, "
                          f"confidence={result.get('confidence', 0):.2f}, "
                          f"processing_time={result.get('processing_time', 0):.2f}s, "
                          f"preprocessing={result.get('preprocessing_applied', [])}")
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced region OCR failed: {e}")
            # Fallback to legacy processing
            return self._process_region_legacy(image_path, region_coords)
    
    def _process_region_legacy(self, image_path: str, region_coords: Dict) -> Dict[str, Any]:
        """
        Legacy region processing using Tesseract
        """
        try:
            import cv2
            
            # Load and crop image to region
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image from {image_path}")
            
            x = region_coords['x']
            y = region_coords['y']
            w = region_coords['width'] 
            h = region_coords['height']
            
            # Crop to region
            cropped_image = image[y:y+h, x:x+w]
            
            # Convert to PIL Image
            from PIL import Image
            pil_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
            
            # Use legacy OCR processing
            result = self.process_image_with_ocr(pil_image)
            
            return {
                'text': result.get('text', ''),
                'confidence': result.get('confidence', 0.0),
                'success': result.get('success', False),
                'engine': 'Legacy Tesseract',
                'processing_time': 0.0,
                'preprocessing_applied': []
            }
            
        except Exception as e:
            logger.error(f"Legacy region OCR failed: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'success': False,
                'error': str(e),
                'engine': 'Legacy (Failed)',
                'processing_time': 0.0
            }
    
    def get_ocr_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics from enhanced OCR system
        """
        if self.enhanced_ocr_available:
            try:
                return enhanced_ocr.get_performance_stats()
            except Exception as e:
                logger.warning(f"Could not get enhanced OCR stats: {e}")
        
        return {
            'enhanced_ocr_available': self.enhanced_ocr_available,
            'legacy_processors': {
                'tesseract_available': self.tesseract_processor.tesseract_available,
                'easyocr_available': self.easyocr_processor.available
            }
        }
    
    def benchmark_ocr_performance(self, test_images: List[str] = None) -> Dict[str, Any]:
        """
        Run OCR performance benchmarks
        """
        if not self.enhanced_ocr_available or not test_images:
            return {'benchmark_available': False, 'reason': 'Enhanced OCR or test images not available'}
        
        try:
            return enhanced_ocr.benchmark_engines(test_images, iterations=3)
        except Exception as e:
            logger.error(f"OCR benchmark failed: {e}")
            return {'benchmark_failed': True, 'error': str(e)}
    
    def _should_try_easyocr(self, tesseract_result: Dict[str, Any]) -> bool:
        """
        Determine if EasyOCR should be tried based on Tesseract results
        """
        if not tesseract_result.get('success'):
            return True
        
        # Check average confidence
        total_confidence = 0
        total_pages = 0
        
        for page in tesseract_result.get('pages', []):
            if 'confidence' in page:
                total_confidence += page['confidence']
                total_pages += 1
        
        if total_pages > 0:
            avg_confidence = total_confidence / total_pages
            return avg_confidence < 70  # Try EasyOCR if confidence is low
        
        return False