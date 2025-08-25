"""
PDF to Image Conversion Module
Handles conversion of PDF pages to images for advanced processing
"""

import io
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
import tempfile
import shutil

try:
    from pdf2image import convert_from_path, convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logging.warning("pdf2image not available. Install with: pip install pdf2image")

logger = logging.getLogger('pdf_extractor.pdf_to_image')


class PDFToImageConverter:
    """
    Converts PDF pages to images with optimized settings for different purposes
    """
    
    # DPI settings for different use cases
    DPI_DETECTION = 150  # Lower DPI for initial detection (faster)
    DPI_OCR = 300       # Higher DPI for OCR (better accuracy)
    DPI_PREVIEW = 100   # Low DPI for thumbnails
    
    # Image format settings
    DEFAULT_FORMAT = 'PNG'
    SUPPORTED_FORMATS = ['PNG', 'JPEG', 'TIFF']
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize PDF to Image converter
        
        Args:
            cache_dir: Directory for caching converted images
        """
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError(
                "pdf2image is required for PDF to image conversion. "
                "Install it with: pip install pdf2image"
            )
        
        # Setup cache directory
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = os.path.join(
                settings.MEDIA_ROOT, 
                'pdf_image_cache'
            )
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Conversion settings
        self.max_parallel_pages = 4  # Process 4 pages at a time
        self.jpeg_quality = 85       # JPEG compression quality
        
    def convert_pdf_to_images(
        self, 
        pdf_file: UploadedFile, 
        dpi: int = None,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None,
        fmt: str = 'PNG',
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Convert PDF pages to images
        
        Args:
            pdf_file: PDF file to convert
            dpi: DPI for conversion (default: DPI_DETECTION)
            first_page: First page to convert (1-indexed)
            last_page: Last page to convert
            fmt: Image format (PNG, JPEG, TIFF)
            use_cache: Whether to use cached images if available
            
        Returns:
            Dict containing conversion results
        """
        if dpi is None:
            dpi = self.DPI_DETECTION
            
        if fmt not in self.SUPPORTED_FORMATS:
            fmt = self.DEFAULT_FORMAT
            
        result = {
            'success': False,
            'images': [],
            'page_count': 0,
            'dpi': dpi,
            'format': fmt,
            'errors': []
        }
        
        try:
            # Generate cache key based on file content
            pdf_file.seek(0)
            file_hash = self._generate_file_hash(pdf_file.read())
            pdf_file.seek(0)
            
            # Check cache if enabled
            if use_cache:
                cached_images = self._get_cached_images(file_hash, dpi, fmt)
                if cached_images:
                    result['success'] = True
                    result['images'] = cached_images
                    result['page_count'] = len(cached_images)
                    result['from_cache'] = True
                    logger.info(f"Retrieved {len(cached_images)} images from cache")
                    return result
            
            # Convert PDF to images
            logger.info(f"Converting PDF to images at {dpi} DPI")
            
            # Use temporary file for pdf2image
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_file.read())
                tmp_file.flush()
                
                # Convert pages
                images = convert_from_path(
                    tmp_file.name,
                    dpi=dpi,
                    first_page=first_page,
                    last_page=last_page,
                    fmt=fmt,
                    thread_count=self.max_parallel_pages,
                    use_pdftocairo=True  # Better quality
                )
                
                # Process and save images
                image_data = []
                for i, image in enumerate(images):
                    page_num = (first_page or 1) + i
                    
                    # Save to cache
                    image_path = self._save_image_to_cache(
                        image, file_hash, page_num, dpi, fmt
                    )
                    
                    # Get image info
                    image_info = {
                        'page_number': page_num,
                        'path': image_path,
                        'width': image.width,
                        'height': image.height,
                        'dpi': dpi,
                        'format': fmt,
                        'size_bytes': os.path.getsize(image_path)
                    }
                    
                    image_data.append(image_info)
                
                # Clean up temp file
                os.unlink(tmp_file.name)
                
            result['success'] = True
            result['images'] = image_data
            result['page_count'] = len(image_data)
            result['from_cache'] = False
            
            logger.info(f"Successfully converted {len(image_data)} pages")
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            result['errors'].append(str(e))
            
        return result
    
    def convert_page_for_ocr(
        self, 
        pdf_file: UploadedFile, 
        page_number: int
    ) -> Optional[Image.Image]:
        """
        Convert a single PDF page to high-quality image for OCR
        
        Args:
            pdf_file: PDF file
            page_number: Page number to convert (1-indexed)
            
        Returns:
            PIL Image object or None if error
        """
        try:
            result = self.convert_pdf_to_images(
                pdf_file,
                dpi=self.DPI_OCR,
                first_page=page_number,
                last_page=page_number,
                fmt='PNG',
                use_cache=True
            )
            
            if result['success'] and result['images']:
                image_path = result['images'][0]['path']
                return Image.open(image_path)
                
        except Exception as e:
            logger.error(f"Error converting page {page_number} for OCR: {str(e)}")
            
        return None
    
    def convert_for_region_detection(
        self, 
        pdf_file: UploadedFile
    ) -> Dict[str, Any]:
        """
        Convert PDF pages for region detection (lower DPI for speed)
        
        Args:
            pdf_file: PDF file to process
            
        Returns:
            Dict with conversion results optimized for detection
        """
        return self.convert_pdf_to_images(
            pdf_file,
            dpi=self.DPI_DETECTION,
            fmt='PNG',
            use_cache=True
        )
    
    def create_page_thumbnails(
        self, 
        pdf_file: UploadedFile,
        max_width: int = 200,
        max_height: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Create thumbnail images for all PDF pages
        
        Args:
            pdf_file: PDF file
            max_width: Maximum thumbnail width
            max_height: Maximum thumbnail height
            
        Returns:
            List of thumbnail information
        """
        thumbnails = []
        
        try:
            # Convert at low DPI for thumbnails
            result = self.convert_pdf_to_images(
                pdf_file,
                dpi=self.DPI_PREVIEW,
                fmt='JPEG',
                use_cache=True
            )
            
            if result['success']:
                for image_info in result['images']:
                    # Open and resize image
                    image = Image.open(image_info['path'])
                    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    
                    # Save thumbnail
                    thumb_path = image_info['path'].replace('.jpg', '_thumb.jpg')
                    image.save(thumb_path, 'JPEG', quality=80)
                    
                    thumbnails.append({
                        'page_number': image_info['page_number'],
                        'path': thumb_path,
                        'width': image.width,
                        'height': image.height
                    })
                    
        except Exception as e:
            logger.error(f"Error creating thumbnails: {str(e)}")
            
        return thumbnails
    
    def _generate_file_hash(self, file_content: bytes) -> str:
        """Generate hash for file content"""
        import hashlib
        return hashlib.md5(file_content).hexdigest()
    
    def _get_cache_path(
        self, 
        file_hash: str, 
        page_num: int, 
        dpi: int, 
        fmt: str
    ) -> str:
        """Generate cache file path"""
        filename = f"{file_hash}_p{page_num}_dpi{dpi}.{fmt.lower()}"
        return os.path.join(self.cache_dir, filename)
    
    def _save_image_to_cache(
        self, 
        image: Image.Image, 
        file_hash: str, 
        page_num: int, 
        dpi: int, 
        fmt: str
    ) -> str:
        """Save image to cache"""
        cache_path = self._get_cache_path(file_hash, page_num, dpi, fmt)
        
        if fmt == 'JPEG':
            image.save(cache_path, fmt, quality=self.jpeg_quality)
        else:
            image.save(cache_path, fmt)
            
        return cache_path
    
    def _get_cached_images(
        self, 
        file_hash: str, 
        dpi: int, 
        fmt: str
    ) -> List[Dict[str, Any]]:
        """Check if cached images exist"""
        cached_images = []
        page_num = 1
        
        while True:
            cache_path = self._get_cache_path(file_hash, page_num, dpi, fmt)
            if os.path.exists(cache_path):
                image = Image.open(cache_path)
                cached_images.append({
                    'page_number': page_num,
                    'path': cache_path,
                    'width': image.width,
                    'height': image.height,
                    'dpi': dpi,
                    'format': fmt,
                    'size_bytes': os.path.getsize(cache_path)
                })
                page_num += 1
            else:
                break
                
        return cached_images if cached_images else None
    
    def clear_cache(self, older_than_days: int = 7):
        """
        Clear cached images older than specified days
        
        Args:
            older_than_days: Remove files older than this many days
        """
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (older_than_days * 24 * 60 * 60)
        
        cleared_count = 0
        cleared_size = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    
                    if file_stat.st_mtime < cutoff_time:
                        cleared_size += file_stat.st_size
                        os.remove(file_path)
                        cleared_count += 1
                        
            logger.info(
                f"Cleared {cleared_count} cached images "
                f"({cleared_size / 1024 / 1024:.2f} MB)"
            )
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
    
    def get_cache_size(self) -> Dict[str, Any]:
        """Get current cache size and file count"""
        total_size = 0
        file_count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                    
        except Exception as e:
            logger.error(f"Error calculating cache size: {str(e)}")
            
        return {
            'total_size_mb': total_size / 1024 / 1024,
            'file_count': file_count,
            'cache_dir': self.cache_dir
        }


class ImagePreprocessor:
    """
    Preprocesses images for better OCR and region detection
    """
    
    def __init__(self):
        self.has_cv2 = self._check_opencv()
        
    def _check_opencv(self) -> bool:
        """Check if OpenCV is available"""
        try:
            import cv2
            return True
        except ImportError:
            logger.warning("OpenCV not available. Some preprocessing features will be limited.")
            return False
    
    def preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        
        Args:
            image: PIL Image to preprocess
            
        Returns:
            Preprocessed PIL Image
        """
        if not self.has_cv2:
            # Basic preprocessing with PIL only
            return self._basic_preprocessing(image)
            
        try:
            import cv2
            
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
                
            # Apply noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL
            return Image.fromarray(thresh)
            
        except Exception as e:
            logger.error(f"Error in OpenCV preprocessing: {str(e)}")
            return self._basic_preprocessing(image)
    
    def _basic_preprocessing(self, image: Image.Image) -> Image.Image:
        """Basic preprocessing using PIL only"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
            
        # Enhance contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        return image
    
    def detect_and_correct_skew(self, image: Image.Image) -> Tuple[Image.Image, float]:
        """
        Detect and correct image skew
        
        Args:
            image: PIL Image
            
        Returns:
            Tuple of (corrected image, skew angle in degrees)
        """
        if not self.has_cv2:
            return image, 0.0
            
        try:
            import cv2
            
            # Convert to OpenCV format
            img_array = np.array(image)
            
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
                
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
            
            if lines is not None:
                # Calculate average angle
                angles = []
                for rho, theta in lines[:, 0]:
                    angle = theta * 180 / np.pi - 90
                    if -45 <= angle <= 45:
                        angles.append(angle)
                        
                if angles:
                    median_angle = np.median(angles)
                    
                    # Rotate image
                    if abs(median_angle) > 0.5:
                        (h, w) = gray.shape[:2]
                        center = (w // 2, h // 2)
                        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                        rotated = cv2.warpAffine(
                            img_array, M, (w, h),
                            flags=cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_REPLICATE
                        )
                        
                        return Image.fromarray(rotated), median_angle
                        
            return image, 0.0
            
        except Exception as e:
            logger.error(f"Error in skew correction: {str(e)}")
            return image, 0.0