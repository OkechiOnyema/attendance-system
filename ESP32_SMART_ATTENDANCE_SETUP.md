# 🚀 ESP32 Smart Attendance System - Complete Setup Guide

## 🎯 **System Overview**

The ESP32 Smart Attendance System is a **physical presence authentication system** that:
- ✅ **Fetches active course sessions** automatically from Django
- ✅ **Shows course info** (code, name, session) to students
- ✅ **Students only enter matric number** (no manual course input needed)
- ✅ **Validates enrollment** before recording attendance
- ✅ **Guarantees physical presence** (must connect to ESP32 WiFi)
- ✅ **Blocks internet access** for connected devices (security)

---

## 🔧 **Hardware Requirements**

- **ESP32 Development Board** (WiFi + Bluetooth)
- **USB Cable** for programming and power
- **Computer/Laptop** with Arduino IDE
- **Mobile Phone** for testing (student device)

---

## 📱 **Network Architecture**

```
📱 Student Phone → 🔌 ESP32 WiFi (NO INTERNET) → 💻 Laptop Hotspot → 🌐 Internet → 🚀 Django Server
```

**Key Points:**
- **ESP32 connects to laptop hotspot** (for internet access to Django)
- **ESP32 creates its own WiFi network** (for students - NO INTERNET)
- **Students connect to ESP32 WiFi** (physical presence guaranteed)
- **Laptop maintains internet access** through hotspot

---

## ⚙️ **Step 1: Configure WiFi Settings**

### **Edit the ESP32 Code:**
Open `esp32_attendance/esp32_smart_attendance.ino` and update these lines:

```cpp
// ESP32 connects to your laptop hotspot for internet access
const char* WIFI_SSID = "AttendanceWiFi";        // Your laptop hotspot name
const char* WIFI_PASSWORD = "attendance123";      // Your laptop hotspot password

// ESP32 creates its own network for students (NO INTERNET ACCESS)
const char* AP_SSID = "ESP32_Attendance";
const char* AP_PASSWORD = "esp32pass123";
const char* AP_IP = "192.168.5.1";

// Django Server (Your live system)
const char* DJANGO_SERVER = "https://attendance-system-muqs.onrender.com";
```

**⚠️ IMPORTANT:** Update `WIFI_SSID` and `WIFI_PASSWORD` to match your laptop hotspot!

---

## 🔌 **Step 2: Upload Code to ESP32**

### **2.1: Open Arduino IDE**
- Launch Arduino IDE
- Go to **File → Open**
- Navigate to `esp32_attendance/esp32_smart_attendance.ino`
- Click **Open**

### **2.2: Install Required Libraries**
Go to **Tools → Manage Libraries** and install:
- `WiFi` (usually pre-installed)
- `WebServer` (usually pre-installed)
- `HTTPClient` (usually pre-installed)
- `ArduinoJson` (search and install)
- `DNSServer` (usually pre-installed)

### **2.3: Configure Board Settings**
Go to **Tools → Board** and select:
- **Board:** `ESP32 Dev Module`
- **Upload Speed:** `115200`
- **CPU Frequency:** `240MHz (WiFi/BT)`
- **Flash Frequency:** `80MHz`
- **Flash Mode:** `QIO`
- **Flash Size:** `4MB (32Mb)`
- **Partition Scheme:** `Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS)`

### **2.4: Select Port**
- Connect ESP32 via USB
- Go to **Tools → Port**
- Select the COM port where ESP32 appears

### **2.5: Upload Code**
- Click **Upload** button (→)
- Wait for compilation and upload to complete
- You should see: `"Hard resetting via RTS pin..."`

---

## 🌐 **Step 3: Setup Laptop Hotspot**

### **3.1: Enable Mobile Hotspot**
- **Windows 10/11:**
  - Go to **Settings → Network & Internet → Mobile Hotspot**
  - Turn on **Mobile Hotspot**
  - Set **Network name** to: `AttendanceWiFi`
  - Set **Network password** to: `attendance123`
  - Click **Edit** to save changes

### **3.2: Verify Hotspot**
- Your laptop should show: `"Mobile hotspot is on"`
- Note the **Network name** and **Password**
- Ensure they match the ESP32 code settings

---

## 📱 **Step 4: Test ESP32 System**

### **4.1: Open Serial Monitor**
- In Arduino IDE, click **Tools → Serial Monitor**
- Set **Baud Rate** to: `115200`
- You should see ESP32 startup messages

### **4.2: Expected Serial Output**
```
🚀 ESP32 Smart Attendance System Starting...
🎓 This system fetches active course sessions and validates enrollment
🔒 Students must connect to ESP32 to mark attendance
🌐 Connecting to laptop hotspot...
✅ Connected to laptop hotspot!
📶 Hotspot IP: 192.168.137.xxx
🎓 Fetching active course session from Django...
✅ Django response: {...}
🎓 Active Course Found!
📚 Course Code: CS101
📖 Course Name: Introduction to Computer Science
🆔 Session: 2024/2025
🌐 Setting up ESP32 WiFi network (NO INTERNET ACCESS)...
✅ ESP32 WiFi Network Started Successfully!
📶 SSID: ESP32_Attendance
🔑 Password: esp32pass123
🌐 IP Address: 192.168.5.1
🔒 Connected devices will have NO INTERNET ACCESS
🌐 Setting up Web Server...
✅ Web Server started on port 80
🔒 All external requests will be blocked
✅ ESP32 Smart Attendance System Ready!
📱 Students connect to ESP32 WiFi (NO INTERNET)
💻 Laptop keeps internet access through hotspot
🎓 ESP32 will fetch active course sessions from Django
```

