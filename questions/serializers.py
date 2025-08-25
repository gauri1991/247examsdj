from rest_framework import serializers
from .models import QuestionBank, Question, QuestionOption, TestQuestion, UserAnswer


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('id', 'option_text', 'is_correct', 'order')
        extra_kwargs = {
            'is_correct': {'write_only': True}
        }


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, required=False)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'question_bank', 'question_text', 'question_type', 'difficulty',
                 'marks', 'negative_marks', 'expected_answer', 'topic', 'subtopic',
                 'tags', 'explanation', 'image', 'options', 'created_by', 'created_by_name',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        question = Question.objects.create(**validated_data)
        
        for option_data in options_data:
            QuestionOption.objects.create(question=question, **option_data)
        
        return question
    
    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if options_data is not None:
            instance.options.all().delete()
            for option_data in options_data:
                QuestionOption.objects.create(question=instance, **option_data)
        
        return instance


class QuestionBankSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)
    
    class Meta:
        model = QuestionBank
        fields = ('id', 'name', 'description', 'is_public', 'created_by', 
                 'created_by_name', 'questions_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')


class TestQuestionSerializer(serializers.ModelSerializer):
    question_detail = QuestionSerializer(source='question', read_only=True)
    
    class Meta:
        model = TestQuestion
        fields = ('id', 'test', 'section', 'question', 'order', 'marks', 'question_detail')


class UserAnswerSerializer(serializers.ModelSerializer):
    question_detail = QuestionSerializer(source='question', read_only=True)
    
    class Meta:
        model = UserAnswer
        fields = ('id', 'test_attempt', 'question', 'question_detail', 'selected_options',
                 'text_answer', 'boolean_answer', 'is_marked_for_review', 'time_spent_seconds',
                 'is_correct', 'marks_obtained', 'answered_at')
        read_only_fields = ('id', 'is_correct', 'marks_obtained')


class QuestionImportSerializer(serializers.Serializer):
    file = serializers.FileField()
    question_bank = serializers.UUIDField(required=False)