#!/usr/bin/env python
"""
Test script for the Attendance System
This script tests the basic functionality of the attendance system
"""

import os
import sys
import django
from datetime import date, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from admin_ui.models import (
    Course, Student, CourseEnrollment, AssignedCourse, 
    AttendanceSession, AttendanceRecord
)

def test_attendance_system():
    """Test the attendance system functionality"""
    print("🧪 Testing Attendance System...")
    
    try:
        # Check if we have the required models
        print("✅ Models imported successfully")
        
        # Check if we have any courses
        courses = Course.objects.all()
        print(f"📚 Found {courses.count()} courses")
        
        if courses.exists():
            course = courses.first()
            print(f"   - Sample course: {course.code} - {course.title}")
        
        # Check if we have any students
        students = Student.objects.all()
        print(f"👥 Found {students.count()} students")
        
        if students.exists():
            student = students.first()
            print(f"   - Sample student: {student.name} ({student.matric_no})")
        
        # Check if we have any lecturers
        lecturers = User.objects.filter(is_staff=True)
        print(f"👨‍🏫 Found {lecturers.count()} staff users")
        
        if lecturers.exists():
            lecturer = lecturers.first()
            print(f"   - Sample lecturer: {lecturer.username}")
        
        # Check if we have any course enrollments
        enrollments = CourseEnrollment.objects.all()
        print(f"📝 Found {enrollments.count()} course enrollments")
        
        # Check if we have any assigned courses
        assignments = AssignedCourse.objects.all()
        print(f"🔗 Found {assignments.count()} course assignments")
        
        # Check if we have any attendance sessions
        sessions = AttendanceSession.objects.all()
        print(f"📅 Found {sessions.count()} attendance sessions")
        
        # Check if we have any attendance records
        records = AttendanceRecord.objects.all()
        print(f"✅ Found {records.count()} attendance records")
        
        print("\n🎯 Attendance System Status: READY")
        print("\n📋 Next Steps:")
        print("1. Create a lecturer account")
        print("2. Assign courses to the lecturer")
        print("3. Enroll students in courses")
        print("4. Start attendance sessions")
        print("5. Mark attendance for students")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing attendance system: {str(e)}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("\n🔧 Creating sample data...")
    
    try:
        # Create a sample course if none exists
        if not Course.objects.exists():
            course = Course.objects.create(
                code="CS101",
                title="Introduction to Computer Science"
            )
            print(f"✅ Created course: {course.code} - {course.title}")
        else:
            course = Course.objects.first()
            print(f"📚 Using existing course: {course.code} - {course.title}")
        
        # Create a sample lecturer if none exists
        if not User.objects.filter(is_staff=True).exists():
            lecturer = User.objects.create_user(
                username="lecturer1",
                email="lecturer1@example.com",
                password="testpass123",
                is_staff=True
            )
            print(f"✅ Created lecturer: {lecturer.username}")
        else:
            lecturer = User.objects.filter(is_staff=True).first()
            print(f"👨‍🏫 Using existing lecturer: {lecturer.username}")
        
        # Create a sample student if none exists
        if not Student.objects.exists():
            student = Student.objects.create(
                matric_no="2024001",
                name="John Doe",
                department="Computer Science",
                level="100"
            )
            print(f"✅ Created student: {student.name} ({student.matric_no})")
        else:
            student = Student.objects.first()
            print(f"👥 Using existing student: {student.name} ({student.matric_no})")
        
        # Create course assignment
        assignment, created = AssignedCourse.objects.get_or_create(
            lecturer=lecturer,
            course=course,
            session="2024/2025",
            semester="1st Semester"
        )
        if created:
            print(f"✅ Assigned course {course.code} to lecturer {lecturer.username}")
        else:
            print(f"📋 Course assignment already exists")
        
        # Create course enrollment
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=student,
            course=course,
            session="2024/2025",
            semester="1st Semester"
        )
        if created:
            print(f"✅ Enrolled student {student.name} in course {course.code}")
        else:
            print(f"📝 Student enrollment already exists")
        
        # Create attendance session
        session, created = AttendanceSession.objects.get_or_create(
            course=course,
            lecturer=lecturer,
            session="2024/2025",
            semester="1st Semester",
            date=date.today()
        )
        if created:
            print(f"✅ Created attendance session for {course.code} on {date.today()}")
        else:
            print(f"📅 Attendance session already exists")
        
        # Create attendance record
        record, created = AttendanceRecord.objects.get_or_create(
            attendance_session=session,
            student=student,
            defaults={
                'status': 'present',
                'marked_by': lecturer
            }
        )
        if created:
            print(f"✅ Marked {student.name} as present")
        else:
            print(f"✅ Attendance record already exists")
        
        print("\n🎉 Sample data created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Attendance System Test Script")
    print("=" * 40)
    
    # Test the system
    if test_attendance_system():
        print("\n" + "=" * 40)
        
        # Ask if user wants to create sample data
        response = input("\n🤔 Would you like to create sample data? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            create_sample_data()
    
    print("\n✨ Test completed!")
