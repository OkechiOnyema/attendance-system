#!/usr/bin/env python
"""
Test script for lecturer system functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from admin_ui.models import Course, AssignedCourse, Student, CourseEnrollment

def test_lecturer_system():
    """Test the complete lecturer system"""
    print("🧪 Testing Lecturer System...")
    
    # Check if we have the necessary data
    print("\n1. Checking system data...")
    
    # Check courses
    courses = Course.objects.all()
    print(f"   Courses: {[c.code for c in courses]}")
    
    # Check assigned courses
    assigned_courses = AssignedCourse.objects.all()
    print(f"   Assigned Courses: {[(ac.course.code, ac.lecturer.username, ac.session, ac.semester) for ac in assigned_courses]}")
    
    # Check users
    users = User.objects.all()
    print(f"   Users: {[u.username for u in users]}")
    
    # Test lecturer login
    print("\n2. Testing lecturer login...")
    client = Client()
    
    # Try to access course management without login (should redirect to login)
    response = client.get('/admin-panel/course/1/manage/')
    print(f"   Course management without login: {response.status_code}")
    
    # Try to login as lecturer
    lecturer = User.objects.filter(username='okechilec1').first()
    if lecturer:
        print(f"   Testing login for lecturer: {lecturer.username}")
        
        # Login
        login_success = client.login(username='okechilec1', password='password123')
        print(f"   Login successful: {login_success}")
        
        if login_success:
            # Try to access dashboard
            response = client.get('/admin-panel/dashboard/')
            print(f"   Dashboard access: {response.status_code}")
            
            # Try to access course management
            response = client.get('/admin-panel/course/1/manage/')
            print(f"   Course management with login: {response.status_code}")
            
            # Check if lecturer is assigned to course 1
            assigned = AssignedCourse.objects.filter(
                lecturer=lecturer,
                course_id=1
            ).first()
            
            if assigned:
                print(f"   Lecturer assigned to course: {assigned.course.code}")
                print(f"   Session: {assigned.session}, Semester: {assigned.semester}")
            else:
                print("   Lecturer not assigned to course 1")
        else:
            print("   Login failed - need to set password")
    else:
        print("   Lecturer 'okechilec1' not found")
    
    print("\n3. Testing course enrollment system...")
    
    # Check if there are any enrolled students
    enrollments = CourseEnrollment.objects.all()
    print(f"   Total enrollments: {enrollments.count()}")
    
    for enrollment in enrollments:
        print(f"   - {enrollment.student.name} in {enrollment.course.code} ({enrollment.session}, {enrollment.semester})")
    
    print("\n✅ Lecturer system test completed!")

if __name__ == '__main__':
    test_lecturer_system()
