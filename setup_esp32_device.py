#!/usr/bin/env python3
"""
ESP32 Device Setup Script

This script creates an ESP32 device and network session for testing
the ESP32 access point functionality.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import ESP32Device, NetworkSession, Course, User
from django.utils import timezone
from datetime import datetime, timedelta

def create_esp32_device():
    """Create an ESP32 device for testing"""
    print("🔧 Creating ESP32 Device...")
    
    # Check if device already exists
    device_id = 'ESP32_CS101_001'
    try:
        device = ESP32Device.objects.get(device_id=device_id)
        print(f"✅ ESP32 Device already exists: {device}")
        return device
    except ESP32Device.DoesNotExist:
        pass
    
    # Create new ESP32 device
    device = ESP32Device.objects.create(
        device_id=device_id,
        device_name='CS101 Classroom ESP32',
        ssid='CS101_Attendance',
        password='',
        location='Computer Science Lab 1',
        is_active=True
    )
    
    print(f"✅ ESP32 Device created: {device}")
    return device

def create_network_session(esp32_device):
    """Create a network session for testing"""
    print("🌐 Creating Network Session...")
    
    # Get the first course
    try:
        course = Course.objects.first()
        print(f"📚 Using course: {course}")
    except Course.DoesNotExist:
        print("❌ No courses found. Please create a course first.")
        return None
    
    # Get the first lecturer
    try:
        lecturer = User.objects.filter(is_staff=True).first()
        print(f"👨‍🏫 Using lecturer: {lecturer}")
    except User.DoesNotExist:
        print("❌ No lecturers found. Please create a lecturer first.")
        return None
    
    # Check if active session already exists
    active_session = NetworkSession.objects.filter(
        esp32_device=esp32_device,
        is_active=True
    ).first()
    
    if active_session:
        print(f"✅ Active session already exists: {active_session}")
        return active_session
    
    # Create new network session
    session = NetworkSession.objects.create(
        esp32_device=esp32_device,
        course=course,
        lecturer=lecturer,
        session='2024/2025',
        semester='1st Semester',
        date=timezone.now().date(),
        start_time=timezone.now(),
        is_active=True
    )
    
    print(f"✅ Network Session created: {session}")
    return session

def print_system_status():
    """Print current system status"""
    print("\n📊 System Status")
    print("=" * 50)
    
    # ESP32 Devices
    devices = ESP32Device.objects.all()
    print(f"ESP32 Devices: {devices.count()}")
    for device in devices:
        print(f"  - {device.device_id}: {device.device_name} ({'Active' if device.is_active else 'Inactive'})")
    
    # Network Sessions
    sessions = NetworkSession.objects.all()
    print(f"\nNetwork Sessions: {sessions.count()}")
    for session in sessions:
        status = "Active" if session.is_active else "Inactive"
        print(f"  - {session.course.code} ({status}): {session.date}")
    
    # Courses
    courses = Course.objects.all()
    print(f"\nCourses: {courses.count()}")
    for course in courses:
        print(f"  - {course.code}: {course.title}")
    
    # Users
    users = User.objects.filter(is_staff=True)
    print(f"\nStaff Users: {users.count()}")
    for user in users:
        print(f"  - {user.username}: {user.get_full_name() or 'No name'}")

def main():
    """Main setup function"""
    print("🚀 ESP32 Device Setup")
    print("=" * 30)
    
    try:
        # Create ESP32 device
        esp32_device = create_esp32_device()
        
        # Create network session
        network_session = create_network_session(esp32_device)
        
        # Print system status
        print_system_status()
        
        print("\n🎉 Setup Complete!")
        print("=" * 20)
        print("Next steps:")
        print("1. Upload esp32_attendance.ino to your ESP32")
        print("2. Power up ESP32 and connect to ESP32_Attendance WiFi")
        print("3. Start Django server on ESP32 network")
        print("4. Test the complete system")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
