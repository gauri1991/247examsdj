"""
Region Extraction and Cropping Module
Handles detection, extraction, and cropping of question-answer regions

Enhanced with intelligent question-answer pattern detection:
- Detects numbered questions (e.g., "114.", "Q.1")
- Identifies multiple choice options (e.g., "(a)", "(b)", "(c)", "(d)")
- Groups questions with their corresponding options
- Supports multi-column layouts
- Falls back to original detection methods if smart detection fails
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
import json
import re

logger = logging.getLogger('pdf_extractor.region_extractor')


@dataclass
class Region:
    """Represents a detected region in a document"""
    x: int
    y: int
    width: int
    height: int
    page_number: int
    region_type: str  # 'question', 'answer_options', 'answer_block', 'image', 'table'
    confidence: float
    text: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def x2(self) -> int:
        return self.x + self.width
    
    @property
    def y2(self) -> int:
        return self.y + self.height
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def overlaps_with(self, other: 'Region', threshold: float = 0.1) -> bool:
        """Check if this region overlaps with another region"""
        # Calculate intersection
        x_overlap = max(0, min(self.x2, other.x2) - max(self.x, other.x))
        y_overlap = max(0, min(self.y2, other.y2) - max(self.y, other.y))
        
        if x_overlap == 0 or y_overlap == 0:
            return False
        
        intersection_area = x_overlap * y_overlap
        union_area = self.area + other.area - intersection_area
        
        return (intersection_area / union_area) > threshold
    
    def distance_to(self, other: 'Region') -> float:
        """Calculate distance between region centers"""
        x1, y1 = self.center
        x2, y2 = other.center
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert region to dictionary for JSON serialization"""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'page_number': self.page_number,
            'region_type': self.region_type,
            'confidence': self.confidence,
            'text': self.text,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Region':
        """Create region from dictionary"""
        return cls(**data)


