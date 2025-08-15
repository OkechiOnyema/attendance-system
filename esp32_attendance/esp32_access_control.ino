#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DNSServer.h>

// WiFi Access Point Configuration
const char* AP_SSID = "AttendanceWiFi";
const char* AP_PASSWORD = "attendance123";
const char* AP_IP = "192.168.4.1";
const char* AP_GATEWAY = "192.168.4.1";
const char* AP_SUBNET = "255.255.255.0";

// DNS Configuration
const char* PRIMARY_DNS = "8.8.8.8";      // Google DNS
const char* SECONDARY_DNS = "8.8.4.4";    // Google DNS Backup

// Django Server (Render)
const char* DJANGO_SERVER = "https://attendance-system-muqs.onrender.com";
const char* DEVICE_ID = "ESP32_Access_Control_001";
const char* DEVICE_NAME = "CS101_Classroom_Controller";

// Web Server
WebServer server(80);
DNSServer dnsServer;

// Connected devices tracking
struct ConnectedDevice {
    String mac;
    String ip;
    unsigned long lastSeen;
    bool active;
};

#define MAX_DEVICES 50
ConnectedDevice connectedDevices[MAX_DEVICES];
int deviceCount = 0;

// Heartbeat interval
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 30000; // 30 seconds

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("🚀 ESP32 Access Control System Starting...");
    
    // Setup WiFi Access Point
    setupAccessPoint();
    
    // Setup Web Server
    setupWebServer();
    
    // Setup DNS Server (for captive portal)
    dnsServer.start(53, "*", AP_IP);
    
    // Configure DNS for connected devices
    WiFi.dnsServer(IPAddress(8, 8, 8, 8), IPAddress(8, 8, 4, 4));
    
    Serial.println("✅ ESP32 Access Control System Ready!");
    Serial.println("📱 Students must connect to ESP32 WiFi to access attendance system");
}

void setupAccessPoint() {
    Serial.println("🌐 Setting up WiFi Access Point...");
    
    // Configure WiFi Access Point
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(IPAddress(192, 168, 4, 1), IPAddress(192, 168, 4, 1), IPAddress(255, 255, 255, 0));
    
    // Start Access Point
    if (WiFi.softAP(AP_SSID, AP_PASSWORD)) {
        Serial.println("✅ WiFi Access Point Started Successfully!");
        Serial.print("📶 SSID: ");
        Serial.println(AP_SSID);
        Serial.print("🔑 Password: ");
        Serial.println(AP_PASSWORD);
        Serial.print("🌐 IP Address: ");
        Serial.println(WiFi.softAPIP());
    } else {
        Serial.println("❌ Failed to start WiFi Access Point!");
    }
}

void setupWebServer() {
    Serial.println("🌐 Setting up Web Server...");
    
    // Main attendance page
    server.on("/", HTTP_GET, handleAttendancePage);
    
    // API endpoints
    server.on("/api/attendance", HTTP_POST, handleAttendanceSubmission);
    server.on("/api/status", HTTP_GET, handleStatus);
    server.on("/api/devices", HTTP_GET, handleDevicesList);
    
    // Captive portal - redirect all other requests to main page
    server.onNotFound(handleCaptivePortal);
    
    server.begin();
    Serial.println("✅ Web Server started on port 80");
}

void handleAttendancePage() {
    String html = R"(
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 Student Attendance System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 16px;
        }
        
        .form-container {
            padding: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }
        
        .form-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e8ed;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .submit-btn {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
        }
        
        .submit-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
            font-weight: 600;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .device-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            text-align: center;
        }
        
        .device-info h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Student Attendance</h1>
            <p>Mark your attendance using the form below</p>
        </div>
        
        <div class="form-container">
            <form id="attendanceForm">
                <div class="form-group">
                    <label class="form-label" for="studentId">Student ID</label>
                    <input type="text" id="studentId" class="form-input" placeholder="Enter your student ID" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="courseCode">Course Code</label>
                    <input type="text" id="courseCode" class="form-input" placeholder="e.g., CS101, MAT201" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label" for="deviceId">Device ID</label>
                    <input type="text" id="deviceId" class="form-input" placeholder="ESP32 Device ID" required>
                </div>
                
                <button type="submit" class="submit-btn" id="submitBtn">
                    Mark Attendance
                </button>
            </form>
            
            <div id="status" class="status" style="display: none;"></div>
            
            <div class="device-info">
                <h3>📶 Connected to ESP32</h3>
                <p>You're now connected to the secure attendance network</p>
                <p><strong>Device:</strong> )" + String(DEVICE_NAME) + R"(</p>
                <p><strong>Network:</strong> )" + String(AP_SSID) + R"(</p>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('attendanceForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const statusDiv = document.getElementById('status');
            
            // Get form data
            const studentId = document.getElementById('studentId').value;
            const courseCode = document.getElementById('courseCode').value;
            const deviceId = document.getElementById('deviceId').value;
            
            // Show loading
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span>Marking Attendance...';
            statusDiv.style.display = 'none';
            
            try {
                // Submit to ESP32 API
                const response = await fetch('/api/attendance', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        studentId: studentId,
                        courseCode: courseCode,
                        deviceId: deviceId
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('✅ Attendance marked successfully!', 'success');
                    document.getElementById('attendanceForm').reset();
                } else {
                    showStatus('❌ ' + result.message, 'error');
                }
            } catch (error) {
                showStatus('❌ Error: ' + error.message, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Mark Attendance';
            }
        });
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';
            
            // Auto-hide success messages
            if (type === 'success') {
                setTimeout(() => {
                    statusDiv.style.display = 'none';
                }, 5000);
            }
        }
    </script>
