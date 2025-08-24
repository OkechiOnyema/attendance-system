#!/usr/bin/env python3
"""
Test script for ESP32 Student Verification API
Tests the attendance marking functionality
"""

import requests
import json

# Django server URL
DJANGO_URL = "http://127.0.0.1:8001"  # Change to your Django server URL

def test_esp32_attendance_api():
    """Test the ESP32 student verification API"""
    
    # Test data - using existing student matric number with session/semester
    test_data = {
        "matric_number": "2021001",  # John Doe - exists in database
        "course_code": "CSC101",
        "device_mac": "ESP32_DIRECT",
        "esp32_device_id": "ESP32_PRESENCE_001",
        "action": "mark_present",
        "session": "2024/2025",
        "semester": "1st Semester"
    }
    
    # API endpoint
    api_url = f"{DJANGO_URL}/admin-panel/api/esp32/student-verification/"
    
    print(f"Testing ESP32 API endpoint: {api_url}")
    print(f"Test data: {json.dumps(test_data, indent=2)}")
    print("-" * 50)
    
    try:
        # Make POST request
        response = requests.post(
            api_url,
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print("❌ FAILED!")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {e}")
        print(f"Raw Response: {response.text}")

def test_django_server():
    """Test if Django server is running"""
    try:
        response = requests.get(f"{DJANGO_URL}/admin-panel/")
        print(f"✅ Django server is running (Status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Django server is not running: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing ESP32 Attendance API")
    print("=" * 50)
    
    # First check if Django server is running
    if test_django_server():
        print()
        test_esp32_attendance_api()
    else:
        print("\nPlease start your Django server first:")
        print("python manage.py runserver")
