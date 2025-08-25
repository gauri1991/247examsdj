"""
Utility functions for exam and question bank management.
"""
from django.db.models import Q
from questions.models import QuestionBank
from exams.models import Exam


def find_compatible_question_banks(exam):
    """
    Find question banks that are compatible with the given exam.
    
    Args:
        exam: Exam instance
        
    Returns:
        QuerySet of compatible QuestionBank instances
    """
    if not exam:
        return QuestionBank.objects.none()
    
    # Start with all public question banks
    compatible_banks = QuestionBank.objects.filter(is_public=True)
    
    # Filter by matching criteria
    filters = Q()
    
    # Match by exam type
    if exam.exam_type:
        filters |= Q(exam_type=exam.exam_type)
    
    # Match by category
    if exam.category:
        filters |= Q(category=exam.category)
    
    # Match by subject
    if exam.subject:
        filters |= Q(subject__icontains=exam.subject)
    
    # Match by topic
    if exam.topic:
        filters |= Q(topic__icontains=exam.topic)
    
    # Match by tags (if any tag matches) - SQLite compatible
    if exam.tags:
        for tag in exam.tags:
            # Use icontains for SQLite compatibility instead of JSONField contains
            filters |= Q(tags__icontains=tag)
    
    # Match by difficulty level
    if exam.difficulty_level:
        filters |= Q(difficulty_level=exam.difficulty_level)
    
    # Match by target audience
    if exam.target_audience:
        filters |= Q(target_audience=exam.target_audience)
    
    # Match by language
    if exam.language:
        filters |= Q(language=exam.language)
    
    # Match by state specific content
    if exam.state_specific:
        filters |= Q(state_specific__icontains=exam.state_specific)
    
    # Apply filters
    if filters:
        compatible_banks = compatible_banks.filter(filters)
    
    # Order by relevance (more matches first)
    return compatible_banks.distinct().order_by('-created_at')


def find_compatible_exams(question_bank):
    """
    Find exams that are compatible with the given question bank.
    
    Args:
        question_bank: QuestionBank instance
        
    Returns:
        QuerySet of compatible Exam instances
    """
    if not question_bank:
        return Exam.objects.none()
    
    # Start with all active exams
    compatible_exams = Exam.objects.filter(is_active=True)
    
    # Filter by matching criteria
    filters = Q()
    
    # Match by exam type
    if question_bank.exam_type:
        filters |= Q(exam_type=question_bank.exam_type)
    
    # Match by category
    if question_bank.category:
        filters |= Q(category=question_bank.category)
    
    # Match by subject
    if question_bank.subject:
        filters |= Q(subject__icontains=question_bank.subject)
    
    # Match by topic
    if question_bank.topic:
        filters |= Q(topic__icontains=question_bank.topic)
    
    # Match by tags (if any tag matches) - SQLite compatible
    if question_bank.tags:
        for tag in question_bank.tags:
            # Use icontains for SQLite compatibility instead of JSONField contains
            filters |= Q(tags__icontains=tag)
    
    # Match by difficulty level
    if question_bank.difficulty_level:
        filters |= Q(difficulty_level=question_bank.difficulty_level)
    
    # Match by target audience
    if question_bank.target_audience:
        filters |= Q(target_audience=question_bank.target_audience)
    
    # Match by language
    if question_bank.language:
        filters |= Q(language=question_bank.language)
    
    # Match by state specific content
    if question_bank.state_specific:
        filters |= Q(state_specific__icontains=question_bank.state_specific)
    
    # Apply filters
    if filters:
        compatible_exams = compatible_exams.filter(filters)
    
    # Order by relevance
    return compatible_exams.distinct().order_by('-created_at')


