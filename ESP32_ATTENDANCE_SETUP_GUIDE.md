# 🚀 ESP32 Secure Attendance System Setup Guide

This guide will walk you through setting up the complete ESP32-based attendance system with secure communication to your Django backend.

## 📋 Prerequisites

- ESP32 development board
- Arduino IDE with ESP32 board support
- Django backend running on Render/Supabase
- Required Arduino libraries (see below)

## 📚 Required Arduino Libraries

Install these libraries in Arduino IDE:

1. **WiFi** (built-in with ESP32)
2. **WiFiClientSecure** (built-in with ESP32)
3. **ArduinoJson** (by Benoit Blanchon) - Version 6.x
4. **DNSServer** (built-in with ESP32)
5. **WebServer** (built-in with ESP32)
6. **EEPROM** (built-in with ESP32)

## 🔧 Step 1: Django Backend Setup

### 1.1 Create ESP32 Device in Django Admin

1. Go to your Django admin panel
2. Navigate to **ESP32 Devices**
3. Click **Add ESP32 Device**
4. Fill in the details:
   - **Device ID**: `ESP32_CS101_001` (unique identifier)
   - **Device Name**: `CS101_Classroom_ESP32`
   - **SSID**: `CS101_Attendance`
   - **Password**: `attendance123`
   - **Location**: `Computer Science Lab 1`
   - **Is Active**: ✅ Checked

5. Save the device and note the **Device ID** - this is your authentication token

### 1.2 Verify API Endpoints

Your Django backend now has these secure API endpoints:

- `POST /api/esp32/start-session/` - Start attendance session
- `POST /api/esp32/end-session/` - End attendance session
- `POST /api/esp32/device-connected/` - Report device connection
- `POST /api/esp32/device-disconnected/` - Report device disconnection
- `POST /api/esp32/record-attendance/` - Record student attendance
- `POST /api/esp32/heartbeat/` - Send device heartbeat
- `GET /api/esp32/session-status/` - Get session status
- `POST /api/esp32/verify-student/` - Verify student enrollment

## 🔌 Step 2: ESP32 Hardware Setup

### 2.1 Connect ESP32

1. Connect ESP32 to your computer via USB
2. Open Arduino IDE
3. Select board: **Tools → Board → ESP32 Arduino → ESP32 Dev Module**
4. Select port: **Tools → Port → [Your ESP32 Port]**

### 2.2 Configure ESP32 Code

1. Open `esp32_secure_attendance.ino` in Arduino IDE
2. Update these configuration values:

```cpp
// Configuration
#define DEVICE_ID "ESP32_CS101_001"  // Must match Django admin
#define DEVICE_NAME "CS101_Classroom_ESP32"
#define WIFI_SSID "CS101_Attendance"
#define WIFI_PASSWORD "attendance123"

// Django Backend Configuration
#define DJANGO_HOST "your-domain.onrender.com"  // Your actual domain
#define DJANGO_PORT 443
#define DJANGO_TOKEN "ESP32_CS101_001"  // Your device ID from Django admin
```

### 2.3 Upload Code

1. Click **Verify** to check for errors
2. Click **Upload** to flash the ESP32
3. Open **Serial Monitor** (Tools → Serial Monitor)
4. Set baud rate to **115200**

## 📱 Step 3: Testing the System

### 3.1 Test ESP32 Setup

1. Power on the ESP32
2. Check Serial Monitor for:
   ```
   🚀 ESP32 Secure Attendance System Starting...
   📡 Setting up WiFi Access Point...
   ✅ WiFi AP 'CS101_Attendance' created successfully
   🌐 AP IP: 192.168.4.1
   ✅ ESP32 Attendance System Ready!
   ```

3. On your phone/computer, connect to WiFi network `CS101_Attendance`
4. Open browser and go to `192.168.4.1`
5. You should see the attendance system status page

### 3.2 Test Django Communication

1. Install the Python test client:
   ```bash
   pip install requests
   ```

2. Run the test client:
   ```bash
   python esp32_test_client.py --host your-domain.onrender.com --token ESP32_CS101_001
   ```

3. The test will simulate a complete class session

