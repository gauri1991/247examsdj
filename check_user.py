#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/gss/Documents/projects/dts/test_platform')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform.settings')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    user = User.objects.get(username='teststudent')
    print(f"Username: {user.username}")
    print(f"is_superuser: {user.is_superuser}")
    print(f"is_staff: {user.is_staff}")
    print(f"role: {user.role}")
except User.DoesNotExist:
    print("User 'teststudent' not found")
    
    # List all users
    print("\nAll users:")
    for u in User.objects.all():
        print(f"- {u.username}: superuser={u.is_superuser}, staff={u.is_staff}, role={getattr(u, 'role', 'N/A')}")