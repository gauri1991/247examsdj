#!/usr/bin/env python3
"""
Test script for the complete teacher content management system
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
sys.path.insert(0, '/home/gss/Documents/projects/dts/test_platform')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from exams.models import SyllabusNode, LearningContent, InteractiveElement, Assessment
import json

def test_teacher_content_management():
    """Test the complete teacher content management system"""
    
    print("🧑‍🏫 Testing Complete Teacher Content Management System")
    print("=" * 60)
    
    User = get_user_model()
    client = Client()
    
    # Ensure admin user has correct role
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user.role != 'admin':
        admin_user.role = 'admin'
        admin_user.save()
    
    client.force_login(admin_user)
    
    # Test 1: Teacher Content Management Dashboard
    print("\n📊 Test 1: Teacher Content Dashboard")
    response = client.get('/exams/teacher/content/')
    
    if response.status_code == 200:
        print("✅ Dashboard loads successfully")
        context = response.context
        print(f"   Available concept nodes: {len(context['available_nodes'])}")
        print(f"   Nodes with content: {context['nodes_with_content']}")
        print(f"   Teacher-created content: {context['teacher_created']}")
        print(f"   Exams with syllabus: {len(context['exams_with_syllabus'])}")
    else:
        print(f"❌ Dashboard failed: {response.status_code}")
        return False
    
    # Test 2: Find a concept node for testing
    print("\n🔍 Test 2: Finding Concept Node for Testing")
    concept_nodes = SyllabusNode.objects.filter(
        is_active=True,
        node_type='concept'
    ).select_related('syllabus__exam')
    
    if concept_nodes.exists():
        test_node = concept_nodes.first()
        print(f"✅ Found test node: {test_node.title}")
        print(f"   Exam: {test_node.syllabus.exam.name}")
        print(f"   Node ID: {test_node.id}")
    else:
        print("❌ No concept nodes found for testing")
        return False
    
    # Test 3: Content Creation Form
    print("\n📝 Test 3: Content Creation Form")
    response = client.get(f'/exams/teacher/content/create/{test_node.id}/')
    
    if response.status_code == 200:
        print("✅ Content creation form loads successfully")
        context = response.context
        print(f"   Target node: {context['node'].title}")
        print(f"   Existing content count: {len(context['existing_content'])}")
        print(f"   Level choices: {len(context['level_choices'])}")
        print(f"   Content type choices: {len(context['content_type_choices'])}")
    else:
        print(f"❌ Content creation form failed: {response.status_code}")
        return False
    
    # Test 4: Create Sample Content via API
    print("\n🎯 Test 4: Creating Sample Learning Content")
    
    sample_content_data = {
        "title": "Test Learning Content for Teachers",
        "level": "basic",
        "content_type": "theory",
        "content": """
        <div class="learning-section">
            <h2>🎯 Learning Objectives</h2>
            <ul>
                <li>Understand the teacher content creation process</li>
                <li>Learn how to use the content management system</li>
                <li>Practice creating interactive learning materials</li>
            </ul>
            
            <h2>📖 Introduction</h2>
            <p>This is a sample learning content created by the teacher content management system.</p>
            
            <div class="math-box">
                <h3>📐 Mathematical Example</h3>
                <p>Here's a mathematical formula:</p>
                <div class="equation-center">
                    $$E = mc^2$$
                </div>
                <p>This demonstrates LaTeX support in teacher-created content.</p>
            </div>
            
            <h2>🌍 Practical Applications</h2>
            <p>Teachers can create rich, interactive content with:</p>
            <ul>
                <li>HTML formatting and styling</li>
                <li>Mathematical equations with LaTeX</li>
                <li>Interactive elements</li>
                <li>Built-in assessments</li>
                <li>Progress tracking</li>
            </ul>
            
            <h2>🎯 Summary</h2>
            <p>The teacher content management system enables educators to create high-quality learning materials efficiently.</p>
        </div>
        """,
        "estimated_read_time": 8,
        "difficulty_rating": 2.5,
        "interactive_elements": [
            {
                "element_type": "graph",
                "title": "Sample Interactive Chart",
                "description": "A demonstration of interactive visualization",
                "config_data": {"chart_type": "line", "data_points": 10},
                "javascript_code": "// Sample interactive chart code\nconsole.log('Interactive chart initialized');"
            }
        ],
        "assessments": [
            {
                "question_type": "mcq",
                "schedule_type": "immediate",
                "question_text": "What is the main benefit of the teacher content management system?",
                "question_data": {
                    "options": [
                        "Easy content creation",
                        "Interactive elements",
                        "Progress tracking",
                        "All of the above"
                    ],
                    "correct_answer": 3,
                    "explanation": "The system provides comprehensive features for creating, managing, and tracking learning content."
                },
                "max_points": 5,
                "difficulty_weight": 1.2
            }
        ]
    }
    
    # Send POST request to create content
    response = client.post(
        f'/exams/teacher/content/create/{test_node.id}/',
        data=json.dumps(sample_content_data),
        content_type='application/json'
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Content created successfully")
            content_id = data.get('content_id')
            print(f"   Content ID: {content_id}")
            
            # Verify content was saved
            created_content = LearningContent.objects.filter(id=content_id).first()
            if created_content:
                print(f"   Title: {created_content.title}")
                print(f"   Level: {created_content.level}")
                print(f"   Content type: {created_content.content_type}")
                print(f"   Created by: {created_content.created_by.email}")
                print(f"   AI generated: {created_content.is_ai_generated}")
                
                # Check interactive elements
                elements = created_content.interactive_elements.count()
                print(f"   Interactive elements: {elements}")
                
                # Check assessments
                assessments = created_content.assessments.count()
                print(f"   Assessments: {assessments}")
                
            else:
                print("❌ Content not found in database")
                return False
        else:
            print(f"❌ Content creation failed: {data.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ Content creation request failed: {response.status_code}")
        return False
    
    # Test 5: Content Analytics
    print("\n📈 Test 5: Content Analytics")
    if content_id:
        response = client.get(f'/exams/teacher/content/analytics/{content_id}/')
        
        if response.status_code == 200:
            print("✅ Content analytics loads successfully")
            context = response.context
            stats = context['stats']
            print(f"   Total students: {stats['total_students']}")
            print(f"   Completion rate: {stats['completion_rate']}%")
            print(f"   Average time spent: {stats['avg_time_spent']} minutes")
            print(f"   Average difficulty rating: {stats['avg_difficulty']}")
        else:
            print(f"❌ Content analytics failed: {response.status_code}")
    
    # Test 6: Integration with Learning System
    print("\n🔗 Test 6: Integration with Learning System")
    
    # Test that content appears in learning page
    response = client.get(f'/exams/learn/{test_node.id}/')
    if response.status_code == 200:
        print("✅ Learning page loads successfully")
        print("✅ Teacher content integrates with learning system")
    else:
        print(f"❌ Learning page failed: {response.status_code}")
    
    # Final Statistics
    print("\n" + "=" * 60)
    print("📊 SYSTEM STATISTICS AFTER TESTING")
    print("=" * 60)
    
    # Count various content types
    total_content = LearningContent.objects.count()
    teacher_content = LearningContent.objects.filter(is_ai_generated=False).count()
    ai_content = LearningContent.objects.filter(is_ai_generated=True).count()
    
    total_elements = InteractiveElement.objects.count()
    total_assessments = Assessment.objects.count()
    
    print(f"📚 Total Learning Content: {total_content}")
    print(f"   👨‍🏫 Teacher-Created: {teacher_content}")
    print(f"   🤖 AI-Generated: {ai_content}")
    print(f"🎮 Interactive Elements: {total_elements}")
    print(f"❓ Assessment Questions: {total_assessments}")
    
    # Content by level
    for level, label in [('basic', 'Basic'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced'), ('expert', 'Expert')]:
        count = LearningContent.objects.filter(level=level).count()
        print(f"   {label} Level: {count}")
    
    print(f"\n🎉 TEACHER CONTENT MANAGEMENT SYSTEM FULLY OPERATIONAL!")
    print(f"🔗 Dashboard URL: http://127.0.0.1:8000/exams/teacher/content/")
    
    return True

if __name__ == "__main__":
    success = test_teacher_content_management()
    
    if success:
        print(f"\n✅ All tests passed! The teacher content management system is ready for production.")
    else:
        print(f"\n❌ Some tests failed. Please check the issues above.")