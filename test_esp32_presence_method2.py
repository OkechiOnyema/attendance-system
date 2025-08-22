#!/usr/bin/env python3
"""
Test ESP32 Presence Verification System - Method 2

This script tests the simplified ESP32 presence verification system:
1. Tests the Django API endpoint
2. Simulates ESP32 sending presence data
3. Tests presence verification functionality
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
DJANGO_SERVER = "http://127.0.0.1:8000"
PRESENCE_API_URL = f"{DJANGO_SERVER}/admin-panel/api/esp32/presence-update/"
DEVICE_ID = "ESP32_PRESENCE_001"

def test_presence_api():
    """Test the ESP32 presence update API"""
    print("🧪 Testing ESP32 Presence Verification API")
    print("=" * 50)
    
    # Simulate connected devices
    connected_devices = []
    for i in range(random.randint(3, 8)):
        device_id = f"DEV_{random.randint(1000, 9999)}"
        connected_devices.append(device_id)
    
    data = {
        "device_id": DEVICE_ID,
        "connected_devices": connected_devices,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"📤 Sending data to: {PRESENCE_API_URL}")
    print(f"📱 Simulating {len(connected_devices)} connected devices")
    print(f"🆔 Device ID: {DEVICE_ID}")
    
    try:
        response = requests.post(PRESENCE_API_URL, json=data, timeout=10)
        
        print(f"\n📥 Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Data: {json.dumps(result, indent=2)}")
            print("✅ Presence API test successful!")
            return True
        else:
            print(f"   Error: {response.text}")
            print("❌ Presence API test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def simulate_continuous_presence():
    """Simulate continuous presence updates like the ESP32 would send"""
    print("\n🔄 Simulating Continuous Presence Updates")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    
    try:
        for i in range(10):  # Send 10 updates
            # Simulate varying number of connected devices
            num_devices = random.randint(2, 12)
            connected_devices = [f"STU_{random.randint(1000, 9999)}" for _ in range(num_devices)]
            
            data = {
                "device_id": DEVICE_ID,
                "connected_devices": connected_devices,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(PRESENCE_API_URL, json=data, timeout=5)
            
            if response.status_code == 200:
                print(f"📤 Update {i+1}/10: {num_devices} devices - ✅ Success")
            else:
                print(f"📤 Update {i+1}/10: {num_devices} devices - ❌ Failed ({response.status_code})")
            
            time.sleep(2)  # Wait 2 seconds between updates
            
    except KeyboardInterrupt:
        print("\n⏹️ Simulation stopped by user")
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")

def test_django_server():
    """Test if Django server is running"""
    print("🔍 Checking Django Server Status...")
    
    try:
        response = requests.get(DJANGO_SERVER, timeout=5)
        if response.status_code == 200:
            print("✅ Django server is running!")
            return True
        else:
            print(f"⚠️ Django server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Django server is not accessible: {e}")
        print("💡 Make sure to run: python manage.py runserver")
        return False

def main():
    """Main test function"""
    print("🚀 ESP32 Presence Verification Test Suite")
    print("=" * 60)
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Django Server: {DJANGO_SERVER}")
    print(f"🔗 Device ID: {DEVICE_ID}")
    print("=" * 60)
    
    # Test 1: Check Django server
    if not test_django_server():
        return
    
    # Test 2: Single API test
    print()
    if not test_presence_api():
        return
    
    # Test 3: Continuous simulation
    print()
    choice = input("🤔 Run continuous presence simulation? (y/n): ").lower()
    if choice == 'y':
        simulate_continuous_presence()
    
    print("\n" + "=" * 60)
    print("✅ ESP32 Presence Verification Tests Complete!")
    print("\n📱 Next Steps:")
    print("1. Upload ESP32_Presence_Verification.ino to your ESP32")
    print("2. Update the DJANGO_SERVER IP in the ESP32 code")
    print("3. Power on the ESP32 and test with student devices")
    print("4. Students connect to 'Classroom_Attendance' WiFi")
    print("5. Use your existing Django attendance system normally")
    print("\n💡 The system will automatically verify presence when students mark attendance!")

if __name__ == "__main__":
    main()
