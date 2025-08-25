import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class QuestionTypeClassifier:
    """
    Advanced question type classification system using pattern matching and NLP
    """
    
    def __init__(self):
        # Define patterns for different question types
        self.mcq_patterns = [
            r'\b[A-E]\s*[\.:\)]\s*',  # A. B. C. etc.
            r'\b\d+\s*[\.:\)]\s*\w+.*\n\s*[A-E]\s*[\.:\)]',  # Question followed by options
            r'(?i)choose\s+(?:the\s+)?(?:correct|best|most\s+appropriate)',
            r'(?i)which\s+(?:of\s+)?(?:the\s+)?following',
            r'(?i)select\s+(?:the\s+)?(?:correct|best)',
        ]
        
        self.true_false_patterns = [
            r'(?i)true\s*(?:or|\/)\s*false',
            r'(?i)state\s+(?:whether\s+)?true\s+or\s+false',
            r'(?i)\b(?:T|F)\s*[\.:\)]\s*',
            r'(?i)mark\s+as\s+true\s+or\s+false',
            r'(?i)indicate\s+(?:whether\s+)?true\s+or\s+false',
        ]
        
        self.fill_blank_patterns = [
            r'_{2,}',  # Multiple underscores
            r'\[?\s*(?:blank|_+)\s*\]?',  # [blank] or variations
            r'(?i)fill\s+in\s+the\s+blank',
            r'(?i)complete\s+the\s+(?:following\s+)?(?:sentence|statement)',
            r'\.{3,}',  # Multiple dots indicating blank
        ]
        
        self.essay_patterns = [
            r'(?i)(?:explain|describe|discuss|analyze|evaluate|compare|contrast)',
            r'(?i)write\s+(?:a\s+)?(?:short\s+)?(?:note|essay|paragraph)',
            r'(?i)what\s+(?:is|are|was|were)\s+(?:the\s+)?(?:importance|significance|effects?|causes?)',
            r'(?i)(?:how|why|when|where)\s+(?:does?|did|is|are|was|were)',
            r'(?i)give\s+(?:your\s+)?(?:opinion|views?)',
            r'(?i)(?:elaborate|justify|summarize|outline)',
        ]
        
        self.multi_select_patterns = [
            r'(?i)select\s+all\s+that\s+apply',
            r'(?i)choose\s+(?:all|multiple)\s+correct',
            r'(?i)mark\s+all\s+(?:that\s+)?(?:are\s+)?correct',
            r'(?i)tick\s+all\s+(?:that\s+)?apply',
            r'(?i)check\s+all\s+(?:that\s+)?apply',
        ]
        
        # Enhanced question numbering patterns
        self.question_number_patterns = [
            r'^(\d+)\s*[\.:\)]\s*',  # 1. 2) 3:
            r'^Q\s*(\d+)\s*[\.:\)]\s*',  # Q1. Q2)
            r'^Question\s*(\d+)\s*[\.:\)]\s*',  # Question 1.
            r'^\((\d+)\)\s*',  # (1) (2)
            r'^([IVX]+)\s*[\.:\)]\s*',  # Roman numerals I. II.
            r'^([a-z])\s*[\.:\)]\s*',  # a. b) c:
            r'^([A-Z])\s*[\.:\)]\s*',  # A. B) C:
            r'^\[(\d+)\]\s*',  # [1] [2]
        ]
        
        # Sub-question patterns
        self.sub_question_patterns = [
            r'^\s*\(([a-z])\)\s*',  # (a) (b)
            r'^\s*([a-z])\s*[\.:\)]\s*',  # a. b)
            r'^\s*\(([ivx]+)\)\s*',  # (i) (ii)
            r'^\s*([ivx]+)\s*[\.:\)]\s*',  # i. ii)
        ]
        
        # Advanced question indicators
        self.question_indicators = [
            r'(?i)^(?:question|q)\s*\d+',
            r'(?i)^(?:problem|prob)\s*\d+',
            r'(?i)^(?:exercise|ex)\s*\d+',
            r'(?i)^\d+\.\s*(?:what|who|when|where|why|how|which)',
            r'(?i)^\d+\.\s*(?:explain|describe|discuss|analyze)',
            r'(?i)^\d+\.\s*(?:find|calculate|solve|determine)',
            r'(?i)^\d+\.\s*(?:state|define|identify|list)',
            r'(?i)mark\s+all\s+(?:the\s+)?correct',
            r'(?i)which\s+of\s+the\s+following\s+are',  # plural form
            r'(?i)identify\s+all',
        ]
    
    def classify_question(self, question_text: str, answer_options: List[Dict] = None) -> Tuple[str, float]:
        """
        Classify the question type based on text patterns and structure
        
        Returns:
            Tuple of (question_type, confidence)
        """
        if not question_text:
            return 'unknown', 0.0
        
        # Clean and normalize text
        text = question_text.strip().lower()
        
        # Track classification scores
        scores = {
            'mcq': 0.0,
            'multi_select': 0.0,
            'true_false': 0.0,
            'fill_blank': 0.0,
            'essay': 0.0,
        }
        
        # Check for multi-select patterns first
        for pattern in self.multi_select_patterns:
            if re.search(pattern, text):
                scores['multi_select'] += 3.0
        
        # Check for True/False patterns
        for pattern in self.true_false_patterns:
            if re.search(pattern, text):
                scores['true_false'] += 2.5
        
        # Check if only two options and they are True/False
        if answer_options and len(answer_options) == 2:
            option_texts = [opt.get('text', '').lower() for opt in answer_options]
            if any('true' in opt for opt in option_texts) and any('false' in opt for opt in option_texts):
                scores['true_false'] += 3.0
        
        # Check for fill-in-the-blank patterns
        for pattern in self.fill_blank_patterns:
            if re.search(pattern, question_text):  # Use original text to preserve blanks
                scores['fill_blank'] += 2.0
        
        # Check for MCQ patterns
        for pattern in self.mcq_patterns:
            if re.search(pattern, text):
                scores['mcq'] += 1.5
        
        # If answer options are provided, it's likely MCQ or multi-select
        if answer_options and len(answer_options) >= 3:
            scores['mcq'] += 2.0
            if len(answer_options) >= 4:
                scores['mcq'] += 1.0
        
        # Check for essay patterns
        for pattern in self.essay_patterns:
            if re.search(pattern, text):
                scores['essay'] += 1.5
        
        # Additional heuristics
        word_count = len(text.split())
        
        # Long questions without options are likely essays
        if word_count > 20 and not answer_options:
            scores['essay'] += 1.0
        
        # Short questions with blanks
        if word_count < 15 and scores['fill_blank'] > 0:
            scores['fill_blank'] += 1.0
        
        # Questions starting with command verbs
        command_verbs = ['explain', 'describe', 'discuss', 'analyze', 'evaluate', 'write']
        first_word = text.split()[0] if text.split() else ''
        if first_word in command_verbs:
            scores['essay'] += 2.0
        
        # Get the highest scoring type
        if max(scores.values()) == 0:
            return 'unknown', 0.0
        
        question_type = max(scores, key=scores.get)
        confidence = min(scores[question_type] / 5.0, 1.0)  # Normalize to 0-1
        
        # Adjust confidence based on pattern strength
        if scores[question_type] >= 3.0:
            confidence = max(confidence, 0.8)
        elif scores[question_type] >= 2.0:
            confidence = max(confidence, 0.6)
        
        return question_type, confidence
    
    def extract_question_metadata(self, question_text: str, question_type: str) -> Dict:
        """
        Extract additional metadata based on question type
        """
        metadata = {
            'has_math': bool(re.search(r'[+=\-*/^√∫∑∏]', question_text)),
            'has_code': bool(re.search(r'(?:def|class|function|if|for|while|import)', question_text)),
            'has_chemical_formula': bool(re.search(r'[A-Z][a-z]?\d*(?:\s*[A-Z][a-z]?\d*)*', question_text)),
            'estimated_time_minutes': self._estimate_time(question_text, question_type),
            'complexity_indicators': self._get_complexity_indicators(question_text),
        }
        
        return metadata
    
    def _estimate_time(self, question_text: str, question_type: str) -> float:
        """
        Estimate time required to answer the question
        """
        word_count = len(question_text.split())
        
        base_times = {
            'mcq': 1.0,
            'multi_select': 1.5,
            'true_false': 0.5,
            'fill_blank': 1.0,
            'essay': 5.0,
            'unknown': 2.0,
        }
        
        base_time = base_times.get(question_type, 2.0)
        
        # Adjust based on complexity
        if word_count > 50:
            base_time *= 1.5
        elif word_count > 100:
            base_time *= 2.0
        
        return round(base_time, 1)
    
    def _get_complexity_indicators(self, question_text: str) -> List[str]:
        """
        Identify complexity indicators in the question
        """
        indicators = []
        
        # Check for various complexity indicators
        if re.search(r'(?i)(?:analyze|evaluate|synthesize|critique)', question_text):
            indicators.append('higher_order_thinking')
        
        if re.search(r'(?i)(?:calculate|compute|solve|derive)', question_text):
            indicators.append('calculation_required')
        
        if re.search(r'(?i)(?:compare|contrast|differentiate)', question_text):
            indicators.append('comparison_required')
        
        if re.search(r'(?i)(?:example|illustrate|demonstrate)', question_text):
            indicators.append('example_required')
        
        if len(question_text.split()) > 50:
            indicators.append('long_question')
        
        if re.search(r'\d+\s*(?:marks?|points?)', question_text):
            indicators.append('marks_specified')
        
        return indicators
    
    def detect_question_boundaries(self, text_lines: List[str]) -> List[Dict]:
        """
        Detect question boundaries in a list of text lines
        
        Args:
            text_lines: List of text lines from the document
            
        Returns:
            List of dictionaries containing question boundary information
        """
        questions = []
        current_question = None
        current_lines = []
        
        for i, line in enumerate(text_lines):
            line = line.strip()
            if not line:
                continue
                
            # Check if this line starts a new question
            question_match = self._detect_question_start(line)
            
            if question_match:
                # Save previous question if exists
                if current_question and current_lines:
                    current_question['end_line'] = i - 1
                    current_question['text'] = '\n'.join(current_lines)
                    current_question['line_count'] = len(current_lines)
                    questions.append(current_question)
                
                # Start new question
                current_question = {
                    'question_number': question_match['number'],
                    'numbering_type': question_match['type'],
                    'start_line': i,
                    'end_line': None,
                    'text': '',
                    'line_count': 0
                }
                current_lines = [line]
            else:
                # Add to current question if we have one
                if current_question:
                    current_lines.append(line)
        
        # Don't forget the last question
        if current_question and current_lines:
            current_question['end_line'] = len(text_lines) - 1
            current_question['text'] = '\n'.join(current_lines)
            current_question['line_count'] = len(current_lines)
            questions.append(current_question)
        
        return questions
    
    def _detect_question_start(self, line: str) -> Optional[Dict]:
        """
        Detect if a line starts a new question
        
        Args:
            line: Text line to analyze
            
        Returns:
            Dict with question number and type, or None if not a question start
        """
        # Check each numbering pattern
        for pattern in self.question_number_patterns:
            match = re.match(pattern, line)
            if match:
                return {
                    'number': match.group(1) if match.groups() else '',
                    'type': self._determine_numbering_type(pattern),
                    'full_match': match.group(0)
                }
        
        # Check question indicators
        for pattern in self.question_indicators:
            if re.search(pattern, line):
                return {
                    'number': self._extract_number_from_indicator(line),
                    'type': 'indicator',
                    'full_match': line
                }
        
        return None
    
    def _determine_numbering_type(self, pattern: str) -> str:
        """Determine the type of numbering based on the pattern"""
        if 'Q' in pattern:
            return 'Q_format'
        elif 'Question' in pattern:
            return 'question_word'
        elif '[IVX]' in pattern:
            return 'roman'
        elif '[a-z]' in pattern:
            return 'lowercase'
        elif '[A-Z]' in pattern:
            return 'uppercase'
        elif r'\(' in pattern:
            return 'parentheses'
        elif r'\[' in pattern:
            return 'brackets'
        else:
            return 'numeric'
    
    def _extract_number_from_indicator(self, line: str) -> str:
        """Extract question number from indicator patterns"""
        number_match = re.search(r'\d+', line)
        return number_match.group(0) if number_match else ''


