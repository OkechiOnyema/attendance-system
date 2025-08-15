#!/usr/bin/env python3
"""
ESP32 WiFi Configuration Setup Script

This script helps you configure the ESP32 with your WiFi credentials
and test the connection to Django.
"""

import os
import re
import requests
import json

def get_wifi_credentials():
    """Get WiFi credentials from user"""
    print("🔧 ESP32 WiFi Configuration Setup")
    print("=" * 50)
    
    # Get WiFi network name
    while True:
        wifi_name = input("📶 Enter your WiFi network name (SSID): ").strip()
        if wifi_name:
            break
        print("❌ WiFi name cannot be empty!")
    
    # Get WiFi password
    wifi_password = input("🔑 Enter your WiFi password (leave empty if none): ").strip()
    
    # Get Django server IP
    while True:
        django_ip = input("🌐 Enter Django server IP address (e.g., 192.168.1.100): ").strip()
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', django_ip):
            break
        print("❌ Please enter a valid IP address!")
    
    return wifi_name, wifi_password, django_ip

def update_config_file(wifi_name, wifi_password, django_ip):
    """Update the esp32_config.h file with WiFi credentials"""
    config_file = "esp32_config.h"
    
    if not os.path.exists(config_file):
        print(f"❌ Configuration file {config_file} not found!")
        return False
    
    try:
        # Read current config
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Update WiFi credentials
        content = re.sub(
            r'#define WIFI_NETWORK_NAME ".*?"',
            f'#define WIFI_NETWORK_NAME "{wifi_name}"',
            content
        )
        
        content = re.sub(
            r'#define WIFI_NETWORK_PASSWORD ".*?"',
            f'#define WIFI_NETWORK_PASSWORD "{wifi_password}"',
            content
        )
        
        content = re.sub(
            r'#define DJANGO_SERVER_URL "http://.*?:8000"',
            f'#define DJANGO_SERVER_URL "http://{django_ip}:8000"',
            content
        )
        
        # Write updated config
        with open(config_file, 'w') as f:
            f.write(content)
        
        print("✅ Configuration file updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration file: {e}")
        return False

def test_django_connection(django_ip):
    """Test connection to Django server"""
    print(f"\n🔍 Testing Django server connection...")
    
    try:
        url = f"http://{django_ip}:8000/admin-panel/api/esp32/active-course/"
        data = {
            "base_device_id": "ESP32_",
            "request_type": "course_check"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Django server connection successful!")
            
            if result.get('active_course'):
                print(f"📚 Active course found: {result.get('course_code')} - {result.get('course_title')}")
                print(f"📶 WiFi SSID: {result.get('ssid')}")
                print(f"🔗 Device ID: {result.get('device_id')}")
            else:
                print("ℹ️ No active course session found")
                print("💡 Create a network session in Django to test ESP32 functionality")
            
            return True
        else:
            print(f"❌ Django server responded with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Django server at {django_ip}:8000")
        print("💡 Make sure:")
        print("   - Django server is running")
        print("   - IP address is correct")
        print("   - No firewall blocking the connection")
        return False
        
    except Exception as e:
        print(f"❌ Error testing Django connection: {e}")
        return False

def create_network_session_guide(django_ip):
    """Show guide for creating network session"""
    print(f"\n📋 To create a network session:")
    print(f"1. Go to: http://{django_ip}:8000/admin-panel/network-sessions/create/")
    print(f"2. Select a course")
    print(f"3. Select an ESP32 device")
    print(f"4. Set session duration")
    print(f"5. Click 'Create Session'")

def main():
    """Main setup function"""
    print("🚀 ESP32 Attendance System Setup")
    print("=" * 50)
    
    # Get credentials
    wifi_name, wifi_password, django_ip = get_wifi_credentials()
    
    print(f"\n📝 Configuration Summary:")
    print(f"   WiFi Network: {wifi_name}")
    print(f"   WiFi Password: {'*' * len(wifi_password) if wifi_password else 'None'}")
    print(f"   Django Server: {django_ip}:8000")
    
    # Confirm configuration
    confirm = input("\n✅ Proceed with this configuration? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Setup cancelled")
        return
    
    # Update config file
    if not update_config_file(wifi_name, wifi_password, django_ip):
        return
    
    # Test Django connection
    if test_django_connection(django_ip):
        create_network_session_guide(django_ip)
        
        print(f"\n🎉 Setup completed successfully!")
        print(f"📱 Next steps:")
        print(f"   1. Upload esp32_attendance.ino to your ESP32")
        print(f"   2. Open Serial Monitor (115200 baud)")
        print(f"   3. Create a network session in Django")
        print(f"   4. Watch ESP32 automatically detect the course!")
    else:
        print(f"\n⚠️ Setup completed with warnings")
        print(f"💡 Fix Django connection issues before uploading to ESP32")

if __name__ == "__main__":
    main()
