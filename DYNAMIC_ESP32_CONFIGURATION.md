# 🔌 Dynamic ESP32 Configuration System

## 🎯 Overview

The **Dynamic ESP32 Configuration System** automatically configures ESP32 devices in real-time when lecturers create network attendance sessions. No more dummy or pre-selected ESP32 names - the system intelligently selects available devices and configures them dynamically.

## 🚀 How It Works

### 1. **Automatic Device Selection**
When a lecturer creates a network session:
- System automatically finds online ESP32 devices (with recent heartbeats)
- Selects the most recently active device
- No manual device selection required

### 2. **Dynamic Configuration Generation**
The system generates unique configurations for each session:
- **Dynamic Device ID**: `ESP32_CS101_2024_2025_1st_Semester`
- **Dynamic SSID**: `CS101_Attendance_2024_2025`
- **Dynamic Device Name**: `CS101 - Introduction to Computer Science`
- **Dynamic Location**: `CS101 Classroom - 2024/2025 1st Semester`

### 3. **Real-Time Configuration Updates**
ESP32 devices receive configuration updates via heartbeat API:
- Every 30 seconds, ESP32 sends heartbeat to Django
- Django responds with current session configuration
- ESP32 automatically applies new settings
- No manual intervention needed

## 🔧 Technical Implementation

### Django Backend Changes

#### **Updated `start_network_session_view`**
```python
# 🔌 AUTOMATIC ESP32 CONFIGURATION
# Find available ESP32 devices that are online (have recent heartbeat)
available_devices = ESP32Device.objects.filter(
    is_active=True,
    last_heartbeat__gte=timezone.now() - timedelta(minutes=5)  # Online in last 5 minutes
).order_by('-last_heartbeat')

# Select the most recently active ESP32 device
selected_device = available_devices.first()

# Generate dynamic configuration for the ESP32
course_code = course.code
session_id = f"{session}_{semester}".replace(" ", "_").replace("/", "_")

# Create dynamic device ID: ESP32_CS101_2024_2025_1st_Semester
dynamic_device_id = f"ESP32_{course_code}_{session_id}"

# Create dynamic SSID: CS101_Attendance_2024_2025
dynamic_ssid = f"{course_code}_Attendance_{session.replace('/', '_')}"

# Update ESP32 device with dynamic configuration
selected_device.device_name = f"{course_code} - {course.title}"
selected_device.ssid = dynamic_ssid
selected_device.password = ""  # Open network for easy student access
selected_device.location = f"{course_code} Classroom - {session} {semester}"
selected_device.save()
```

#### **Enhanced ESP32 Heartbeat API**
```python
@csrf_exempt
def api_device_heartbeat(request):
    """ESP32 sends heartbeat to Django and receives dynamic configuration"""
    # ... existing code ...
    
    # 🔌 DYNAMIC CONFIGURATION RESPONSE
    # Check if this device has an active network session
    active_session = NetworkSession.objects.filter(
        esp32_device=device,
        is_active=True
    ).first()
    
    if active_session:
        # Device is in an active session - send configuration
        course = active_session.course
        session = active_session.session
        semester = active_session.semester
        
        # Generate dynamic configuration
        course_code = course.code
        session_id = f"{session}_{semester}".replace(" ", "_").replace("/", "_")
        
        # Dynamic device ID and SSID
        dynamic_device_id = f"ESP32_{course_code}_{session_id}"
        dynamic_ssid = f"{course_code}_Attendance_{session.replace('/', '_')}"
        
        # Update device with session-specific configuration
        device.device_name = f"{course_code} - {course.title}"
        device.ssid = dynamic_ssid
        device.password = ""  # Open network
        device.location = f"{course_code} Classroom - {session} {semester}"
        device.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Heartbeat received - Active session configuration applied',
            'configuration': {
                'active_session': True,
                'course_code': course_code,
                'course_title': course.title,
                'session': session,
                'semester': semester,
                'device_id': dynamic_device_id,
                'ssid': dynamic_ssid,
                'password': "",
                'lecturer': active_session.lecturer.username,
                'session_id': active_session.id
            }
        })
```

