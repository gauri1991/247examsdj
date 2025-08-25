#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
django.setup()

from django.test import Client

def test_views():
    client = Client()
    
    try:
        print("Testing home page...")
        response = client.get('/')
        print(f"Home: {response.status_code}")
        
        print("Testing login page...")
        response = client.get('/users/login/')
        print(f"Login: {response.status_code}")
        
        if response.status_code == 500:
            print("Content:", response.content.decode()[:500])
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_views()