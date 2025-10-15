#!/usr/bin/env python
"""
Script to create admin users for the Django application
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

def create_admin_user(username, password, email=None):
    """Create a new admin user"""
    try:
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"User '{username}' already exists!")
            user = User.objects.get(username=username)
            # Update to superuser if not already
            if not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.save()
                print(f"Updated '{username}' to superuser status.")
            else:
                print(f"'{username}' is already a superuser.")
            return user
        
        # Create new superuser
        if not email:
            email = f"{username}@example.com"
        
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        print(f"Successfully created admin user '{username}'")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Login at: http://dts.com:8000/admin/")
        
        return user
        
    except IntegrityError as e:
        print(f"Error creating user: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    print("Creating admin user...")
    create_admin_user(
        username="vk1",
        password="admin123",
        email="vk1@example.com"
    )
    
    print("\nAdmin user details:")
    print("-" * 40)
    print("Username: vk1")
    print("Password: admin123")
    print("Access admin panel at: http://dts.com:8000/admin/")
    print("-" * 40)