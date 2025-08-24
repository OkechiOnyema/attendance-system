#!/usr/bin/env python
"""
Test script to verify attendance system functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import *
from django.utils import timezone

def test_attendance_system():
    """Test the complete attendance system"""
    print("🔍 Testing Attendance System...")
    print("=" * 50)
    
    # Test 1: Check assigned courses
    print("\n1. Assigned Courses:")
    assigned_courses = AssignedCourse.objects.all()
    for ac in assigned_courses:
        print(f"   - {ac.course.code} → {ac.lecturer.username} ({ac.session}, {ac.semester})")
    
    # Test 2: Check attendance sessions
    print("\n2. Attendance Sessions:")
    sessions = AttendanceSession.objects.all().order_by('-date', '-time')
    for session in sessions:
        print(f"   - {session.course.code} on {session.date} at {session.time} (ID: {session.id})")
    
    # Test 3: Check attendance records
    print("\n3. Attendance Records:")
    records = AttendanceRecord.objects.all().select_related('student', 'attendance_session')
    for record in records:
        print(f"   - {record.student.name} ({record.student.matric_no}) - {record.status}")
        print(f"     Session: {record.attendance_session.date} at {record.attendance_session.time}")
        print(f"     Marked by: {record.marked_by.username if record.marked_by else 'System'}")
    
    # Test 4: Test the specific query used in the view
    print("\n4. Testing View Query:")
    if assigned_courses.exists():
        assigned = assigned_courses.first()
        print(f"   Testing for: {assigned.course.code} - {assigned.session} {assigned.semester}")
        
        # This is the exact query used in the view
        attendance_records = AttendanceRecord.objects.filter(
            attendance_session__course=assigned.course,
            attendance_session__session=assigned.session,
            attendance_session__semester=assigned.semester
        ).select_related('student', 'attendance_session', 'marked_by')
        
        print(f"   Records found: {attendance_records.count()}")
        for record in attendance_records:
            print(f"     - {record.student.name}: {record.status} on {record.attendance_session.date} at {record.attendance_session.time}")
    
    # Test 5: Check for any data inconsistencies
    print("\n5. Data Consistency Check:")
    for session in sessions:
        session_records = AttendanceRecord.objects.filter(attendance_session=session)
        print(f"   Session {session.id}: {session_records.count()} records")
        if session_records.count() == 0:
            print(f"     ⚠️  Warning: Session {session.id} has no attendance records!")
    
    print("\n" + "=" * 50)
    print("✅ Attendance system test completed!")

if __name__ == "__main__":
    test_attendance_system()
