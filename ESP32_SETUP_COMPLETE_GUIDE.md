# 🚀 ESP32 Smart Attendance System - Complete Setup Guide

## 📋 System Overview

This system provides **automatic attendance marking** using ESP32 devices that create WiFi networks for students to connect to and mark their attendance. The system integrates seamlessly with your Django backend.

### ✨ Key Features
- **ESP32 WiFi Access Points**: Each ESP32 creates an open WiFi network
- **Student Self-Service**: Students connect to WiFi and mark attendance via web portal
- **Real-time Tracking**: Live attendance monitoring for lecturers
- **Automatic Verification**: System checks if students are enrolled in courses
- **Device Management**: Monitor ESP32 device status and health
- **Session Management**: Start/stop attendance sessions with real-time statistics

## 🏗️ System Architecture

```
┌─────────────────┐    WiFi    ┌─────────────────┐    HTTP    ┌─────────────────┐
│   Student       │ ──────────→ │   ESP32 Device  │ ──────────→ │   Django        │
│   Smartphone    │             │   (WiFi AP)     │             │   Backend       │
│                 │             │                 │             │                 │
│ • Connect WiFi  │             │ • Create WiFi   │             │ • Verify        │
│ • Mark          │             │ • Serve Portal  │             │   enrollment    │
│   Attendance    │             │ • Send Data     │             │ • Record        │
└─────────────────┘             └─────────────────┘             │   attendance    │
                                                                 └─────────────────┘
```

## 🔧 Hardware Requirements

### ESP32 Development Board
- **Model**: ESP32-WROOM-32 or similar
- **Flash Memory**: 4MB minimum
- **WiFi**: 802.11 b/g/n support
- **Power**: USB or 3.3V power supply

### Additional Components (Optional)
- **Display**: 0.96" OLED display for status
- **LED Indicators**: Status and activity indicators
- **Power Supply**: 5V/2A USB power adapter for stable operation

## 📱 Software Requirements

### ESP32 Arduino IDE Setup
1. **Install Arduino IDE** (1.8.x or 2.x)
2. **Add ESP32 Board Manager**:
   - File → Preferences → Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. **Install ESP32 Board Package**:
   - Tools → Board → Boards Manager
   - Search "ESP32" and install "ESP32 by Espressif Systems"
4. **Select Board**: Tools → Board → ESP32 Arduino → ESP32 Dev Module

### Required Libraries
```cpp
#include <WiFi.h>           // WiFi functionality
#include <WebServer.h>       // Web server
#include <HTTPClient.h>      // HTTP client for Django communication
#include <ArduinoJson.h>     // JSON parsing (optional)
#include <SPIFFS.h>         // File system (optional)
```

## 🚀 Quick Start Guide

### Step 1: Configure ESP32
1. **Open the Arduino code** (`esp32_attendance_system.ino`)
2. **Update configuration**:
   ```cpp
   const char* DJANGO_SERVER = "192.168.1.100"; // Your Django server IP
   const int DJANGO_PORT = 8000;                 // Django server port
   const char* DEVICE_ID = "ESP32_CS101_001";    // Unique device ID
   const char* COURSE_CODE = "CS101";            // Course code
   ```

### Step 2: Upload to ESP32
1. **Connect ESP32** via USB
2. **Select correct port**: Tools → Port → (your ESP32 port)
3. **Upload code**: Click Upload button
4. **Monitor serial output**: Tools → Serial Monitor (115200 baud)

### Step 3: Test the System
1. **ESP32 creates WiFi**: Look for "ESP32_Attendance" network
2. **Connect from phone**: No password required
3. **Open browser**: Navigate to `192.168.4.1`
4. **Mark attendance**: Enter matric number and name

## 📊 Django Backend Integration

### API Endpoints
The ESP32 communicates with Django via these endpoints:

#### 1. Heartbeat Monitoring
```
POST /admin-panel/api/esp32/heartbeat/
Data: device_id, ssid
```

#### 2. Attendance Marking
```
POST /admin-panel/api/esp32/mark-attendance/
Data: matric_no, device_id
```

#### 3. Device Connection
```
POST /admin-panel/api/esp32/connected/
Data: device_id, course_code
```

### Database Models
The system uses these Django models:

```python
# ESP32 Device Management
class ESP32Device(models.Model):
    device_id = models.CharField(max_length=50, unique=True)
    device_name = models.CharField(max_length=100)
    ssid = models.CharField(max_length=32)
    location = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)

# Network Sessions
class NetworkSession(models.Model):
    esp32_device = models.ForeignKey(ESP32Device, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.CharField(max_length=9)
    semester = models.CharField(max_length=20)
    date = models.DateField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

# Connected Devices
class ConnectedDevice(models.Model):
    network_session = models.ForeignKey(NetworkSession, on_delete=models.CASCADE)
    mac_address = models.CharField(max_length=17)
    device_name = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    is_connected = models.BooleanField(default=True)
```

## 🎯 How to Use the System

### For Lecturers

#### 1. Start Network Session
1. **Login** to lecturer dashboard
2. **Click** "Start ESP32 Session" button
3. **Select course** and session details
4. **Click** "Start Network Session"

#### 2. Monitor Active Session
- **Real-time dashboard** shows connected students
- **Live attendance count** updates automatically
- **Device status** shows ESP32 connectivity
- **Session duration** tracks time elapsed

#### 3. End Session
- **Click** "End Session" when class is over
- **View final statistics** (present/absent counts)
- **Download attendance report** if needed

