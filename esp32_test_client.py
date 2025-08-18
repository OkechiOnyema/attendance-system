#!/usr/bin/env python3
"""
ESP32 Test Client for Smart Attendance System
This script simulates an ESP32 device to test the attendance API endpoints
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000/admin-panel"
DEVICE_ID = "ESP32_TEST_001"

def test_get_active_session():
    """Test getting active session details"""
    print("🔍 Testing: Get Active Session")
    
    url = f"{BASE_URL}/api/session/active/"
    params = {"device_id": DEVICE_ID}
    
    try:
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('active'):
                print("✅ Active session found!")
                print(f"   Course: {data['course_code']} - {data['course_title']}")
                print(f"   Lecturer: {data['lecturer_name']}")
                print(f"   Date: {data['date']}")
                print(f"   Enrolled Students: {data['total_enrolled']}")
                print(f"   Current Attendance: {data['attendance_count']}")
                return data
            else:
                print("❌ No active session found")
                print(f"   Message: {data.get('message', 'Unknown')}")
                return None
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_submit_attendance(session_data, matric_no):
    """Test submitting attendance"""
    print(f"\n📝 Testing: Submit Attendance for {matric_no}")
    
    url = f"{BASE_URL}/api/attendance/submit/"
    
    payload = {
        "session_id": session_data['session_id'],
        "student_matric_no": matric_no,
        "device_id": DEVICE_ID,
        "client_ip": "192.168.4.100",  # Simulate ESP32 network IP
        "device_mac": "AA:BB:CC:DD:EE:FF",
        "device_name": "Test Device"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Attendance submitted successfully!")
                print(f"   Student: {data['student_name']}")
                print(f"   Course: {data['course_code']}")
                print(f"   Timestamp: {data['timestamp']}")
                return True
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
                return False
        elif response.status_code == 403:
            data = response.json()
            print("✅ Correctly rejected: Device not connected to ESP32 network")
            print(f"   Error: {data.get('error', 'Unknown')}")
            return False
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_get_session_status():
    """Test getting session status"""
    print("\n📊 Testing: Get Session Status")
    
    url = f"{BASE_URL}/api/session/status/"
    params = {"device_id": DEVICE_ID}
    
    try:
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('active'):
                print("✅ Session status retrieved!")
                print(f"   Course: {data['course_code']} - {data['course_title']}")
                print(f"   Statistics: {data['statistics']['present']}/{data['statistics']['total_enrolled']} present ({data['statistics']['percentage']}%)")
                
                if data.get('recent_attendance'):
                    print("   Recent Attendance:")
                    for record in data['recent_attendance'][:3]:  # Show first 3
                        print(f"     {record['student_name']} ({record['matric_no']}) - {record['timestamp']}")
                return data
            else:
                print("❌ No active session found")
                return None
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_duplicate_attendance(session_data, matric_no):
    """Test submitting duplicate attendance (should fail)"""
    print(f"\n🔄 Testing: Duplicate Attendance for {matric_no}")
    
    url = f"{BASE_URL}/api/attendance/submit/"
    
    payload = {
        "session_id": session_data['session_id'],
        "student_matric_no": matric_no,
        "device_id": DEVICE_ID
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 400:
            data = response.json()
            if "already recorded" in data.get('error', ''):
                print("✅ Correctly rejected duplicate attendance!")
                return True
            else:
                print(f"❌ Unexpected error: {data.get('error', 'Unknown')}")
                return False
        else:
            print(f"❌ Should have rejected duplicate, got status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_invalid_student(session_data):
    """Test submitting attendance for invalid student"""
    print(f"\n👤 Testing: Invalid Student")
    
    url = f"{BASE_URL}/api/attendance/submit/"
    
    payload = {
        "session_id": session_data['session_id'],
        "student_matric_no": "INVALID123",
        "device_id": DEVICE_ID
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 404:
            data = response.json()
            if "not found" in data.get('error', ''):
                print("✅ Correctly rejected invalid student!")
                return True
            else:
                print(f"❌ Unexpected error: {data.get('error', 'Unknown')}")
                return False
        else:
            print(f"❌ Should have rejected invalid student, got status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 ESP32 Smart Attendance System - Test Client")
    print("=" * 50)
    
    # Test 1: Get active session
    session_data = test_get_active_session()
    if not session_data:
        print("\n❌ Cannot proceed without active session")
        print("   Please start a network session first")
        return
    
    # Test 2: Submit attendance for valid students
    test_students = ["STU001", "STU002", "STU003"]  # Replace with actual matric numbers
    
    for student in test_students:
        success = test_submit_attendance(session_data, student)
        if success:
            time.sleep(1)  # Small delay between requests
    
    # Test 3: Get updated session status
    test_get_session_status()
    
    # Test 4: Try duplicate attendance
    if test_students:
        test_duplicate_attendance(session_data, test_students[0])
    
    # Test 5: Try invalid student
    test_invalid_student(session_data)
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    print("\nTo test with real students:")
    print("1. Update test_students list with actual matric numbers")
    print("2. Make sure you have an active network session")
    print("3. Run this script again")

if __name__ == "__main__":
    main()
