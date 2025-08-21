/*
 * ESP32 Smart Attendance System
 * 
 * Features:
 * - Connects to lecturer's phone hotspot
 * - Hosts local web page for student attendance
 * - Validates student submissions locally
 * - Sends attendance logs to Django backend
 * - Captive portal for easy connection
 * 
 * Hardware: ESP32 DevKit
 * Libraries: WiFi, WebServer, HTTPClient, ArduinoJson, DNSServer
 */

#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DNSServer.h>
#include <EEPROM.h>

// Configuration
#define EEPROM_SIZE 512
#define SERVER_URL "https://your-render-app.onrender.com"  // Update with your Django server URL
#define API_KEY "your-secret-api-key"  // Update with your API key

// WiFi credentials (will be configured via web interface)
String wifi_ssid = "";
String wifi_password = "";
bool wifi_configured = false;

// ESP32 device info
String device_id = "ESP32_" + String(random(1000, 9999));
String device_name = "Smart Attendance Device";

// Web server and DNS server
WebServer server(80);
DNSServer dnsServer;
const byte DNS_PORT = 53;

// Session management
bool session_active = false;
String current_course = "";
String current_lecturer = "";
String current_session_id = "";

// Attendance tracking
struct AttendanceRecord {
  String matric_number;
  String student_name;
  String timestamp;
  String device_mac;
};

std::vector<AttendanceRecord> attendance_log;

// HTML page for attendance submission
const char* attendance_html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Attendance System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 15px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: #45a049;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
        }
        .success {
            background: rgba(76, 175, 80, 0.3);
            border: 1px solid #4CAF50;
        }
        .error {
            background: rgba(244, 67, 54, 0.3);
            border: 1px solid #f44336;
        }
        .info {
            background: rgba(33, 150, 243, 0.3);
            border: 1px solid #2196F3;
        }
        .device-info {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 Smart Attendance System</h1>
        
        <div class="device-info">
            <strong>Device:</strong> %DEVICE_NAME%<br>
            <strong>Course:</strong> %COURSE%<br>
            <strong>Lecturer:</strong> %LECTURER%<br>
            <strong>Status:</strong> %STATUS%
        </div>
        
        <form id="attendanceForm">
            <div class="form-group">
                <label for="matric_number">Matric Number:</label>
                <input type="text" id="matric_number" name="matric_number" 
                       placeholder="Enter your matric number" required>
            </div>
            
            <div class="form-group">
                <label for="student_name">Full Name:</label>
                <input type="text" id="student_name" name="student_name" 
                       placeholder="Enter your full name" required>
            </div>
            
            <button type="submit">✅ Mark Attendance</button>
        </form>
        
        <div id="status" class="status" style="display: none;"></div>
    </div>
    
    <script>
        document.getElementById('attendanceForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const matricNumber = document.getElementById('matric_number').value;
            const studentName = document.getElementById('student_name').value;
            
            if (!matricNumber || !studentName) {
                showStatus('Please fill in all fields', 'error');
                return;
            }
            
            // Send attendance data
            fetch('/submit_attendance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'matric_number=' + encodeURIComponent(matricNumber) + 
                      '&student_name=' + encodeURIComponent(studentName)
            })
            .then(response => response.text())
            .then(data => {
                if (data.includes('SUCCESS')) {
                    showStatus('✅ Attendance marked successfully!', 'success');
                    document.getElementById('attendanceForm').reset();
                } else {
                    showStatus('❌ ' + data, 'error');
                }
            })
            .catch(error => {
                showStatus('❌ Network error. Please try again.', 'error');
            });
        });
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';
            
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
    </script>
</body>
</html>
)rawliteral";

void setup() {
  Serial.begin(115200);
  EEPROM.begin(EEPROM_SIZE);
  
  // Load saved WiFi credentials
  loadWiFiCredentials();
  
  // Initialize device
  setupDevice();
  
  // Setup WiFi
  if (wifi_configured) {
    connectToWiFi();
  } else {
    setupAccessPoint();
  }
  
  // Setup web server
  setupWebServer();
  
  // Setup DNS server for captive portal
  dnsServer.start(DNS_PORT, "*", WiFi.softAPIP());
  
  Serial.println("ESP32 Smart Attendance System Ready!");
}

void loop() {
  if (wifi_configured) {
    // Handle web server requests
    server.handleClient();
    
    // Send heartbeat to server
    static unsigned long lastHeartbeat = 0;
    if (millis() - lastHeartbeat > 30000) { // Every 30 seconds
      sendHeartbeat();
      lastHeartbeat = millis();
    }
    
    // Check for active session
    static unsigned long lastSessionCheck = 0;
    if (millis() - lastSessionCheck > 10000) { // Every 10 seconds
      checkActiveSession();
      lastSessionCheck = millis();
    }
  } else {
    // Handle captive portal
    dnsServer.processNextRequest();
    server.handleClient();
  }
  
  delay(10);
}

