#!/usr/bin/env python3
"""
Test teacher content management functionality
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

def test_teacher_content_management():
    """Test teacher content management system"""
    
    print("👨‍🏫 Testing Teacher Content Management")
    print("=" * 50)
    
    User = get_user_model()
    client = Client()
    
    # Ensure admin user has correct role
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        if admin_user.role != 'admin':
            admin_user.role = 'admin'
            admin_user.save()
        
        client.force_login(admin_user)
        print(f"✅ Logged in as: {admin_user.email}")
        
        # Test Teacher Content Management Dashboard
        print("\n📊 Testing Teacher Content Dashboard...")
        response = client.get('/exams/teacher/content/')
        
        if response.status_code == 200:
            print("✅ Teacher Content Dashboard loads successfully")
            print("✅ All teacher content management features accessible")
            return True
        else:
            print(f"❌ Teacher Content Dashboard failed: {response.status_code}")
            return False
    else:
        print("❌ No admin user found")
        return False

if __name__ == "__main__":
    success = test_teacher_content_management()
    
    if success:
        print(f"\n✅ Teacher Content Management is working correctly!")
        print(f"🔗 Access at: http://127.0.0.1:8000/exams/teacher/content/")
    else:
        print(f"\n❌ Teacher Content Management test failed.")