### **4.3: If Connection Fails**
- **Check hotspot settings** (name/password)
- **Verify laptop hotspot is active**
- **Check WiFi credentials** in ESP32 code
- **Restart ESP32** (unplug/replug USB)

---

## 📱 **Step 5: Test Student Connection**

### **5.1: Connect Phone to ESP32**
- On your phone, go to **WiFi Settings**
- Look for network: `ESP32_Attendance`
- Enter password: `esp32pass123`
- Connect to the network

### **5.2: Access Attendance System**
- Open phone browser
- Navigate to: `http://192.168.5.1`
- You should see the **Smart Attendance System** page

### **5.3: Expected Behavior**
- **Course info displayed** (if active session exists)
- **Attendance form visible** (if course is active)
- **No internet access** (security feature)
- **All external URLs blocked** (captive portal)

---

## 🎓 **Step 6: Test Complete Flow**

### **6.1: Prerequisites**
- Django system must have **active course session**
- Student must be **enrolled in the course**
- ESP32 must be **connected to laptop hotspot**

### **6.2: Test Attendance Marking**
1. **Student connects** to ESP32 WiFi
2. **Student opens** `http://192.168.5.1`
3. **System shows** active course info
4. **Student enters** matric number
5. **Student clicks** "Mark Attendance"
6. **System validates** enrollment
7. **Attendance recorded** in Django database

### **6.3: Expected Results**
- **Success:** "✅ Attendance marked successfully!"
- **Enrollment Error:** "❌ Student is not enrolled in course"
- **No Session:** "⚠️ No active course session found"

---

## 🔒 **Security Features**

### **Physical Presence Authentication**
- ✅ Students **must connect** to ESP32 WiFi
- ✅ **No direct access** to Django server
- ✅ **Captive portal** blocks all external URLs
- ✅ **DNS server** redirects all requests to ESP32

### **Enrollment Validation**
- ✅ **Matric number verification**
- ✅ **Course enrollment check**
- ✅ **Active session validation**
- ✅ **Device tracking** (ESP32 ID)

---

## 🚨 **Troubleshooting**

### **ESP32 Won't Connect to Hotspot**
- **Check hotspot name/password** in code
- **Verify hotspot is active** on laptop
- **Check WiFi credentials** match exactly
- **Restart ESP32** and laptop

### **Students Can't Access ESP32**
- **Check ESP32 IP address** (should be 192.168.5.1)
- **Verify WiFi network** is visible
- **Check password** is correct
- **Restart ESP32** if needed

### **Attendance Not Recording**
- **Check Django system** has active course
- **Verify student enrollment** in course
- **Check ESP32 internet connection**
- **Review Django logs** for errors

### **Serial Monitor Issues**
- **Check baud rate** (115200)
- **Verify USB connection**
- **Check COM port** selection
- **Restart Arduino IDE**

---

## 📊 **System Status Indicators**

### **Serial Monitor Status**
- 🟢 **Green:** System working normally
- 🟡 **Yellow:** Warning (partial functionality)
- 🔴 **Red:** Error (system not working)

### **WiFi Status**
- ✅ **Connected:** ESP32 has internet access
- ❌ **Disconnected:** ESP32 offline mode only
- 📱 **Devices:** Number of connected students

### **Course Status**
- 🎓 **Active:** Course session available
- ⚠️ **Inactive:** No active session
- 🔄 **Refreshing:** Updating from Django

---

## 🎯 **Next Steps After Setup**

1. **Test with real students** in classroom
2. **Monitor attendance records** in Django admin
3. **Verify enrollment validation** works correctly
4. **Check physical presence** authentication
5. **Optimize WiFi settings** if needed

---

## 🆘 **Need Help?**

### **Common Issues:**
- **WiFi connection problems** → Check hotspot settings
- **Code upload errors** → Verify board configuration
- **Attendance not recording** → Check Django system
- **Students can't connect** → Verify ESP32 network

### **Debug Steps:**
1. **Check Serial Monitor** for error messages
2. **Verify WiFi credentials** match exactly
3. **Test laptop hotspot** with other devices
4. **Check Django system** is accessible
5. **Restart ESP32** and try again

---

## 🎉 **Success Indicators**

Your ESP32 Smart Attendance System is working when:
- ✅ **ESP32 connects** to laptop hotspot
- ✅ **ESP32 creates** its own WiFi network
- ✅ **Students can connect** to ESP32 WiFi
- ✅ **Students can access** attendance page
- ✅ **Course info displays** correctly
- ✅ **Attendance records** in Django
- ✅ **Enrollment validation** works
- ✅ **Physical presence** is guaranteed

---

**🚀 Congratulations! You now have a fully functional ESP32 Smart Attendance System! 🎓**
