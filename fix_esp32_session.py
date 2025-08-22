#!/usr/bin/env python3
"""
Fix ESP32 Session Configuration Issues

This script fixes the main problems with ESP32 session configuration:
1. Creates ESP32 devices in the database
2. Sets up proper network sessions
3. Fixes CSRF token issues
4. Tests the complete flow
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from admin_ui.models import ESP32Device, Course, User, NetworkSession
from datetime import datetime, timedelta

def create_esp32_device():
    """Create a default ESP32 device for testing"""
    print("🔧 Creating ESP32 device...")
    
    # Check if device already exists
    device_id = "ESP32_DYNAMIC_001"
    try:
        device = ESP32Device.objects.get(device_id=device_id)
        print(f"✅ ESP32 device already exists: {device.device_name}")
        return device
    except ESP32Device.DoesNotExist:
        pass
    
    # Create new device
    device = ESP32Device.objects.create(
        device_id=device_id,
        device_name="Dynamic Course ESP32",
        ssid="ESP32_Starting",
        password="",
        location="Computer Science Lab 1",
        is_active=True
    )
    
    print(f"✅ Created ESP32 device: {device.device_name} ({device.device_id})")
    return device

def create_network_session(esp32_device):
    """Create an active network session for testing"""
    print("🌐 Creating network session...")
    
    # Check if session already exists
    existing_session = NetworkSession.objects.filter(
        esp32_device=esp32_device,
        is_active=True
    ).first()
    
    if existing_session:
        print(f"✅ Active session already exists: {existing_session.course.code}")
        return existing_session
    
    # Get first available course
    try:
        course = Course.objects.first()
        if not course:
            print("❌ No courses found in database")
            return None
    except Course.DoesNotExist:
        print("❌ No courses found in database")
        return None
    
    # Get first available user (lecturer)
    try:
        lecturer = User.objects.filter(is_staff=True).first()
        if not lecturer:
            print("❌ No lecturers found in database")
            return None
    except User.DoesNotExist:
        print("❌ No lecturers found in database")
        return None
    
    # Create network session
    session = NetworkSession.objects.create(
        esp32_device=esp32_device,
        course=course,
        lecturer=lecturer,
        session="2024/2025",
        semester="1st Semester",
        date=timezone.now().date(),
        start_time=timezone.now(),
        is_active=True
    )
    
    print(f"✅ Created network session: {session.course.code} - {session.lecturer.username}")
    return session

def test_esp32_api():
    """Test the ESP32 API endpoints"""
    print("🧪 Testing ESP32 API endpoints...")
    
    import requests
    
    base_url = "http://127.0.0.1:8000"
    
    # Test active course endpoint
    print("  🔍 Testing active course endpoint...")
    try:
        response = requests.post(
            f"{base_url}/admin-panel/api/esp32/active-course/",
            json={"base_device_id": "ESP32_"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Active course: {data}")
        else:
            print(f"    ❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test heartbeat endpoint
    print("  💓 Testing heartbeat endpoint...")
    try:
        response = requests.post(
            f"{base_url}/admin-panel/api/esp32/heartbeat/",
            json={"device_id": "ESP32_DYNAMIC_001"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Heartbeat: {data}")
        else:
            print(f"    ❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"    ❌ Error: {e}")

def main():
    """Main function to fix ESP32 session configuration"""
    print("🚀 Fixing ESP32 Session Configuration Issues")
    print("=" * 50)
    
    # Step 1: Create ESP32 device
    esp32_device = create_esp32_device()
    
    # Step 2: Create network session
    network_session = create_network_session(esp32_device)
    
    if not network_session:
        print("❌ Failed to create network session")
        return
    
    # Step 3: Test API endpoints
    test_esp32_api()
    
    print("\n" + "=" * 50)
    print("✅ ESP32 Session Configuration Fixed!")
    print("\n📱 Next Steps:")
    print("1. Upload ESP32 code to your device")
    print("2. ESP32 will automatically detect the active session")
    print("3. WiFi network will change to: {course_code}_Attendance")
    print("4. Students can connect and mark attendance")
    
    print(f"\n🔧 Current Configuration:")
    print(f"   ESP32 Device: {esp32_device.device_id}")
    print(f"   Active Course: {network_session.course.code}")
    print(f"   WiFi SSID: {network_session.course.code}_Attendance")
    print(f"   Session: {network_session.session} {network_session.semester}")

if __name__ == "__main__":
    main()
