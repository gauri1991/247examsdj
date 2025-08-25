"""
Enhanced OCR Processor - Production-Grade OCR Pipeline
Combines multiple OCR engines with preprocessing and confidence scoring for maximum accuracy.

Phase 1: Production OCR Upgrade
- PaddleOCR as primary engine
- OpenCV preprocessing pipeline  
- Multi-engine confidence scoring
- Performance benchmarking
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, List, Tuple, Optional, Union
import logging
import time
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Optional imports with graceful fallbacks
try:
    from skimage import restoration
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False

try:
    from deskew import determine_skew
    DESKEW_AVAILABLE = True
except ImportError:
    DESKEW_AVAILABLE = False

# EasyOCR - stable and reliable OCR engine
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """Structured OCR result with confidence scoring"""
    text: str
    confidence: float
    engine: str
    processing_time: float
    bbox: Optional[List[Tuple[int, int]]] = None
    word_confidences: Optional[List[float]] = None
    preprocessing_applied: Optional[List[str]] = None
    
    def to_dict(self):
        return asdict(self)


class ImagePreprocessor:
    """Advanced image preprocessing pipeline using OpenCV and scikit-image"""
    
    def __init__(self):
        self.preprocessing_steps = []
    
    def enhance_image(self, image: np.ndarray, steps: List[str] = None) -> Tuple[np.ndarray, List[str]]:
        """Apply preprocessing pipeline to enhance OCR accuracy"""
        if steps is None:
            steps = ['denoise', 'deskew', 'contrast', 'sharpen', 'binarize']
        
        processed_image = image.copy()
        applied_steps = []
        
        try:
            # Convert to grayscale if needed
            if len(processed_image.shape) == 3:
                processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
            
            # 1. Noise Reduction
            if 'denoise' in steps:
                processed_image = cv2.bilateralFilter(processed_image, 9, 75, 75)
                # Additional denoising using scikit-image (if available)
                if SKIMAGE_AVAILABLE:
                    processed_image = restoration.denoise_tv_chambolle(
                        processed_image, weight=0.1
                    ).astype(np.uint8)
                    applied_steps.append('denoise_advanced')
                else:
                    applied_steps.append('denoise_basic')
            
            # 2. Deskew correction
            if 'deskew' in steps and DESKEW_AVAILABLE:
                try:
                    angle = determine_skew(processed_image)
                    if abs(angle) > 0.5:  # Only deskew if significant skew detected
                        h, w = processed_image.shape
                        center = (w // 2, h // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                        processed_image = cv2.warpAffine(
                            processed_image, rotation_matrix, (w, h),
                            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
                        )
                        applied_steps.append(f'deskew_{angle:.1f}deg')
                except Exception:
                    applied_steps.append('deskew_skipped')
            
            # 3. Contrast Enhancement
            if 'contrast' in steps:
                # CLAHE (Contrast Limited Adaptive Histogram Equalization)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                processed_image = clahe.apply(processed_image)
                applied_steps.append('contrast')
            
            # 4. Sharpening
            if 'sharpen' in steps:
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                processed_image = cv2.filter2D(processed_image, -1, kernel)
                applied_steps.append('sharpen')
            
            # 5. Morphological operations for text enhancement
            if 'morphology' in steps:
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                processed_image = cv2.morphologyEx(processed_image, cv2.MORPH_CLOSE, kernel)
                applied_steps.append('morphology')
            
            # 6. Binarization (Adaptive Thresholding)
            if 'binarize' in steps:
                processed_image = cv2.adaptiveThreshold(
                    processed_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
                applied_steps.append('binarize')
            
            # 7. Resize for better OCR (if image is too small)
            if 'resize' in steps:
                h, w = processed_image.shape
                if h < 300 or w < 300:  # Minimum size for good OCR
                    scale_factor = max(300 / h, 300 / w)
                    new_w, new_h = int(w * scale_factor), int(h * scale_factor)
                    processed_image = cv2.resize(
                        processed_image, (new_w, new_h), interpolation=cv2.INTER_CUBIC
                    )
                    applied_steps.append(f'resize_{scale_factor:.1f}x')
            
        except Exception as e:
            logger.error(f"Error in image preprocessing: {e}")
            return image, ['error']
        
        self.preprocessing_steps = applied_steps
        return processed_image, applied_steps


class EnhancedOCRProcessor:
    """Production-grade OCR processor with multiple engines and confidence scoring"""
    
    def __init__(self):
        # Initialize OCR engines
        self.easyocr_reader = None
        self.tesseract_available = False
        self.preprocessor = ImagePreprocessor()
        
        # Performance tracking
        self.performance_stats = {
            'total_requests': 0,
            'easyocr_requests': 0,
            'tesseract_requests': 0,
            'avg_processing_time': 0.0,
            'confidence_scores': []
        }
        
        # Thread lock for performance stats
        self.stats_lock = threading.Lock()
        
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize available OCR engines"""
        # Initialize EasyOCR
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)  # CPU mode for stability
                logger.info("EasyOCR initialized successfully (CPU mode)")
            except Exception as e:
                logger.warning(f"EasyOCR initialization failed: {e}")
                self.easyocr_reader = None
        else:
            logger.warning("EasyOCR not installed")
            self.easyocr_reader = None
        
        try:
            # Test Tesseract availability
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            logger.info("Tesseract OCR available")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            self.tesseract_available = False
    
    def _easyocr_extract(self, image: np.ndarray) -> OCRResult:
        """Extract text using EasyOCR"""
        if not self.easyocr_reader:
            raise ValueError("EasyOCR not available")
        
        start_time = time.time()
        
        try:
            # EasyOCR works with RGB images
            if len(image.shape) == 3 and image.shape[2] == 3:
                # Ensure RGB format
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if image.shape[2] == 3 else image
            else:
                image_rgb = image
            
            # EasyOCR readtext with detailed results
            results = self.easyocr_reader.readtext(
                image_rgb, 
                detail=1,
                paragraph=True,  # Group text into paragraphs
                width_ths=0.7,   # Width threshold for text grouping
                height_ths=0.7   # Height threshold for text grouping
            )
            
            # Extract text and confidence
            text_parts = []
            confidences = []
            bboxes = []
            
            for (bbox, text, confidence) in results:
                if text.strip() and confidence > 0.1:  # Filter low confidence
                    text_parts.append(text.strip())
                    confidences.append(confidence)
                    bboxes.append(bbox)
            
            # Join text parts with proper spacing
            full_text = ' '.join(text_parts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                engine="EasyOCR",
                processing_time=processing_time,
                bbox=bboxes,
                word_confidences=confidences
            )
            
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return OCRResult(
                text="", confidence=0.0, engine="EasyOCR",
                processing_time=time.time() - start_time
            )
    
    def _tesseract_extract(self, image: np.ndarray, config: str = None) -> OCRResult:
        """Extract text using Tesseract OCR"""
        if not self.tesseract_available:
            raise ValueError("Tesseract not available")
        
        start_time = time.time()
        
        try:
            if config is None:
                # Optimized config for exam papers with proper spacing
                config = '--oem 3 --psm 6 -c preserve_interword_spaces=1 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,?!()- '
            
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(image)
            
            # Extract text with confidence
            data = pytesseract.image_to_data(pil_image, config=config, output_type=pytesseract.Output.DICT)
            
            # Filter out low confidence detections and combine text
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > 0:  # Filter out negative confidence scores
                    word = data['text'][i].strip()
                    if word:  # Only include non-empty words
                        text_parts.append(word)
                        confidences.append(int(conf))
            
            full_text = ' '.join(text_parts)
            avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0  # Convert to 0-1 range
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                engine="Tesseract",
                processing_time=processing_time,
                word_confidences=[c/100.0 for c in confidences]
            )
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return OCRResult(
                text="", confidence=0.0, engine="Tesseract",
                processing_time=time.time() - start_time
            )
    
    def extract_text(self, image: Union[np.ndarray, str], 
                    use_preprocessing: bool = True,
                    engines: List[str] = None,
                    return_best: bool = True) -> Union[OCRResult, List[OCRResult]]:
        """
        Enhanced text extraction with multiple engines and preprocessing
        
        Args:
            image: Input image (numpy array or file path)
            use_preprocessing: Apply image preprocessing pipeline
            engines: List of engines to use ['paddle', 'tesseract'] or None for all available
            return_best: Return only the best result or all results
            
        Returns:
            OCRResult or List[OCRResult]
        """
        # Load image if path provided
        if isinstance(image, str):
            image = cv2.imread(image)
            if image is None:
                raise ValueError(f"Could not load image from {image}")
        
        # Apply preprocessing if requested
        processed_image = image
        preprocessing_applied = []
        
        if use_preprocessing:
            processed_image, preprocessing_applied = self.preprocessor.enhance_image(image)
        
        # Determine which engines to use
        if engines is None:
            engines = []
            if self.easyocr_reader:
                engines.append('easyocr')
            if self.tesseract_available:
                engines.append('tesseract')
        
        if not engines:
            raise ValueError("No OCR engines available")
        
        # Run OCR with selected engines
        results = []
        
        # Use threading for concurrent processing when multiple engines
        if len(engines) > 1:
            with ThreadPoolExecutor(max_workers=len(engines)) as executor:
                future_to_engine = {}
                
                for engine in engines:
                    if engine == 'easyocr' and self.easyocr_reader:
                        future = executor.submit(self._easyocr_extract, processed_image)
                        future_to_engine[future] = engine
                    elif engine == 'tesseract' and self.tesseract_available:
                        future = executor.submit(self._tesseract_extract, processed_image)
                        future_to_engine[future] = engine
                
                for future in as_completed(future_to_engine):
                    try:
                        result = future.result()
                        result.preprocessing_applied = preprocessing_applied
                        results.append(result)
                    except Exception as e:
                        engine = future_to_engine[future]
                        logger.error(f"Error in {engine} OCR: {e}")
        else:
            # Single engine processing
            engine = engines[0]
            try:
                if engine == 'easyocr' and self.easyocr_reader:
                    result = self._easyocr_extract(processed_image)
                elif engine == 'tesseract' and self.tesseract_available:
                    result = self._tesseract_extract(processed_image)
                else:
                    raise ValueError(f"Engine {engine} not available")
                
                result.preprocessing_applied = preprocessing_applied
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error in {engine} OCR: {e}")
        
        # Update performance stats
        self._update_performance_stats(results)
        
        if not results:
            # Return empty result if all engines failed
            return OCRResult(
                text="", confidence=0.0, engine="None",
                processing_time=0.0, preprocessing_applied=preprocessing_applied
            )
        
        # Return best result or all results
        if return_best:
            # Select best result based on confidence and text length
            best_result = max(results, key=lambda r: (r.confidence, len(r.text.strip())))
            return best_result
        else:
            return results
    
    def _update_performance_stats(self, results: List[OCRResult]):
        """Update performance statistics"""
        with self.stats_lock:
            self.performance_stats['total_requests'] += 1
            
            for result in results:
                if result.engine == 'EasyOCR':
                    self.performance_stats['easyocr_requests'] += 1
                elif result.engine == 'Tesseract':
                    self.performance_stats['tesseract_requests'] += 1
                
                self.performance_stats['confidence_scores'].append(result.confidence)
            
            # Update average processing time
            if results:
                avg_time = np.mean([r.processing_time for r in results])
                current_avg = self.performance_stats['avg_processing_time']
                total_requests = self.performance_stats['total_requests']
                
                # Calculate running average
                self.performance_stats['avg_processing_time'] = (
                    (current_avg * (total_requests - 1) + avg_time) / total_requests
                )
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        with self.stats_lock:
            stats = self.performance_stats.copy()
            
            # Calculate additional metrics
            if stats['confidence_scores']:
                stats['avg_confidence'] = np.mean(stats['confidence_scores'])
                stats['min_confidence'] = np.min(stats['confidence_scores'])
                stats['max_confidence'] = np.max(stats['confidence_scores'])
            
            return stats
    
    def benchmark_engines(self, test_images: List[Union[str, np.ndarray]], 
                         iterations: int = 3) -> Dict:
        """Benchmark different OCR engines for performance comparison"""
        logger.info(f"Starting OCR benchmark with {len(test_images)} images, {iterations} iterations")
        
        benchmark_results = {
            'easyocr': {'times': [], 'confidences': [], 'text_lengths': []},
            'tesseract': {'times': [], 'confidences': [], 'text_lengths': []}
        }
        
        for image in test_images:
            for _ in range(iterations):
                # Test EasyOCR
                if self.easyocr_reader:
                    result = self.extract_text(image, engines=['easyocr'], return_best=True)
                    benchmark_results['easyocr']['times'].append(result.processing_time)
                    benchmark_results['easyocr']['confidences'].append(result.confidence)
                    benchmark_results['easyocr']['text_lengths'].append(len(result.text))
                
                # Test Tesseract
                if self.tesseract_available:
                    result = self.extract_text(image, engines=['tesseract'], return_best=True)
                    benchmark_results['tesseract']['times'].append(result.processing_time)
                    benchmark_results['tesseract']['confidences'].append(result.confidence)
                    benchmark_results['tesseract']['text_lengths'].append(len(result.text))
        
        # Calculate summary statistics
        summary = {}
        for engine, data in benchmark_results.items():
            if data['times']:  # Only if engine was tested
                summary[engine] = {
                    'avg_time': np.mean(data['times']),
                    'std_time': np.std(data['times']),
                    'avg_confidence': np.mean(data['confidences']),
                    'avg_text_length': np.mean(data['text_lengths']),
                    'total_tests': len(data['times'])
                }
        
        logger.info("OCR benchmark completed")
        return summary


