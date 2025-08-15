# ESP32 Attendance System Setup Guide

## 🚀 Quick Setup

### 1. Configure WiFi Credentials
Edit `esp32_config.h` and update these values:

```cpp
// Replace with your actual WiFi network details
#define WIFI_NETWORK_NAME "YourActualWiFiName"
#define WIFI_NETWORK_PASSWORD "YourActualWiFiPassword"

// Update with your Django server IP address
#define DJANGO_SERVER_URL "http://YOUR_IP_ADDRESS:8000"
```

**Important:** The ESP32 needs to connect to your WiFi network to communicate with Django!

### 2. Upload Code to ESP32
1. Open `esp32_attendance/esp32_attendance.ino` in Arduino IDE
2. Install required libraries:
   - WiFi
   - HTTPClient  
   - ArduinoJson
   - DNSServer
3. Select your ESP32 board
4. Upload the code

### 3. Start Django Network Session
1. Go to Django admin: `http://YOUR_IP:8000/admin-panel/network-sessions/create/`
2. Create a new network session with:
   - Course: Select an active course
   - ESP32 Device: Select your ESP32 device
   - Duration: Set session length
3. Click "Create Session"

## 🔧 How It Works

### WiFi Modes
- **Client Mode**: Connects to your WiFi network to talk to Django
- **Access Point Mode**: Creates a WiFi network for students to connect

### Course Detection
1. ESP32 connects to your WiFi network
2. Checks Django API every minute for active courses
3. When a course is found, updates WiFi SSID to match course
4. Students connect to course-specific WiFi (no password needed)

### Attendance Tracking
1. Students connect to ESP32 WiFi
2. ESP32 records connection and sends to Django
3. Django creates attendance records automatically

## 📱 Student Experience

1. Students see WiFi network: `CS101_Attendance` (example)
2. No password required
3. Connect and get redirected to captive portal
4. Portal shows course information and confirms attendance
5. Students can close portal and use internet normally

## 🐛 Troubleshooting

### ESP32 Not Finding Courses
- ✅ Check WiFi credentials in `esp32_config.h`
- ✅ Ensure Django server is running
- ✅ Verify Django server IP is correct
- ✅ Check if network session is active in Django

### WiFi Connection Issues
- ✅ ESP32 must be in range of your WiFi network
- ✅ Check WiFi password is correct
- ✅ Ensure WiFi network supports 2.4GHz (ESP32 limitation)

### Django Communication Issues
- ✅ Check Django server is accessible from ESP32's network
- ✅ Verify firewall settings allow HTTP traffic
- ✅ Check Django logs for API errors

### Serial Monitor Output
Expected startup sequence:
```
🚀 ESP32 Dynamic Attendance System Starting...
📡 Connecting to WiFi: YourWiFiName
✅ WiFi Client Connected!
📡 IP Address: 192.168.1.xxx
🔍 Checking for active course sessions...
🌐 Making API call to Django...
📥 Response received: {"active_course": true, ...}
✅ Active course session found!
📚 Course: CS101
📶 SSID: CS101_Attendance
✅ WiFi configuration updated successfully!
```

## 🔄 Testing

### Test ESP32 Integration
Run the test script:
```bash
python test_esp32_integration.py
```

### Test Django API Directly
```bash
curl -X POST http://YOUR_IP:8000/admin-panel/api/esp32/active-course/ \
  -H "Content-Type: application/json" \
  -d '{"base_device_id": "ESP32_", "request_type": "course_check"}'
```

## 📊 Monitoring

### Django Admin
- Network Sessions: `http://YOUR_IP:8000/admin-panel/network-sessions/`
- ESP32 Devices: `http://YOUR_IP:8000/admin-panel/esp32-devices/`
- Attendance Records: `http://YOUR_IP:8000/admin-panel/attendance-records/`

### ESP32 Serial Monitor
- Real-time connection status
- Course detection logs
- Device connection tracking
- Error messages and debugging info

## 🎯 Next Steps

1. **Configure WiFi credentials** in `esp32_config.h`
2. **Upload code** to your ESP32
3. **Create network session** in Django
4. **Test with student devices**
5. **Monitor attendance** in Django admin

## 💡 Tips

- Use a static IP for Django server if possible
- Keep ESP32 close to WiFi router for stable connection
- Test with one student device first
- Check serial monitor for detailed debugging info
- Restart ESP32 after changing configuration

## 🆘 Need Help?

1. Check serial monitor output
2. Verify Django server is running
3. Test API endpoints manually
4. Check WiFi network compatibility
5. Review Django logs for errors

The ESP32 will now properly connect to your WiFi network and communicate with Django to get active course information! 🎉