class RegionExtractor:
    """
    Extracts and processes regions from document images
    """
    
    def __init__(self):
        self.min_region_area = 500  # Minimum area for a valid region
        self.max_region_area = 200000  # Maximum area to prevent whole-page regions
        self.text_line_height_range = (10, 50)  # Expected text line height range
        self.margin_threshold = 20  # Minimum margin between regions
        
        # OCR and text detection parameters
        self.contour_approximation = cv2.CHAIN_APPROX_SIMPLE
        self.morphology_kernel_size = (3, 3)
        
        # Enhanced detection parameters for question-answer patterns
        self.question_number_patterns = [
            r'^\s*(\d+)\.\s+',  # "114. " format from dsr1.txt
            r'^\s*Q\.?\s*(\d+)[:\.]?\s*',  # Alternative Q formats
            r'^\s*(\d+)\)\s*',  # "114) " format
        ]
        self.option_pattern = r'^\s*\(([a-d])\)\s*(.+)'  # "(a) text" format
        self.column_gap_threshold = 80  # Minimum gap to detect columns
        self.enable_smart_detection = True  # Enable enhanced question detection
        
    def extract_regions_from_image(
        self, 
        image: Union[Image.Image, np.ndarray], 
        page_number: int = 1
    ) -> List[Region]:
        """
        Extract text regions from a document image
        
        Args:
            image: PIL Image or numpy array
            page_number: Page number for reference
            
        Returns:
            List of detected regions
        """
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image.copy()
            
        # Convert to grayscale if needed
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
            
        regions = []
        
        try:
            # Try enhanced smart detection first if enabled
            if self.enable_smart_detection:
                smart_regions = self._detect_question_answer_groups(gray, page_number)
                if smart_regions:
                    logger.info(f"Smart detection found {len(smart_regions)} question groups")
                    regions.extend(smart_regions)
                    return regions
            
            # Fallback to original detection methods
            text_regions = self._detect_text_regions(gray)
            block_regions = self._detect_block_regions(gray)
            contour_regions = self._detect_contour_regions(gray)
            
            # Combine and filter regions
            all_regions = text_regions + block_regions + contour_regions
            filtered_regions = self._filter_and_merge_regions(all_regions, gray.shape)
            
            # Convert to Region objects
            for i, region_data in enumerate(filtered_regions):
                region = Region(
                    x=region_data['x'],
                    y=region_data['y'],
                    width=region_data['width'],
                    height=region_data['height'],
                    page_number=page_number,
                    region_type=region_data.get('type', 'text_block'),
                    confidence=region_data.get('confidence', 0.5),
                    metadata={
                        'detection_method': region_data.get('method', 'unknown'),
                        'area': region_data['width'] * region_data['height'],
                        'aspect_ratio': region_data['width'] / region_data['height'],
                        'region_id': f"region_{page_number}_{i}"
                    }
                )
                regions.append(region)
                
        except Exception as e:
            logger.error(f"Error extracting regions from image: {str(e)}")
            
        return regions
    
    def _detect_text_regions(self, gray_image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect text regions using morphological operations
        """
        regions = []
        
        try:
            # Apply morphological operations to connect text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
            morph = cv2.morphologyEx(gray_image, cv2.MORPH_CLOSE, kernel)
            
            # Threshold the image
            _, thresh = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Filter based on size and aspect ratio
                if (self.min_region_area <= area <= self.max_region_area and
                    self.text_line_height_range[0] <= h <= self.text_line_height_range[1] * 10):
                    
                    regions.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'type': 'text_line',
                        'confidence': 0.7,
                        'method': 'morphological',
                        'area': area
                    })
                    
        except Exception as e:
            logger.error(f"Error in text region detection: {str(e)}")
            
        return regions
    
    def _detect_block_regions(self, gray_image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect larger text blocks and paragraphs
        """
        regions = []
        
        try:
            # Use larger kernel for block detection
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 5))
            morph = cv2.morphologyEx(gray_image, cv2.MORPH_CLOSE, kernel)
            
            # Apply Gaussian blur to connect nearby text
            blurred = cv2.GaussianBlur(morph, (5, 5), 0)
            
            # Threshold
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Look for larger regions that could be question blocks
                if (area >= self.min_region_area * 3 and 
                    area <= self.max_region_area and
                    h >= 30):  # Minimum height for a question block
                    
                    regions.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'type': 'text_block',
                        'confidence': 0.8,
                        'method': 'block_detection',
                        'area': area
                    })
                    
        except Exception as e:
            logger.error(f"Error in block region detection: {str(e)}")
            
        return regions
    
    def _detect_contour_regions(self, gray_image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect regions using edge detection and contours
        """
        regions = []
        
        try:
            # Edge detection
            edges = cv2.Canny(gray_image, 50, 150)
            
            # Dilate edges to close gaps
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Approximate contour to reduce complexity
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                x, y, w, h = cv2.boundingRect(approx)
                area = w * h
                
                if (self.min_region_area <= area <= self.max_region_area and
                    w > 50 and h > 20):  # Minimum dimensions
                    
                    regions.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'type': 'contour_region',
                        'confidence': 0.6,
                        'method': 'contour_detection',
                        'area': area
                    })
                    
        except Exception as e:
            logger.error(f"Error in contour region detection: {str(e)}")
            
        return regions
    
    def _filter_and_merge_regions(
        self, 
        regions: List[Dict[str, Any]], 
        image_shape: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """
        Filter overlapping regions and merge nearby ones
        """
        if not regions:
            return []
            
        # Sort by area (largest first)
        regions.sort(key=lambda r: r['area'], reverse=True)
        
        filtered_regions = []
        
        for region in regions:
            # Check if this region overlaps significantly with existing ones
            should_add = True
            
            for existing in filtered_regions:
                if self._regions_overlap(region, existing, threshold=0.5):
                    should_add = False
                    break
            
            if should_add:
                filtered_regions.append(region)
        
        # Merge nearby regions that could be part of the same question
        merged_regions = self._merge_nearby_regions(filtered_regions)
        
        return merged_regions
    
    def _regions_overlap(
        self, 
        region1: Dict[str, Any], 
        region2: Dict[str, Any], 
        threshold: float = 0.3
    ) -> bool:
        """Check if two regions overlap significantly"""
        x1, y1, w1, h1 = region1['x'], region1['y'], region1['width'], region1['height']
        x2, y2, w2, h2 = region2['x'], region2['y'], region2['width'], region2['height']
        
        # Calculate intersection
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        
        if x_overlap == 0 or y_overlap == 0:
            return False
        
        intersection_area = x_overlap * y_overlap
        smaller_area = min(w1 * h1, w2 * h2)
        
        return (intersection_area / smaller_area) > threshold
    
    def _merge_nearby_regions(self, regions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge regions that are close to each other and could be part of same question
        """
        if len(regions) <= 1:
            return regions
            
        merged = []
        used_indices = set()
        
        for i, region in enumerate(regions):
            if i in used_indices:
                continue
                
            # Find nearby regions to merge
            nearby_regions = [region]
            merge_indices = [i]
            
            for j, other_region in enumerate(regions[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                # Check if regions are vertically close (could be same question)
                if self._are_regions_vertically_close(region, other_region):
                    nearby_regions.append(other_region)
                    merge_indices.append(j)
            
            # Merge if we found nearby regions
            if len(nearby_regions) > 1:
                merged_region = self._merge_region_group(nearby_regions)
                merged.append(merged_region)
                used_indices.update(merge_indices)
            else:
                merged.append(region)
                used_indices.add(i)
        
        return merged
    
    def _detect_question_answer_groups(self, gray_image: np.ndarray, page_number: int) -> List[Region]:
        """
        Enhanced detection method for question-answer groups using OCR and pattern matching
        """
        try:
            import pytesseract
        except ImportError:
            logger.warning("pytesseract not available, falling back to basic detection")
            return []
        
        try:
            # Get text data from OCR with bounding boxes
            ocr_data = pytesseract.image_to_data(gray_image, output_type=pytesseract.Output.DICT, config='--psm 6')
            
            # Extract text lines with coordinates
            text_lines = self._extract_text_lines_from_ocr(ocr_data)
            
            if not text_lines:
                logger.info("No text lines detected by OCR")
                return []
            
            # Detect column structure
            columns = self._detect_columns_from_text_lines(text_lines, gray_image.shape[1])
            logger.info(f"Detected {len(columns)} columns")
            
            # Process each column separately for better accuracy
            all_question_groups = []
            for column in columns:
                column_groups = self._process_column_for_questions(column['lines'], page_number)
                all_question_groups.extend(column_groups)
            
            logger.info(f"Smart detection found {len(all_question_groups)} question groups")
            return all_question_groups
            
        except Exception as e:
            logger.error(f"Error in smart question detection: {str(e)}")
            return []
    
    def _extract_text_lines_from_ocr(self, ocr_data: Dict) -> List[Dict[str, Any]]:
        """
        Extract meaningful text lines from OCR data with coordinates
        """
        text_lines = []
        
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            confidence = int(ocr_data['conf'][i])
            
            # Filter out low confidence and empty text
            if confidence > 30 and len(text) > 1:
                text_lines.append({
                    'text': text,
                    'x': ocr_data['left'][i],
                    'y': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i],
                    'confidence': confidence
                })
        
        # Sort by vertical position (top to bottom)
        text_lines.sort(key=lambda x: x['y'])
        return text_lines
    
    def _detect_columns_from_text_lines(self, text_lines: List[Dict], page_width: int) -> List[Dict[str, Any]]:
        """
        Detect column structure from text line positions
        """
        if not text_lines:
            return [{'x': 0, 'width': page_width, 'lines': []}]
        
        x_positions = [line['x'] for line in text_lines]
        x_positions.sort()
        
        # Find significant gaps in x-coordinates (column breaks)
        gaps = []
        for i in range(len(x_positions) - 1):
            gap = x_positions[i + 1] - x_positions[i]
            if gap > self.column_gap_threshold:
                gaps.append((x_positions[i], gap))
        
        if gaps:
            # Two-column layout detected
            column_break = max(gaps, key=lambda x: x[1])[0] + 40
            
            return [
                {
                    'x': 0, 
                    'width': column_break, 
                    'lines': [l for l in text_lines if l['x'] < column_break]
                },
                {
                    'x': column_break, 
                    'width': page_width - column_break, 
                    'lines': [l for l in text_lines if l['x'] >= column_break]
                }
            ]
        else:
            # Single column
            return [{'x': 0, 'width': page_width, 'lines': text_lines}]
    
    def _process_column_for_questions(self, column_lines: List[Dict], page_number: int) -> List[Region]:
        """
        Process a single column to detect question-answer groups
        """
        # Detect questions and options separately
        questions = self._detect_question_patterns(column_lines)
        options = self._detect_option_patterns(column_lines)
        
        # Group questions with their options
        question_groups = self._group_questions_with_options(questions, options)
        
        # Convert to Region objects
        regions = []
        for group in question_groups:
            region = self._create_question_group_region(group, page_number)
            if region:
                regions.append(region)
        
        return regions
    
    def _detect_question_patterns(self, text_lines: List[Dict]) -> List[Dict[str, Any]]:
        """
        Detect question starting patterns like "114. ", "Q.1", etc.
        """
        questions = []
        current_question = None
        
        for line in text_lines:
            text = line['text']
            
            # Check if line starts a new question
            question_match = None
            for pattern in self.question_number_patterns:
                match = re.match(pattern, text)
                if match:
                    question_match = match
                    break
            
            if question_match:
                # Save previous question if exists
                if current_question:
                    questions.append(current_question)
                
                # Start new question
                current_question = {
                    'number': int(question_match.group(1)),
                    'start_line': line,
                    'lines': [line],
                    'confidence': 0.95
                }
            elif current_question and self._is_question_continuation(text, current_question):
                # Add line to current question
                current_question['lines'].append(line)
        
        # Don't forget the last question
        if current_question:
            questions.append(current_question)
        
        return questions
    
    def _detect_option_patterns(self, text_lines: List[Dict]) -> List[Dict[str, Any]]:
        """
        Detect option patterns like "(a) text", "(b) text", etc.
        """
        options = []
        
        for line in text_lines:
            text = line['text']
            match = re.match(self.option_pattern, text)
            
            if match:
                options.append({
                    'label': match.group(1),
                    'text': match.group(2).strip(),
                    'line': line,
                    'confidence': 0.9
                })
        
        return options
    
    def _is_question_continuation(self, text: str, current_question: Dict) -> bool:
        """
        Check if a text line is a continuation of the current question
        """
        # Don't continue if it looks like an option or new question
        if re.match(self.option_pattern, text):
            return False
        
        for pattern in self.question_number_patterns:
            if re.match(pattern, text):
                return False
        
        # Don't let questions get too long
        if len(current_question['lines']) >= 8:
            return False
        
        return True
    
    def _group_questions_with_options(self, questions: List[Dict], options: List[Dict]) -> List[Dict[str, Any]]:
        """
        Group questions with their corresponding options based on position
        """
        question_groups = []
        
        for question in questions:
            # Get question boundaries
            question_end_y = question['lines'][-1]['y'] + question['lines'][-1]['height']
            
            # Find next question to set boundary
            next_question_y = float('inf')
            for other_q in questions:
                if other_q['number'] > question['number']:
                    other_start_y = other_q['start_line']['y']
                    if other_start_y > question_end_y:
                        next_question_y = min(next_question_y, other_start_y)
            
            # Find options for this question
            question_options = []
            for option in options:
                option_y = option['line']['y']
                
                # Option belongs to question if it's in the right vertical range
                # and roughly the same x-coordinate (same column)
                if (question_end_y <= option_y < next_question_y and
                    self._same_column(question['start_line'], option['line'])):
                    question_options.append(option)
            
            # Sort options by position and validate sequence
            question_options.sort(key=lambda x: x['line']['y'])
            
            if self._is_valid_option_sequence(question_options):
                question_groups.append({
                    'question': question,
                    'options': question_options,
                    'confidence': self._calculate_group_confidence(question, question_options)
                })
        
        return question_groups
    
    def _same_column(self, line1: Dict, line2: Dict, tolerance: int = 60) -> bool:
        """
        Check if two lines are in the same column based on x-coordinates
        """
        return abs(line1['x'] - line2['x']) < tolerance
    
    def _is_valid_option_sequence(self, options: List[Dict]) -> bool:
        """
        Validate that options are in proper sequence: a, b, c, d
        """
        if len(options) < 2:
            return False
        
        expected_labels = ['a', 'b', 'c', 'd']
        actual_labels = [opt['label'] for opt in options]
        
        # Check if actual labels match expected sequence (allowing partial sequences)
        return actual_labels == expected_labels[:len(actual_labels)]
    
    def _calculate_group_confidence(self, question: Dict, options: List[Dict]) -> float:
        """
        Calculate confidence score for a question-option group
        """
        base_confidence = question['confidence']
        
        # Boost confidence based on number of valid options
        if len(options) >= 4:
            confidence_boost = 0.15
        elif len(options) >= 2:
            confidence_boost = 0.1
        else:
            confidence_boost = 0.0
        
        return min(0.98, base_confidence + confidence_boost)
    
    def _create_question_group_region(self, question_group: Dict, page_number: int, padding: int = 8) -> Region:
        """
        Create a Region object for a question-answer group
        """
        try:
            # Combine all lines (question + options)
            all_lines = question_group['question']['lines'].copy()
            all_lines.extend([opt['line'] for opt in question_group['options']])
            
            if not all_lines:
                return None
            
            # Calculate tight bounding box
            min_x = min(line['x'] for line in all_lines)
            min_y = min(line['y'] for line in all_lines)
            max_x = max(line['x'] + line['width'] for line in all_lines)
            max_y = max(line['y'] + line['height'] for line in all_lines)
            
            # Create region with minimal padding
            region = Region(
                x=max(0, min_x - padding),
                y=max(0, min_y - padding),
                width=(max_x - min_x) + (2 * padding),
                height=(max_y - min_y) + (2 * padding),
                page_number=page_number,
                region_type='question_group',
                confidence=question_group['confidence'],
                text=f"Question {question_group['question']['number']} with {len(question_group['options'])} options",
                metadata={
                    'detection_method': 'smart_question_detection',
                    'question_number': question_group['question']['number'],
                    'option_count': len(question_group['options']),
                    'option_labels': [opt['label'] for opt in question_group['options']],
                    'is_complete': len(question_group['options']) >= 2,
                    'area': (max_x - min_x) * (max_y - min_y),
                    'aspect_ratio': (max_x - min_x) / (max_y - min_y) if (max_y - min_y) > 0 else 1
                }
            )
            
            return region
            
        except Exception as e:
            logger.error(f"Error creating question group region: {str(e)}")
            return None
    
    def _are_regions_vertically_close(
        self, 
        region1: Dict[str, Any], 
        region2: Dict[str, Any], 
        max_distance: int = 50
    ) -> bool:
        """Check if two regions are vertically close"""
        y1_bottom = region1['y'] + region1['height']
        y2_top = region2['y']
        
        # Check if region2 is below region1 and close
        vertical_gap = y2_top - y1_bottom
        
        return 0 <= vertical_gap <= max_distance
    
    def _merge_region_group(self, regions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge a group of regions into a single bounding box
        """
        if not regions:
            return None
            
        # Find bounding box of all regions
        min_x = min(r['x'] for r in regions)
        min_y = min(r['y'] for r in regions)
        max_x = max(r['x'] + r['width'] for r in regions)
        max_y = max(r['y'] + r['height'] for r in regions)
        
        # Calculate confidence as average
        avg_confidence = sum(r['confidence'] for r in regions) / len(regions)
        
        return {
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x,
            'height': max_y - min_y,
            'type': 'merged_region',
            'confidence': avg_confidence,
            'method': 'region_merging',
            'area': (max_x - min_x) * (max_y - min_y),
            'merged_from': len(regions)
        }
    
    def crop_region_from_image(
        self, 
        image: Union[Image.Image, np.ndarray], 
        region: Region,
        padding: int = 10
    ) -> Image.Image:
        """
        Crop a specific region from an image with optional padding
        
        Args:
            image: Source image
            region: Region to crop
            padding: Padding around the region
            
        Returns:
            Cropped PIL Image
        """
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
            
        # Calculate crop boundaries with padding
        left = max(0, region.x - padding)
        top = max(0, region.y - padding)
        right = min(pil_image.width, region.x + region.width + padding)
        bottom = min(pil_image.height, region.y + region.height + padding)
        
        # Crop the image
        cropped = pil_image.crop((left, top, right, bottom))
        
        return cropped
    
    def visualize_regions(
        self, 
        image: Union[Image.Image, np.ndarray], 
        regions: List[Region],
        output_path: Optional[str] = None
    ) -> Image.Image:
        """
        Create a visualization of detected regions on the image
        
        Args:
            image: Source image
            regions: List of regions to visualize
            output_path: Optional path to save the visualization
            
        Returns:
            PIL Image with region overlays
        """
        if isinstance(image, np.ndarray):
            viz_image = Image.fromarray(image)
        else:
            viz_image = image.copy()
            
        draw = ImageDraw.Draw(viz_image)
        
        # Color mapping for different region types
        color_map = {
            'text_line': 'blue',
            'text_block': 'green',
            'contour_region': 'red',
            'merged_region': 'purple',
            'question': 'orange',
            'answer_options': 'cyan',
            'question_group': 'gold'
        }
        
        for i, region in enumerate(regions):
            color = color_map.get(region.region_type, 'gray')
            
            # Draw rectangle
            draw.rectangle(
                [region.x, region.y, region.x2, region.y2],
                outline=color,
                width=2
            )
            
            # Add label
            label = f"{region.region_type}_{i}"
            draw.text(
                (region.x, region.y - 15),
                label,
                fill=color
            )
        
        if output_path:
            viz_image.save(output_path)
            
        return viz_image
    
    def save_regions_to_json(self, regions: List[Region], filepath: str):
        """Save regions to JSON file"""
        regions_data = [region.to_dict() for region in regions]
        
        with open(filepath, 'w') as f:
            json.dump(regions_data, f, indent=2)
    
    def load_regions_from_json(self, filepath: str) -> List[Region]:
        """Load regions from JSON file"""
        with open(filepath, 'r') as f:
            regions_data = json.load(f)
            
        return [Region.from_dict(data) for data in regions_data]


class RegionCorrector:
    """
    Handles manual corrections and refinements of detected regions
    """
    
    def __init__(self):
        self.correction_history = []
    
    def resize_region(
        self, 
        region: Region, 
        new_x: int, 
        new_y: int, 
        new_width: int, 
        new_height: int,
        user_id: str = None
    ) -> Region:
        """
        Resize a region with new coordinates
        
        Args:
            region: Original region
            new_x, new_y, new_width, new_height: New dimensions
            user_id: ID of user making the correction
            
        Returns:
            Updated region
        """
        # Record the correction
        correction = {
            'type': 'resize',
            'original': region.to_dict(),
            'changes': {
                'x': new_x - region.x,
                'y': new_y - region.y,
                'width': new_width - region.width,
                'height': new_height - region.height
            },
            'user_id': user_id,
            'timestamp': self._get_timestamp()
        }
        self.correction_history.append(correction)
        
        # Update region
        region.x = new_x
        region.y = new_y
        region.width = new_width
        region.height = new_height
        region.metadata['manually_corrected'] = True
        region.metadata['correction_count'] = region.metadata.get('correction_count', 0) + 1
        
        return region
    
    def split_region(
        self, 
        region: Region, 
        split_point: Tuple[int, int],
        split_direction: str = 'horizontal',
        user_id: str = None
    ) -> Tuple[Region, Region]:
        """
        Split a region into two regions
        
        Args:
            region: Region to split
            split_point: (x, y) point where to split
            split_direction: 'horizontal' or 'vertical'
            user_id: ID of user making the correction
            
        Returns:
            Tuple of two new regions
        """
        if split_direction == 'horizontal':
            # Split horizontally at y coordinate
            split_y = split_point[1]
            
            region1 = Region(
                x=region.x,
                y=region.y,
                width=region.width,
                height=split_y - region.y,
                page_number=region.page_number,
                region_type=region.region_type,
                confidence=region.confidence * 0.9,  # Reduce confidence for splits
                text=region.text,
                metadata={**region.metadata, 'split_from': region.metadata.get('region_id', ''), 'split_part': 1}
            )
            
            region2 = Region(
                x=region.x,
                y=split_y,
                width=region.width,
                height=region.y + region.height - split_y,
                page_number=region.page_number,
                region_type=region.region_type,
                confidence=region.confidence * 0.9,
                text="",
                metadata={**region.metadata, 'split_from': region.metadata.get('region_id', ''), 'split_part': 2}
            )
        else:
            # Split vertically at x coordinate
            split_x = split_point[0]
            
            region1 = Region(
                x=region.x,
                y=region.y,
                width=split_x - region.x,
                height=region.height,
                page_number=region.page_number,
                region_type=region.region_type,
                confidence=region.confidence * 0.9,
                text=region.text,
                metadata={**region.metadata, 'split_from': region.metadata.get('region_id', ''), 'split_part': 1}
            )
            
            region2 = Region(
                x=split_x,
                y=region.y,
                width=region.x + region.width - split_x,
                height=region.height,
                page_number=region.page_number,
                region_type=region.region_type,
                confidence=region.confidence * 0.9,
                text="",
                metadata={**region.metadata, 'split_from': region.metadata.get('region_id', ''), 'split_part': 2}
            )
        
        # Record correction
        correction = {
            'type': 'split',
            'original': region.to_dict(),
            'result': [region1.to_dict(), region2.to_dict()],
            'split_direction': split_direction,
            'split_point': split_point,
            'user_id': user_id,
            'timestamp': self._get_timestamp()
        }
        self.correction_history.append(correction)
        
        return region1, region2
    
    def merge_regions(
        self, 
        regions: List[Region],
        user_id: str = None
    ) -> Region:
        """
        Merge multiple regions into one
        
        Args:
            regions: List of regions to merge
            user_id: ID of user making the correction
            
        Returns:
            Merged region
        """
        if not regions:
            return None
            
        # Calculate bounding box
        min_x = min(r.x for r in regions)
        min_y = min(r.y for r in regions)
        max_x = max(r.x + r.width for r in regions)
        max_y = max(r.y + r.height for r in regions)
        
        # Combine text
        combined_text = '\n'.join(r.text for r in regions if r.text.strip())
        
        # Average confidence
        avg_confidence = sum(r.confidence for r in regions) / len(regions)
        
        merged_region = Region(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y,
            page_number=regions[0].page_number,
            region_type=regions[0].region_type,
            confidence=avg_confidence,
            text=combined_text,
            metadata={
                'merged_from': [r.metadata.get('region_id', '') for r in regions],
                'merge_count': len(regions),
                'manually_corrected': True
            }
        )
        
        # Record correction
        correction = {
            'type': 'merge',
            'original': [r.to_dict() for r in regions],
            'result': merged_region.to_dict(),
            'user_id': user_id,
            'timestamp': self._get_timestamp()
        }
        self.correction_history.append(correction)
        
        return merged_region
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_correction_stats(self) -> Dict[str, Any]:
        """Get statistics about corrections made"""
        total_corrections = len(self.correction_history)
        
        if total_corrections == 0:
            return {'total_corrections': 0}
        
        correction_types = {}
        users = set()
        
        for correction in self.correction_history:
            correction_type = correction['type']
            correction_types[correction_type] = correction_types.get(correction_type, 0) + 1
            
            if correction.get('user_id'):
                users.add(correction['user_id'])
        
        return {
            'total_corrections': total_corrections,
            'correction_types': correction_types,
            'unique_users': len(users),
            'most_common_correction': max(correction_types.items(), key=lambda x: x[1])[0] if correction_types else None
        }