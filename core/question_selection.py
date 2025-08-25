"""
Question Selection Engine for Smart Test Creation
Handles various selection strategies: random, rule-based, manual, and hybrid
"""

from django.db.models import Q, Count, F
from django.utils import timezone
from django.db import transaction
import random
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

from questions.models import Question, QuestionBank, TestQuestion
from exams.models import Test, TestSelectionRule, TestAttempt


class QuestionSelectionEngine:
    """Main engine for selecting questions based on various rules and strategies"""
    
    def __init__(self, exam, selection_rule: TestSelectionRule):
        self.exam = exam
        self.rule = selection_rule
        self.test = selection_rule.test
        self.selected_questions = []
        self.selection_metadata = {}
        
    def select_questions(self) -> List[Question]:
        """Main method to select questions based on configured rules"""
        if self.rule.selection_mode == 'random':
            return self._random_selection()
        elif self.rule.selection_mode == 'rule_based':
            return self._rule_based_selection()
        elif self.rule.selection_mode == 'hybrid':
            return self._hybrid_selection()
        elif self.rule.selection_mode == 'manual':
            # Manual selection is handled through UI
            return []
        else:
            raise ValueError(f"Unknown selection mode: {self.rule.selection_mode}")
    
    def _get_eligible_questions(self) -> 'QuerySet':
        """Get base queryset of eligible questions based on filters"""
        # Start with all questions
        questions = Question.objects.all()
        
        # Filter by included question banks
        if self.rule.included_banks:
            questions = questions.filter(question_bank_id__in=self.rule.included_banks)
        else:
            # Get compatible question banks based on exam properties
            from core.exam_utils import get_exam_question_bank_suggestions
            suggestions = get_exam_question_bank_suggestions(self.exam)
            
            # Get all matches with score >= 0.5
            bank_ids = []
            all_matches = suggestions['exact_matches'] + suggestions['good_matches'] + suggestions['partial_matches']
            for match in all_matches:
                if match['score'] >= 0.5:
                    bank_ids.append(match['bank'].id)
            
            questions = questions.filter(question_bank_id__in=bank_ids)
        
        # Filter by year range
        if self.rule.year_range:
            start_year = self.rule.year_range.get('start')
            end_year = self.rule.year_range.get('end')
            if start_year:
                questions = questions.filter(created_at__year__gte=start_year)
            if end_year:
                questions = questions.filter(created_at__year__lte=end_year)
        
        # Filter by included topics
        if self.rule.included_topics:
            topic_q = Q()
            for topic in self.rule.included_topics:
                topic_q |= Q(topic__icontains=topic) | Q(subtopic__icontains=topic)
            questions = questions.filter(topic_q)
        
        # Exclude specific topics
        if self.rule.excluded_topics:
            for topic in self.rule.excluded_topics:
                questions = questions.exclude(
                    Q(topic__icontains=topic) | Q(subtopic__icontains=topic)
                )
        
        # Exclude specific questions
        if self.rule.excluded_questions:
            questions = questions.exclude(id__in=self.rule.excluded_questions)
        
        # Avoid duplicates from previous attempts if configured
        if self.rule.avoid_duplicates_from_attempts:
            # Get all questions used in previous attempts of tests in this exam
            used_question_ids = TestQuestion.objects.filter(
                test__exam=self.exam,
                test__attempts__user=self.test.created_by
            ).values_list('question_id', flat=True).distinct()
            questions = questions.exclude(id__in=used_question_ids)
        
        # Ensure questions have required fields
        questions = questions.exclude(question_text='').exclude(question_text__isnull=True)
        
        return questions.select_related('question_bank').prefetch_related('options')
    
    def _random_selection(self) -> List[Question]:
        """Random selection with distribution constraints"""
        eligible_questions = self._get_eligible_questions()
        selected = []
        
        # If difficulty distribution is specified
        if self.rule.difficulty_distribution:
            for difficulty, percentage in self.rule.difficulty_distribution.items():
                count = int(self.rule.total_questions * percentage / 100)
                difficulty_questions = list(
                    eligible_questions.filter(difficulty=difficulty)
                )
                
                # Randomly select required number
                if len(difficulty_questions) >= count:
                    selected.extend(random.sample(difficulty_questions, count))
                else:
                    # If not enough questions, take all available
                    selected.extend(difficulty_questions)
                    self.selection_metadata[f'shortage_{difficulty}'] = count - len(difficulty_questions)
        
        # If category distribution is specified
        elif self.rule.category_distribution:
            for category, percentage in self.rule.category_distribution.items():
                count = int(self.rule.total_questions * percentage / 100)
                category_questions = list(
                    eligible_questions.filter(question_bank__category=category)
                )
                
                if len(category_questions) >= count:
                    selected.extend(random.sample(category_questions, count))
                else:
                    selected.extend(category_questions)
                    self.selection_metadata[f'shortage_{category}'] = count - len(category_questions)
        
        # If question type distribution is specified
        elif self.rule.question_type_distribution:
            for qtype, percentage in self.rule.question_type_distribution.items():
                count = int(self.rule.total_questions * percentage / 100)
                type_questions = list(
                    eligible_questions.filter(question_type=qtype)
                )
                
                if len(type_questions) >= count:
                    selected.extend(random.sample(type_questions, count))
                else:
                    selected.extend(type_questions)
                    self.selection_metadata[f'shortage_{qtype}'] = count - len(type_questions)
        
        # If no distribution specified, pure random
        else:
            all_questions = list(eligible_questions)
            if len(all_questions) >= self.rule.total_questions:
                selected = random.sample(all_questions, self.rule.total_questions)
            else:
                selected = all_questions
                self.selection_metadata['shortage_total'] = self.rule.total_questions - len(all_questions)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_selected = []
        for q in selected:
            if q.id not in seen:
                seen.add(q.id)
                unique_selected.append(q)
        
        self.selected_questions = unique_selected
        return unique_selected
    
    def _rule_based_selection(self) -> List[Question]:
        """Complex rule-based selection with scoring"""
        eligible_questions = self._get_eligible_questions()
        
        # Score each question based on multiple criteria
        scored_questions = []
        for question in eligible_questions:
            score = self._calculate_question_score(question)
            scored_questions.append((score, question))
        
        # Sort by score descending
        scored_questions.sort(key=lambda x: x[0], reverse=True)
        
        # Select top N questions
        selected = [q[1] for q in scored_questions[:self.rule.total_questions]]
        
        # Ensure distribution requirements are met
        selected = self._ensure_distribution_requirements(selected, eligible_questions)
        
        self.selected_questions = selected
        return selected
    
    def _calculate_question_score(self, question: Question) -> float:
        """Calculate question score based on multiple criteria"""
        score = 0.0
        
        # Base score
        score += 100
        
        # Difficulty match bonus
        if self.rule.difficulty_distribution and question.difficulty in self.rule.difficulty_distribution:
            score += self.rule.difficulty_distribution[question.difficulty] * 2
        
        # Category match bonus
        if (self.rule.category_distribution and 
            question.question_bank and 
            question.question_bank.category in self.rule.category_distribution):
            score += self.rule.category_distribution[question.question_bank.category] * 2
        
        # Question type match bonus
        if self.rule.question_type_distribution and question.question_type in self.rule.question_type_distribution:
            score += self.rule.question_type_distribution[question.question_type] * 1.5
        
        # Topic coverage bonus
        if self.rule.ensure_topic_coverage and question.topic:
            score += 20
            if question.subtopic:
                score += 10
        
        # Freshness bonus (newer questions get higher scores)
        if self.rule.priority_new_questions:
            days_old = (timezone.now() - question.created_at).days
            freshness_score = max(0, 100 - (days_old * 0.5))
            score += freshness_score
        
        # Quality indicators
        if hasattr(question, 'analytics'):
            # Higher score for questions with good success rate (40-80%)
            success_rate = question.analytics.get('success_rate', 50)
            if 40 <= success_rate <= 80:
                score += 30
            
            # Bonus for frequently used questions (proven quality)
            usage_count = question.analytics.get('usage_count', 0)
            score += min(usage_count * 0.5, 50)
        
        # Penalty for questions without explanations
        if not question.explanation:
            score -= 20
        
        # Bonus for questions with images (more engaging)
        if question.image:
            score += 15
        
        return score
    
    def _hybrid_selection(self) -> List[Question]:
        """Hybrid approach combining random and rule-based selection"""
        # First, apply rule-based selection for 70% of questions
        rule_based_count = int(self.rule.total_questions * 0.7)
        self.rule.total_questions = rule_based_count
        rule_based_questions = self._rule_based_selection()
        
        # Then, random selection for remaining 30%
        random_count = self.rule.total_questions - len(rule_based_questions)
        if random_count > 0:
            # Exclude already selected questions
            eligible_questions = self._get_eligible_questions().exclude(
                id__in=[q.id for q in rule_based_questions]
            )
            random_questions = list(eligible_questions.order_by('?')[:random_count])
            
            # Combine both sets
            self.selected_questions = rule_based_questions + random_questions
        else:
            self.selected_questions = rule_based_questions
        
        return self.selected_questions
    
    def _ensure_distribution_requirements(self, selected: List[Question], 
                                        eligible_questions: 'QuerySet') -> List[Question]:
        """Ensure selected questions meet distribution requirements"""
        # Check difficulty distribution
        if self.rule.difficulty_distribution:
            current_distribution = self._calculate_distribution(selected, 'difficulty')
            selected = self._adjust_distribution(
                selected, eligible_questions, 'difficulty', 
                self.rule.difficulty_distribution, current_distribution
            )
        
        # Check category distribution
        if self.rule.category_distribution:
            current_distribution = self._calculate_distribution(selected, 'question_bank__category')
            selected = self._adjust_distribution(
                selected, eligible_questions, 'question_bank__category',
                self.rule.category_distribution, current_distribution
            )
        
        return selected
    
    def _calculate_distribution(self, questions: List[Question], field: str) -> Dict[str, int]:
        """Calculate current distribution of questions by field"""
        distribution = defaultdict(int)
        for question in questions:
            if '__' in field:
                # Handle related field
                parts = field.split('__')
                value = question
                for part in parts:
                    value = getattr(value, part, None)
                    if value is None:
                        break
            else:
                value = getattr(question, field, None)
            
            if value:
                distribution[value] += 1
        
        return dict(distribution)
    
    def _adjust_distribution(self, selected: List[Question], eligible_questions: 'QuerySet',
                           field: str, target_distribution: Dict[str, int],
                           current_distribution: Dict[str, int]) -> List[Question]:
        """Adjust selection to match target distribution"""
        adjusted = selected.copy()
        
        for value, target_percentage in target_distribution.items():
            target_count = int(self.rule.total_questions * target_percentage / 100)
            current_count = current_distribution.get(value, 0)
            
            if current_count < target_count:
                # Need more questions of this type
                needed = target_count - current_count
                
                # Get additional questions
                if '__' in field:
                    filter_kwargs = {f"{field}": value}
                else:
                    filter_kwargs = {field: value}
                
                additional = eligible_questions.filter(**filter_kwargs).exclude(
                    id__in=[q.id for q in adjusted]
                ).order_by('?')[:needed]
                
                adjusted.extend(additional)
            
            elif current_count > target_count:
                # Too many questions of this type, remove some
                excess = current_count - target_count
                
                # Find questions to remove
                to_remove = []
                for q in adjusted:
                    if '__' in field:
                        parts = field.split('__')
                        q_value = q
                        for part in parts:
                            q_value = getattr(q_value, part, None)
                    else:
                        q_value = getattr(q, field, None)
                    
                    if q_value == value and len(to_remove) < excess:
                        to_remove.append(q)
                
                for q in to_remove:
                    adjusted.remove(q)
        
        return adjusted
    
    def get_distribution_preview(self) -> Dict[str, any]:
        """Get preview of question distribution"""
        if not self.selected_questions:
            return {'error': 'No questions selected yet'}
        
        questions = self.selected_questions
        total = len(questions)
        
        preview = {
            'total': total,
            'metadata': self.selection_metadata,
            'distributions': {
                'by_difficulty': self._get_percentage_distribution(questions, 'difficulty'),
                'by_category': self._get_percentage_distribution(questions, 'question_bank__category'),
                'by_type': self._get_percentage_distribution(questions, 'question_type'),
                'by_topic': self._get_count_distribution(questions, 'topic'),
            }
        }
        
        # Add warnings if targets not met
        warnings = []
        if 'shortage_total' in self.selection_metadata:
            warnings.append(f"Could only find {total} questions out of {self.rule.total_questions} requested")
        
        for key, value in self.selection_metadata.items():
            if key.startswith('shortage_'):
                field = key.replace('shortage_', '')
                warnings.append(f"Shortage of {value} questions for {field}")
        
        if warnings:
            preview['warnings'] = warnings
        
        return preview
    
    def _get_percentage_distribution(self, questions: List[Question], field: str) -> List[Dict]:
        """Get percentage distribution for visualization"""
        distribution = self._calculate_distribution(questions, field)
        total = len(questions)
        
        result = []
        for value, count in distribution.items():
            percentage = (count / total) * 100 if total > 0 else 0
            result.append({
                'label': value,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        return sorted(result, key=lambda x: x['count'], reverse=True)
    
    def _get_count_distribution(self, questions: List[Question], field: str) -> List[Dict]:
        """Get count distribution for fields with many unique values"""
        distribution = self._calculate_distribution(questions, field)
        
        result = []
        for value, count in distribution.items():
            if value:  # Skip empty values
                result.append({
                    'label': value,
                    'count': count
                })
        
        return sorted(result, key=lambda x: x['count'], reverse=True)[:10]  # Top 10
    
    @transaction.atomic
    def apply_selection_to_test(self, marks_per_question: Optional[int] = None) -> bool:
        """Apply the selected questions to the test"""
        if not self.selected_questions:
            return False
        
        # Clear existing questions if any
        TestQuestion.objects.filter(test=self.test).delete()
        
        # Calculate marks per question if not provided
        if marks_per_question is None:
            marks_per_question = self.test.total_marks // len(self.selected_questions)
        
        # Create TestQuestion objects
        test_questions = []
        for order, question in enumerate(self.selected_questions):
            test_questions.append(
                TestQuestion(
                    test=self.test,
                    question=question,
                    order=order + 1,
                    marks=marks_per_question
                )
            )
        
        # Bulk create
        TestQuestion.objects.bulk_create(test_questions)
        
        # Update test total marks to match actual
        actual_total = marks_per_question * len(self.selected_questions)
        if actual_total != self.test.total_marks:
            self.test.total_marks = actual_total
            self.test.save(update_fields=['total_marks'])
        
        return True
    
    def validate_selection(self) -> Tuple[bool, List[str]]:
        """Validate if selection meets all requirements"""
        errors = []
        
        if not self.selected_questions:
            errors.append("No questions selected")
            return False, errors
        
        # Check total count
        if len(self.selected_questions) < self.rule.total_questions * 0.8:
            errors.append(
                f"Could only select {len(self.selected_questions)} questions "
                f"out of {self.rule.total_questions} requested (less than 80%)"
            )
        
        # Validate distributions if specified
        if self.rule.difficulty_distribution:
            actual_dist = self._calculate_distribution(self.selected_questions, 'difficulty')
            for difficulty, target_pct in self.rule.difficulty_distribution.items():
                actual_pct = (actual_dist.get(difficulty, 0) / len(self.selected_questions)) * 100
                if abs(actual_pct - target_pct) > 10:  # Allow 10% deviation
                    errors.append(
                        f"Difficulty '{difficulty}' distribution is {actual_pct:.1f}% "
                        f"instead of target {target_pct}%"
                    )
        
        return len(errors) == 0, errors