class QuestionDifficultyEstimator:
    """
    Estimate question difficulty based on various factors
    """
    
    def __init__(self):
        # Define difficulty keywords
        self.easy_keywords = [
            'define', 'list', 'name', 'state', 'identify', 'what is', 'simple',
            'basic', 'fundamental', 'elementary', 'introduction'
        ]
        
        self.medium_keywords = [
            'explain', 'describe', 'discuss', 'compare', 'differentiate',
            'calculate', 'determine', 'find', 'solve'
        ]
        
        self.hard_keywords = [
            'analyze', 'evaluate', 'critical', 'justify', 'prove', 'derive',
            'synthesize', 'design', 'develop', 'complex', 'advanced'
        ]
        
        # Bloom's taxonomy levels
        self.blooms_levels = {
            'remember': 1,
            'understand': 2,
            'apply': 3,
            'analyze': 4,
            'evaluate': 5,
            'create': 6
        }
    
    def estimate_difficulty(self, question_text: str, question_type: str = None, 
                          answer_options: List[Dict] = None) -> Tuple[str, float]:
        """
        Estimate question difficulty
        
        Returns:
            Tuple of (difficulty_level, confidence)
        """
        if not question_text:
            return 'medium', 0.0
        
        text_lower = question_text.lower()
        scores = {'easy': 0, 'medium': 0, 'hard': 0}
        
        # Check for difficulty keywords
        for keyword in self.easy_keywords:
            if keyword in text_lower:
                scores['easy'] += 2
        
        for keyword in self.medium_keywords:
            if keyword in text_lower:
                scores['medium'] += 2
        
        for keyword in self.hard_keywords:
            if keyword in text_lower:
                scores['hard'] += 2
        
        # Analyze complexity based on length
        word_count = len(question_text.split())
        if word_count < 20:
            scores['easy'] += 1
        elif word_count > 50:
            scores['hard'] += 1
        else:
            scores['medium'] += 1
        
        # Check for mathematical/technical content
        if re.search(r'[∫∑∏√≈≠≤≥∞∂∇]', question_text):
            scores['hard'] += 2
        elif re.search(r'[+=\-*/^]', question_text):
            scores['medium'] += 1
        
        # Essay questions tend to be harder
        if question_type == 'essay':
            scores['hard'] += 1
        elif question_type == 'true_false':
            scores['easy'] += 1
        
        # Determine bloom's taxonomy level
        bloom_level = self._get_bloom_level(text_lower)
        if bloom_level >= 4:
            scores['hard'] += 2
        elif bloom_level >= 2:
            scores['medium'] += 1
        else:
            scores['easy'] += 1
        
        # Calculate final difficulty
        max_score = max(scores.values())
        if max_score == 0:
            return 'medium', 0.5
        
        difficulty = max(scores, key=scores.get)
        confidence = min(max_score / 10.0, 1.0)
        
        return difficulty, confidence
    
    def _get_bloom_level(self, text: str) -> int:
        """
        Determine Bloom's taxonomy level based on action verbs
        """
        bloom_verbs = {
            1: ['define', 'list', 'name', 'state', 'identify', 'match', 'select'],
            2: ['explain', 'describe', 'discuss', 'summarize', 'interpret', 'classify'],
            3: ['apply', 'solve', 'calculate', 'demonstrate', 'implement', 'use'],
            4: ['analyze', 'compare', 'contrast', 'examine', 'differentiate', 'investigate'],
            5: ['evaluate', 'assess', 'judge', 'critique', 'justify', 'recommend'],
            6: ['create', 'design', 'develop', 'construct', 'formulate', 'invent']
        }
        
        for level, verbs in bloom_verbs.items():
            for verb in verbs:
                if verb in text:
                    return level
        
        return 2  # Default to understand level


