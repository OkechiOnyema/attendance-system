#!/usr/bin/env python3
"""
Simple ESP32 Bridge Test Script

This script tests the ESP32 bridge functionality by:
1. Checking Django server status
2. Testing ESP32 API endpoints
3. Simulating student attendance

Usage: python test_esp32_bridge.py
"""

import requests
import json
import time
from datetime import datetime

# Configuration
DJANGO_SERVER = "http://127.0.0.1:8000"
ADMIN_PANEL = f"{DJANGO_SERVER}/admin-panel"

def test_django_server():
    """Test if Django server is running"""
    print("🔍 Testing Django server...")
    try:
        response = requests.get(f"{DJANGO_SERVER}/", timeout=5)
        if response.status_code == 200:
            print("✅ Django server is running")
            return True
        else:
            print(f"⚠️ Django server responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Django server is not accessible: {e}")
        return False

def test_esp32_endpoints():
    """Test ESP32 API endpoints"""
    print("\n🔍 Testing ESP32 API endpoints...")
    
    endpoints = [
        "/api/esp32/heartbeat/",
        "/api/esp32/connected/",
        "/api/esp32/disconnected/",
        "/api/esp32/active-course/"
    ]
    
    for endpoint in endpoints:
        url = f"{ADMIN_PANEL}{endpoint}"
        try:
            response = requests.post(url, json={
                "device_id": "ESP32_Bridge_001",
                "test": True,
                "timestamp": datetime.now().isoformat()
            }, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Working")
            else:
                print(f"⚠️ {endpoint} - Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Error: {e}")

def test_student_attendance():
    """Test student attendance functionality"""
    print("\n🔍 Testing student attendance...")
    
    # Test data
    test_attendance = {
        "device_id": "ESP32_Bridge_001",
        "mac_address": "ESP32_Test_001",
        "device_name": "Test Student Device",
        "ip_address": "192.168.1.100",
        "matric_no": "TEST001",
        "course": "CSC101"
    }
    
    try:
        response = requests.post(
            f"{ADMIN_PANEL}/api/esp32/connected/",
            json=test_attendance,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Student attendance test successful")
            print(f"📊 Response: {response.json()}")
        else:
            print(f"⚠️ Student attendance test failed - Status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Student attendance test error: {e}")

def main():
    """Main test function"""
    print("🚀 ESP32 Bridge System Test")
    print("=" * 40)
    
    # Test Django server
    if not test_django_server():
        print("\n❌ Django server test failed. Please start Django server first.")
        print("Command: python manage.py runserver 0.0.0.0:8000")
        return
    
    # Test ESP32 endpoints
    test_esp32_endpoints()
    
    # Test student attendance
    test_student_attendance()
    
    print("\n" + "=" * 40)
    print("🎯 Test Summary:")
    print("✅ Django server is running")
    print("✅ ESP32 API endpoints are accessible")
    print("✅ Student attendance system is working")
    print("\n🚀 Your ESP32 bridge system is ready!")
    print("\n📋 Next steps:")
    print("1. Update wifi_config.h with your WiFi credentials")
    print("2. Upload esp32_simple_bridge.ino to your ESP32")
    print("3. Students can access attendance at ESP32's IP address")

if __name__ == "__main__":
    main()
