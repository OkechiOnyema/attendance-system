#!/usr/bin/env python3
"""
ESP32 Test Client for Django Attendance System

This script simulates an ESP32 device communicating with the Django backend
to test the attendance API endpoints.

Usage:
    python esp32_test_client.py --host your-domain.com --token your_device_token

Author: Okechi Onyema
Date: 2024
"""

import requests
import json
import time
import argparse
import random
from datetime import datetime, timedelta

class ESP32TestClient:
    def __init__(self, host, token, use_https=True):
        self.host = host
        self.token = token
        self.protocol = "https" if use_https else "http"
        self.base_url = f"{self.protocol}://{host}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.session_id = None
        
    def test_connection(self):
        """Test basic connection to Django backend"""
        try:
            response = requests.get(f"{self.base_url}/", headers=self.headers, timeout=10)
            print(f"✅ Connection test: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def start_session(self, course_code="CS101", lecturer_username="lecturer1"):
        """Start a network session"""
        data = {
            "course_code": course_code,
            "lecturer_username": lecturer_username,
            "session": "2024/2025",
            "semester": "1st Semester"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/esp32/start-session/",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.session_id = result.get('session_id')
                print(f"✅ Session started: {result.get('message')}")
                return True
            else:
                print(f"❌ Failed to start session: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting session: {e}")
            return False
    
    def end_session(self):
        """End the current network session"""
        if not self.session_id:
            print("❌ No active session to end")
            return False
            
        data = {"session_id": self.session_id}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/esp32/end-session/",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Session ended: {result.get('message')}")
                self.session_id = None
                return True
            else:
                print(f"❌ Failed to end session: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error ending session: {e}")
            return False
    
    def report_device_connected(self, mac_address, device_name="", ip_address=""):
        """Report a student device connection"""
        data = {
            "mac_address": mac_address,
            "device_name": device_name,
            "ip_address": ip_address
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/esp32/device-connected/",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Device connected: {result.get('message')}")
                return True
            else:
                print(f"❌ Failed to report device connection: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error reporting device connection: {e}")
            return False
    
    def report_device_disconnected(self, mac_address):
        """Report a student device disconnection"""
        data = {"mac_address": mac_address}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/esp32/device-disconnected/",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Device disconnected: {result.get('message')}")
                return True
            else:
                print(f"❌ Failed to report device disconnection: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error reporting device disconnection: {e}")
            return False
    
    def record_attendance(self, student_matric_no, mac_address, status="present"):
        """Record student attendance"""
        data = {
            "student_matric_no": student_matric_no,
            "mac_address": mac_address,
            "status": status
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/esp32/record-attendance/",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Attendance recorded: {result.get('message')}")
                return True
            else:
                print(f"❌ Failed to record attendance: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error recording attendance: {e}")
            return False
    
    def verify_student(self, student_matric_no):
        """Verify student enrollment"""
        data = {"student_matric_no": student_matric_no}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/esp32/verify-student/",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                student = result.get('student', {})
                print(f"✅ Student verified: {student.get('name')} - Enrolled: {student.get('is_enrolled')}")
                return True
            else:
                print(f"❌ Failed to verify student: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying student: {e}")
            return False
    
    def get_session_status(self):
        """Get current session status"""
        try:
            response = requests.get(
                f"{self.base_url}/api/esp32/session-status/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('session'):
                    session = result['session']
                    print(f"✅ Session active: {session.get('course_code')} - {session.get('course_title')}")
                    print(f"   Lecturer: {session.get('lecturer')}")
                    print(f"   Connected devices: {session.get('connected_devices')}")
                    print(f"   Attendance count: {session.get('attendance_count')}")
                else:
                    print("ℹ️  No active session")
                return True
            else:
                print(f"❌ Failed to get session status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting session status: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat to Django backend"""
        data = {
            "device_id": "ESP32_TEST_CLIENT",
            "timestamp": int(time.time())
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/esp32/heartbeat/",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"💓 Heartbeat sent: {result.get('message')}")
                return True
            else:
                print(f"❌ Failed to send heartbeat: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending heartbeat: {e}")
            return False
    
    def simulate_class_session(self, duration_minutes=5):
        """Simulate a complete class session"""
        print(f"\n🎓 Simulating class session for {duration_minutes} minutes...")
        
        # Start session
        if not self.start_session():
            return False
        
        # Simulate students connecting
        test_students = [
            ("2021001", "AA:BB:CC:DD:EE:01"),
            ("2021002", "AA:BB:CC:DD:EE:02"),
            ("2021003", "AA:BB:CC:DD:EE:03"),
            ("2021004", "AA:BB:CC:DD:EE:04"),
            ("2021005", "AA:BB:CC:DD:EE:05")
        ]
        
        print("\n📱 Simulating student connections...")
        for matric_no, mac_address in test_students:
            # Report device connection
            self.report_device_connected(mac_address, f"Student_{matric_no}")
            time.sleep(1)
            
            # Verify student
            self.verify_student(matric_no)
            time.sleep(1)
            
            # Record attendance
            self.record_attendance(matric_no, mac_address)
            time.sleep(1)
        
        # Send heartbeats during session
        print("\n💓 Sending heartbeats during session...")
        for i in range(duration_minutes):
            self.send_heartbeat()
            time.sleep(30)  # Wait 30 seconds between heartbeats
        
        # Check session status
        print("\n📊 Checking session status...")
        self.get_session_status()
        
        # End session
        print("\n🔚 Ending session...")
        self.end_session()
        
        print("\n✅ Class session simulation completed!")
        return True

def main():
    parser = argparse.ArgumentParser(description="ESP32 Test Client for Django Attendance System")
    parser.add_argument("--host", required=True, help="Django backend host (e.g., your-domain.com)")
    parser.add_argument("--token", required=True, help="ESP32 device token")
    parser.add_argument("--https", action="store_true", default=True, help="Use HTTPS (default: True)")
    parser.add_argument("--test", choices=["connection", "session", "attendance", "full"], 
                       default="full", help="Type of test to run")
    
    args = parser.parse_args()
    
    # Create test client
    client = ESP32TestClient(args.host, args.token, args.https)
    
    print(f"🚀 ESP32 Test Client")
    print(f"🌐 Backend: {args.host}")
    print(f"🔐 Token: {args.token[:8]}...")
    print(f"🔒 Protocol: {'HTTPS' if args.https else 'HTTP'}")
    print("=" * 50)
    
    # Run tests based on selection
    if args.test == "connection":
        client.test_connection()
        
    elif args.test == "session":
        client.start_session()
        client.get_session_status()
        client.end_session()
        
    elif args.test == "attendance":
        client.start_session()
        client.record_attendance("2021001", "AA:BB:CC:DD:EE:01")
        client.get_session_status()
        client.end_session()
        
    elif args.test == "full":
        # Test connection first
        if not client.test_connection():
            print("❌ Cannot proceed without connection")
            return
        
        # Run full simulation
        client.simulate_class_session(duration_minutes=2)  # 2 minutes for testing
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    main()
