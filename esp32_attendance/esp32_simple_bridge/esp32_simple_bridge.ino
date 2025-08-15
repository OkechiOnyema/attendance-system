/*
 * ESP32 Simple WiFi Bridge for Attendance
 * 
 * This ESP32 connects to your WiFi and acts as a bridge
 * for students to access the Django attendance system.
 * 
 * MUCH SIMPLER than the access point approach!
 * 
 * Hardware: ESP32 DevKit or ESP32 CAM
 * 
 * Setup:
 * 1. Upload this code to ESP32
 * 2. ESP32 connects to your WiFi automatically
 * 3. Students access Django through ESP32
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WebServer.h>

// ===== WIFI CONFIGURATION - YOUR SETUP =====
const char* WIFI_SSID = "AttendanceWiFi";        // Your laptop hotspot name
const char* WIFI_PASSWORD = "attendance123";      // Your laptop hotspot password
const char* DJANGO_SERVER = "http://10.141.126.27:8000"; // Django server URL

// ===== ESP32 DEVICE CONFIGURATION =====
const char* DEVICE_ID = "ESP32_Bridge_001";
const char* DEVICE_NAME = "CS101_Classroom_Bridge";

// ===== GLOBAL VARIABLES =====
WebServer server(80);
HTTPClient http;

// Device tracking
struct ConnectedDevice {
  String ip;
  String userAgent;
  unsigned long lastSeen;
};

ConnectedDevice devices[20];
int deviceCount = 0;

// Timing
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 60000; // 1 minute

// ===== SETUP =====
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("🚀 ESP32 Simple WiFi Bridge Starting...");
  Serial.println("📋 Configuration:");
  Serial.print("   WiFi SSID: ");
  Serial.println(WIFI_SSID);
  Serial.print("   Django Server: ");
  Serial.println(DJANGO_SERVER);
  Serial.print("   Device ID: ");
  Serial.println(DEVICE_ID);
  
  // Connect to WiFi
  connectToWiFi();
  
  // Setup web server
  setupWebServer();
  
  Serial.println("✅ ESP32 Bridge Ready!");
  Serial.print("📶 Connected to WiFi: ");
  Serial.println(WIFI_SSID);
  Serial.print("🌐 ESP32 IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("💻 Django Server: ");
  Serial.println(DJANGO_SERVER);
}

// ===== MAIN LOOP =====
void loop() {
  // Handle web server requests
  server.handleClient();
  
  // Send heartbeat to Django
  if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  delay(100);
}

// ===== WIFI CONNECTION =====
void connectToWiFi() {
  Serial.print("📡 Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  unsigned long startAttemptTime = millis();
  const unsigned long WIFI_TIMEOUT = 30000; // 30 seconds timeout
  
  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < WIFI_TIMEOUT) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println();
    Serial.println("❌ WiFi connection failed! Check credentials and try again.");
    Serial.println("🔄 Restarting ESP32 in 5 seconds...");
    delay(5000);
    ESP.restart();
  }
  
  Serial.println();
  Serial.println("✅ WiFi Connected!");
  Serial.print("🌐 IP Address: ");
  Serial.println(WiFi.localIP());
}

// ===== WEB SERVER SETUP =====
void setupWebServer() {
  // Main attendance page
  server.on("/", HTTP_GET, handleAttendancePage);
  
  // Mark attendance
  server.on("/mark-attendance", HTTP_POST, handleMarkAttendance);
  
  // Status page
  server.on("/status", HTTP_GET, handleStatus);
  
  // Start server
  server.begin();
  Serial.println("🌐 Web server started on port 80");
}

// ===== WEB SERVER HANDLERS =====
void handleAttendancePage() {
  String html = R"(
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>ESP32 Attendance System</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .container { max-width: 400px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }
        .form-group { margin: 20px 0; text-align: left; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 12px; border: none; border-radius: 8px; font-size: 16px; }
        .btn { background: #4ade80; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; width: 100%; }
        .btn:hover { background: #22c55e; }
        .status { margin-top: 20px; padding: 15px; border-radius: 8px; }
        .success { background: rgba(34, 197, 94, 0.2); border: 1px solid #22c55e; }
        .error { background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; }
    </style>
</head>
<body>
    <div class='container'>
        <h2>🌉 ESP32 Attendance System</h2>
        <p>Mark your attendance through this ESP32 bridge</p>
        
        <form id='attendanceForm'>
            <div class='form-group'>
                <label for='matric_no'>Matriculation Number:</label>
                <input type='text' id='matric_no' name='matric_no' required placeholder='Enter your matric number'>
            </div>
            
            <div class='form-group'>
                <label for='course'>Course:</label>
                <select id='course' name='course' required>
                    <option value=''>Select Course</option>
                    <option value='CSC101'>CSC101 - Introduction to Computer Science</option>
                    <option value='MTH102'>MTH102 - Calculus I</option>
                    <option value='PHY103'>PHY103 - General Physics</option>
                </select>
            </div>
            
            <button type='submit' class='btn'>✅ Mark Attendance</button>
        </form>
        
        <div id='status'></div>
        
        <p style='margin-top: 30px; font-size: 14px;'>
            💻 Access full Django system: <a href='http://10.141.126.27:8000' style='color: #4ade80;'>http://10.141.126.27:8000</a>
        </p>
    </div>
    
    <script>
        document.getElementById('attendanceForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const statusDiv = document.getElementById('status');
            
            try {
                const response = await fetch('/mark-attendance', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusDiv.innerHTML = '<div class="status success">✅ Attendance marked successfully!</div>';
                    document.getElementById('attendanceForm').reset();
                } else {
                    statusDiv.innerHTML = '<div class="status error">❌ ' + result.message + '</div>';
                }
            } catch (error) {
                statusDiv.innerHTML = '<div class="status error">❌ Error: ' + error.message + '</div>';
            }
        });
    </script>
</body>
</html>
  )";
  
  server.send(200, "text/html", html);
}

void handleMarkAttendance() {
  String matricNo = server.hasArg("matric_no") ? server.arg("matric_no") : "";
  String course = server.hasArg("course") ? server.arg("course") : "";
  
  if (matricNo.isEmpty() || course.isEmpty()) {
    server.send(400, "application/json", "{\"success\": false, \"message\": \"Missing required fields\"}");
    return;
  }
  
  // Record device connection
  String clientIP = server.client().remoteIP().toString();
  recordDeviceConnection(clientIP, server.header("User-Agent"));
  
  // Send to Django
  bool success = sendAttendanceToDjango(matricNo, course, clientIP);
  
  if (success) {
    server.send(200, "application/json", "{\"success\": true, \"message\": \"Attendance recorded successfully\"}");
  } else {
    server.send(500, "application/json", "{\"success\": false, \"message\": \"Failed to record attendance\"}");
  }
}

void handleStatus() {
  String json = "{\"wifi_status\": \"" + String(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected") + "\",";
  json += "\"wifi_ssid\": \"" + String(WIFI_SSID) + "\",";
  json += "\"esp32_ip\": \"" + WiFi.localIP().toString() + "\",";
  json += "\"django_server\": \"" + String(DJANGO_SERVER) + "\",";
  json += "\"connected_devices\": " + String(deviceCount) + "}";
  
  server.send(200, "application/json", json);
}

// ===== DEVICE MANAGEMENT =====
void recordDeviceConnection(String ip, String userAgent) {
  Serial.println("📱 Device connected - recording attendance");
  
  // Check if device already exists
  for (int i = 0; i < deviceCount; i++) {
    if (devices[i].ip == ip) {
      devices[i].lastSeen = millis();
      return;
    }
  }
  
  // Add new device
  if (deviceCount < 20) {
    devices[deviceCount].ip = ip;
    devices[deviceCount].userAgent = userAgent;
    devices[deviceCount].lastSeen = millis();
    deviceCount++;
    
    Serial.print("✅ New device connected: ");
    Serial.println(ip);
  }
}

// ===== DJANGO COMMUNICATION =====
bool sendAttendanceToDjango(String matricNo, String course, String clientIP) {
  Serial.println("📤 Sending attendance to Django...");
  
  http.begin(DJANGO_SERVER + String("/admin-panel/api/esp32/connected/"));
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<300> doc;
  doc["device_id"] = String(DEVICE_ID);
  doc["mac_address"] = "ESP32_" + String(random(1000, 9999));
  doc["device_name"] = "Student Device";
  doc["ip_address"] = clientIP;
  doc["matric_no"] = matricNo;
  doc["course"] = course;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.print("📤 Sending data: ");
  Serial.println(jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    Serial.println("✅ Attendance sent to Django successfully");
    Serial.print("📊 Response code: ");
    Serial.println(httpResponseCode);
    return true;
  } else {
    Serial.print("❌ Failed to send attendance, error: ");
    Serial.println(httpResponseCode);
    return false;
  }
  
  http.end();
}

void sendHeartbeat() {
  Serial.println("💓 Sending heartbeat to Django...");
  
  http.begin(DJANGO_SERVER + String("/admin-panel/api/esp32/heartbeat/"));
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["device_id"] = String(DEVICE_ID);
  doc["wifi_status"] = WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected";
  doc["wifi_ssid"] = String(WIFI_SSID);
  doc["esp32_ip"] = WiFi.localIP().toString();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    Serial.println("✅ Heartbeat sent successfully");
  } else {
    Serial.print("❌ Heartbeat failed, error: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}