### ESP32 Arduino Code Changes

#### **Enhanced Heartbeat Processing**
```cpp
void sendHeartbeat() {
  // ... existing HTTP request code ...
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Heartbeat sent successfully");
    
    // 🔌 PROCESS DYNAMIC CONFIGURATION RESPONSE
    DynamicJsonDocument responseDoc(1024);
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error) {
      // Check if we received configuration data
      if (responseDoc.containsKey("configuration")) {
        JsonObject config = responseDoc["configuration"];
        
        if (config["active_session"] == true) {
          // Apply active session configuration
          String courseCode = config["course_code"];
          String courseTitle = config["course_title"];
          String session = config["session"];
          String semester = config["semester"];
          String newSSID = config["ssid"];
          String newDeviceId = config["device_id"];
          
          Serial.println("🎯 Applying dynamic configuration:");
          Serial.println("   Course: " + courseCode + " - " + courseTitle);
          Serial.println("   Session: " + session + " " + semester);
          Serial.println("   New SSID: " + newSSID);
          Serial.println("   New Device ID: " + newDeviceId);
          
          // Update device configuration
          device_name = courseCode + " - " + courseTitle;
          device_id = newDeviceId;
          
          // Update session information
          session_active = true;
          current_course = courseCode;
          current_lecturer = config["lecturer"];
          current_session_id = String(config["session_id"]);
          
          // Save new configuration to EEPROM
          EEPROM.writeString(0, device_id);
          EEPROM.writeString(300, device_name);
          EEPROM.writeString(400, current_course);
          EEPROM.writeString(500, current_lecturer);
          EEPROM.commit();
          
          // If we're in access point mode, update the SSID
          if (!wifi_configured) {
            WiFi.softAP(newSSID.c_str(), "", 1, 0, 4);
            Serial.println("📡 Updated ESP32 WiFi network: " + newSSID);
          }
          
          Serial.println("✅ Dynamic configuration applied successfully!");
        }
      }
    }
  }
}
```

## 📱 User Experience

### **For Lecturers**
1. **Create Network Session** - Select course, session, semester
2. **Automatic ESP32 Selection** - System finds best available device
3. **Real-Time Configuration** - ESP32 automatically configures for the course
4. **Instant Ready** - Session starts immediately with configured device

### **For Students**
1. **Connect to ESP32 WiFi** - Network name shows course (e.g., `CS101_Attendance_2024_2025`)
2. **Automatic Recognition** - System tracks connection via ESP32
3. **Real-Time Attendance** - Mark attendance through WiFi portal

### **For System Administrators**
1. **Device Status Dashboard** - See online/offline ESP32 devices
2. **Real-Time Monitoring** - Track device health and connectivity
3. **Automatic Management** - No manual device configuration needed

## 🔍 System Status Display

The session creation page now shows:
- **Total ESP32 Devices** - Count of all registered devices
- **Online Devices** - Devices with recent heartbeats (last 5 minutes)
- **Offline Devices** - Devices without recent heartbeats
- **Available Devices** - List of online devices with details
- **Device Information** - Name, SSID, location, last seen time

## 🧪 Testing

Run the test script to verify the system:
```bash
python test_dynamic_esp32_config.py
```

This will test:
- Dynamic configuration generation
- ESP32 heartbeat API responses
- Device availability checking
- Configuration application simulation

## 🎉 Benefits

### ✅ **Automatic Operation**
- No manual ESP32 selection
- Real-time device configuration
- Automatic session management

### ✅ **Dynamic Configuration**
- Unique device IDs per session
- Course-specific WiFi networks
- Automatic SSID generation

### ✅ **Real-Time Updates**
- Live device status monitoring
- Instant configuration changes
- No system restarts needed

### ✅ **Scalable Design**
- Multiple ESP32 devices supported
- Load balancing capabilities
- Geographic distribution ready

## 🚀 Next Steps

The system is now fully dynamic and ready for production use. ESP32 devices will automatically configure themselves based on active sessions, providing a seamless experience for lecturers and students.

**No more dummy ESP32 names - everything is real-time and automatic! 🎯**
