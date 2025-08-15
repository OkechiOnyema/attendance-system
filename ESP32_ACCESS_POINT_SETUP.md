# 🌉 ESP32 Access Point Setup Guide

## Overview

Your ESP32 will act as a **Central Hub** that creates its own WiFi network. Students and the Django server will connect to this network, and the ESP32 will monitor all connections to track attendance.

## 🚀 Quick Start

### 1. Hardware Requirements
- ESP32 DevKit or ESP32 CAM
- USB cable for programming
- Power supply (USB or external)

### 2. Software Requirements
- Arduino IDE with ESP32 board support
- Required libraries:
  - WiFi
  - HTTPClient
  - ArduinoJson
  - DNSServer

### 3. Upload Code
1. Open `esp32_attendance/esp32_attendance.ino` in Arduino IDE
2. Select your ESP32 board
3. Upload the code

## ⚙️ Configuration

### ESP32 Network Settings (`esp32_config.h`)

```cpp
// ESP32 creates its own network
#define ESP32_AP_SSID "ESP32_Attendance"     // Network name
#define ESP32_AP_PASSWORD ""                  // No password (open)
#define ESP32_AP_IP "192.168.4.1"            // ESP32 IP address
#define ESP32_AP_GATEWAY "192.168.4.1"       // Gateway
#define ESP32_AP_SUBNET "255.255.255.0"      // Subnet mask

// Django server URL (when Django connects to ESP32 network)
#define DJANGO_SERVER_URL "http://192.168.4.1:8000"
```

### Network Topology

```
┌─────────────────┐    WiFi    ┌─────────────────┐
│   Django Server │ ◄─────────► │   ESP32 Hub     │
│   (192.168.4.2) │            │ (192.168.4.1)   │
└─────────────────┘            └─────────────────┘
                                        │
                                        │ WiFi
                                        ▼
                               ┌─────────────────┐
                               │  Student Phone  │
                               │ (192.168.4.3)   │
                               └─────────────────┘
```

## 🔧 Setup Steps

### Step 1: Configure ESP32
1. **Edit `esp32_config.h`**:
   - Set your desired network name
   - Configure IP addresses
   - Update Django server URL

2. **Upload to ESP32**:
   ```bash
   # In Arduino IDE
   # Select Board: ESP32 Dev Module
   # Select Port: Your ESP32 COM port
   # Click Upload
   ```

### Step 2: Power Up ESP32
1. Connect ESP32 to power
2. Open Serial Monitor (115200 baud)
3. You should see:
   ```
   🚀 ESP32 Central Hub Starting...
   🌉 Setting up ESP32 as Central Hub...
   📡 ESP32 Hub IP address: 192.168.4.1
   ✅ ESP32 Central Hub Ready!
   📶 Network Name: ESP32_Attendance
   🔓 No password required
   ```

### Step 3: Connect Django Server
1. **On your computer, connect to ESP32 WiFi**:
   - Network: `ESP32_Attendance`
   - Password: (none)
   - IP: `192.168.4.2` (or auto)

2. **Update Django settings** (if needed):
   ```python
   # In config/settings.py
   ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', '192.168.4.1', '192.168.4.2']
   ```

3. **Start Django server**:
   ```bash
   python manage.py runserver 192.168.4.2:8000
   ```

### Step 4: Test ESP32 Communication
1. **Run the test script**:
   ```bash
   python test_esp32_access_point.py
   ```

2. **Check Serial Monitor** for ESP32 activity

## 📱 Student Experience

### For Students
1. **Connect to ESP32 WiFi**:
   - Network: `ESP32_Attendance`
   - No password required

2. **Access Django Dashboard**:
   - Open browser to: `http://192.168.4.2:8000`
   - Login and mark attendance

3. **Automatic Tracking**:
   - ESP32 monitors connection
   - Django verifies network presence
   - Attendance automatically marked

### Captive Portal
When students connect, they see a welcome page:
- ✅ Connected to ESP32 network
- 💻 Access Django at: 192.168.4.2:8000
- 📱 Mark attendance through Django

