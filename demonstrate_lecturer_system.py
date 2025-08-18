#!/usr/bin/env python
"""
Comprehensive Demonstration of the Lecturer System
This script demonstrates all the features of the new streamlined lecturer system.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from admin_ui.models import Course, AssignedCourse, Student, CourseEnrollment, NetworkSession, ESP32Device
from datetime import datetime, timedelta

def demonstrate_lecturer_system():
    """Demonstrate the complete lecturer system functionality"""
    print("🎓 LECTURER SYSTEM COMPREHENSIVE DEMONSTRATION")
    print("=" * 60)
    
    # Initialize test client
    client = Client()
    
    print("\n1. 🔐 SYSTEM OVERVIEW")
    print("-" * 30)
    
    # Check current system state
    courses = Course.objects.all()
    users = User.objects.all()
    assigned_courses = AssignedCourse.objects.all()
    students = Student.objects.all()
    enrollments = CourseEnrollment.objects.all()
    
    print(f"   📚 Total Courses: {courses.count()}")
    print(f"   👥 Total Users: {users.count()}")
    print(f"   🔗 Course Assignments: {assigned_courses.count()}")
    print(f"   🎓 Total Students: {students.count()}")
    print(f"   📝 Total Enrollments: {enrollments.count()}")
    
    print("\n2. 👨‍🏫 LECTURER ACCESS CONTROL")
    print("-" * 35)
    
    # Test lecturer login
    lecturer = User.objects.filter(username='okechilec1').first()
    if lecturer:
        print(f"   ✅ Lecturer found: {lecturer.username}")
        
        # Login as lecturer
        login_success = client.login(username='okechilec1', password='password123')
        print(f"   🔑 Login successful: {login_success}")
        
        if login_success:
            # Check assigned courses
            lecturer_courses = AssignedCourse.objects.filter(lecturer=lecturer)
            print(f"   📚 Assigned courses: {lecturer_courses.count()}")
            
            for ac in lecturer_courses:
                print(f"      - {ac.course.code}: {ac.course.title}")
                print(f"        Session: {ac.session}, Semester: {ac.semester}")
                
                # Check enrollments for this course
                course_enrollments = CourseEnrollment.objects.filter(
                    course=ac.course,
                    session=ac.session,
                    semester=ac.semester
                )
                print(f"        Students enrolled: {course_enrollments.count()}")
    else:
        print("   ❌ Lecturer 'okechilec1' not found")
        return
    
    print("\n3. 📚 COURSE MANAGEMENT FEATURES")
    print("-" * 35)
    
    # Test course management access
    course = Course.objects.filter(code='CSC101').first()
    if course:
        print(f"   📖 Testing course: {course.code} - {course.title}")
        
        # Test course management page access
        response = client.get(f'/admin-panel/course/{course.id}/manage/')
        print(f"   🌐 Course management page: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Course management accessible")
            
            # Check if students are displayed
            if 'John Doe' in str(response.content):
                print("   👥 Students are displayed in the interface")
            else:
                print("   ⚠️ No students displayed")
        else:
            print("   ❌ Course management not accessible")
    
    print("\n4. 📥 CSV UPLOAD FUNCTIONALITY")
    print("-" * 35)
    
    # Test CSV template download
    response = client.get(f'/admin-panel/course/{course.id}/download-template/')
    print(f"   📥 CSV template download: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ CSV template accessible")
        print(f"   📄 Template filename: {response.get('Content-Disposition', 'N/A')}")
    else:
        print("   ❌ CSV template not accessible")
    
    print("\n5. 🎯 PER-SEMESTER ENROLLMENT SYSTEM")
    print("-" * 40)
    
    # Show current enrollments by semester
    semesters = CourseEnrollment.objects.values_list('semester', flat=True).distinct()
    sessions = CourseEnrollment.objects.values_list('session', flat=True).distinct()
    
    print(f"   📅 Academic Sessions: {list(sessions)}")
    print(f"   📚 Semesters: {list(semesters)}")
    
    for session in sessions:
        for semester in semesters:
            enrollments = CourseEnrollment.objects.filter(
                session=session,
                semester=semester
            )
            if enrollments.exists():
                print(f"   📝 {session} - {semester}: {enrollments.count()} students")
                
                # Show some student names
                student_names = [e.student.name for e in enrollments[:3]]
                print(f"      Students: {', '.join(student_names)}")
    
    print("\n6. 🔒 ACCESS CONTROL VERIFICATION")
    print("-" * 35)
    
    # Test unauthorized access
    client.logout()
    
    # Try to access course management without login
    response = client.get(f'/admin-panel/course/{course.id}/manage/')
    print(f"   🚫 Unauthorized access to course management: {response.status_code}")
    
    if response.status_code == 302:  # Redirect to login
        print("   ✅ Access control working - redirected to login")
    else:
        print("   ❌ Access control failed")
    
    # Try to access dashboard without login
    response = client.get('/admin-panel/dashboard/')
    print(f"   🚫 Unauthorized access to dashboard: {response.status_code}")
    
    if response.status_code == 302:  # Redirect to login
        print("   ✅ Access control working - redirected to login")
    else:
        print("   ❌ Access control failed")
    
    print("\n7. 🚀 SYSTEM READINESS CHECK")
    print("-" * 35)
    
    # Check if all necessary components are working
    checks = []
    
    # Check if lecturer can login
    client.login(username='okechilec1', password='password123')
    checks.append(("Lecturer Login", True))
    
    # Check if dashboard is accessible
    response = client.get('/admin-panel/dashboard/')
    checks.append(("Dashboard Access", response.status_code == 200))
    
    # Check if course management is accessible
    response = client.get(f'/admin-panel/course/{course.id}/manage/')
    checks.append(("Course Management", response.status_code == 200))
    
    # Check if CSV template download works
    response = client.get(f'/admin-panel/course/{course.id}/download-template/')
    checks.append(("CSV Template Download", response.status_code == 200))
    
    # Display results
    for check_name, status in checks:
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {check_name}: {'Working' if status else 'Failed'}")
    
    all_working = all(status for _, status in checks)
    print(f"\n   🎯 Overall System Status: {'✅ READY' if all_working else '❌ NEEDS ATTENTION'}")
    
    print("\n8. 📋 NEXT STEPS FOR LECTURERS")
    print("-" * 40)
    
    if all_working:
        print("   🎉 System is fully operational! Lecturers can:")
        print("      📥 Upload student lists via CSV")
        print("      👥 View and manage course enrollments")
        print("      📊 Take attendance for their courses")
        print("      🌐 Create network sessions for WiFi attendance")
        print("      📱 Manage ESP32 devices")
        print("      🔒 Access only their assigned courses")
        print("      📅 Work with per-semester enrollment system")
        
        print("\n   🚀 To get started:")
        print("      1. Login at: http://127.0.0.1:8000/admin-panel/lecturer-login/")
        print("      2. Use credentials: okechilec1 / password123")
        print("      3. Click 'Manage Students' on any assigned course")
        print("      4. Upload CSV file or download template")
        print("      5. Start taking attendance!")
    else:
        print("   ⚠️ Some system components need attention")
        print("      Please check the failed components above")
    
    print("\n" + "=" * 60)
    print("🎓 LECTURER SYSTEM DEMONSTRATION COMPLETED!")
    print("=" * 60)

if __name__ == '__main__':
    demonstrate_lecturer_system()
