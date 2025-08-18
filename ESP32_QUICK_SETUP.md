# 🚀 ESP32 Quick Setup Guide - Your Django Server

## ⚡ Quick Configuration

### **Step 1: Update Django Server IP**
In the ESP32 code, change this line:

```cpp
// Django Server Configuration
const char* DJANGO_SERVER = "192.168.4.100";  // UPDATE: Your Django server IP
```

**To your actual Django server IP address:**

```cpp
// Django Server Configuration
const char* DJANGO_SERVER = "192.168.1.100";  // Your actual Django server IP
```

### **Step 2: Customize Device Settings**
Update these values for your specific ESP32:

```cpp
// ESP32 Device Configuration
const char* DEVICE_ID = "ESP32_CS101_001";    // Make unique per device
const char* DEVICE_NAME = "CS101_Classroom";  // Descriptive name
const char* LOCATION = "Computer Science Building Room 101"; // Actual location

// WiFi Configuration
const char* WIFI_PREFIX = "CS101_Attendance_"; // WiFi network name prefix
```

## 🔧 **How to Find Your Django Server IP**

### **Option 1: Check Your Computer's IP**
1. **Open Command Prompt** (Windows) or **Terminal** (Mac/Linux)
2. **Run**: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
3. **Look for**: Your computer's IP address (usually starts with `192.168.1.` or `192.168.4.`)

### **Option 2: Check Django Server Logs**
When you run `python manage.py runserver`, Django shows:
```
Starting development server at http://127.0.0.1:8000/
```
- `127.0.0.1` = localhost (only accessible from same computer)
- You need your **network IP** (like `192.168.1.100`)

### **Option 3: Use Network Scanner**
1. **Download** a network scanner app
2. **Scan** your network for devices
3. **Find** your computer's IP address

## 📱 **Multiple ESP32 Devices Setup**

### **Classroom 1 - Computer Science**
```cpp
const char* DEVICE_ID = "ESP32_CS101_001";
const char* DEVICE_NAME = "CS101_Computer_Science";
const char* LOCATION = "Computer Science Building Room 101";
const char* WIFI_PREFIX = "CS101_Attendance_";
```

### **Classroom 2 - Mathematics**
```cpp
const char* DEVICE_ID = "ESP32_MATH201_001";
const char* DEVICE_NAME = "MATH201_Mathematics";
const char* LOCATION = "Mathematics Building Room 201";
const char* WIFI_PREFIX = "MATH201_Attendance_";
```

### **Classroom 3 - Engineering**
```cpp
const char* DEVICE_ID = "ESP32_ENG301_001";
const char* DEVICE_NAME = "ENG301_Engineering";
const char* LOCATION = "Engineering Building Room 301";
const char* WIFI_PREFIX = "ENG301_Attendance_";
```

## 🌐 **Network Configuration Examples**

### **Home Network (192.168.1.x)**
```cpp
const char* DJANGO_SERVER = "192.168.1.100";  // Your computer's IP
const int DJANGO_PORT = 8000;
```

### **School Network (192.168.4.x)**
```cpp
const char* DJANGO_SERVER = "192.168.4.100";  // Your computer's IP
const int DJANGO_PORT = 8000;
```

### **Custom Network (10.0.0.x)**
```cpp
const char* DJANGO_SERVER = "10.0.0.100";     // Your computer's IP
const int DJANGO_PORT = 8000;
```

## ✅ **Configuration Checklist**

Before uploading to ESP32:

- [ ] **Django Server IP** - Set to your computer's actual IP address
- [ ] **Device ID** - Make unique for each ESP32
- [ ] **Device Name** - Descriptive name for the device
- [ ] **Location** - Actual physical location
- [ ] **WiFi Prefix** - Choose a meaningful prefix
- [ ] **Port Number** - Usually 8000 for Django development

## 🚀 **Upload and Test**

1. **Connect ESP32** via USB
2. **Select correct port** in Arduino IDE
3. **Upload code** to ESP32
4. **Open Serial Monitor** (115200 baud)
5. **Look for**:
   ```
   === ESP32 Dynamic Smart Attendance System ===
   Setting up WiFi Access Point...
   WiFi AP IP address: 192.168.4.1
   SSID: CS101_Attendance_ESP32_CS101_001
   Students can now connect to this WiFi network
   ```

## 📱 **Test Student Connection**

1. **Connect phone** to WiFi network `CS101_Attendance_ESP32_CS101_001`
2. **Open browser** and go to `192.168.4.1`
3. **Should see**: "Waiting for active session..." message
4. **Start session** from Django lecturer dashboard
5. **Refresh page** - should now show attendance form

## 🔍 **Troubleshooting**

### **ESP32 Not Creating WiFi**
- Check power supply
- Verify code upload success
- Check Serial Monitor for errors

### **Can't Connect to Django**
- Verify IP address is correct
- Check if Django server is running
- Ensure both devices are on same network

### **Students Can't Connect**
- Check WiFi range (~10-20m)
- Verify network name in WiFi settings
- Ensure stable power supply

## 🎯 **Your Specific Setup**

Based on your Django server, you'll need to:

1. **Find your computer's IP address** on your network
2. **Update the ESP32 code** with that IP address
3. **Choose unique device IDs** for each ESP32
4. **Test the connection** between ESP32 and Django

**Example for your setup:**
```cpp
const char* DJANGO_SERVER = "192.168.1.100";  // Your actual IP
const char* DEVICE_ID = "ESP32_001";          // First device
const char* DEVICE_NAME = "Main_Classroom";   // Descriptive name
const char* LOCATION = "Main Building Room 101"; // Your location
const char* WIFI_PREFIX = "Attendance_";      // WiFi prefix
```

This will create a WiFi network named: `Attendance_ESP32_001`

**Happy coding! 🚀**
