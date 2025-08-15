#!/usr/bin/env python3
"""
Phone Connection Test Script

This script tests if a phone can access:
1. The ESP32 web server
2. The Django server
3. The network connectivity

Usage: python test_phone_connection.py
"""

import requests
import socket
import subprocess
import platform

def get_local_ip():
    """Get the local IP address of this computer"""
    try:
        # Create a socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"❌ Error getting local IP: {e}")
        return None

def test_django_server():
    """Test if Django server is accessible"""
    print("🔍 Testing Django server...")
    
    # Test local access
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Django server accessible locally")
            return True
        else:
            print(f"⚠️ Django server responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Django server not accessible locally: {e}")
        return False

def test_network_interface():
    """Test network interface binding"""
    print("\n🔍 Testing network interface...")
    
    local_ip = get_local_ip()
    if local_ip:
        print(f"✅ Local IP address: {local_ip}")
        
        # Test if Django is bound to all interfaces
        try:
            response = requests.get(f"http://{local_ip}:8000/", timeout=5)
            if response.status_code == 200:
                print(f"✅ Django accessible via local IP: {local_ip}:8000")
                return local_ip
            else:
                print(f"⚠️ Django not accessible via local IP: {local_ip}:8000")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Django not accessible via local IP: {e}")
            return None
    else:
        print("❌ Could not determine local IP")
        return None

def check_django_binding():
    """Check how Django server is bound"""
    print("\n🔍 Checking Django server binding...")
    
    try:
        # Check if Django is running on 0.0.0.0:8000
        result = subprocess.run(
            ["netstat", "-an"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if "0.0.0.0:8000" in result.stdout:
            print("✅ Django bound to 0.0.0.0:8000 (all interfaces)")
            return True
        elif "127.0.0.1:8000" in result.stdout:
            print("⚠️ Django bound to 127.0.0.1:8000 (localhost only)")
            return False
        else:
            print("❌ Django port 8000 not found in netstat")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Django binding: {e}")
        return False

def provide_solutions():
    """Provide solutions based on test results"""
    print("\n" + "=" * 50)
    print("🔧 SOLUTIONS")
    print("=" * 50)
    
    print("\n📱 **Phone Can't Access ESP32?**")
    print("1. Make sure ESP32 is connected to AttendanceWiFi hotspot")
    print("2. Check Serial Monitor for ESP32's IP address")
    print("3. Phone must be on SAME AttendanceWiFi hotspot")
    print("4. Try accessing: http://[ESP32_IP] in phone browser")
    
    print("\n🌐 **Django Server Issues?**")
    print("1. Stop current Django server (Ctrl+C)")
    print("2. Restart with: python manage.py runserver 0.0.0.0:8000")
    print("3. This binds Django to ALL network interfaces")
    
    print("\n📶 **Network Issues?**")
    print("1. ESP32 and phone must be on same WiFi network")
    print("2. Check Windows Firewall settings")
    print("3. Try disabling Windows Firewall temporarily for testing")
    
    print("\n🎯 **Quick Test Steps:**")
    print("1. Turn on AttendanceWiFi hotspot")
    print("2. Connect ESP32 to hotspot")
    print("3. Connect phone to same hotspot")
    print("4. Get ESP32 IP from Serial Monitor")
    print("5. Phone browser: http://[ESP32_IP]")

def main():
    """Main test function"""
    print("📱 Phone Connection Test")
    print("=" * 50)
    
    # Test Django server
    django_ok = test_django_server()
    
    # Test network interface
    local_ip = test_network_interface()
    
    # Check Django binding
    binding_ok = check_django_binding()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Django Server: {'✅ OK' if django_ok else '❌ Issue'}")
    print(f"Network Interface: {'✅ OK' if local_ip else '❌ Issue'}")
    print(f"Django Binding: {'✅ OK' if binding_ok else '❌ Issue'}")
    
    if not binding_ok:
        print("\n⚠️ Django is only bound to localhost!")
        print("Restart Django with: python manage.py runserver 0.0.0.0:8000")
    
    # Provide solutions
    provide_solutions()

if __name__ == "__main__":
    main()
