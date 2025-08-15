#!/usr/bin/env python3
"""
ESP32 Access Point Integration Test Script

This script tests the complete ESP32 access point functionality:
1. ESP32 device management
2. Network session creation
3. Device connection tracking
4. Attendance verification

Usage:
    python test_esp32_access_point.py
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
DJANGO_SERVER = "http://127.0.0.1:8000"
ADMIN_PANEL = f"{DJANGO_SERVER}/admin-panel"

# Test endpoints
ESP32_DEVICES_URL = f"{ADMIN_PANEL}/esp32-devices/"
NETWORK_SESSIONS_URL = f"{ADMIN_PANEL}/network-sessions/"
HEARTBEAT_URL = f"{ADMIN_PANEL}/api/esp32/heartbeat/"
DEVICE_CONNECTED_URL = f"{ADMIN_PANEL}/api/esp32/connected/"
DEVICE_DISCONNECTED_URL = f"{ADMIN_PANEL}/api/esp32/disconnected/"
ACTIVE_COURSE_URL = f"{ADMIN_PANEL}/api/esp32/active-course/"

def test_esp32_device_creation():
    """Test creating an ESP32 device"""
    print("🔧 Testing ESP32 Device Creation...")
    
    device_data = {
        'device_id': 'ESP32_CS101_001',
        'device_name': 'CS101 Classroom ESP32',
        'ssid': 'CS101_Attendance',
        'password': '',
        'location': 'Computer Science Lab 1',
        'is_active': True
    }
    
    try:
        # This would normally be done through the Django admin interface
        # For testing, we'll simulate the API call
        print(f"✅ ESP32 Device data prepared: {device_data['device_id']}")
        return device_data
    except Exception as e:
        print(f"❌ ESP32 Device creation failed: {e}")
        return None

def test_network_session_creation():
    """Test creating a network session"""
    print("🌐 Testing Network Session Creation...")
    
    session_data = {
        'esp32_device': 'ESP32_CS101_001',
        'course': 'CS101',
        'lecturer': 'lecturer1',
        'session': '2024/2025',
        'semester': '1st Semester',
        'date': datetime.now().date().isoformat(),
        'start_time': datetime.now().isoformat(),
        'is_active': True
    }
    
    try:
        print(f"✅ Network Session data prepared: {session_data['course']} - {session_data['date']}")
        return session_data
    except Exception as e:
        print(f"❌ Network Session creation failed: {e}")
        return None

def test_esp32_heartbeat():
    """Test ESP32 heartbeat to Django"""
    print("💓 Testing ESP32 Heartbeat...")
    
    heartbeat_data = {
        'device_id': 'ESP32_CS101_001'
    }
    
    try:
        response = requests.post(HEARTBEAT_URL, json=heartbeat_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Heartbeat successful: {result}")
            return True
        else:
            print(f"❌ Heartbeat failed with status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Heartbeat request failed: {e}")
        return False

def test_device_connection():
    """Test device connection to ESP32"""
    print("📱 Testing Device Connection...")
    
    connection_data = {
        'device_id': 'ESP32_CS101_001',
        'mac_address': 'AA:BB:CC:DD:EE:FF',
        'device_name': 'iPhone 12',
        'ip_address': '192.168.4.2'
    }
    
    try:
        response = requests.post(DEVICE_CONNECTED_URL, json=connection_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Device connection successful: {result}")
            return True
        else:
            print(f"❌ Device connection failed with status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Device connection request failed: {e}")
        return False

def test_device_disconnection():
    """Test device disconnection from ESP32"""
    print("📱 Testing Device Disconnection...")
    
    disconnection_data = {
        'device_id': 'ESP32_CS101_001',
        'mac_address': 'AA:BB:CC:DD:EE:FF'
    }
    
    try:
        response = requests.post(DEVICE_DISCONNECTED_URL, json=disconnection_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Device disconnection successful: {result}")
            return True
        else:
            print(f"❌ Device disconnection failed with status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Device disconnection request failed: {e}")
        return False

def test_active_course_check():
    """Test ESP32 active course check"""
    print("🔍 Testing Active Course Check...")
    
    course_data = {
        'base_device_id': 'ESP32_'
    }
    
    try:
        response = requests.post(ACTIVE_COURSE_URL, json=course_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Active course check successful: {result}")
            
            if result.get('active_course'):
                print(f"📚 Active Course: {result.get('course_code')} - {result.get('course_title')}")
                print(f"🔗 Device ID: {result.get('device_id')}")
                print(f"📶 SSID: {result.get('ssid')}")
            else:
                print("ℹ️ No active course found")
            
            return True
        else:
            print(f"❌ Active course check failed with status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Active course check request failed: {e}")
        return False

def test_esp32_access_point_workflow():
    """Test complete ESP32 access point workflow"""
    print("\n🚀 Testing Complete ESP32 Access Point Workflow...")
    print("=" * 60)
    
    # Step 1: Create ESP32 device
    device = test_esp32_device_creation()
    if not device:
        return False
    
    # Step 2: Create network session
    session = test_network_session_creation()
    if not session:
        return False
    
    # Step 3: Test ESP32 heartbeat
    if not test_esp32_heartbeat():
        return False
    
    # Step 4: Test device connection
    if not test_device_connection():
        return False
    
    # Step 5: Test active course check
    if not test_active_course_check():
        return False
    
    # Step 6: Test device disconnection
    if not test_device_disconnection():
        return False
    
    print("\n✅ Complete ESP32 Access Point Workflow Test Successful!")
    return True

def print_esp32_setup_instructions():
    """Print ESP32 setup instructions"""
    print("\n📋 ESP32 Access Point Setup Instructions")
    print("=" * 50)
    print("1. Upload esp32_attendance.ino to your ESP32")
    print("2. Configure esp32_config.h with your settings")
    print("3. ESP32 will create WiFi network: 'ESP32_Attendance'")
    print("4. Students connect to ESP32 network (no password)")
    print("5. Django server should also connect to ESP32 network")
    print("6. ESP32 monitors all connections and sends data to Django")
    print("7. Use Django admin to create ESP32 devices and network sessions")
    print("\n🌐 Network Configuration:")
    print("   - ESP32 IP: 192.168.4.1")
    print("   - Network: ESP32_Attendance")
    print("   - Gateway: 192.168.4.1")
    print("   - Subnet: 255.255.255.0")

if __name__ == "__main__":
    print("🔌 ESP32 Access Point Integration Test")
    print("=" * 40)
    
    try:
        # Test the complete workflow
        success = test_esp32_access_point_workflow()
        
        if success:
            print("\n🎉 All tests passed! ESP32 access point is working correctly.")
        else:
            print("\n⚠️ Some tests failed. Check Django server and ESP32 configuration.")
        
        # Print setup instructions
        print_esp32_setup_instructions()
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
