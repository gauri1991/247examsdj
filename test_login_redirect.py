#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
django.setup()

from django.test import Client
from users.models import User

def test_login_redirect():
    client = Client()
    
    # Test the login form submission
    print("Testing login form submission...")
    
    # First, let's check if admin user exists
    try:
        admin = User.objects.get(username='admin')
        print(f"Admin user found: {admin.email}")
    except User.DoesNotExist:
        print("Admin user not found!")
        return
    
    # Test POST to login URL
    response = client.post('/users/login/', {
        'email': 'admin@example.com',
        'password': 'admin123'
    }, follow=False)
    
    print(f"Response status: {response.status_code}")
    print(f"Response location: {response.get('Location', 'No redirect')}")
    
    if response.status_code == 302:
        print("Redirect detected! Following redirect...")
        response = client.get(response['Location'])
        print(f"Final status: {response.status_code}")
        print(f"Final URL: {response.wsgi_request.path}")
    
    # Check if user is authenticated
    if '_auth_user_id' in client.session:
        print(f"User authenticated: Yes (ID: {client.session['_auth_user_id']})")
    else:
        print("User authenticated: No")
    
    # Try to access dashboard directly
    print("\nTrying to access dashboard directly...")
    dashboard_response = client.get('/dashboard/')
    print(f"Dashboard access status: {dashboard_response.status_code}")

if __name__ == '__main__':
    test_login_redirect()