# Global instance for easy import
enhanced_ocr = EnhancedOCRProcessor()


def extract_text_enhanced(image: Union[np.ndarray, str], **kwargs) -> OCRResult:
    """Convenience function for enhanced OCR extraction"""
    return enhanced_ocr.extract_text(image, **kwargs)


# Backward compatibility function for existing code
def extract_text_from_region_enhanced(image_path: str, region_coords: Dict) -> Dict:
    """
    Enhanced OCR extraction for region compatibility with existing codebase
    
    Args:
        image_path: Path to the image file
        region_coords: Dictionary with 'x', 'y', 'width', 'height' keys
        
    Returns:
        Dictionary with OCR results in expected format
    """
    try:
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
        
        # Extract text using enhanced OCR
        result = enhanced_ocr.extract_text(cropped_image, use_preprocessing=True, return_best=True)
        
        # Return in expected format
        return {
            'text': result.text,
            'confidence': result.confidence,
            'success': True,
            'engine': result.engine,
            'processing_time': result.processing_time,
            'preprocessing_applied': result.preprocessing_applied
        }
        
    except Exception as e:
        logger.error(f"Enhanced OCR extraction failed: {e}")
        return {
            'text': '',
            'confidence': 0.0,
            'success': False,
            'error': str(e),
            'engine': 'Enhanced OCR',
            'processing_time': 0.0
        }