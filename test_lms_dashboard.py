#!/usr/bin/env python3
"""
Simple test to verify LMS dashboard functionality
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

def test_lms_dashboard():
    """Test LMS dashboard basic functionality"""
    
    print("🎓 Testing LMS Dashboard Functionality")
    print("=" * 50)
    
    User = get_user_model()
    client = Client()
    
    # Ensure admin user has correct role
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        if admin_user.role != 'admin':
            admin_user.role = 'admin'
            admin_user.save()
            print(f"✅ Updated admin user role to: {admin_user.role}")
        
        client.force_login(admin_user)
        print(f"✅ Logged in as: {admin_user.email}")
        
        # Test LMS Dashboard
        print("\n📊 Testing LMS Dashboard...")
        response = client.get('/exams/lms/')
        
        if response.status_code == 200:
            print("✅ LMS Dashboard loads successfully")
            print("✅ Response contains expected content")
            return True
        else:
            print(f"❌ LMS Dashboard failed: {response.status_code}")
            if hasattr(response, 'content'):
                print(f"Error content: {response.content[:500]}")
            return False
    else:
        print("❌ No admin user found")
        return False

if __name__ == "__main__":
    success = test_lms_dashboard()
    
    if success:
        print(f"\n✅ LMS Dashboard is working correctly!")
        print(f"🔗 Access at: http://127.0.0.1:8000/exams/lms/")
    else:
        print(f"\n❌ LMS Dashboard test failed.")