void setupDevice() {
  // Load saved device configuration from EEPROM
  device_id = EEPROM.readString(0);
  device_name = EEPROM.readString(300);
  current_course = EEPROM.readString(400);
  current_lecturer = EEPROM.readString(500);
  
  // Generate unique device ID if not set
  if (device_id == "") {
    device_id = "ESP32_" + String(random(1000, 9999));
    EEPROM.writeString(0, device_id);
    EEPROM.commit();
  }
  
  // Set default device name if not saved
  if (device_name == "") {
    device_name = "Smart Attendance Device";
  }
  
  // Check if we have session information saved
  if (current_course != "" && current_lecturer != "") {
    session_active = true;
    Serial.println("📚 Restored session state from EEPROM");
  }
  
  Serial.println("Device ID: " + device_id);
  Serial.println("Device Name: " + device_name);
  if (session_active) {
    Serial.println("Active Course: " + current_course);
    Serial.println("Active Lecturer: " + current_lecturer);
  }
}

void loadWiFiCredentials() {
  wifi_ssid = EEPROM.readString(100);
  wifi_password = EEPROM.readString(200);
  wifi_configured = (wifi_ssid.length() > 0);
  
  Serial.println("WiFi SSID: " + wifi_ssid);
  Serial.println("WiFi configured: " + String(wifi_configured));
}

void setupAccessPoint() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP("ESP32_Attendance", "12345678");
  
  Serial.println("Access Point Started");
  Serial.println("SSID: ESP32_Attendance");
  Serial.println("Password: 12345678");
  Serial.println("IP Address: " + WiFi.softAPIP().toString());
}

void connectToWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifi_ssid.c_str(), wifi_password.c_str());
  
  Serial.println("Connecting to WiFi: " + wifi_ssid);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected!");
    Serial.println("IP Address: " + WiFi.localIP().toString());
    
    // Register device with server
    registerDevice();
  } else {
    Serial.println("\nWiFi connection failed. Starting AP mode.");
    setupAccessPoint();
  }
}

void setupWebServer() {
  // Main attendance page
  server.on("/", HTTP_GET, handleAttendancePage);
  
  // Submit attendance
  server.on("/submit_attendance", HTTP_POST, handleSubmitAttendance);
  
  // WiFi configuration
  server.on("/configure_wifi", HTTP_POST, handleConfigureWiFi);
  
  // Device status
  server.on("/status", HTTP_GET, handleStatus);
  
  // API endpoints
  server.on("/api/heartbeat", HTTP_POST, handleHeartbeat);
  
  server.begin();
  Serial.println("Web server started");
}

void handleAttendancePage() {
  String html = String(attendance_html);
  
  // Replace placeholders
  html.replace("%DEVICE_NAME%", device_name);
  html.replace("%COURSE%", current_course.length() > 0 ? current_course : "Not Set");
  html.replace("%LECTURER%", current_lecturer.length() > 0 ? current_lecturer : "Not Set");
  html.replace("%STATUS%", session_active ? "🟢 Active" : "🔴 Inactive");
  
  server.send(200, "text/html", html);
}

void handleSubmitAttendance() {
  if (!session_active) {
    server.send(400, "text/plain", "No active session");
    return;
  }
  
  String matric_number = server.hasArg("matric_number") ? server.arg("matric_number") : "";
  String student_name = server.hasArg("student_name") ? server.arg("student_name") : "";
  
  if (matric_number.length() == 0 || student_name.length() == 0) {
    server.send(400, "text/plain", "Missing required fields");
    return;
  }
  
  // Validate locally (basic validation)
  if (matric_number.length() < 5 || matric_number.length() > 20) {
    server.send(400, "text/plain", "Invalid matric number format");
    return;
  }
  
  // Check if already marked attendance
  for (const auto& record : attendance_log) {
    if (record.matric_number == matric_number) {
      server.send(400, "text/plain", "Attendance already marked for this student");
      return;
    }
  }
  
  // Create attendance record
  AttendanceRecord record;
  record.matric_number = matric_number;
  record.student_name = student_name;
  record.timestamp = getCurrentTimestamp();
  record.device_mac = WiFi.macAddress();
  
  attendance_log.push_back(record);
  
  // Send to server
  if (sendAttendanceToServer(record)) {
    server.send(200, "text/plain", "SUCCESS: Attendance recorded");
  } else {
    server.send(500, "text/plain", "Failed to send to server, but recorded locally");
  }
}

