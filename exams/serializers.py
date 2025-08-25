from rest_framework import serializers
from .models import Exam, Test, TestSection, TestAttempt
from questions.serializers import TestQuestionSerializer


class ExamSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    tests_count = serializers.IntegerField(source='tests.count', read_only=True)
    
    class Meta:
        model = Exam
        fields = ('id', 'name', 'description', 'category', 'is_active', 
                 'created_by', 'created_by_name', 'tests_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')


class TestSectionSerializer(serializers.ModelSerializer):
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)
    
    class Meta:
        model = TestSection
        fields = ('id', 'name', 'description', 'order', 'questions_count')


class TestSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(source='exam.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    sections = TestSectionSerializer(many=True, read_only=True)
    questions_count = serializers.IntegerField(source='test_questions.count', read_only=True)
    attempts_count = serializers.IntegerField(source='attempts.count', read_only=True)
    
    class Meta:
        model = Test
        fields = ('id', 'exam', 'exam_name', 'title', 'description', 'duration_minutes',
                 'total_marks', 'pass_percentage', 'is_published', 'randomize_questions',
                 'show_result_immediately', 'allow_review', 'max_attempts',
                 'start_time', 'end_time', 'created_by', 'created_by_name',
                 'sections', 'questions_count', 'attempts_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')


class TestAttemptSerializer(serializers.ModelSerializer):
    test_title = serializers.CharField(source='test.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = TestAttempt
        fields = ('id', 'test', 'test_title', 'user', 'user_name', 'status',
                 'start_time', 'end_time', 'time_spent_seconds', 'total_questions',
                 'attempted_questions', 'correct_answers', 'marks_obtained', 'percentage')
        read_only_fields = ('id', 'user', 'start_time')


class TestDetailSerializer(TestSerializer):
    questions = TestQuestionSerializer(source='test_questions', many=True, read_only=True)
    
    class Meta(TestSerializer.Meta):
        fields = TestSerializer.Meta.fields + ('questions',)