#!/usr/bin/env python3
"""
ESP32 Dynamic Integration Test Script

This script tests the ESP32 dynamic course communication with Django by simulating
device connections and checking the new API endpoints.

Usage:
    python test_esp32_integration.py
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
DJANGO_SERVER = "http://127.0.0.1:8000"
BASE_DEVICE_ID = "ESP32_"  # Base device ID prefix

# Test endpoints
ACTIVE_COURSE_URL = f"{DJANGO_SERVER}/admin-panel/api/esp32/active-course/"
HEARTBEAT_URL = f"{DJANGO_SERVER}/admin-panel/api/esp32/heartbeat/"
DEVICE_CONNECTED_URL = f"{DJANGO_SERVER}/admin-panel/api/esp32/connected/"
DEVICE_DISCONNECTED_URL = f"{DJANGO_SERVER}/admin-panel/api/esp32/disconnected/"

def test_active_course_check():
    """Test ESP32 active course endpoint"""
    print("🔍 Testing ESP32 Active Course Check...")
    
    data = {
        "base_device_id": BASE_DEVICE_ID,
        "request_type": "course_check"
    }
    
    try:
        response = requests.post(ACTIVE_COURSE_URL, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Active course check successful: {result}")
            
            if result.get('active_course'):
                print(f"📚 Course: {result.get('course_code')} - {result.get('course_title')}")
                print(f"🔗 Device ID: {result.get('device_id')}")
                print(f"📶 SSID: {result.get('ssid')}")
                return True, result
            else:
                print("ℹ️ No active course found")
                return True, result
        else:
            print(f"❌ Active course check failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Active course check error: {e}")
        return False, None

def test_heartbeat(course_info=None):
    """Test ESP32 heartbeat endpoint with course information"""
    print("🔍 Testing ESP32 Heartbeat...")
    
    if course_info and course_info.get('active_course'):
        data = {
            "device_id": course_info.get('device_id'),
            "course_code": course_info.get('course_code'),
            "course_title": course_info.get('course_title'),
            "session": course_info.get('session'),
            "semester": course_info.get('semester'),
            "ssid": course_info.get('ssid'),
            "connected_devices": 0
        }
    else:
        data = {
            "device_id": f"{BASE_DEVICE_ID}DEFAULT",
            "course_code": "NO_COURSE",
            "course_title": "No Active Course",
            "session": "",
            "semester": "",
            "ssid": "ESP32_Default",
            "connected_devices": 0
        }
    
    try:
        response = requests.post(HEARTBEAT_URL, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Heartbeat successful: {result}")
            return True
        else:
            print(f"❌ Heartbeat failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Heartbeat error: {e}")
        return False

def test_device_connected(mac_address, device_name="Test Device", course_info=None):
    """Test device connection endpoint with course information"""
    print(f"🔍 Testing Device Connection: {mac_address}")
    
    if course_info and course_info.get('active_course'):
        data = {
            "device_id": course_info.get('device_id'),
            "mac_address": mac_address,
            "device_name": device_name,
            "ip_address": f"192.168.4.{random.randint(100, 200)}",
            "course_code": course_info.get('course_code'),
            "course_title": course_info.get('course_title'),
            "session": course_info.get('session'),
            "semester": course_info.get('semester')
        }
    else:
        data = {
            "device_id": f"{BASE_DEVICE_ID}DEFAULT",
            "mac_address": mac_address,
            "device_name": device_name,
            "ip_address": f"192.168.4.{random.randint(100, 200)}",
            "course_code": "NO_COURSE",
            "course_title": "No Active Course",
            "session": "",
            "semester": ""
        }
    
    try:
        response = requests.post(DEVICE_CONNECTED_URL, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Device connection successful: {result}")
            return True
        else:
            print(f"❌ Device connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Device connection error: {e}")
        return False

def test_device_disconnected(mac_address, course_info=None):
    """Test device disconnection endpoint with course information"""
    print(f"🔍 Testing Device Disconnection: {mac_address}")
    
    if course_info and course_info.get('active_course'):
        data = {
            "device_id": course_info.get('device_id'),
            "mac_address": mac_address,
            "course_code": course_info.get('course_code'),
            "course_title": course_info.get('course_title')
        }
    else:
        data = {
            "device_id": f"{BASE_DEVICE_ID}DEFAULT",
            "mac_address": mac_address,
            "course_code": "NO_COURSE",
            "course_title": "No Active Course"
        }
    
    try:
        response = requests.post(DEVICE_DISCONNECTED_URL, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Device disconnection successful: {result}")
            return True
        else:
            print(f"❌ Device disconnection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Device disconnection error: {e}")
        return False

def generate_mac_address():
    """Generate a random MAC address for testing"""
    mac = [0x00, 0x16, 0x3e, 0x00, 0x00, 0x00]
    for i in range(3, 6):
        mac[i] = random.randint(0, 255)
    return ':'.join([f"{x:02x}" for x in mac])

def simulate_student_session(course_info=None):
    """Simulate a complete student attendance session"""
    print("\n🎓 Simulating Student Attendance Session...")
    
    # Generate test MAC address
    mac_address = generate_mac_address()
    device_name = f"Student_{random.randint(1000, 9999)}_Phone"
    
    print(f"📱 Student Device: {device_name}")
    print(f"🔗 MAC Address: {mac_address}")
    
    if course_info and course_info.get('active_course'):
        print(f"📚 Course: {course_info.get('course_code')} - {course_info.get('course_title')}")
        print(f"📶 WiFi: {course_info.get('ssid')} (No Password)")
    else:
        print("⚠️ No active course - using default settings")
    
    # Connect device
    if test_device_connected(mac_address, device_name, course_info):
        print("✅ Student connected successfully")
        
        # Simulate device staying connected
        print("⏳ Device connected for 5 seconds...")
        time.sleep(5)
        
        # Disconnect device
        if test_device_disconnected(mac_address, course_info):
            print("✅ Student disconnected successfully")
            return True
        else:
            print("❌ Student disconnection failed")
            return False
    else:
        print("❌ Student connection failed")
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 ESP32 Dynamic Integration Test Suite")
    print("=" * 60)
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Django Server: {DJANGO_SERVER}")
    print(f"🔗 Base Device ID: {BASE_DEVICE_ID}")
    print("=" * 60)
    
    # Test results
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Active Course Check
    tests_total += 1
    course_check_success, course_info = test_active_course_check()
    if course_check_success:
        tests_passed += 1
    
    # Test 2: Heartbeat (with course info)
    tests_total += 1
    if test_heartbeat(course_info):
        tests_passed += 1
    
    # Test 3: Device Connection (with course info)
    tests_total += 1
    if test_device_connected("AA:BB:CC:DD:EE:FF", "Test Device 1", course_info):
        tests_passed += 1
    
    # Test 4: Device Disconnection (with course info)
    tests_total += 1
    if test_device_disconnected("AA:BB:CC:DD:EE:FF", course_info):
        tests_passed += 1
    
    # Test 5: Multiple Devices (with course info)
    tests_total += 1
    if test_device_connected("11:22:33:44:55:66", "Test Device 2", course_info):
        tests_passed += 1
    
    # Test 6: Student Session Simulation (with course info)
    tests_total += 1
    if simulate_student_session(course_info):
        tests_passed += 1
    
    # Test 7: Cleanup - Disconnect remaining device
    tests_total += 1
    if test_device_disconnected("11:22:33:44:55:66", course_info):
        tests_passed += 1
    
    # Results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"✅ Tests Passed: {tests_passed}/{tests_total}")
    print(f"📈 Success Rate: {(tests_passed/tests_total)*100:.1f}%")
    
    if course_info and course_info.get('active_course'):
        print(f"🎯 Active Course: {course_info.get('course_code')} - {course_info.get('course_title')}")
        print(f"📶 WiFi Network: {course_info.get('ssid')} (No Password)")
        print(f"🔗 Device ID: {course_info.get('device_id')}")
    else:
        print("ℹ️ No active course session found")
        print("💡 Start a network session in Django to test dynamic functionality")
    
    if tests_passed == tests_total:
        print("🎉 All tests passed! ESP32 dynamic integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        return False

def check_django_server():
    """Check if Django server is running"""
    try:
        response = requests.get(f"{DJANGO_SERVER}/", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🔍 Checking Django server status...")
    
    if not check_django_server():
        print("❌ Django server is not running!")
        print("Please start your Django server first:")
        print("python manage.py runserver")
        exit(1)
    
    print("✅ Django server is running!")
    
    # Run tests
    success = run_integration_tests()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Upload the updated Arduino code to your ESP32")
        print("2. Start a network session in Django")
        print("3. Watch ESP32 automatically update WiFi to match the course")
        print("4. Test with real devices (no password needed!)")
        print("5. Monitor attendance in Django admin")
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Check Django server logs for errors")
        print("2. Verify ESP32 API endpoints are accessible")
        print("3. Check network connectivity")
        print("4. Review ESP32 configuration")
        print("5. Ensure you have an active network session")
    
    print("\n📚 For more help, see: ESP32_SETUP_GUIDE.md")
    print("🚀 New Dynamic Features:")
    print("   - Auto course-based WiFi names")
    print("   - No password required")
    print("   - Dynamic device IDs")
    print("   - Real-time course detection")