class TopicExtractor:
    """
    Extract and categorize topics from questions using keyword matching
    """
    
    def __init__(self):
        # Define topic patterns and keywords
        self.topic_patterns = {
            'Mathematics': {
                'keywords': ['algebra', 'geometry', 'calculus', 'trigonometry', 'statistics',
                           'probability', 'matrix', 'vector', 'equation', 'function', 'integral',
                           'derivative', 'theorem', 'proof', 'polynomial'],
                'patterns': [r'\b\d+[x|y|z]\b', r'[∫∑∏√]', r'\bsin\b|\bcos\b|\btan\b']
            },
            'Physics': {
                'keywords': ['force', 'energy', 'momentum', 'velocity', 'acceleration', 'mass',
                           'gravity', 'electric', 'magnetic', 'wave', 'quantum', 'relativity',
                           'thermodynamics', 'optics', 'mechanics'],
                'patterns': [r'\b[F|E|P|V|a|m|g]\s*=', r'\bN\b|\bJ\b|\bW\b|\bHz\b']
            },
            'Chemistry': {
                'keywords': ['element', 'compound', 'reaction', 'acid', 'base', 'molecule',
                           'atom', 'electron', 'proton', 'neutron', 'bond', 'oxidation',
                           'reduction', 'periodic', 'organic', 'inorganic'],
                'patterns': [r'[A-Z][a-z]?\d*', r'pH', r'mol', r'→']
            },
            'Biology': {
                'keywords': ['cell', 'organism', 'species', 'evolution', 'genetics', 'DNA',
                           'RNA', 'protein', 'enzyme', 'metabolism', 'photosynthesis',
                           'respiration', 'ecology', 'anatomy', 'physiology'],
                'patterns': [r'ATP', r'mRNA', r'tRNA']
            },
            'Computer Science': {
                'keywords': ['algorithm', 'data structure', 'programming', 'software', 'hardware',
                           'network', 'database', 'operating system', 'compiler', 'binary',
                           'loop', 'function', 'variable', 'array', 'object'],
                'patterns': [r'O\([n|log|1]\)', r'\bif\b|\belse\b|\bfor\b|\bwhile\b']
            },
            'History': {
                'keywords': ['war', 'revolution', 'empire', 'civilization', 'dynasty', 'era',
                           'century', 'ancient', 'medieval', 'modern', 'colonial', 'independence',
                           'treaty', 'constitution', 'monarchy'],
                'patterns': [r'\b\d{3,4}\s*(?:BC|AD|BCE|CE)\b', r'\b(?:I+|IV|V|VI+|IX|X+)\b']
            },
            'Geography': {
                'keywords': ['continent', 'country', 'ocean', 'mountain', 'river', 'climate',
                           'latitude', 'longitude', 'population', 'resource', 'map', 'region',
                           'hemisphere', 'equator', 'topography'],
                'patterns': [r'°[N|S|E|W]', r'\bkm\b|\bmiles?\b']
            },
            'Literature': {
                'keywords': ['novel', 'poem', 'poetry', 'author', 'character', 'plot', 'theme',
                           'metaphor', 'simile', 'narrative', 'protagonist', 'antagonist',
                           'genre', 'literary', 'prose'],
                'patterns': [r'"[^"]*"', r'\'[^\']*\'']
            },
            'Economics': {
                'keywords': ['demand', 'supply', 'market', 'price', 'cost', 'profit', 'GDP',
                           'inflation', 'unemployment', 'trade', 'budget', 'tax', 'investment',
                           'capital', 'finance'],
                'patterns': [r'\$\d+', r'%', r'\bGDP\b|\bCPI\b']
            }
        }
    
    def extract_topic(self, question_text: str) -> Tuple[str, float]:
        """
        Extract the most likely topic from the question
        
        Returns:
            Tuple of (topic, confidence)
        """
        if not question_text:
            return 'General', 0.0
        
        text_lower = question_text.lower()
        topic_scores = {}
        
        for topic, data in self.topic_patterns.items():
            score = 0
            
            # Check keywords
            for keyword in data['keywords']:
                if keyword.lower() in text_lower:
                    score += 2
            
            # Check patterns
            for pattern in data['patterns']:
                if re.search(pattern, question_text, re.IGNORECASE):
                    score += 3
            
            if score > 0:
                topic_scores[topic] = score
        
        if not topic_scores:
            return 'General', 0.3
        
        # Get the highest scoring topic
        best_topic = max(topic_scores, key=topic_scores.get)
        confidence = min(topic_scores[best_topic] / 15.0, 1.0)
        
        return best_topic, confidence