void handleConfigureWiFi() {
  String ssid = server.hasArg("ssid") ? server.arg("ssid") : "";
  String password = server.hasArg("password") ? server.arg("password") : "";
  
  if (ssid.length() > 0) {
    // Save WiFi credentials
    EEPROM.writeString(100, ssid);
    EEPROM.writeString(200, password);
    EEPROM.commit();
    
    wifi_ssid = ssid;
    wifi_password = password;
    wifi_configured = true;
    
    server.send(200, "text/plain", "WiFi configured. Restarting...");
    delay(1000);
    ESP.restart();
  } else {
    server.send(400, "text/plain", "SSID required");
  }
}

void handleStatus() {
  DynamicJsonDocument doc(1024);
  doc["device_id"] = device_id;
  doc["device_name"] = device_name;
  doc["wifi_connected"] = (WiFi.status() == WL_CONNECTED);
  doc["session_active"] = session_active;
  doc["current_course"] = current_course;
  doc["current_lecturer"] = current_lecturer;
  doc["attendance_count"] = attendance_log.size();
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

void handleHeartbeat() {
  server.send(200, "text/plain", "OK");
}

void registerDevice() {
  HTTPClient http;
  http.begin(SERVER_URL + "/admin-panel/api/device/connected/");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  
  DynamicJsonDocument doc(512);
  doc["device_id"] = device_id;
  doc["device_name"] = device_name;
  doc["mac_address"] = WiFi.macAddress();
  doc["ip_address"] = WiFi.localIP().toString();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Device registered: " + response);
  } else {
    Serial.println("Failed to register device");
  }
  
  http.end();
}

void sendHeartbeat() {
  HTTPClient http;
  http.begin(SERVER_URL + "/admin-panel/api/esp32/heartbeat/");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  
  DynamicJsonDocument doc(256);
  doc["device_id"] = device_id;
  doc["timestamp"] = getCurrentTimestamp();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
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
            WiFi.softAP(newSSID.c_str(), "", 1, 0, 4); // Channel 1, hidden=false, max_connections=4
            Serial.println("📡 Updated ESP32 WiFi network: " + newSSID);
          }
          
          Serial.println("✅ Dynamic configuration applied successfully!");
          
        } else {
          // No active session - device in standby
          if (session_active) {
            Serial.println("💤 No active session - device entering standby mode");
            session_active = false;
            current_course = "";
            current_lecturer = "";
            current_session_id = "";
            
            // Reset to default device name
            device_name = "Smart Attendance Device";
            
            // Save standby state
            EEPROM.writeString(300, device_name);
            EEPROM.writeString(400, "");
            EEPROM.writeString(500, "");
            EEPROM.commit();
          }
        }
      }
    } else {
      Serial.println("❌ Failed to parse configuration response: " + String(error.c_str()));
    }
    
  } else {
    Serial.println("Failed to send heartbeat");
  }
  
  http.end();
}

void checkActiveSession() {
  HTTPClient http;
  http.begin(SERVER_URL + "/admin-panel/api/session/active/");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  
  DynamicJsonDocument doc(256);
  doc["device_id"] = device_id;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    parseSessionResponse(response);
  }
  
  http.end();
}

void parseSessionResponse(String response) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, response);
  
  if (!error) {
    if (doc.containsKey("session_active") && doc["session_active"]) {
      session_active = true;
      current_course = doc["course_code"].as<String>();
      current_lecturer = doc["lecturer_name"].as<String>();
      current_session_id = doc["session_id"].as<String>();
      
      Serial.println("Active session: " + current_course + " by " + current_lecturer);
    } else {
      session_active = false;
      current_course = "";
      current_lecturer = "";
      current_session_id = "";
    }
  }
}

bool sendAttendanceToServer(AttendanceRecord& record) {
  HTTPClient http;
  http.begin(SERVER_URL + "/admin-panel/api/attendance/submit/");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  
  DynamicJsonDocument doc(512);
  doc["session_id"] = current_session_id;
  doc["matric_number"] = record.matric_number;
  doc["student_name"] = record.student_name;
  doc["timestamp"] = record.timestamp;
  doc["device_mac"] = record.device_mac;
  doc["device_id"] = device_id;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Attendance sent to server: " + response);
    return true;
  } else {
    Serial.println("Failed to send attendance to server");
    return false;
  }
  
  http.end();
}

String getCurrentTimestamp() {
  // Get current time from NTP server or use millis() as fallback
  time_t now;
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    // Fallback to millis-based timestamp
    unsigned long currentMillis = millis();
    return String(currentMillis);
  }
  
  char timestamp[25];
  strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", &timeinfo);
  return String(timestamp);
}

// WiFi event handler
void WiFiEvent(WiFiEvent_t event) {
  switch (event) {
    case SYSTEM_EVENT_STA_DISCONNECTED:
      Serial.println("WiFi disconnected. Reconnecting...");
      WiFi.reconnect();
      break;
    case SYSTEM_EVENT_STA_CONNECTED:
      Serial.println("WiFi connected");
      break;
  }
}