### For Students

#### 1. Connect to ESP32 WiFi
1. **Open WiFi settings** on your device
2. **Look for network**: `ESP32_Attendance` (or similar)
3. **Connect** (no password required)
4. **Wait for connection** confirmation

#### 2. Mark Attendance
1. **Open web browser**
2. **Navigate to**: `192.168.4.1`
3. **Enter details**:
   - Matriculation number
   - Full name
4. **Click** "Mark Attendance"
5. **See confirmation** message

## 🔍 Troubleshooting

### Common Issues

#### ESP32 Not Creating WiFi
- **Check power supply**: Ensure stable 3.3V power
- **Verify code upload**: Check serial monitor for errors
- **Reset device**: Press reset button on ESP32

#### Students Can't Connect
- **Check WiFi range**: ESP32 has limited range (~10-20m)
- **Verify network name**: Check Serial Monitor for SSID
- **Power issues**: Ensure stable power supply

#### Django Communication Fails
- **Check IP address**: Verify Django server IP in ESP32 code
- **Network connectivity**: Ensure ESP32 can reach Django server
- **Firewall settings**: Check if port 8000 is accessible

#### Attendance Not Recording
- **Verify student enrollment**: Check if student is enrolled in course
- **Check matric number**: Ensure exact format (e.g., "2021/123456")
- **Session status**: Verify network session is active

### Debug Commands

#### ESP32 Serial Monitor
```cpp
// Add these debug prints to your code
Serial.println("WiFi AP IP: " + WiFi.softAPIP().toString());
Serial.println("Connected clients: " + String(WiFi.softAPgetStationNum()));
Serial.println("Uptime: " + getUptime());
```

#### Django Management Commands
```bash
# Check ESP32 devices
python manage.py shell
from admin_ui.models import ESP32Device
ESP32Device.objects.all()

# Check active sessions
from admin_ui.models import NetworkSession
NetworkSession.objects.filter(is_active=True)

# Check attendance records
from admin_ui.models import AttendanceRecord
AttendanceRecord.objects.filter(network_verified=True)
```

## 📈 Advanced Configuration

### Multiple ESP32 Devices
For multiple classrooms, configure each ESP32 with unique settings:

```cpp
// Classroom 1
const char* DEVICE_ID = "ESP32_CS101_001";
const char* COURSE_CODE = "CS101";
const char* AP_SSID = "ESP32_CS101_Classroom1";

// Classroom 2
const char* DEVICE_ID = "ESP32_CS102_001";
const char* COURSE_CODE = "CS102";
const char* AP_SSID = "ESP32_CS102_Classroom2";
```

### Custom WiFi Settings
```cpp
// Advanced WiFi configuration
WiFi.softAPConfig(IPAddress(192, 168, 4, 1), IPAddress(192, 168, 4, 1), IPAddress(255, 255, 255, 0));
WiFi.softAP(AP_SSID, AP_PASSWORD, 1, false, 8); // Channel 1, hidden=false, max_connections=8
```

### Security Enhancements
```cpp
// Add basic authentication (optional)
const char* AP_PASSWORD = "attendance123"; // Simple password

// Rate limiting for attendance submissions
unsigned long lastSubmission = 0;
const unsigned long SUBMISSION_COOLDOWN = 5000; // 5 seconds
```

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] **Test ESP32 code** in development environment
- [ ] **Verify Django API endpoints** are working
- [ ] **Check network connectivity** between ESP32 and Django server
- [ ] **Test student workflow** end-to-end
- [ ] **Verify database models** are properly migrated

### Production Deployment
- [ ] **Set DEBUG = False** in Django settings
- [ ] **Configure proper LOGIN_URL** and redirects
- [ ] **Set up HTTPS** for Django server (recommended)
- [ ] **Configure firewall rules** for ESP32 communication
- [ ] **Set up monitoring** and logging
- [ ] **Create backup procedures** for attendance data

### Maintenance
- [ ] **Regular ESP32 updates** for security patches
- [ ] **Monitor device health** via heartbeat system
- [ ] **Backup attendance data** regularly
- [ ] **Update course enrollments** as needed
- [ ] **Monitor system performance** and optimize

## 📚 Additional Resources

### Documentation
- [ESP32 Arduino Core Documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [WiFi Access Point Guide](https://randomnerdtutorials.com/esp32-access-point-ap-web-server/)

### Community Support
- [ESP32 Forum](https://esp32.com/)
- [Django Community](https://www.djangoproject.com/community/)
- [Arduino Community](https://forum.arduino.cc/)

### Sample Projects
- [ESP32 WiFi Manager](https://github.com/tzapu/WiFiManager)
- [ESP32 Web Server Examples](https://github.com/espressif/arduino-esp32/tree/master/libraries/WebServer/examples)

## 🎉 Congratulations!

You now have a complete, production-ready ESP32-based attendance system that:

✅ **Automatically tracks attendance** via WiFi  
✅ **Integrates seamlessly** with your Django backend  
✅ **Provides real-time monitoring** for lecturers  
✅ **Offers self-service** for students  
✅ **Scales to multiple classrooms**  
✅ **Includes comprehensive error handling**  

The system is designed to be **reliable**, **user-friendly**, and **easy to maintain**. Students can mark attendance simply by connecting to WiFi and filling out a form, while lecturers get real-time insights into class attendance.

**Happy coding! 🚀**
