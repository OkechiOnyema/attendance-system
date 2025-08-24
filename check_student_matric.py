#!/usr/bin/env python3
"""
Check student matric numbers in database
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import Student, Course, CourseEnrollment

def check_students():
    """Check all students in database"""
    
    print("👥 All Students in Database")
    print("=" * 50)
    
    students = Student.objects.all()
    
    if students.count() == 0:
        print("❌ No students found")
        return
    
    for student in students:
        print(f"Name: {student.name}")
        print(f"Matric No: {student.matric_no}")
        print("-" * 30)

def check_course_enrollments():
    """Check course enrollments"""
    
    print("\n📚 Course Enrollments")
    print("=" * 50)
    
    enrollments = CourseEnrollment.objects.select_related('student', 'course').all()
    
    if enrollments.count() == 0:
        print("❌ No enrollments found")
        return
    
    for enrollment in enrollments:
        print(f"Student: {enrollment.student.name} ({enrollment.student.matric_no})")
        print(f"Course: {enrollment.course.code} - {enrollment.course.title}")
        print(f"Session: {enrollment.session}")
        print(f"Semester: {enrollment.semester}")
        print("-" * 30)

if __name__ == "__main__":
    check_students()
    check_course_enrollments()
