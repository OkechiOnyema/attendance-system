#!/usr/bin/env python3
"""
Test ESP32 Heartbeat API Directly
"""

import requests
import json

def test_heartbeat():
    """Test the ESP32 heartbeat API directly"""
    url = "http://127.0.0.1:8000/admin-panel/api/esp32/heartbeat/"
    
    data = {
        "device_id": "ESP32_DYNAMIC_001",
        "wifi_ssid": "TestWiFi",
        "connected_students": 0
    }
    
    print(f"🔍 Testing heartbeat API: {url}")
    print(f"📤 Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        
        print(f"📥 Status: {response.status_code}")
        print(f"📥 Headers: {dict(response.headers)}")
        print(f"📥 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_heartbeat()
