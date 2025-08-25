#!/usr/bin/env python3
"""
Test script to validate question bank functionality
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from questions.models import QuestionBank, Question

User = get_user_model()

def test_question_bank_setup():
    """Test that question bank setup is working correctly"""
    print("Testing Question Bank Setup...")
    
    try:
        # Test URL configuration
        question_bank_url = reverse('question-bank')
        print(f"✓ Question bank URL resolved: {question_bank_url}")
        
        # Test model creation
        user = User.objects.filter(role='admin').first()
        if not user:
            print("✗ No admin user found - create one first")
            return False
        
        # Create test question bank
        bank = QuestionBank.objects.create(
            name="Test Bank",
            description="Test description",
            is_public=True,
            created_by=user
        )
        print(f"✓ Question bank created: {bank.name}")
        
        # Create test question
        question = Question.objects.create(
            question_bank=bank,
            question_text="What is 2+2?",
            question_type="mcq",
            difficulty="easy",
            marks=1,
            created_by=user
        )
        print(f"✓ Question created: {question.question_text}")
        
        # Test template exists
        template_path = "templates/questions/question_bank_list.html"
        if os.path.exists(template_path):
            print(f"✓ Template exists: {template_path}")
        else:
            print(f"✗ Template missing: {template_path}")
            return False
        
        print("✓ All question bank components are properly set up!")
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_question_bank_setup()
    if success:
        print("\n🎉 Question bank functionality is ready!")
        print("\nNext steps:")
        print("1. Start the server: python manage.py runserver")
        print("2. Login as admin/teacher")
        print("3. Navigate to /questions/banks/ to see the comprehensive question bank interface")
    else:
        print("\n❌ Some issues found - please check the setup")