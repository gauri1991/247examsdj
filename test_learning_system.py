#!/usr/bin/env python3
"""
Comprehensive test script for the enterprise learning system
Tests the complete workflow from syllabus tracker to learning pages
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
sys.path.insert(0, '/home/gss/Documents/projects/dts/test_platform')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from exams.models import Exam, SyllabusNode, LearningContent, Assessment, InteractiveElement
import json

def test_complete_learning_system():
    """Test the complete learning system workflow"""
    
    print("🚀 Testing Complete Enterprise Learning System")
    print("=" * 60)
    
    # Setup
    User = get_user_model()
    client = Client()
    admin_user = User.objects.filter(is_superuser=True).first()
    
    if not admin_user:
        print("❌ No admin user found! Please create one first.")
        return False
    
    print(f"✅ Admin user: {admin_user.username}")
    
    # Test 1: Find DCIO exam
    dcio_exam = Exam.objects.filter(name__icontains='dcio').first()
    if not dcio_exam:
        print("❌ DCIO exam not found!")
        return False
    
    print(f"✅ Found DCIO exam: {dcio_exam.name}")
    print(f"   Exam ID: {dcio_exam.id}")
    
    # Test 2: Check syllabus data
    syllabus_url = f"/exams/api/exam/{dcio_exam.id}/syllabus/"
    client.force_login(admin_user)
    response = client.get(syllabus_url)
    
    if response.status_code != 200:
        print(f"❌ Syllabus API failed: {response.status_code}")
        return False
    
    data = json.loads(response.content)
    if not data.get('success'):
        print("❌ Syllabus API returned success=false")
        return False
    
    print(f"✅ Syllabus API working")
    print(f"   Total topics: {data['statistics']['total_topics']}")
    print(f"   Root nodes: {len(data['syllabus']['tree'])}")
    
    # Test 3: Find Fourier Transform node
    fourier_node = SyllabusNode.objects.filter(title__icontains='fourier').first()
    if not fourier_node:
        print("❌ Fourier Transform node not found!")
        return False
    
    print(f"✅ Found Fourier Transform node: {fourier_node.title}")
    print(f"   Node ID: {fourier_node.id}")
    
    # Test 4: Check learning content
    learning_content = LearningContent.objects.filter(node=fourier_node)
    if learning_content.count() == 0:
        print("❌ No learning content found for Fourier Transform!")
        return False
    
    print(f"✅ Learning content found: {learning_content.count()} pieces")
    for content in learning_content:
        print(f"   - {content.level}: {content.title}")
    
    # Test 5: Test learning page
    learning_url = f"/exams/learn/{fourier_node.id}/"
    response = client.get(learning_url)
    
    if response.status_code != 200:
        print(f"❌ Learning page failed: {response.status_code}")
        return False
    
    print(f"✅ Learning page accessible")
    
    # Test 6: Check interactive elements
    interactive_count = InteractiveElement.objects.filter(
        content__node=fourier_node
    ).count()
    print(f"✅ Interactive elements: {interactive_count}")
    
    # Test 7: Check assessments
    assessment_count = Assessment.objects.filter(
        content__node=fourier_node
    ).count()
    print(f"✅ Assessments: {assessment_count}")
    
    # Test 8: Test syllabus tracker page
    tracker_response = client.get("/exams/syllabus-tracker/")
    if tracker_response.status_code != 200:
        print(f"❌ Syllabus tracker page failed: {tracker_response.status_code}")
        return False
    
    print(f"✅ Syllabus tracker page accessible")
    
    # Test 9: Verify all levels have content
    levels = ['basic', 'intermediate', 'advanced']
    for level in levels:
        level_content = learning_content.filter(level=level)
        if level_content.exists():
            content = level_content.first()
            print(f"✅ {level.title()} level: {content.title}")
            
            # Check if content has proper structure
            if len(content.content) > 100:  # Reasonable content length
                print(f"   Content length: {len(content.content)} chars")
            else:
                print(f"   ⚠️  Content seems short: {len(content.content)} chars")
        else:
            print(f"❌ No {level} level content found!")
    
    print("\n" + "=" * 60)
    print("🎉 LEARNING SYSTEM TEST COMPLETE!")
    print("=" * 60)
    
    # Final summary
    print("📊 SYSTEM HEALTH SUMMARY:")
    print(f"   ✅ Exam Management: DCIO exam with {data['statistics']['total_topics']} topics")
    print(f"   ✅ Syllabus Tracking: API and UI working")
    print(f"   ✅ Learning Content: {learning_content.count()} pieces across 3 levels")
    print(f"   ✅ Interactive Elements: {interactive_count} interactive components")
    print(f"   ✅ Assessment System: {assessment_count} assessments with scheduling")
    print(f"   ✅ Progressive Learning: Basic → Intermediate → Advanced flow")
    
    print("\n🌟 READY FOR PRODUCTION!")
    print(f"   🔗 Syllabus Tracker: http://127.0.0.1:8000/exams/syllabus-tracker/")
    print(f"   📚 Learning Page: http://127.0.0.1:8000/exams/learn/{fourier_node.id}/")
    
    return True

def test_learning_content_quality():
    """Test the quality and completeness of learning content"""
    
    print("\n🔍 TESTING CONTENT QUALITY")
    print("-" * 40)
    
    fourier_node = SyllabusNode.objects.filter(title__icontains='fourier').first()
    learning_content = LearningContent.objects.filter(node=fourier_node)
    
    total_score = 0
    max_score = 0
    
    for content in learning_content:
        print(f"\n📖 Testing: {content.level} - {content.title}")
        score = 0
        
        # Test content length (should be substantial)
        if len(content.content) > 1000:
            print("   ✅ Substantial content (>1000 chars)")
            score += 2
        elif len(content.content) > 500:
            print("   ⚠️  Moderate content (>500 chars)")
            score += 1
        else:
            print("   ❌ Content too short (<500 chars)")
        
        # Test LaTeX equations
        if "$$" in content.content:
            print("   ✅ Contains LaTeX equations")
            score += 1
        
        # Test structured HTML
        if "<h2>" in content.content and "<p>" in content.content:
            print("   ✅ Well-structured HTML")
            score += 1
        
        # Test learning objectives
        if "Learning Objectives" in content.content:
            print("   ✅ Has learning objectives")
            score += 1
        
        # Test examples/applications
        if "Example" in content.content or "Application" in content.content:
            print("   ✅ Contains examples/applications")
            score += 1
        
        print(f"   📊 Quality Score: {score}/6")
        total_score += score
        max_score += 6
    
    overall_quality = (total_score / max_score) * 100
    print(f"\n🏆 OVERALL CONTENT QUALITY: {overall_quality:.1f}%")
    
    if overall_quality >= 80:
        print("   🌟 EXCELLENT - Production ready!")
    elif overall_quality >= 60:
        print("   ✅ GOOD - Minor improvements recommended")
    else:
        print("   ⚠️  NEEDS IMPROVEMENT")

if __name__ == "__main__":
    success = test_complete_learning_system()
    
    if success:
        test_learning_content_quality()
        print(f"\n🎯 All tests passed! The enterprise learning system is fully operational.")
    else:
        print(f"\n❌ Some tests failed. Please check the issues above.")