def get_exam_question_bank_suggestions(exam):
    """
    Get suggestions for linking question banks to an exam.
    
    Args:
        exam: Exam instance
        
    Returns:
        dict with categorized suggestions
    """
    compatible_banks = find_compatible_question_banks(exam)
    
    suggestions = {
        'exact_matches': [],
        'good_matches': [],
        'partial_matches': [],
        'total_count': compatible_banks.count()
    }
    
    for bank in compatible_banks[:20]:  # Limit to top 20
        match_score = calculate_match_score(exam, bank)
        
        if match_score >= 0.8:
            suggestions['exact_matches'].append({
                'bank': bank,
                'score': match_score,
                'reasons': get_match_reasons(exam, bank)
            })
        elif match_score >= 0.6:
            suggestions['good_matches'].append({
                'bank': bank,
                'score': match_score,
                'reasons': get_match_reasons(exam, bank)
            })
        else:
            suggestions['partial_matches'].append({
                'bank': bank,
                'score': match_score,
                'reasons': get_match_reasons(exam, bank)
            })
    
    return suggestions


def calculate_match_score(exam, question_bank):
    """
    Calculate a match score between an exam and question bank.
    
    Args:
        exam: Exam instance
        question_bank: QuestionBank instance
        
    Returns:
        float: Match score between 0.0 and 1.0
    """
    score = 0.0
    total_criteria = 0
    
    # Exam type match (weight: 0.2)
    if exam.exam_type and question_bank.exam_type:
        total_criteria += 0.2
        if exam.exam_type == question_bank.exam_type:
            score += 0.2
    
    # Category match (weight: 0.15)
    if exam.category and question_bank.category:
        total_criteria += 0.15
        if exam.category == question_bank.category:
            score += 0.15
    
    # Subject match (weight: 0.15)
    if exam.subject and question_bank.subject:
        total_criteria += 0.15
        if exam.subject.lower() in question_bank.subject.lower() or question_bank.subject.lower() in exam.subject.lower():
            score += 0.15
    
    # Topic match (weight: 0.1)
    if exam.topic and question_bank.topic:
        total_criteria += 0.1
        if exam.topic.lower() in question_bank.topic.lower() or question_bank.topic.lower() in exam.topic.lower():
            score += 0.1
    
    # Tags match (weight: 0.2)
    if exam.tags and question_bank.tags:
        total_criteria += 0.2
        common_tags = set(exam.tags) & set(question_bank.tags)
        if common_tags:
            tag_score = len(common_tags) / max(len(exam.tags), len(question_bank.tags))
            score += 0.2 * tag_score
    
    # Difficulty level match (weight: 0.1)
    if exam.difficulty_level and question_bank.difficulty_level:
        total_criteria += 0.1
        if exam.difficulty_level == question_bank.difficulty_level:
            score += 0.1
    
    # Target audience match (weight: 0.05)
    if exam.target_audience and question_bank.target_audience:
        total_criteria += 0.05
        if exam.target_audience == question_bank.target_audience:
            score += 0.05
    
    # Language match (weight: 0.05)
    if exam.language and question_bank.language:
        total_criteria += 0.05
        if exam.language == question_bank.language:
            score += 0.05
    
    # Normalize score based on available criteria
    if total_criteria > 0:
        return score / total_criteria
    else:
        return 0.0


def get_match_reasons(exam, question_bank):
    """
    Get reasons why an exam and question bank match.
    
    Args:
        exam: Exam instance
        question_bank: QuestionBank instance
        
    Returns:
        list: List of match reasons
    """
    reasons = []
    
    if exam.exam_type == question_bank.exam_type:
        reasons.append(f"Same exam type: {exam.get_exam_type_display()}")
    
    if exam.category == question_bank.category:
        reasons.append(f"Same category: {exam.get_category_display()}")
    
    if exam.subject and question_bank.subject and (
        exam.subject.lower() in question_bank.subject.lower() or 
        question_bank.subject.lower() in exam.subject.lower()
    ):
        reasons.append(f"Related subjects: {exam.subject} ↔ {question_bank.subject}")
    
    if exam.tags and question_bank.tags:
        common_tags = set(exam.tags) & set(question_bank.tags)
        if common_tags:
            reasons.append(f"Common tags: {', '.join(common_tags)}")
    
    if exam.difficulty_level == question_bank.difficulty_level:
        reasons.append(f"Same difficulty: {exam.get_difficulty_level_display()}")
    
    if exam.language == question_bank.language:
        reasons.append(f"Same language: {exam.language}")
    
    return reasons