#!/usr/bin/env python3
"""
Test Network Session Script

This script creates a network session to test ESP32 dynamic functionality.
"""

import os
import sys
import django
from datetime import timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import NetworkSession, ESP32Device, Course, User, AssignedCourse
from django.utils import timezone

def start_network_session():
    """Start a test network session"""
    try:
        # Get the first ESP32 device
        esp32_device = ESP32Device.objects.first()
        if not esp32_device:
            print("❌ No ESP32 device found! Run setup_esp32.py first.")
            return None
        
        # Get the first course
        course = Course.objects.first()
        if not course:
            print("❌ No course found! Run setup_esp32.py first.")
            return None
        
        # Get the test lecturer
        lecturer = User.objects.filter(username='test_lecturer').first()
        if not lecturer:
            print("❌ No test lecturer found! Run setup_esp32.py first.")
            return None
        
        # Check if there's already an active session
        if NetworkSession.objects.filter(is_active=True).exists():
            print("⚠️ There's already an active network session!")
            active_session = NetworkSession.objects.filter(is_active=True).first()
            print(f"   Course: {active_session.course.code}")
            print(f"   Started: {active_session.start_time}")
            print(f"   ESP32: {active_session.esp32_device.device_name}")
            return active_session
        
        # Create new network session
        current_time = timezone.now()
        end_time = current_time + timedelta(minutes=90)
        
        network_session = NetworkSession.objects.create(
            course=course,
            lecturer=lecturer,
            esp32_device=esp32_device,
            session="2024/2025",
            semester="1st Semester",
            date=current_time.date(),
            start_time=current_time,
            end_time=end_time,
            is_active=True
        )
        
        print("✅ Network session started successfully!")
        print(f"   Course: {network_session.course.code}")
        print(f"   Lecturer: {network_session.lecturer.username}")
        print(f"   ESP32 Device: {network_session.esp32_device.device_name}")
        print(f"   Start Time: {network_session.start_time.strftime('%H:%M:%S')}")
        print(f"   End Time: {network_session.end_time.strftime('%H:%M:%S')}")
        print(f"   Duration: 90 minutes")
        
        print("\n🎯 Now ESP32 should automatically:")
        print("   1. Check for active course")
        print("   2. Update WiFi SSID to 'CSC101_Attendance'")
        print("   3. Remove password (open WiFi)")
        print("   4. Update device ID dynamically")
        
        return network_session
        
    except Exception as e:
        print(f"❌ Error starting network session: {e}")
        return None

def check_esp32_status():
    """Check ESP32 device status"""
    try:
        esp32_device = ESP32Device.objects.first()
        if esp32_device:
            print(f"\n📱 ESP32 Device Status:")
            print(f"   Device ID: {esp32_device.device_id}")
            print(f"   Device Name: {esp32_device.device_name}")
            print(f"   Location: {esp32_device.location}")
            print(f"   Status: {'Active' if esp32_device.is_active else 'Inactive'}")
            print(f"   Last Heartbeat: {esp32_device.last_heartbeat or 'Never'}")
            print(f"   Last Seen: {esp32_device.last_seen}")
        else:
            print("❌ No ESP32 device found!")
    except Exception as e:
        print(f"❌ Error checking ESP32 status: {e}")

def main():
    """Main function"""
    print("🚀 Test Network Session Script")
    print("=" * 50)
    
    # Check ESP32 status
    check_esp32_status()
    
    # Start network session
    print("\n🎯 Starting Network Session...")
    session = start_network_session()
    
    if session:
        print("\n" + "=" * 50)
        print("🎉 SUCCESS! Network session is now active.")
        print("\n📱 Next Steps:")
        print("1. Check your ESP32 - WiFi should now be 'CSC101_Attendance'")
        print("2. WiFi should be open (no password)")
        print("3. Connect any device to test")
        print("4. Check Django admin for connected devices")
        print("5. Run test_esp32_integration.py to see dynamic behavior")
        
        print(f"\n🔗 Django Admin: http://127.0.0.1:8000/admin-panel/")
        print(f"📊 Network Sessions: http://127.0.0.1:8000/admin-panel/network-sessions/")

if __name__ == "__main__":
    main()
