#!/usr/bin/env python
"""
Simple test to check view functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import *
from django.contrib.auth.models import User
from django.test import RequestFactory
from admin_ui.views import course_attendance

def test_simple_view():
    """Test the view with minimal setup"""
    print("🔍 Testing Simple View...")
    print("=" * 50)
    
    try:
        # Get user and assigned course
        user = User.objects.get(username='okechilec1')
        assigned_course = AssignedCourse.objects.get(id=2)
        
        print(f"User: {user.username}")
        print(f"Assigned course: {assigned_course.course.code} (ID: {assigned_course.id})")
        
        # Check user groups
        groups = [g.name for g in user.groups.all()]
        print(f"User groups: {groups}")
        
        # Check if user passes the test
        def lecturer_test(u):
            return u.groups.filter(name='Lecturers').exists()
        
        passes_test = lecturer_test(user)
        print(f"Passes lecturer test: {passes_test}")
        
        # Create request
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = user
        
        print(f"\nCalling view...")
        response = course_attendance(request, assigned_course.id)
        
        print(f"Response type: {type(response)}")
        print(f"Response status: {getattr(response, 'status_code', 'N/A')}")
        
        if hasattr(response, 'url'):
            print(f"Redirect URL: {response.url}")
        
        if hasattr(response, 'context_data'):
            print(f"Context data: {list(response.context_data.keys())}")
        
        print("✅ View test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_view()
