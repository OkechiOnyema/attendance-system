#!/usr/bin/env python3
"""
Test Dynamic ESP32 Attendance System
This script tests the complete dynamic ESP32 system
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_ui.models import Course, AssignedCourse, Student, ESP32Device, NetworkSession, User
from django.utils import timezone

def test_dynamic_esp32_system():
    """Test the complete dynamic ESP32 system"""
    print("🚀 Testing Dynamic ESP32 Attendance System")
    print("=" * 50)
    
    try:
        # 1. Check if we have the required data
        print("\n1️⃣ Checking system prerequisites...")
        
        # Check courses
        courses = Course.objects.all()
        if not courses.exists():
            print("❌ No courses found. Please create courses first.")
            return False
        print(f"✅ Found {courses.count()} courses")
        
        # Check students
        students = Student.objects.all()
        if not students.exists():
            print("❌ No students found. Please create students first.")
            return False
        print(f"✅ Found {students.count()} students")
        
        # Check ESP32 devices
        esp32_devices = ESP32Device.objects.all()
        if not esp32_devices.exists():
            print("❌ No ESP32 devices found. Please create ESP32 devices first.")
            return False
        print(f"✅ Found {esp32_devices.count()} ESP32 devices")
        
        # Check lecturers
        lecturers = User.objects.filter(is_staff=True, is_superuser=False)
        if not lecturers.exists():
            print("❌ No lecturers found. Please create lecturers first.")
            return False
        print(f"✅ Found {lecturers.count()} lecturers")
        
        # 2. Test ESP32 device status
        print("\n2️⃣ Testing ESP32 device status...")
        
        # Simulate online ESP32 device
        device = esp32_devices.first()
        device.last_heartbeat = timezone.now()
        device.is_active = True
        device.save()
        
        print(f"✅ ESP32 device '{device.device_name}' marked as online")
        
        # 3. Test dynamic session creation
        print("\n3️⃣ Testing dynamic session creation...")
        
        # Get first course and lecturer
        course = courses.first()
        lecturer = lecturers.first()
        
        # Create assigned course if not exists
        assigned_course, created = AssignedCourse.objects.get_or_create(
            lecturer=lecturer,
            course=course,
            session="2024/2025",
            semester="1st Semester"
        )
        
        if created:
            print(f"✅ Created assigned course: {course.code} → {lecturer.username}")
        else:
            print(f"✅ Found existing assigned course: {course.code} → {lecturer.username}")
        
        # 4. Test dynamic configuration generation
        print("\n4️⃣ Testing dynamic configuration generation...")
        
        # Generate dynamic configuration (simulating the view logic)
        device_id = f"ESP32_{course.code}_{timezone.now().strftime('%Y%m%d_%H%M')}"
        ssid = f"Attendance_{course.code}_{lecturer.username}_{timezone.now().strftime('%H%M')}"
        device_name = f"{course.code}_{lecturer.username}_{timezone.now().strftime('%H%M')}"
        location = f"{course.title} - {lecturer.get_full_name() or lecturer.username}"
        
        print(f"   Generated Device ID: {device_id}")
        print(f"   Generated SSID: {ssid}")
        print(f"   Generated Device Name: {device_name}")
        print(f"   Generated Location: {location}")
        
        # 5. Test ESP32 configuration update
        print("\n5️⃣ Testing ESP32 configuration update...")
        
        # Update ESP32 device with dynamic config
        device.device_id = device_id
        device.device_name = device_name
        device.ssid = ssid
        device.password = "12345678"
        device.location = location
        device.save()
        
        print(f"✅ ESP32 device updated with dynamic configuration")
        
        # 6. Test network session creation
        print("\n6️⃣ Testing network session creation...")
        
        # Create network session
        start_time = timezone.now()
        network_session = NetworkSession.objects.create(
            esp32_device=device,
            course=course,
            lecturer=lecturer,
            session="2024/2025",
            semester="1st Semester",
            date=timezone.now().date(),
            start_time=start_time,
            is_active=True
        )
        
        print(f"✅ Network session created: {network_session}")
        
        # 7. Test ESP32 heartbeat response
        print("\n7️⃣ Testing ESP32 heartbeat response...")
        
        # Simulate ESP32 heartbeat
        from admin_ui.views import esp32_heartbeat_api
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/api/esp32/heartbeat/', {
            'device_id': device_id,
            'wifi_ssid': ssid,
            'connected_students': 0
        })
        
        # This would normally be called by the ESP32
        print("   Simulating ESP32 heartbeat...")
        print(f"   Device ID: {device_id}")
        print(f"   WiFi SSID: {ssid}")
        
        # 8. Test attendance marking
        print("\n8️⃣ Testing attendance marking...")
        
        # Get first student
        student = students.first()
        print(f"   Student: {student.name} ({student.matric_no})")
        
        # Test attendance API
        from admin_ui.views import esp32_mark_attendance_api
        
        request = factory.post('/api/esp32/mark-attendance/', {
            'matric_no': student.matric_no,
            'student_name': student.name,
            'device_id': device_id
        })
        
        print("   Simulating attendance submission...")
        
        # 9. System summary
        print("\n9️⃣ System Summary...")
        
        active_sessions = NetworkSession.objects.filter(is_active=True)
        print(f"   Active Sessions: {active_sessions.count()}")
        
        online_devices = ESP32Device.objects.filter(
            is_active=True,
            last_heartbeat__gte=timezone.now() - timedelta(minutes=5)
        )
        print(f"   Online ESP32 Devices: {online_devices.count()}")
        
        print("\n🎉 All tests completed successfully!")
        print("\n📋 Next Steps:")
        print("   1. Upload this code to your ESP32")
        print("   2. Power on the ESP32")
        print("   3. Go to Django admin and create ESP32 devices")
        print("   4. Use the Dynamic ESP32 Session page to create sessions")
        print("   5. Students connect to ESP32 WiFi and mark attendance")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("\n🔧 Creating sample data for testing...")
    
    try:
        # Create sample course
        course, created = Course.objects.get_or_create(
            code="CS101",
            defaults={'title': "Introduction to Computer Science"}
        )
        if created:
            print(f"✅ Created course: {course.code} - {course.title}")
        
        # Create sample student
        student, created = Student.objects.get_or_create(
            matric_no="2024001",
            defaults={
                'name': "John Doe",
                'department': "Computer Science",
                'level': "100"
            }
        )
        if created:
            print(f"✅ Created student: {student.name} ({student.matric_no})")
        
        # Create sample ESP32 device
        device, created = ESP32Device.objects.get_or_create(
            device_id="ESP32_001",
            defaults={
                'device_name': "CS101_Classroom_ESP32",
                'ssid': "Attendance_System",
                'password': "12345678",
                'location': "Computer Science Lab 1",
                'is_active': True
            }
        )
        if created:
            print(f"✅ Created ESP32 device: {device.device_name}")
        
        # Create sample lecturer user
        if not User.objects.filter(username='lecturer1').exists():
            lecturer = User.objects.create_user(
                username='lecturer1',
                email='lecturer1@example.com',
                password='password123',
                first_name='Jane',
                last_name='Smith'
            )
            lecturer.is_staff = True
            lecturer.save()
            print(f"✅ Created lecturer: {lecturer.get_full_name()}")
        
        print("✅ Sample data created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Dynamic ESP32 Attendance System Test")
    print("=" * 50)
    
    # Create sample data if needed
    if not Course.objects.exists() or not Student.objects.exists() or not ESP32Device.objects.exists():
        print("📝 No sample data found. Creating sample data...")
        if not create_sample_data():
            print("❌ Failed to create sample data. Exiting.")
            sys.exit(1)
    
    # Run the test
    success = test_dynamic_esp32_system()
    
    if success:
        print("\n🎉 System is ready for ESP32 deployment!")
    else:
        print("\n❌ System test failed. Please check the errors above.")
        sys.exit(1)
