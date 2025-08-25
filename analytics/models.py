from django.db import models
from django.conf import settings
import uuid


class UserAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analytics')
    
    total_tests_taken = models.IntegerField(default=0)
    total_tests_passed = models.IntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_time_spent_minutes = models.IntegerField(default=0)
    
    strongest_topics = models.JSONField(default=list)
    weakest_topics = models.JSONField(default=list)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_analytics'


class TestAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.OneToOneField('exams.Test', on_delete=models.CASCADE, related_name='analytics')
    
    total_attempts = models.IntegerField(default=0)
    total_completions = models.IntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_completion_time = models.IntegerField(default=0)  # in minutes
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    difficulty_distribution = models.JSONField(default=dict)  # {easy: %, medium: %, hard: %}
    question_performance = models.JSONField(default=list)  # [{question_id, correct_rate, avg_time}]
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_analytics'


class QuestionAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.OneToOneField('questions.Question', on_delete=models.CASCADE, related_name='analytics')
    
    times_appeared = models.IntegerField(default=0)
    times_answered = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    average_time_spent = models.IntegerField(default=0)  # in seconds
    difficulty_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)  # 0-5
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'question_analytics'
