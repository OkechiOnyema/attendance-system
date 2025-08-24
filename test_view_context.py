#!/usr/bin/env python
"""
Test script to verify view context and template rendering
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import *
from django.utils import timezone
from django.test import RequestFactory
from django.contrib.auth.models import User
from admin_ui.views import course_attendance

def test_view_context():
    """Test the view context to ensure attendance_records are passed correctly"""
    print("🔍 Testing View Context...")
    print("=" * 50)
    
    # Get a test user and assigned course
    try:
        user = User.objects.filter(groups__name='Lecturers').first()
        if not user:
            user = User.objects.filter(is_staff=True).first()
        
        if not user:
            print("❌ No suitable user found for testing")
            return
        
        print(f"Using user: {user.username}")
        
        # Get an assigned course for this user
        assigned_course = AssignedCourse.objects.filter(lecturer=user).first()
        if not assigned_course:
            print("❌ No assigned course found for this user")
            return
        
        print(f"Testing with course: {assigned_course.course.code}")
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get(f'/course/{assigned_course.id}/attendance/')
        request.user = user
        
        # Call the view
        print("\nCalling course_attendance view...")
        response = course_attendance(request, assigned_course.id)
        
        # Check if it's a render response
        if hasattr(response, 'context_data'):
            context = response.context_data
        elif hasattr(response, 'context'):
            context = response.context
        else:
            print("❌ Response doesn't have context data")
            return
        
        print(f"\nView context keys: {list(context.keys())}")
        
        # Check attendance_records
        if 'attendance_records' in context:
            records = context['attendance_records']
            print(f"\n✅ attendance_records found in context")
            print(f"   Type: {type(records)}")
            print(f"   Count: {records.count() if hasattr(records, 'count') else len(records)}")
            
            # Show first few records
            for i, record in enumerate(records[:3]):
                print(f"   Record {i+1}: {record.student.name} - {record.status}")
                print(f"     Session: {record.attendance_session.date} at {record.attendance_session.time}")
        else:
            print("❌ attendance_records NOT found in context")
        
        # Check other context variables
        print(f"\nOther context variables:")
        for key, value in context.items():
            if key != 'attendance_records':
                if hasattr(value, 'count'):
                    print(f"   {key}: {value.count()} items")
                else:
                    print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error testing view context: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_view_context()