## 🔌 API Endpoints

### ESP32 → Django Communication

1. **Heartbeat** (`POST /api/esp32/heartbeat/`):
   ```json
   {
     "device_id": "ESP32_CS101_001"
   }
   ```

2. **Device Connected** (`POST /api/esp32/connected/`):
   ```json
   {
     "device_id": "ESP32_CS101_001",
     "mac_address": "AA:BB:CC:DD:EE:FF",
     "device_name": "iPhone 12",
     "ip_address": "192.168.4.3"
   }
   ```

3. **Device Disconnected** (`POST /api/esp32/disconnected/`):
   ```json
   {
     "device_id": "ESP32_CS101_001",
     "mac_address": "AA:BB:CC:DD:EE:FF"
   }
   ```

4. **Active Course Check** (`POST /api/esp32/active-course/`):
   ```json
   {
     "base_device_id": "ESP32_"
   }
   ```

## 🗂️ Django Admin Setup

### 1. Create ESP32 Device
- Go to: `/admin-panel/esp32-devices/create/`
- Fill in:
  - Device ID: `ESP32_CS101_001`
  - Device Name: `CS101 Classroom ESP32`
  - SSID: `CS101_Attendance`
  - Location: `Computer Science Lab 1`

### 2. Create Network Session
- Go to: `/admin-panel/network-sessions/create/`
- Fill in:
  - ESP32 Device: Select your ESP32 device
  - Course: Select course (e.g., CS101)
  - Lecturer: Select lecturer
  - Session: `2024/2025`
  - Semester: `1st Semester`
  - Date: Today's date
  - Start Time: Current time

### 3. Monitor Connections
- View connected devices in network session
- Check ESP32 device status
- Monitor attendance records

## 🧪 Testing

### Test Script
```bash
python test_esp32_access_point.py
```

### Manual Testing
1. **Connect phone to ESP32 WiFi**
2. **Check ESP32 serial monitor** for connection logs
3. **Verify Django receives data** via API endpoints
4. **Check Django admin** for new records

## 🔍 Troubleshooting

### Common Issues

1. **ESP32 won't start**:
   - Check power supply
   - Verify code upload
   - Check serial monitor for errors

2. **Can't connect to ESP32 WiFi**:
   - Verify ESP32 is powered
   - Check network name in config
   - Try resetting ESP32

3. **Django can't reach ESP32**:
   - Ensure Django is on ESP32 network
   - Check IP addresses
   - Verify firewall settings

4. **API calls failing**:
   - Check Django server is running
   - Verify URL endpoints
   - Check network connectivity

### Debug Mode
Enable debug output in `esp32_config.h`:
```cpp
#define DEBUG_SERIAL true
#define DEBUG_HTTP true
```

## 📊 Monitoring

### ESP32 Serial Monitor
- Connection logs
- API request/response
- Device status
- Error messages

### Django Admin
- ESP32 device status
- Network sessions
- Connected devices
- Attendance records

### Network Tools
- WiFi analyzer apps
- IP scanner tools
- Network monitoring

## 🚀 Advanced Features

### Dynamic Course Configuration
- ESP32 can change SSID based on active course
- Automatic device ID generation
- Course-specific network sessions

### Scalability
- Multiple ESP32 devices
- Load balancing
- Geographic distribution

### Security
- WPA2 encryption (optional)
- MAC address filtering
- Connection logging

## 📝 Notes

- **No Password**: ESP32 network is open for easy student access
- **Static IPs**: Fixed IP addresses for reliable communication
- **Captive Portal**: Students see welcome page when connecting
- **Automatic Tracking**: No manual intervention needed
- **Real-time Updates**: Live connection monitoring

## 🎯 Next Steps

1. **Test basic functionality** with test script
2. **Create ESP32 device** in Django admin
3. **Start network session** for a course
4. **Have students connect** to ESP32 WiFi
5. **Monitor attendance** in Django dashboard

Your ESP32 access point system is now ready to revolutionize attendance tracking! 🎉
