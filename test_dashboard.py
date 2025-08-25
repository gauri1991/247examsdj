#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
django.setup()

from django.test import Client
from users.models import User

def test_dashboard():
    client = Client()
    
    try:
        # Get the admin user
        admin_user = User.objects.get(username='admin')
        
        # Login as admin
        login_success = client.login(username='admin@example.com', password='admin123')
        print(f"Login successful: {login_success}")
        
        if login_success:
            print("Testing dashboard...")
            response = client.get('/dashboard/')
            print(f"Dashboard: {response.status_code}")
            
            if response.status_code != 200:
                print("Dashboard content:")
                print(response.content.decode()[:500])
        else:
            print("Login failed, testing login with username...")
            login_success = client.login(username='admin', password='admin123')
            print(f"Login with username successful: {login_success}")
            
            if login_success:
                response = client.get('/dashboard/')
                print(f"Dashboard: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_dashboard()