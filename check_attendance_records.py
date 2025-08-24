#!/usr/bin/env python3
"""
Check attendance records and ESP32 device status in Django database
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import (
    Student, Course, CourseEnrollment, 
    AttendanceSession, AttendanceRecord, 
    ESP32Device, NetworkSession
)
from django.utils import timezone

def check_database_status():
    """Check the current status of the database"""
    
    print("🔍 Checking Database Status")
    print("=" * 50)
    
    # Check students
    students = Student.objects.all()
    print(f"📚 Total Students: {students.count()}")
    
    # Check courses
    courses = Course.objects.all()
    print(f"📖 Total Courses: {courses.count()}")
    
    # Check enrollments
    enrollments = CourseEnrollment.objects.all()
    print(f"📝 Total Enrollments: {enrollments.count()}")
    
    # Check ESP32 devices
    esp32_devices = ESP32Device.objects.all()
    print(f"🛰️ Total ESP32 Devices: {esp32_devices.count()}")
    
    # Check network sessions
    network_sessions = NetworkSession.objects.all()
    print(f"🌐 Total Network Sessions: {network_sessions.count()}")
    
    # Check attendance sessions
    attendance_sessions = AttendanceSession.objects.all()
    print(f"📅 Total Attendance Sessions: {attendance_sessions.count()}")
    
    # Check attendance records
    attendance_records = AttendanceRecord.objects.all()
    print(f"✅ Total Attendance Records: {attendance_records.count()}")
    
    print()

def check_esp32_devices():
    """Check ESP32 device details"""
    
    print("🛰️ ESP32 Device Details")
    print("=" * 50)
    
    esp32_devices = ESP32Device.objects.all()
    
    if esp32_devices.count() == 0:
        print("❌ No ESP32 devices found in database")
        return
    
    for device in esp32_devices:
        print(f"Device ID: {device.device_id}")
        print(f"Name: {device.device_name}")
        print(f"SSID: {device.ssid}")
        print(f"Location: {device.location}")
        print(f"Active: {device.is_active}")
        print(f"Last Seen: {device.last_seen}")
        print(f"Last Heartbeat: {device.last_heartbeat}")
        print("-" * 30)

def check_attendance_records():
    """Check recent attendance records"""
    
    print("✅ Recent Attendance Records")
    print("=" * 50)
    
    # Get today's records
    today = timezone.now().date()
    today_records = AttendanceRecord.objects.filter(
        attendance_session__date=today
    ).select_related('student', 'attendance_session', 'esp32_device')
    
    if today_records.count() == 0:
        print(f"❌ No attendance records found for today ({today})")
        return
    
    print(f"📅 Found {today_records.count()} attendance records for today:")
    print()
    
    for record in today_records:
        print(f"Student: {record.student.name} ({record.student.matric_no})")
        print(f"Course: {record.attendance_session.course.code} - {record.attendance_session.course.title}")
        print(f"Status: {record.status}")
        print(f"Network Verified: {record.network_verified}")
        print(f"Device MAC: {record.device_mac}")
        print(f"ESP32 Device: {record.esp32_device.device_id if record.esp32_device else 'None'}")
        print(f"Marked At: {record.marked_at}")
        print("-" * 30)

def check_course_enrollments():
    """Check course enrollments for specific course"""
    
    print("📝 Course Enrollments for CSC101")
    print("=" * 50)
    
    try:
        course = Course.objects.get(code="CSC101")
        enrollments = CourseEnrollment.objects.filter(course=course)
        
        print(f"Course: {course.code} - {course.title}")
        print(f"Total Enrollments: {enrollments.count()}")
        print()
        
        for enrollment in enrollments:
            print(f"Student: {enrollment.student.name} ({enrollment.student.matric_no})")
            print(f"Session: {enrollment.session}")
            print(f"Semester: {enrollment.semester}")
            print(f"Enrolled: {enrollment.enrolled_on}")
            print("-" * 20)
            
    except Course.DoesNotExist:
        print("❌ Course CSC101 not found")

def create_test_data():
    """Create test data if none exists"""
    
    print("🔧 Creating Test Data")
    print("=" * 50)
    
    # Check if we need to create test data
    if Student.objects.count() == 0:
        print("Creating test student...")
        student = Student.objects.create(
            name="Test Student",
            matric_no="SEN/19/2345",
            email="test@example.com"
        )
        print(f"✅ Created student: {student.name}")
    
    if Course.objects.count() == 0:
        print("Creating test course...")
        course = Course.objects.create(
            code="CSC101",
            title="Introduction to Computer Science",
            credits=3
        )
        print(f"✅ Created course: {course.code}")
    
    if CourseEnrollment.objects.count() == 0:
        print("Creating test enrollment...")
        student = Student.objects.first()
        course = Course.objects.first()
        enrollment = CourseEnrollment.objects.create(
            student=student,
            course=course,
            session="2024/2025",
            semester="1st Semester"
        )
        print(f"✅ Created enrollment: {enrollment}")
    
    if ESP32Device.objects.count() == 0:
        print("Creating test ESP32 device...")
        esp32_device = ESP32Device.objects.create(
            device_id="ESP32_PRESENCE_001",
            device_name="Test ESP32 Device",
            ssid="Classroom_Attendance",
            password="",
            location="Test Classroom",
            is_active=True
        )
        print(f"✅ Created ESP32 device: {esp32_device.device_id}")

if __name__ == "__main__":
    print("🧪 Django Database Status Checker")
    print("=" * 50)
    
    try:
        # Check current status
        check_database_status()
        
        # Check specific areas
        check_esp32_devices()
        check_attendance_records()
        check_course_enrollments()
        
        # Create test data if needed
        if Student.objects.count() == 0 or Course.objects.count() == 0:
            print("\n" + "=" * 50)
            create_test_data()
            print("\n" + "=" * 50)
            check_database_status()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
