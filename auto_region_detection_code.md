# Auto Region Detection Code - PDF Extractor System

This document contains all the code components responsible for automatic region detection/selection functionality in the PDF extractor system.

## Table of Contents
1. [Backend Python Code](#backend-python-code)
2. [Frontend JavaScript Code](#frontend-javascript-code)
3. [URL Patterns & API Endpoints](#url-patterns--api-endpoints)
4. [Supporting Components](#supporting-components)
5. [Configuration & Settings](#configuration--settings)

---

## Backend Python Code

### 1. Main API Endpoint (views.py)

**File Path:** `/home/gss/Desktop/dts/test_platform/pdf_extractor/views.py`

```python
@login_required
def auto_detect_regions_api(request, document_id):
    """
    API endpoint for automatic region detection on PDF pages
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        document = get_object_or_404(PDFDocument, id=document_id, uploaded_by=request.user)
        data = json.loads(request.body)
        page_number = data.get('page_number', 1)
        
        # Convert PDF page to image for processing
        pdf_path = document.file.path
        converter = PDFToImageConverter()
        
        try:
            # Convert specific page to image
            page_images = converter.convert_page_to_image(pdf_path, page_number)
            if not page_images:
                return JsonResponse({
                    'success': False, 
                    'error': f'Failed to convert page {page_number} to image'
                })
            
            actual_image = page_images[0]  # Get the first (and only) image
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'PDF to image conversion failed: {str(e)}'
            })
        
        # Perform region extraction
        region_extractor = RegionExtractor()
        detected_regions = region_extractor.extract_regions_from_image(actual_image, page_number)
        
        # Convert regions to API response format
        regions_data = []
        for i, region in enumerate(detected_regions):
            region_data = {
                'id': f'region_{i}',
                'region_type': region.region_type,
                'coordinates': {
                    'x': int(region.x),
                    'y': int(region.y), 
                    'width': int(region.width),
                    'height': int(region.height)
                },
                'confidence': float(region.confidence),
                'text_preview': region.text_preview[:100] if region.text_preview else '',
                'estimated_difficulty': region.estimated_difficulty,
                'question_indicators': region.question_indicators,
                'layout_info': region.layout_info
            }
            regions_data.append(region_data)
        
        return JsonResponse({
            'success': True,
            'regions': regions_data,
            'total_regions': len(regions_data),
            'page_number': page_number,
            'processing_method': 'auto_detection'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Region detection failed: {str(e)}'
        })
```

### 2. Region Extraction Engine (region_extractor.py)

**File Path:** `/home/gss/Desktop/dts/test_platform/pdf_extractor/region_extractor.py`

```python
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Region:
    """
    Represents a detected region in a PDF page
    """
    def __init__(self, x: int, y: int, width: int, height: int, 
                 region_type: str = 'unknown', confidence: float = 0.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.region_type = region_type  # 'question', 'answer_options', 'text', 'image'
        self.confidence = confidence
        self.text_preview = ""
        self.estimated_difficulty = ""
        self.question_indicators = []
        self.layout_info = {}
    
    @property
    def area(self) -> int:
        """Calculate the area of the region"""
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get the center point of the region"""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Get region bounds as (x, y, x2, y2)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def overlaps_with(self, other: 'Region', threshold: float = 0.1) -> bool:
        """
        Check if this region overlaps with another region
        """
        x1, y1, x2, y2 = self.bounds
        ox1, oy1, ox2, oy2 = other.bounds
        
        # Calculate intersection
        ix1 = max(x1, ox1)
        iy1 = max(y1, oy1)
        ix2 = min(x2, ox2)
        iy2 = min(y2, oy2)
        
        if ix1 < ix2 and iy1 < iy2:
            intersection_area = (ix2 - ix1) * (iy2 - iy1)
            min_area = min(self.area, other.area)
            overlap_ratio = intersection_area / min_area
            return overlap_ratio > threshold
        
        return False
    
    def distance_to(self, other: 'Region') -> float:
        """Calculate distance between region centers"""
        cx1, cy1 = self.center
        cx2, cy2 = other.center
        return ((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2) ** 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert region to dictionary for serialization"""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'region_type': self.region_type,
            'confidence': self.confidence,
            'text_preview': self.text_preview,
            'estimated_difficulty': self.estimated_difficulty,
            'question_indicators': self.question_indicators,
            'layout_info': self.layout_info
        }

class RegionExtractor:
    """
    Main class for extracting regions from PDF page images
    """
    
    def __init__(self):
        # Detection parameters
        self.min_region_area = 500
        self.max_region_area = 200000
        self.min_text_height = 10
        self.max_text_height = 50
    
    def extract_regions_from_image(self, image: np.ndarray, page_number: int = 1) -> List[Region]:
        """
        Main method to extract regions from a PDF page image
        
        Args:
            image: OpenCV image array (BGR format)
            page_number: Page number for reference
            
        Returns:
            List of detected Region objects
        """
        if image is None or image.size == 0:
            logger.error("Invalid image provided for region extraction")
            return []
        
        try:
            logger.info(f"Starting region extraction for page {page_number}")
            logger.info(f"Image shape: {image.shape}")
            
            # Convert to grayscale for processing
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply different detection methods
            detected_regions = []
            
            # Method 1: Morphological text detection
            morph_regions = self._detect_text_regions(gray)
            detected_regions.extend(morph_regions)
            logger.info(f"Morphological detection found {len(morph_regions)} regions")
            
            # Method 2: Block-based detection
            block_regions = self._detect_block_regions(gray)
            detected_regions.extend(block_regions)
            logger.info(f"Block detection found {len(block_regions)} regions")
            
            # Method 3: Contour-based detection
            contour_regions = self._detect_contour_regions(gray)
            detected_regions.extend(contour_regions)
            logger.info(f"Contour detection found {len(contour_regions)} regions")
            
            # Filter and merge overlapping regions
            final_regions = self._filter_and_merge_regions(detected_regions)
            logger.info(f"Final region count after filtering: {len(final_regions)}")
            
            # Classify regions
            classified_regions = self._classify_regions(final_regions, gray)
            
            return classified_regions
            
        except Exception as e:
            logger.error(f"Error in region extraction: {str(e)}")
            return []
    
    def _detect_text_regions(self, gray_image: np.ndarray) -> List[Region]:
        """
        Detect text regions using morphological operations
        """
        regions = []
        
        try:
            # Apply morphological operations to detect text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 2))
            dilated = cv2.dilate(gray_image, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size
                area = w * h
                if (self.min_region_area <= area <= self.max_region_area and
                    self.min_text_height <= h <= self.max_text_height):
                    
                    region = Region(x, y, w, h, 'text', confidence=0.7)
                    regions.append(region)
            
        except Exception as e:
            logger.error(f"Error in morphological text detection: {str(e)}")
        
        return regions
    
    def _detect_block_regions(self, gray_image: np.ndarray) -> List[Region]:
        """
        Detect larger text blocks and question regions
        """
        regions = []
        
        try:
            # Use larger kernel for block detection
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
            closed = cv2.morphologyEx(gray_image, cv2.MORPH_CLOSE, kernel)
            
            # Apply threshold
            _, binary = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Filter for larger blocks
                if area >= 1000 and h >= 30:
                    region = Region(x, y, w, h, 'question', confidence=0.6)
                    regions.append(region)
                    
        except Exception as e:
            logger.error(f"Error in block detection: {str(e)}")
        
        return regions
    
    def _detect_contour_regions(self, gray_image: np.ndarray) -> List[Region]:
        """
        Detect regions using edge detection and contours
        """
        regions = []
        
        try:
            # Edge detection
            edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
            
            # Dilate edges to close gaps
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges = cv2.dilate(edges, kernel, iterations=1)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                if self.min_region_area <= area <= self.max_region_area:
                    region = Region(x, y, w, h, 'unknown', confidence=0.5)
                    regions.append(region)
                    
        except Exception as e:
            logger.error(f"Error in contour detection: {str(e)}")
        
        return regions
    
    def _filter_and_merge_regions(self, regions: List[Region]) -> List[Region]:
        """
        Filter overlapping regions and merge nearby ones
        """
        if not regions:
            return []
        
        # Sort by area (largest first)
        regions.sort(key=lambda r: r.area, reverse=True)
        
        filtered_regions = []
        
        for region in regions:
            should_add = True
            
            # Check for significant overlap with existing regions
            for existing in filtered_regions:
                if region.overlaps_with(existing, threshold=0.3):
                    should_add = False
                    break
            
            if should_add:
                filtered_regions.append(region)
        
        return filtered_regions
    
    def _classify_regions(self, regions: List[Region], gray_image: np.ndarray) -> List[Region]:
        """
        Classify regions as questions, answer options, or general text
        """
        for region in regions:
            # Extract region image for analysis
            roi = gray_image[region.y:region.y + region.height, 
                           region.x:region.x + region.width]
            
            # Simple classification based on region properties
            aspect_ratio = region.width / region.height if region.height > 0 else 0
            
            if aspect_ratio > 5:  # Very wide regions likely text
                region.region_type = 'text'
                region.confidence = 0.8
            elif region.area > 5000:  # Large regions likely questions
                region.region_type = 'question'
                region.confidence = 0.7
            elif 1 < aspect_ratio < 4:  # Medium regions likely answer options
                region.region_type = 'answer_options'
                region.confidence = 0.6
            else:
                region.region_type = 'unknown'
                region.confidence = 0.4
        
        return regions
```

### 3. Advanced Layout Analysis (layout_analysis.py)

**File Path:** `/home/gss/Desktop/dts/test_platform/pdf_extractor/layout_analysis.py`

```python
import cv2
import numpy as np
from typing import List, Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class AdvancedLayoutAnalyzer:
    """
    Advanced layout analysis for complex PDF documents
    """
    
    def __init__(self):
        self.column_gap_threshold = 50
        self.line_height_threshold = 5
        
    def analyze_page_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Perform comprehensive layout analysis on a page image
        
        Args:
            image: OpenCV image array
            
        Returns:
            Dictionary containing layout analysis results
        """
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            layout_info = {
                'page_width': image.shape[1],
                'page_height': image.shape[0],
                'detected_columns': 1,
                'text_regions': [],
                'reading_order': [],
                'layout_type': 'single_column'
            }
            
            # Detect text regions
            text_regions = self._detect_text_regions(gray)
            layout_info['text_regions'] = text_regions
            
            # Detect column structure
            columns = self._detect_columns(text_regions, image.shape[1])
            layout_info['detected_columns'] = len(columns)
            layout_info['columns'] = columns
            
            # Determine reading order
            reading_order = self._determine_reading_order(text_regions, columns)
            layout_info['reading_order'] = reading_order
            
            # Classify layout type
            layout_type = self._classify_layout_type(layout_info)
            layout_info['layout_type'] = layout_type
            
            return layout_info
            
        except Exception as e:
            logger.error(f"Error in layout analysis: {str(e)}")
            return {'error': str(e)}
    
    def _detect_text_regions(self, gray_image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect text regions using advanced image processing
        """
        text_regions = []
        
        try:
            # Apply MSER (Maximally Stable Extremal Regions) for text detection
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray_image)
            
            for region in regions:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(region.reshape(-1, 1, 2))
                
                # Filter by size and aspect ratio
                area = w * h
                aspect_ratio = w / h if h > 0 else 0
                
                if (area >= 100 and 
                    10 <= h <= 100 and 
                    0.1 <= aspect_ratio <= 20):
                    
                    text_regions.append({
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h),
                        'area': int(area),
                        'aspect_ratio': float(aspect_ratio)
                    })
            
            # Sort by vertical position (top to bottom)
            text_regions.sort(key=lambda r: r['y'])
            
        except Exception as e:
            logger.error(f"Error detecting text regions: {str(e)}")
        
        return text_regions
    
    def _detect_columns(self, text_regions: List[Dict], page_width: int) -> List[Dict[str, Any]]:
        """
        Detect column structure from text regions
        """
        if not text_regions:
            return [{'x': 0, 'width': page_width, 'regions': []}]
        
        # Group regions by horizontal position
        x_positions = [region['x'] for region in text_regions]
        x_positions.sort()
        
        # Find column boundaries
        columns = []
        current_column_start = 0
        
        for i in range(len(x_positions) - 1):
            gap = x_positions[i + 1] - x_positions[i]
            if gap > self.column_gap_threshold:
                # Found column boundary
                column_end = x_positions[i] + max(
                    r['width'] for r in text_regions 
                    if r['x'] <= x_positions[i]
                )
                
                columns.append({
                    'x': current_column_start,
                    'width': column_end - current_column_start,
                    'regions': [
                        r for r in text_regions 
                        if current_column_start <= r['x'] < column_end
                    ]
                })
                
                current_column_start = x_positions[i + 1]
        
        # Add final column
        columns.append({
            'x': current_column_start,
            'width': page_width - current_column_start,
            'regions': [
                r for r in text_regions 
                if r['x'] >= current_column_start
            ]
        })
        
        # Remove empty columns
        columns = [col for col in columns if col['regions']]
        
        return columns if columns else [{'x': 0, 'width': page_width, 'regions': text_regions}]
    
    def _determine_reading_order(self, text_regions: List[Dict], columns: List[Dict]) -> List[int]:
        """
        Determine the logical reading order of text regions
        """
        reading_order = []
        
        if len(columns) == 1:
            # Single column - simple top-to-bottom order
            sorted_regions = sorted(text_regions, key=lambda r: r['y'])
            reading_order = list(range(len(sorted_regions)))
        else:
            # Multi-column - column by column, top to bottom within each
            for column in columns:
                column_regions = sorted(column['regions'], key=lambda r: r['y'])
                for region in column_regions:
                    # Find index in original text_regions list
                    idx = text_regions.index(region)
                    reading_order.append(idx)
        
        return reading_order
    
    def _classify_layout_type(self, layout_info: Dict[str, Any]) -> str:
        """
        Classify the overall layout type of the page
        """
        num_columns = layout_info['detected_columns']
        num_regions = len(layout_info['text_regions'])
        
        if num_columns == 1:
            return 'single_column'
        elif num_columns == 2:
            return 'two_column'
        elif num_columns > 2:
            return 'multi_column'
        elif num_regions < 5:
            return 'sparse'
        else:
            return 'mixed'
```

---

## Frontend JavaScript Code

### Interactive PDF Reviewer (interactive_review.html)

**File Path:** `/home/gss/Desktop/dts/test_platform/templates/pdf_extractor/interactive_review.html`

```javascript
class InteractivePDFReviewer {
    constructor() {
        this.documentId = document.getElementById('documentId').value;
        this.currentPage = parseInt(document.getElementById('currentPage').value) || 1;
        this.totalPages = parseInt(document.getElementById('totalPages').value) || 1;
        this.regions = [];
        this.selectedRegions = [];
        this.extractedQuestions = [];
        this.isManualSelecting = false;
        this.selectionStart = null;
        this.currentSelection = null;
        
        this.initializeEventListeners();
    }
    
    // Auto-detection method
    async autoDetectRegions() {
        console.log('Starting auto-detection for page:', this.currentPage);
        this.showLoading('Detecting regions...');
        
        try {
            const url = `/pdf-extractor/api/auto-detect-regions/${this.documentId}/`;
            console.log('Making request to:', url);
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    page_number: this.currentPage
                })
            });
            
            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.success) {
                this.regions = data.regions;
                console.log('Regions detected:', this.regions.length);
                this.renderRegions();
                this.updateRegionsList();
                this.updateProcessButton();
            } else {
                console.error('Auto detection failed:', data.error);
                alert('Auto detection failed: ' + data.error);
            }
        } catch (error) {
            console.error('Error during auto detection:', error);
            alert('Error during auto detection: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    // Region rendering
    renderRegions() {
        const overlaysContainer = document.getElementById('regionOverlays');
        overlaysContainer.innerHTML = '';
        
        console.log('Rendering regions:', this.regions.length);
        
        this.regions.forEach((region, index) => {
            console.log('Rendering region', index, ':', region);
            
            const overlay = document.createElement('div');
            overlay.className = `region-overlay ${region.region_type}`;
            overlay.style.left = `${region.coordinates.x}px`;
            overlay.style.top = `${region.coordinates.y}px`;
            overlay.style.width = `${region.coordinates.width}px`;
            overlay.style.height = `${region.coordinates.height}px`;
            overlay.dataset.regionIndex = index;
            
            // Add region label
            const label = document.createElement('div');
            label.className = 'region-label';
            label.textContent = `${region.region_type} (${Math.round(region.confidence * 100)}%)`;
            overlay.appendChild(label);
            
            // Add click handler for selection
            overlay.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleRegionSelection(index);
            });
            
            overlaysContainer.appendChild(overlay);
        });
    }
    
    // Region selection toggle
    toggleRegionSelection(regionIndex) {
        const selectedIndex = this.selectedRegions.indexOf(regionIndex);
        const overlay = document.querySelector(`[data-region-index="${regionIndex}"]`);
        
        if (selectedIndex === -1) {
            // Select region
            this.selectedRegions.push(regionIndex);
            overlay.classList.add('selected');
        } else {
            // Deselect region
            this.selectedRegions.splice(selectedIndex, 1);
            overlay.classList.remove('selected');
        }
        
        this.updateRegionsList();
        this.updateProcessButton();
    }
    
    // Update regions list in UI
    updateRegionsList() {
        const regionsList = document.getElementById('regionsList');
        
        if (this.regions.length === 0) {
            regionsList.innerHTML = '<p class="text-gray-500 text-sm">No regions detected</p>';
            return;
        }
        
        regionsList.innerHTML = this.regions.map((region, index) => `
            <div class="region-info ${region.region_type} ${this.selectedRegions.includes(index) ? 'selected' : ''}" 
                 data-region-index="${index}">
                <div class="flex justify-between items-center mb-1">
                    <span class="font-medium">Region ${index + 1}</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs bg-gray-200 px-2 py-1 rounded">${region.region_type}</span>
                        <span class="text-xs text-gray-600">${Math.round(region.confidence * 100)}%</span>
                        <button onclick="reviewer.toggleRegionSelection(${index})" 
                                class="text-xs px-2 py-1 border rounded hover:bg-gray-50">
                            ${this.selectedRegions.includes(index) ? 'Deselect' : 'Select'}
                        </button>
                    </div>
                </div>
                <div class="text-preview">${region.text_preview || 'No preview available'}</div>
            </div>
        `).join('');
    }
    
    // Update process button state
    updateProcessButton() {
        const btn = document.getElementById('processRegionsBtn');
        btn.disabled = this.selectedRegions.length === 0;
        btn.textContent = `Process ${this.selectedRegions.length} Selected Region(s)`;
    }
    
    // Clear all regions
    clearRegions() {
        console.log('Clearing all regions');
        this.regions = [];
        this.selectedRegions = [];
        this.extractedQuestions = [];
        document.getElementById('regionOverlays').innerHTML = '';
        document.getElementById('regionsList').innerHTML = '<p class="text-gray-500 text-sm">No regions detected</p>';
        document.getElementById('processRegionsBtn').disabled = true;
        document.getElementById('processRegionsBtn').textContent = 'Process & Extract Text';
        document.getElementById('questionEditor').style.display = 'none';
    }
    
    // Debug function for regions
    debugRegions() {
        console.log('=== DEBUG INFO ===');
        console.log('Total regions:', this.regions.length);
        console.log('Regions array:', this.regions);
        console.log('Selected regions:', this.selectedRegions);
        console.log('Manual selection mode:', this.isManualSelecting);
        
        const overlaysContainer = document.getElementById('regionOverlays');
        console.log('Overlays container children:', overlaysContainer.children.length);
        
        alert(`Regions: ${this.regions.length}\nOverlays: ${overlaysContainer.children.length}\nManual mode: ${this.isManualSelecting}`);
    }
}

// Initialize when page loads
let reviewer;
document.addEventListener('DOMContentLoaded', function() {
    reviewer = new InteractivePDFReviewer();
});
```

---

## URL Patterns & API Endpoints

### URL Configuration (urls.py)

**File Path:** `/home/gss/Desktop/dts/test_platform/pdf_extractor/urls.py`

```python
from django.urls import path
from . import views

app_name = 'pdf_extractor'

urlpatterns = [
    # Interactive Review URLs - Auto Detection System
    path('interactive-review/<uuid:document_id>/', views.interactive_review, name='interactive_review'),
    path('api/auto-detect-regions/<uuid:document_id>/', views.auto_detect_regions_api, name='auto_detect_regions_api'),
    path('api/process-regions/<uuid:document_id>/', views.process_selected_regions_api, name='process_selected_regions_api'),
    path('api/save-questions/<uuid:document_id>/', views.save_extracted_questions_api, name='save_extracted_questions_api'),
    path('api/finish-review/<uuid:document_id>/', views.finish_review_api, name='finish_review_api'),
    
    # Interactive Region Review URLs
    path('review-regions/<uuid:document_id>/', views.region_review_interface, name='region_review_interface'),
    path('api/regions/<uuid:document_id>/<int:page_number>/', views.get_page_regions_api, name='get_page_regions_api'),
    path('api/save-correction/<uuid:document_id>/', views.save_region_correction, name='save_region_correction'),
    path('api/batch-approve/<uuid:document_id>/', views.batch_approve_regions, name='batch_approve_regions'),
]
```

---

## Supporting Components

### OCR Processing Integration (ocr_processors.py)

**File Path:** `/home/gss/Desktop/dts/test_platform/pdf_extractor/ocr_processors.py`

```python
import cv2
import numpy as np
import pytesseract
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class OCRManager:
    """
    Manages OCR processing for detected regions
    """
    
    def __init__(self):
        # Configure Tesseract
        self.tesseract_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789().,?!:;-+*/= '
    
    def process_regions(self, image: np.ndarray, regions: List[Dict]) -> List[Dict[str, Any]]:
        """
        Process detected regions with OCR
        
        Args:
            image: Full page image
            regions: List of region dictionaries from auto-detection
            
        Returns:
            List of processed regions with OCR text
        """
        processed_regions = []
        
        for i, region in enumerate(regions):
            try:
                # Extract region from image
                x = region['coordinates']['x']
                y = region['coordinates']['y']
                w = region['coordinates']['width']
                h = region['coordinates']['height']
                
                # Crop region from image
                roi = image[y:y+h, x:x+w]
                
                if roi.size == 0:
                    continue
                
                # Preprocess region for better OCR
                processed_roi = self._preprocess_for_ocr(roi)
                
                # Perform OCR
                ocr_text = self._extract_text_from_region(processed_roi)
                
                # Calculate confidence
                confidence = self._calculate_ocr_confidence(processed_roi, ocr_text)
                
                processed_region = {
                    'region_id': f'region_{i}',
                    'coordinates': region['coordinates'],
                    'region_type': region.get('region_type', 'unknown'),
                    'text': ocr_text,
                    'confidence': confidence,
                    'ocr_success': len(ocr_text.strip()) > 0
                }
                
                processed_regions.append(processed_region)
                
            except Exception as e:
                logger.error(f"Error processing region {i}: {str(e)}")
                processed_regions.append({
                    'region_id': f'region_{i}',
                    'coordinates': region['coordinates'],
                    'region_type': region.get('region_type', 'unknown'),
                    'text': '',
                    'confidence': 0.0,
                    'ocr_success': False,
                    'error': str(e)
                })
        
        return processed_regions
    
    def _preprocess_for_ocr(self, roi: np.ndarray) -> np.ndarray:
        """
        Preprocess region image for better OCR results
        """
        # Convert to grayscale if needed
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi.copy()
        
        # Apply denoising
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Enhance contrast
        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(denoised)
        
        # Apply threshold
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def _extract_text_from_region(self, roi: np.ndarray) -> str:
        """
        Extract text from preprocessed region using OCR
        """
        try:
            # Use Tesseract OCR
            text = pytesseract.image_to_string(roi, config=self.tesseract_config)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return ""
    
    def _calculate_ocr_confidence(self, roi: np.ndarray, text: str) -> float:
        """
        Calculate confidence score for OCR result
        """
        try:
            # Get detailed OCR data
            data = pytesseract.image_to_data(roi, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                return avg_confidence / 100.0  # Convert to 0-1 scale
            else:
                return 0.5 if len(text) > 0 else 0.0
                
        except Exception:
            return 0.5 if len(text) > 0 else 0.0
```

---

## Configuration & Settings

### Detection Parameters

```python
# Region Extraction Settings
MIN_REGION_AREA = 500          # Minimum area in pixels
MAX_REGION_AREA = 200000       # Maximum area in pixels
MIN_TEXT_HEIGHT = 10           # Minimum text line height
MAX_TEXT_HEIGHT = 50           # Maximum text line height

# Layout Analysis Settings
COLUMN_GAP_THRESHOLD = 50      # Minimum gap between columns
LINE_HEIGHT_THRESHOLD = 5      # Minimum line height variation

# OCR Settings
TESSERACT_CONFIG = '--oem 3 --psm 6'  # Tesseract configuration
OCR_LANGUAGES = 'eng'          # OCR languages

# Detection Methods
DETECTION_METHODS = [
    'morphological',    # Morphological operations
    'contour',         # Edge detection and contours
    'block',           # Block-based detection
    'mser',            # MSER text detection
]

# Classification Thresholds
QUESTION_AREA_THRESHOLD = 5000      # Minimum area for question regions
ANSWER_ASPECT_RATIO_MIN = 1         # Min aspect ratio for answer options
ANSWER_ASPECT_RATIO_MAX = 4         # Max aspect ratio for answer options
TEXT_ASPECT_RATIO_THRESHOLD = 5     # Threshold for text classification

# Confidence Scoring
HIGH_CONFIDENCE_THRESHOLD = 0.8     # High confidence score threshold
MEDIUM_CONFIDENCE_THRESHOLD = 0.6   # Medium confidence score threshold
```

---

## Data Flow Summary

1. **User Interface**: User clicks "Auto Detect Regions" button
2. **JavaScript Call**: `autoDetectRegions()` method triggered
3. **API Request**: POST to `/api/auto-detect-regions/<document_id>/`
4. **Backend Processing**:
   - PDF page converted to image
   - `RegionExtractor.extract_regions_from_image()` called
   - Multiple detection methods applied (morphological, contour, block)
   - Regions filtered, merged, and classified
5. **Response**: JSON with detected regions and metadata
6. **Frontend Rendering**: Regions displayed as visual overlays
7. **User Interaction**: User can select/deselect regions
8. **OCR Processing**: Selected regions processed with OCR
9. **Question Extraction**: Text analyzed for question patterns
10. **Review Interface**: Questions displayed for user review and editing

This comprehensive auto-detection system combines computer vision techniques with OCR processing to automatically identify and extract question-answer regions from PDF documents.