</body>
</html>
    )";
    
    server.send(200, "text/html", html);
}

void handleAttendanceSubmission() {
    if (server.method() != HTTP_POST) {
        server.send(405, "text/plain", "Method Not Allowed");
        return;
    }
    
    String body = server.arg("plain");
    Serial.println("📝 Received attendance submission: " + body);
    
    // Parse JSON
    DynamicJsonDocument doc(512);
    DeserializationError error = deserializeJson(doc, body);
    
    if (error) {
        Serial.println("❌ JSON parsing failed: " + String(error.c_str()));
        server.send(400, "application/json", "{\"success\":false,\"message\":\"Invalid JSON\"}");
        return;
    }
    
    // Extract data
    String studentId = doc["studentId"].as<String>();
    String courseCode = doc["courseCode"].as<String>();
    String deviceId = doc["deviceId"].as<String>();
    
    // Validate data
    if (studentId.isEmpty() || courseCode.isEmpty() || deviceId.isEmpty()) {
        server.send(400, "application/json", "{\"success\":false,\"message\":\"Missing required fields\"}");
        return;
    }
    
    // Send to Django server
    bool success = sendAttendanceToDjango(studentId, courseCode, deviceId);
    
    if (success) {
        server.send(200, "application/json", "{\"success\":true,\"message\":\"Attendance recorded successfully\"}");
    } else {
        server.send(500, "application/json", "{\"success\":false,\"message\":\"Failed to record attendance\"}");
    }
}

bool sendAttendanceToDjango(String studentId, String courseCode, String deviceId) {
    HTTPClient http;
    
    // Create JSON payload
    DynamicJsonDocument doc(512);
    doc["student_id"] = studentId;
    doc["course_code"] = courseCode;
    doc["device_id"] = deviceId;
    doc["timestamp"] = millis();
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    Serial.println("📤 Sending to Django: " + jsonString);
    
    // Send to Django server
    String url = String(DJANGO_SERVER) + "/admin-panel/api/esp32/connected/";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    int httpResponseCode = http.POST(jsonString);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println("✅ Django response: " + response);
        http.end();
        return true;
    } else {
        Serial.println("❌ Django request failed: " + http.errorToString(httpResponseCode));
        http.end();
        return false;
    }
}

void handleStatus() {
    String status = "{\"device_name\":\"" + String(DEVICE_NAME) + "\",\"connected_devices\":" + String(deviceCount) + ",\"status\":\"active\"}";
    server.send(200, "application/json", status);
}

void handleDevicesList() {
    String devices = "[";
    for (int i = 0; i < deviceCount; i++) {
        if (i > 0) devices += ",";
        devices += "{\"mac\":\"" + connectedDevices[i].mac + "\",\"ip\":\"" + connectedDevices[i].ip + "\",\"active\":" + (connectedDevices[i].active ? "true" : "false") + "}";
    }
    devices += "]";
    
    server.send(200, "application/json", devices);
}

void handleCaptivePortal() {
    // Redirect all unknown requests to main page
    server.sendHeader("Location", "http://192.168.4.1", true);
    server.send(302, "text/plain", "");
}

void loop() {
    // Handle web server
    server.handleClient();
    
    // Handle DNS server
    dnsServer.processNextRequest();
    
    // Send heartbeat to Django
    if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
        sendHeartbeat();
        lastHeartbeat = millis();
    }
    
    // Update connected devices
    updateConnectedDevices();
    
    delay(100);
}

void sendHeartbeat() {
    HTTPClient http;
    
    // Create heartbeat payload
    DynamicJsonDocument doc(256);
    doc["device_id"] = DEVICE_ID;
    doc["device_name"] = DEVICE_NAME;
    doc["connected_devices"] = deviceCount;
    doc["status"] = "active";
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    Serial.println("💓 Sending heartbeat to Django...");
    
    // Send to Django server
    String url = String(DJANGO_SERVER) + "/admin-panel/api/esp32/heartbeat/";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    int httpResponseCode = http.POST(jsonString);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println("✅ Heartbeat successful: " + response);
    } else {
        Serial.println("❌ Heartbeat failed: " + http.errorToString(httpResponseCode));
    }
    
    http.end();
}

void updateConnectedDevices() {
    // This is a simplified version - in a real implementation,
    // you would scan for connected WiFi clients
    // For now, we'll simulate device tracking
    
    // Check for new connections (simplified)
    if (WiFi.softAPgetStationNum() > deviceCount) {
        Serial.println("📱 New device connected to ESP32");
        deviceCount = WiFi.softAPgetStationNum();
    }
}