## 🎓 Step 4: Using the System

### 4.1 Start Attendance Session

1. **Lecturer starts class**:
   - ESP32 automatically creates WiFi network
   - Students connect to `CS101_Attendance` WiFi
   - ESP32 detects connected devices
   - Django backend records connections

2. **Record attendance**:
   - Students can mark attendance through the web interface
   - ESP32 verifies student enrollment
   - Attendance is recorded in Django database

### 4.2 Monitor Session

- **Real-time status**: Visit `192.168.4.1` on any connected device
- **Connected devices**: See all students currently connected
- **Session statistics**: View attendance count and course info

### 4.3 End Session

- ESP32 automatically ends session when class ends
- All attendance records are saved
- Device connection logs are maintained

## 🔐 Security Features

### Authentication
- **Bearer Token**: Each ESP32 has unique device ID
- **Device Verification**: Only registered devices can communicate
- **Session Validation**: Attendance only recorded during active sessions

### Data Protection
- **HTTPS Communication**: Encrypted data transmission
- **MAC Address Tracking**: Prevents duplicate submissions
- **Network Verification**: Students must be connected to ESP32 network

### Access Control
- **Course Enrollment**: Only enrolled students can mark attendance
- **Lecturer Assignment**: Only assigned lecturers can start sessions
- **Device Whitelisting**: Only authorized ESP32 devices accepted

## 🚨 Troubleshooting

### Common Issues

1. **ESP32 won't connect to Django**:
   - Check `DJANGO_HOST` and `DJANGO_TOKEN`
   - Verify Django backend is running
   - Check firewall settings

2. **WiFi network not visible**:
   - Verify ESP32 code uploaded correctly
   - Check Serial Monitor for errors
   - Restart ESP32

3. **Attendance not recording**:
   - Check if session is active
   - Verify student enrollment
   - Check Django admin for errors

4. **Device not authenticating**:
   - Verify Device ID matches Django admin
   - Check if device is marked as active
   - Regenerate device token if needed

### Debug Mode

Enable debug output by adding to ESP32 code:
```cpp
#define DEBUG_MODE true

if (DEBUG_MODE) {
    Serial.println("Debug: " + message);
}
```

## 📊 Monitoring and Analytics

### Django Admin Features

- **Real-time Sessions**: View active attendance sessions
- **Device Status**: Monitor ESP32 device health
- **Attendance Reports**: Generate attendance statistics
- **Connection Logs**: Track student device connections

### ESP32 Status Page

- **System Health**: WiFi status and device info
- **Connected Devices**: Real-time student connection list
- **Session Status**: Current course and attendance count
- **Network Info**: WiFi configuration and IP addresses

## 🔄 Maintenance

### Regular Tasks

1. **Check Device Health**: Monitor heartbeat status
2. **Update Device Tokens**: Rotate tokens periodically
3. **Review Logs**: Check for connection issues
4. **Backup Data**: Export attendance records regularly

### Updates

1. **ESP32 Code**: Upload new versions as needed
2. **Django Backend**: Deploy updates through Render
3. **Security Patches**: Keep libraries updated
4. **Feature Additions**: Add new attendance methods

## 📞 Support

### Getting Help

1. **Check Serial Monitor**: ESP32 debug output
2. **Django Logs**: Backend error messages
3. **Network Status**: WiFi connection issues
4. **Documentation**: This guide and code comments

### Common Commands

```bash
# Test Django connection
python esp32_test_client.py --host your-domain.com --token your-token --test connection

# Test full session
python esp32_test_client.py --host your-domain.com --token your-token --test full

# Check ESP32 status
# Visit 192.168.4.1 in browser
```

## 🎯 Next Steps

1. **Deploy to Production**: Use real domain and HTTPS
2. **Add More Features**: QR codes, fingerprint scanning
3. **Scale Up**: Multiple ESP32 devices for different classrooms
4. **Integration**: Connect with existing student management systems

---

**🎉 Congratulations!** You now have a fully functional, secure ESP32-based attendance system integrated with your Django backend.

**Need help?** Check the troubleshooting section or review the code comments for detailed explanations.
