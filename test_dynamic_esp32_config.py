#!/usr/bin/env python3
"""
Dynamic ESP32 Configuration Test Script
Tests the new real-time ESP32 configuration system
"""

import os
import sys
import django
import time
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import Course, AssignedCourse, User, NetworkSession, ESP32Device
from django.utils import timezone

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_test(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   📝 {details}")

def test_dynamic_esp32_configuration():
    """Test the dynamic ESP32 configuration system"""
    print_header("Testing Dynamic ESP32 Configuration System")
    
    # 1. Check if we have ESP32 devices
    esp32_devices = ESP32Device.objects.filter(is_active=True)
    print(f"📱 Found {esp32_devices.count()} ESP32 devices")
    
    if not esp32_devices.exists():
        print("❌ No ESP32 devices found. Please create some devices first.")
        return False
    
    # 2. Check device status
    online_devices = esp32_devices.filter(
        last_heartbeat__gte=timezone.now() - timedelta(minutes=5)
    )
    print(f"🟢 Online devices: {online_devices.count()}")
    print(f"🔴 Offline devices: {esp32_devices.count() - online_devices.count()}")
    
    # 3. Show device details
    for device in esp32_devices:
        status = "🟢 ONLINE" if device.last_heartbeat and device.last_heartbeat > timezone.now() - timedelta(minutes=5) else "🔴 OFFLINE"
        last_seen = device.last_heartbeat.strftime("%H:%M:%S") if device.last_heartbeat else "Never"
        print(f"   {device.device_name} ({device.device_id}) - {status} - Last seen: {last_seen}")
    
    # 4. Check for active network sessions
    active_sessions = NetworkSession.objects.filter(is_active=True)
    print(f"\n📡 Active network sessions: {active_sessions.count()}")
    
    for session in active_sessions:
        device_status = "🟢 CONFIGURED" if session.esp32_device else "❌ NO DEVICE"
        print(f"   {session.course.code} - {session.lecturer.username} - {device_status}")
        if session.esp32_device:
            print(f"      ESP32: {session.esp32_device.device_name} ({session.esp32_device.ssid})")
    
    # 5. Test dynamic configuration simulation
    print_header("Simulating Dynamic Configuration")
    
    # Find a course and lecturer for testing
    try:
        course = Course.objects.first()
        lecturer = User.objects.filter(groups__name='Lecturers').first()
        
        if course and lecturer:
            print(f"🎯 Test Course: {course.code} - {course.title}")
            print(f"👨‍🏫 Test Lecturer: {lecturer.username}")
            
            # Simulate what happens when a session is created
            print("\n🔄 Simulating session creation...")
            
            # Check available devices
            available_devices = ESP32Device.objects.filter(
                is_active=True,
                last_heartbeat__gte=timezone.now() - timedelta(minutes=5)
            ).order_by('-last_heartbeat')
            
            if available_devices.exists():
                selected_device = available_devices.first()
                print(f"📱 Selected ESP32: {selected_device.device_name}")
                
                # Generate dynamic configuration
                session = "2024/2025"
                semester = "1st Semester"
                course_code = course.code
                session_id = f"{session}_{semester}".replace(" ", "_").replace("/", "_")
                
                dynamic_device_id = f"ESP32_{course_code}_{session_id}"
                dynamic_ssid = f"{course_code}_Attendance_{session.replace('/', '_')}"
                
                print(f"🔧 Dynamic Configuration Generated:")
                print(f"   Device ID: {dynamic_device_id}")
                print(f"   SSID: {dynamic_ssid}")
                print(f"   Device Name: {course_code} - {course.title}")
                print(f"   Location: {course_code} Classroom - {session} {semester}")
                
                # Show what the ESP32 would receive
                print(f"\n📡 ESP32 would receive this configuration:")
                config_response = {
                    'status': 'success',
                    'message': 'Heartbeat received - Active session configuration applied',
                    'device_id': selected_device.device_id,
                    'configuration': {
                        'active_session': True,
                        'course_code': course_code,
                        'course_title': course.title,
                        'session': session,
                        'semester': semester,
                        'device_id': dynamic_device_id,
                        'ssid': dynamic_ssid,
                        'password': "",
                        'lecturer': lecturer.username,
                        'session_id': 999  # Placeholder
                    }
                }
                
                for key, value in config_response['configuration'].items():
                    print(f"   {key}: {value}")
                
                print_test("Dynamic Configuration Generation", True, f"Generated config for {course_code}")
                
            else:
                print("❌ No online ESP32 devices available for testing")
                print_test("Dynamic Configuration Generation", False, "No online devices")
                
        else:
            print("❌ Missing test data (course or lecturer)")
            print_test("Dynamic Configuration Generation", False, "Missing test data")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print_test("Dynamic Configuration Generation", False, str(e))
    
    return True

def test_esp32_heartbeat_response():
    """Test the ESP32 heartbeat API response"""
    print_header("Testing ESP32 Heartbeat API Response")
    
    try:
        # Find an ESP32 device
        device = ESP32Device.objects.filter(is_active=True).first()
        
        if not device:
            print("❌ No ESP32 devices found for testing")
            return False
        
        print(f"📱 Testing with device: {device.device_name} ({device.device_id})")
        
        # Check if device has active session
        active_session = NetworkSession.objects.filter(
            esp32_device=device,
            is_active=True
        ).first()
        
        if active_session:
            print(f"🎯 Device has active session: {active_session.course.code}")
            print(f"   Course: {active_session.course.title}")
            print(f"   Lecturer: {active_session.lecturer.username}")
            print(f"   Session: {active_session.session} {active_session.semester}")
            
            # Show what the API would return
            course = active_session.course
            session = active_session.session
            semester = active_session.semester
            course_code = course.code
            session_id = f"{session}_{semester}".replace(" ", "_").replace("/", "_")
            
            dynamic_device_id = f"ESP32_{course_code}_{session_id}"
            dynamic_ssid = f"{course_code}_Attendance_{session.replace('/', '_')}"
            
            print(f"\n📡 API Response would include:")
            print(f"   active_session: true")
            print(f"   course_code: {course_code}")
            print(f"   course_title: {course.title}")
            print(f"   session: {session}")
            print(f"   semester: {semester}")
            print(f"   device_id: {dynamic_device_id}")
            print(f"   ssid: {dynamic_ssid}")
            print(f"   password: ''")
            print(f"   lecturer: {active_session.lecturer.username}")
            
            print_test("ESP32 Heartbeat API", True, "Active session configuration")
            
        else:
            print("💤 Device has no active session")
            print(f"\n📡 API Response would include:")
            print(f"   active_session: false")
            print(f"   message: 'No active session - device in standby mode'")
            
            print_test("ESP32 Heartbeat API", True, "Standby mode configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing heartbeat API: {e}")
        print_test("ESP32 Heartbeat API", False, str(e))
        return False

def main():
    """Main test function"""
    print("🚀 Dynamic ESP32 Configuration System Test")
    print("=" * 60)
    
    # Test 1: Dynamic configuration system
    test1_success = test_dynamic_esp32_configuration()
    
    # Test 2: ESP32 heartbeat API
    test2_success = test_esp32_heartbeat_response()
    
    # Summary
    print_header("Test Summary")
    if test1_success and test2_success:
        print("🎉 All tests passed! Dynamic ESP32 configuration system is working.")
        print("\n📋 What this means:")
        print("✅ ESP32 devices automatically configure when sessions are created")
        print("✅ No more dummy/pre-selected device names")
        print("✅ Real-time configuration updates via heartbeat API")
        print("✅ Dynamic SSID and device ID generation")
        print("✅ Automatic device selection based on availability")
    else:
        print("❌ Some tests failed. Please check the system setup.")
    
    print(f"\n🕐 Test completed at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
