# 🚀 ESP32 Dynamic Attendance System - Quick Start

## ⚡ **Get Running in 5 Minutes!**

### **1. 🔌 Hardware Setup**
- Connect ESP32 to your computer via USB
- Ensure power LED is on

### **2. 📱 Create ESP32 Device in Django**
1. Go to Django admin: `http://127.0.0.1:8000/admin-panel/esp32-devices/`
2. Click "Add ESP32 Device"
3. Fill in:
   - **Device ID**: `ESP32_DYNAMIC` (will auto-generate course-specific IDs)
   - **Device Name**: `Dynamic Course ESP32`
   - **SSID**: `Dynamic` (will auto-generate course-specific SSIDs)
   - **Password**: Leave empty (WiFi is open)
   - **Location**: `Computer Science Lab 1`
4. Click "Save"

### **3. 💻 Upload Code to ESP32**
1. Open Arduino IDE
2. Open `esp32_attendance.ino`
3. Select ESP32 board: **Tools** → **Board** → **ESP32 Arduino** → **ESP32 Dev Module**
4. Select port: **Tools** → **Port** → **COM[X]** (where ESP32 appears)
5. Click **Upload** button (→)

### **4. 🌐 Test Integration**
1. Install test dependencies:
   ```bash
   pip install -r requirements_esp32.txt
   ```
2. Run integration test:
   ```bash
   python test_esp32_integration.py
   ```

### **5. 📚 Start a Network Session**
1. Go to: `http://127.0.0.1:8000/admin-panel/network-sessions/create/`
2. Select your course and ESP32 device
3. Click "Start Session"
4. **ESP32 automatically detects the course and updates WiFi!**

### **6. 📶 Connect Student Device**
1. Look for WiFi network: `CS101_Attendance` (auto-generated from course)
2. **No password required!** Just connect
3. Browser opens automatically
4. See course information and "Attendance Recorded" message

### **7. 📊 Monitor in Django**
1. Go to: `http://127.0.0.1:8000/admin-panel/network-sessions/`
2. Watch real-time device connections
3. ESP32 automatically updates when courses change

## 🎯 **What Happens Automatically:**

1. **ESP32** starts with default WiFi: `ESP32_Starting`
2. **ESP32** checks Django every minute for active courses
3. **When course starts**: WiFi changes to `CS101_Attendance` (no password)
4. **Students connect**: No password needed, just tap to connect
5. **ESP32 records**: Sends course info + device data to Django
6. **When course ends**: ESP32 returns to default mode

## 🔧 **Dynamic Features:**

- ✅ **Auto SSID**: `CS101_Attendance`, `MATH201_Attendance`, etc.
- ✅ **Auto Device ID**: `ESP32_CS101_001`, `ESP32_MATH201_002`, etc.
- ✅ **No Password**: Students connect instantly
- ✅ **Course Detection**: ESP32 automatically finds active courses
- ✅ **Real-time Updates**: WiFi changes when courses start/end

## 🔧 **Troubleshooting:**

- **Upload Failed**: Hold BOOT button during upload
- **WiFi Not Updating**: Check Django server IP in ESP32 config
- **No Course Found**: Ensure network session is active in Django
- **No Devices**: Check Serial Monitor for course detection messages

## 📚 **Full Documentation:**

- **Setup Guide**: `ESP32_SETUP_GUIDE.md`
- **Arduino Code**: `esp32_attendance.ino`
- **Configuration**: `esp32_config.h`
- **Test Script**: `test_esp32_integration.py`

## 🎉 **You're Ready!**

Your ESP32 now automatically adapts to any course! Just start a network session in Django, and the ESP32 will:
- Change WiFi name to match the course
- Remove password requirement
- Update device ID automatically
- Show course information to students

**No more manual configuration needed!** 🚀
