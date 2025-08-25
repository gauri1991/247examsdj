import cv2
import numpy as np
from PIL import Image
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextRegion:
    """Represents a detected text region"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    region_type: str  # 'paragraph', 'heading', 'list', 'table'
    text_density: float


@dataclass
class ColumnInfo:
    """Information about detected columns"""
    x_start: int
    x_end: int
    y_start: int
    y_end: int
    confidence: float


class AdvancedLayoutAnalyzer:
    """
    Advanced layout analysis using OpenCV computer vision techniques
    """
    
    def __init__(self):
        self.min_text_region_area = 100
        self.column_gap_threshold = 50
        self.line_height_threshold = 10
        
    def analyze_page_layout(self, image: Image.Image, page_number: int) -> Dict[str, Any]:
        """
        Perform comprehensive layout analysis on a page image
        """
        layout_info = {
            'page_number': page_number,
            'page_width': image.width,
            'page_height': image.height,
            'columns': [],
            'text_regions': [],
            'reading_order': [],
            'layout_type': 'unknown',
            'confidence': 0.0,
            'analysis_method': 'opencv'
        }
        
        try:
            # Convert PIL Image to OpenCV format
            cv_image = self._pil_to_cv2(image)
            
            # Detect text regions
            text_regions = self._detect_text_regions(cv_image)
            layout_info['text_regions'] = text_regions
            
            # Analyze column structure
            columns = self._detect_columns(text_regions, image.width, image.height)
            layout_info['columns'] = columns
            
            # Determine layout type
            layout_info['layout_type'] = self._classify_layout_type(columns, text_regions)
            
            # Calculate reading order
            layout_info['reading_order'] = self._determine_reading_order(text_regions, columns)
            
            # Calculate overall confidence
            layout_info['confidence'] = self._calculate_layout_confidence(
                text_regions, columns, layout_info['layout_type']
            )
            
        except Exception as e:
            logger.error(f"Layout analysis failed for page {page_number}: {e}")
            layout_info['error'] = str(e)
            layout_info['confidence'] = 0.0
        
        return layout_info
    
    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format"""
        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert to numpy array and change color order from RGB to BGR
        cv_image = np.array(pil_image)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
        
        return cv_image
    
    def _detect_text_regions(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect text regions using morphological operations and contour detection
        """
        text_regions = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Create morphological kernel for text detection
            # Horizontal kernel to connect letters in words
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Vertical kernel to connect lines in paragraphs
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combine horizontal and vertical
            combined = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Dilate to merge nearby text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            dilated = cv2.dilate(combined, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Process each contour
            for i, contour in enumerate(contours):
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter small regions
                if w * h < self.min_text_region_area:
                    continue
                
                # Calculate text density (rough estimate)
                roi = binary[y:y+h, x:x+w]
                text_density = np.sum(roi > 0) / (w * h) if w * h > 0 else 0
                
                # Classify region type based on dimensions and density
                region_type = self._classify_text_region(w, h, text_density)
                
                # Calculate confidence based on region characteristics
                confidence = self._calculate_region_confidence(w, h, text_density, contour)
                
                text_regions.append({
                    'id': i,
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'confidence': float(confidence),
                    'region_type': region_type,
                    'text_density': float(text_density),
                    'area': int(w * h)
                })
            
            # Sort regions by position (top to bottom, left to right)
            text_regions.sort(key=lambda r: (r['y'], r['x']))
            
        except Exception as e:
            logger.error(f"Text region detection failed: {e}")
        
        return text_regions
    
    def _classify_text_region(self, width: int, height: int, text_density: float) -> str:
        """Classify the type of text region based on its characteristics"""
        aspect_ratio = width / height if height > 0 else 0
        
        # Heading: Wide, short, high density
        if aspect_ratio > 3 and height < 50 and text_density > 0.3:
            return 'heading'
        
        # List item: Medium width, short height
        elif aspect_ratio > 2 and height < 30:
            return 'list_item'
        
        # Table cell: Square-ish, medium density
        elif 0.5 < aspect_ratio < 2 and text_density > 0.2:
            return 'table_cell'
        
        # Paragraph: Varies, but typically rectangular
        else:
            return 'paragraph'
    
    def _calculate_region_confidence(self, width: int, height: int, text_density: float, contour) -> float:
        """Calculate confidence score for a text region"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for reasonable dimensions
        if 50 < width < 800 and 20 < height < 400:
            confidence += 0.2
        
        # Boost confidence for good text density
        if 0.1 < text_density < 0.8:
            confidence += 0.2
        
        # Boost confidence for rectangular shape
        rect_area = width * height
        contour_area = cv2.contourArea(contour)
        if contour_area > 0:
            rectangularity = rect_area / contour_area
            if 0.7 < rectangularity < 1.3:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _detect_columns(self, text_regions: List[Dict], page_width: int, page_height: int) -> List[Dict[str, Any]]:
        """
        Detect column structure from text regions
        """
        if not text_regions:
            return []
        
        columns = []
        
        try:
            # Group regions by horizontal position
            x_positions = [region['x'] for region in text_regions]
            x_centers = [region['x'] + region['width'] // 2 for region in text_regions]
            
            # Use K-means-like clustering to find column centers
            column_centers = self._find_column_centers(x_centers, page_width)
            
            # Create column boundaries
            for i, center in enumerate(column_centers):
                # Determine column boundaries
                if i == 0:
                    x_start = 0
                else:
                    x_start = (column_centers[i-1] + center) // 2
                
                if i == len(column_centers) - 1:
                    x_end = page_width
                else:
                    x_end = (center + column_centers[i+1]) // 2
                
                # Find regions in this column
                column_regions = [
                    r for r in text_regions 
                    if x_start <= r['x'] + r['width'] // 2 < x_end
                ]
                
                if column_regions:
                    y_positions = [r['y'] for r in column_regions]
                    y_start = min(y_positions)
                    y_end = max(r['y'] + r['height'] for r in column_regions)
                    
                    # Calculate column confidence
                    confidence = self._calculate_column_confidence(column_regions, x_start, x_end)
                    
                    columns.append({
                        'column_id': i,
                        'x_start': x_start,
                        'x_end': x_end,
                        'y_start': y_start,
                        'y_end': y_end,
                        'confidence': confidence,
                        'region_count': len(column_regions),
                        'width': x_end - x_start
                    })
        
        except Exception as e:
            logger.error(f"Column detection failed: {e}")
        
        return columns
    
    def _find_column_centers(self, x_centers: List[int], page_width: int) -> List[int]:
        """Find column centers using simple clustering"""
        if not x_centers:
            return []
        
        # Sort x centers
        sorted_centers = sorted(x_centers)
        
        # Find gaps that might indicate column separations
        gaps = []
        for i in range(len(sorted_centers) - 1):
            gap = sorted_centers[i + 1] - sorted_centers[i]
            if gap > self.column_gap_threshold:
                gaps.append((sorted_centers[i], sorted_centers[i + 1], gap))
        
        # If no significant gaps, assume single column
        if not gaps:
            return [page_width // 2]
        
        # Create column centers based on gaps
        column_centers = []
        
        # First column center
        if gaps:
            first_gap_start = gaps[0][0]
            first_column_regions = [x for x in sorted_centers if x <= first_gap_start]
            if first_column_regions:
                column_centers.append(sum(first_column_regions) // len(first_column_regions))
        
        # Middle columns
        for i, (gap_start, gap_end, _) in enumerate(gaps):
            if i < len(gaps) - 1:
                next_gap_start = gaps[i + 1][0]
                column_regions = [x for x in sorted_centers if gap_end <= x <= next_gap_start]
            else:
                column_regions = [x for x in sorted_centers if x >= gap_end]
            
            if column_regions:
                column_centers.append(sum(column_regions) // len(column_regions))
        
        return column_centers
    
    def _calculate_column_confidence(self, regions: List[Dict], x_start: int, x_end: int) -> float:
        """Calculate confidence for a detected column"""
        if not regions:
            return 0.0
        
        confidence = 0.5
        
        # Boost confidence for consistent alignment
        left_edges = [r['x'] for r in regions]
        if left_edges:
            alignment_variance = np.var(left_edges)
            if alignment_variance < 100:  # Well-aligned
                confidence += 0.2
        
        # Boost confidence for reasonable region count
        if 2 <= len(regions) <= 20:
            confidence += 0.2
        
        # Boost confidence for reasonable column width
        column_width = x_end - x_start
        if 100 < column_width < 500:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _classify_layout_type(self, columns: List[Dict], text_regions: List[Dict]) -> str:
        """Classify the overall layout type"""
        if not columns:
            return 'unknown'
        
        num_columns = len(columns)
        
        if num_columns == 1:
            # Check if it's actually a single column or just poorly detected
            if len(text_regions) > 5:
                # Analyze text region distribution
                x_positions = [r['x'] for r in text_regions]
                x_variance = np.var(x_positions) if x_positions else 0
                
                if x_variance > 10000:  # High variance might indicate multiple columns
                    return 'multi_column_detected_as_single'
                else:
                    return 'single_column'
            return 'single_column'
        
        elif num_columns == 2:
            return 'two_column'
        
        elif num_columns >= 3:
            return 'multi_column'
        
        return 'unknown'
    
    def _determine_reading_order(self, text_regions: List[Dict], columns: List[Dict]) -> List[int]:
        """Determine the reading order of text regions"""
        if not text_regions:
            return []
        
        reading_order = []
        
        try:
            if len(columns) <= 1:
                # Single column: top to bottom
                sorted_regions = sorted(text_regions, key=lambda r: r['y'])
                reading_order = [r['id'] for r in sorted_regions]
            
            else:
                # Multiple columns: column by column, top to bottom within each
                for column in sorted(columns, key=lambda c: c['x_start']):
                    # Find regions in this column
                    column_regions = []
                    for region in text_regions:
                        region_center_x = region['x'] + region['width'] // 2
                        if column['x_start'] <= region_center_x < column['x_end']:
                            column_regions.append(region)
                    
                    # Sort by y position within column
                    column_regions.sort(key=lambda r: r['y'])
                    reading_order.extend([r['id'] for r in column_regions])
        
        except Exception as e:
            logger.error(f"Reading order determination failed: {e}")
            # Fallback: simple top-to-bottom, left-to-right
            sorted_regions = sorted(text_regions, key=lambda r: (r['y'], r['x']))
            reading_order = [r['id'] for r in sorted_regions]
        
        return reading_order
    
    def _calculate_layout_confidence(self, text_regions: List[Dict], columns: List[Dict], layout_type: str) -> float:
        """Calculate overall confidence in the layout analysis"""
        if not text_regions:
            return 0.0
        
        confidence = 0.3  # Base confidence
        
        # Boost for successful region detection
        if len(text_regions) > 1:
            confidence += 0.2
        
        # Boost for successful column detection
        if columns:
            avg_column_confidence = sum(c['confidence'] for c in columns) / len(columns)
            confidence += 0.3 * avg_column_confidence
        
        # Boost for recognized layout type
        if layout_type != 'unknown':
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def enhance_layout_with_text_data(self, layout_info: Dict[str, Any], text_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance layout analysis using actual extracted text data
        """
        try:
            if 'words' in text_data:
                words = text_data['words']
                
                # Map words to text regions
                for region in layout_info.get('text_regions', []):
                    region_words = []
                    for word in words:
                        # Check if word is within region bounds
                        if (region['x'] <= word['x0'] <= region['x'] + region['width'] and
                            region['y'] <= word['y0'] <= region['y'] + region['height']):
                            region_words.append(word)
                    
                    region['word_count'] = len(region_words)
                    region['text_content'] = ' '.join([w['text'] for w in region_words])
                    
                    # Refine region type based on text content
                    if region_words:
                        region['refined_type'] = self._refine_region_type(
                            region['text_content'], region['region_type']
                        )
            
            # Update confidence based on text enhancement
            if layout_info.get('text_regions'):
                enhanced_regions = [r for r in layout_info['text_regions'] if r.get('word_count', 0) > 0]
                if enhanced_regions:
                    layout_info['confidence'] = min(layout_info['confidence'] + 0.1, 1.0)
        
        except Exception as e:
            logger.error(f"Layout enhancement failed: {e}")
        
        return layout_info
    
    def _refine_region_type(self, text_content: str, original_type: str) -> str:
        """Refine region type based on actual text content"""
        if not text_content:
            return original_type
        
        text_lower = text_content.lower().strip()
        
        # Check for question patterns
        question_indicators = ['?', 'what', 'how', 'why', 'when', 'where', 'which', 'who']
        if any(indicator in text_lower for indicator in question_indicators):
            return 'question'
        
        # Check for answer patterns
        answer_indicators = ['a)', 'b)', 'c)', 'd)', 'answer:', 'solution:']
        if any(indicator in text_lower for indicator in answer_indicators):
            return 'answer_options'
        
        # Check for numbered lists
        if text_lower.startswith(('1.', '2.', '3.', '4.', '5.')):
            return 'numbered_list'
        
        # Check for headings (short, capitalized)
        if len(text_content) < 100 and text_content.isupper():
            return 'heading'
        
        return original_type


class MultiColumnTextProcessor:
    """
    Processes text from multi-column layouts while preserving reading order
    """
    
    def __init__(self):
        self.layout_analyzer = AdvancedLayoutAnalyzer()
    
    def process_multi_column_text(self, extracted_text: Dict[str, Any], layout_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extracted text considering multi-column layout
        """
        processed_result = {
            'success': False,
            'reading_order_text': '',
            'column_texts': [],
            'structured_content': [],
            'confidence': 0.0
        }
        
        try:
            columns = layout_info.get('columns', [])
            text_regions = layout_info.get('text_regions', [])
            reading_order = layout_info.get('reading_order', [])
            
            if not columns or len(columns) == 1:
                # Single column processing
                processed_result['reading_order_text'] = extracted_text.get('text', '')
                processed_result['column_texts'] = [extracted_text.get('text', '')]
                processed_result['success'] = True
                processed_result['confidence'] = 0.8
            
            else:
                # Multi-column processing
                column_texts = []
                structured_content = []
                
                # Process each column
                for column in sorted(columns, key=lambda c: c['x_start']):
                    column_text_parts = []
                    column_regions = []
                    
                    # Find text regions in this column
                    for region in text_regions:
                        region_center_x = region['x'] + region['width'] // 2
                        if column['x_start'] <= region_center_x < column['x_end']:
                            column_regions.append(region)
                    
                    # Sort regions by reading order within column
                    column_regions.sort(key=lambda r: r['y'])
                    
                    # Extract text for each region in the column
                    for region in column_regions:
                        region_text = self._extract_region_text(region, extracted_text)
                        if region_text.strip():
                            column_text_parts.append(region_text)
                            structured_content.append({
                                'column_id': column['column_id'],
                                'region_id': region['id'],
                                'region_type': region.get('refined_type', region['region_type']),
                                'text': region_text,
                                'position': {
                                    'x': region['x'],
                                    'y': region['y'],
                                    'width': region['width'],
                                    'height': region['height']
                                }
                            })
                    
                    column_text = '\n\n'.join(column_text_parts)
                    column_texts.append(column_text)
                
                # Create reading order text by following column order
                processed_result['reading_order_text'] = '\n\n--- Column Break ---\n\n'.join(column_texts)
                processed_result['column_texts'] = column_texts
                processed_result['structured_content'] = structured_content
                processed_result['success'] = True
                processed_result['confidence'] = layout_info.get('confidence', 0.5)
        
        except Exception as e:
            logger.error(f"Multi-column text processing failed: {e}")
            processed_result['error'] = str(e)
        
        return processed_result
    
    def _extract_region_text(self, region: Dict[str, Any], extracted_text: Dict[str, Any]) -> str:
        """Extract text content for a specific region"""
        # If we have enhanced region with text content, use it
        if 'text_content' in region:
            return region['text_content']
        
        # Otherwise, try to extract from words based on position
        words = extracted_text.get('words', [])
        region_words = []
        
        for word in words:
            # Check if word is within region bounds (with some tolerance)
            tolerance = 5
            if (region['x'] - tolerance <= word['x0'] <= region['x'] + region['width'] + tolerance and
                region['y'] - tolerance <= word['y0'] <= region['y'] + region['height'] + tolerance):
                region_words.append(word)
        
        # Sort words by position (top to bottom, left to right)
        region_words.sort(key=lambda w: (w['y0'], w['x0']))
        
        return ' '.join([w['text'] for w in region_words])