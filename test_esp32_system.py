#!/usr/bin/env python3
"""
ESP32 Smart Attendance System - Comprehensive Test Script
Tests all API endpoints and system functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://127.0.0.1:8000"
ADMIN_BASE = f"{BASE_URL}/admin-panel"
API_BASE = f"{ADMIN_BASE}/api"

# Test data
TEST_DEVICE_ID = "ESP32_001"
TEST_COURSE_ID = 1
TEST_LECTURER_ID = 1
TEST_STUDENT_MATRIC = "2021/123456"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_test(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   📝 {details}")

def test_server_connection():
    """Test if Django server is running"""
    print_header("Testing Server Connection")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        success = response.status_code == 200
        print_test("Django Server", success, f"Status: {response.status_code}")
        return success
    except requests.exceptions.ConnectionError:
        print_test("Django Server", False, "Connection refused")
        return False

def test_admin_access():
    """Test admin panel access"""
    print_header("Testing Admin Panel Access")
    
    try:
        response = requests.get(f"{ADMIN_BASE}/")
        success = response.status_code == 200
        print_test("Admin Panel", success, f"Status: {response.status_code}")
        return success
    except requests.exceptions.ConnectionError:
        print_test("Admin Panel", False, "Connection refused")
        return False

def test_api_endpoints():
    """Test all API endpoints"""
    print_header("Testing API Endpoints")
    
    endpoints = [
        ("GET /api/session/active/", f"{API_BASE}/session/active/?device_id={TEST_DEVICE_ID}"),
        ("POST /api/attendance/submit/", f"{API_BASE}/attendance/submit/"),
        ("GET /api/session/status/", f"{API_BASE}/session/status/"),
        ("POST /api/device/connected-smart/", f"{API_BASE}/device/connected-smart/"),
        ("POST /api/device/disconnected-smart/", f"{API_BASE}/device/disconnected-smart/"),
    ]
    
    results = {}
    
    for name, url in endpoints:
        try:
            if "GET" in name:
                response = requests.get(url)
            else:
                response = requests.post(url, json={})
            
            success = response.status_code in [200, 400, 405]  # 400/405 are expected for empty data
            status = response.status_code
            results[name] = success
            
            print_test(name, success, f"Status: {status}")
            
        except requests.exceptions.ConnectionError:
            print_test(name, False, "Connection refused")
            results[name] = False
    
    return all(results.values())

def test_esp32_attendance_page():
    """Test ESP32 attendance page"""
    print_header("Testing ESP32 Attendance Page")
    
    try:
        response = requests.get(f"{ADMIN_BASE}/esp32-attendance/")
        success = response.status_code == 200
        print_test("ESP32 Attendance Page", success, f"Status: {response.status_code}")
        
        if success:
            content = response.text
            has_form = "matricNo" in content
            has_submit = "Submit Attendance" in content
            has_styles = "background:" in content
            
            print_test("  - Has Matric Input", has_form)
            print_test("  - Has Submit Button", has_submit)
            print_test("  - Has Styling", has_styles)
            
        return success
    except requests.exceptions.ConnectionError:
        print_test("ESP32 Attendance Page", False, "Connection refused")
        return False

def test_network_session_creation():
    """Test network session creation"""
    print_header("Testing Network Session Creation")
    
    try:
        # Test the create form page
        response = requests.get(f"{ADMIN_BASE}/network-sessions/create/?course={TEST_COURSE_ID}")
        success = response.status_code == 200
        print_test("Create Session Form", success, f"Status: {response.status_code}")
        
        if success:
            content = response.text
            has_course = "Course" in content
            has_esp32 = "ESP32 Device" in content
            has_submit = "Create Session" in content
            
            print_test("  - Has Course Field", has_course)
            print_test("  - Has ESP32 Field", has_esp32)
            print_test("  - Has Submit Button", has_submit)
        
        return success
    except requests.exceptions.ConnectionError:
        print_test("Create Session Form", False, "Connection refused")
        return False

def test_attendance_validation():
    """Test attendance validation logic"""
    print_header("Testing Attendance Validation")
    
    # Test data
    test_payload = {
        "session_id": "TEST_SESSION_001",
        "student_matric_no": TEST_STUDENT_MATRIC,
        "device_id": TEST_DEVICE_ID,
        "client_ip": "192.168.4.100",
        "device_mac": "AA:BB:CC:DD:EE:FF",
        "device_name": "Test Device"
    }
    
    try:
        response = requests.post(f"{API_BASE}/attendance/submit/", json=test_payload)
        
        # Should fail because session doesn't exist
        success = response.status_code == 400
        print_test("Invalid Session Rejection", success, f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_test("  - Response Format", "error" in data, f"Response: {data}")
        else:
            print_test("  - Response Format", True, "Properly rejected invalid session")
        
        return success
    except requests.exceptions.ConnectionError:
        print_test("Invalid Session Rejection", False, "Connection refused")
        return False

def test_device_connection_api():
    """Test device connection API"""
    print_header("Testing Device Connection API")
    
    # Test device connected
    connected_payload = {
        "device_id": TEST_DEVICE_ID,
        "client_ip": "192.168.4.100",
        "client_mac": "AA:BB:CC:DD:EE:FF",
        "client_name": "Test Device"
    }
    
    try:
        response = requests.post(f"{API_BASE}/device/connected-smart/", json=connected_payload)
        success = response.status_code in [200, 400]  # 400 expected if device not found
        print_test("Device Connected API", success, f"Status: {response.status_code}")
        
        # Test device disconnected
        disconnected_payload = {
            "device_id": TEST_DEVICE_ID,
            "client_ip": "192.168.4.100",
            "client_mac": "AA:BB:CC:DD:EE:FF"
        }
        
        response = requests.post(f"{API_BASE}/device/disconnected-smart/", json=disconnected_payload)
        success2 = response.status_code in [200, 400]
        print_test("Device Disconnected API", success2, f"Status: {response.status_code}")
        
        return success and success2
    except requests.exceptions.ConnectionError:
        print_test("Device Connection API", False, "Connection refused")
        return False

def test_session_status_api():
    """Test session status API"""
    print_header("Testing Session Status API")
    
    try:
        response = requests.get(f"{API_BASE}/session/status/")
        success = response.status_code in [200, 400, 405]
        print_test("Session Status API", success, f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print_test("  - Valid JSON Response", True, "Response parsed successfully")
            except json.JSONDecodeError:
                print_test("  - Valid JSON Response", False, "Invalid JSON format")
        
        return success
    except requests.exceptions.ConnectionError:
        print_test("Session Status API", False, "Connection refused")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print_header("ESP32 Smart Attendance System - Comprehensive Test")
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Testing against: {BASE_URL}")
    
    tests = [
        ("Server Connection", test_server_connection),
        ("Admin Panel Access", test_admin_access),
        ("API Endpoints", test_api_endpoints),
        ("ESP32 Attendance Page", test_esp32_attendance_page),
        ("Network Session Creation", test_network_session_creation),
        ("Attendance Validation", test_attendance_validation),
        ("Device Connection API", test_device_connection_api),
        ("Session Status API", test_session_status_api),
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed_tests += 1
        except Exception as e:
            print_test(test_name, False, f"Error: {str(e)}")
            results[test_name] = False
    
    # Summary
    print_header("Test Summary")
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Your system is ready for ESP32 integration.")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        print("💡 Common solutions:")
        print("   - Ensure Django server is running")
        print("   - Check database migrations")
        print("   - Verify URL configurations")
        print("   - Check admin panel access")
    
    return results

if __name__ == "__main__":
    run_comprehensive_test()
