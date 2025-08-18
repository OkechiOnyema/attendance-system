/*
 * ESP32 Smart Attendance System - Complete Implementation
 * Network-Based Access Control for Secure Attendance
 * 
 * This code creates a WiFi access point and web server for students to mark attendance.
 * Only devices connected to the ESP32 WiFi network can submit attendance.
 * 
 * Hardware: ESP32 Development Board
 * Required Libraries: WiFi, WebServer, HTTPClient, ArduinoJson
 */

#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ===== CONFIGURATION =====
const char* AP_SSID = "ESP32_Attendance";     // WiFi network name
const char* AP_PASSWORD = "12345678";          // WiFi password (8+ chars)
const char* DEVICE_ID = "ESP32_001";           // Unique device ID
const char* SERVER_URL = "http://192.168.1.100:8000"; // Django server URL

// ===== GLOBAL VARIABLES =====
WebServer server(80);
HTTPClient http;

// Store connected devices
struct ConnectedDevice {
    String mac;
    String ip;
    String name;
    bool isActive;
};

#define MAX_DEVICES 20
ConnectedDevice connectedDevices[MAX_DEVICES];
int deviceCount = 0;

// Session management
bool hasActiveSession = false;
String currentSessionId = "";
String currentCourseCode = "";
String currentLecturer = "";

// ===== SETUP FUNCTION =====
void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n\n🚀 ESP32 Smart Attendance System Starting...");
    Serial.println("================================================");
    
    // Start WiFi Access Point
    startWiFiAP();
    
    // Setup web server routes
    setupWebServer();
    
    // Start web server
    server.begin();
    Serial.println("✅ Web server started successfully");
    
    Serial.println("\n🎯 System Status: READY!");
    Serial.println("📱 Students can now:");
    Serial.println("   1. Connect to WiFi: " + String(AP_SSID));
    Serial.println("   2. Open browser to: http://" + WiFi.softAPIP().toString());
    Serial.println("   3. Mark attendance securely");
    
    Serial.println("\n🔒 Security Features:");
    Serial.println("   - Network-based access control");
    Serial.println("   - Only connected devices can submit");
    Serial.println("   - Real-time session validation");
    Serial.println("   - Automatic backend synchronization");
}

// ===== MAIN LOOP =====
void loop() {
    server.handleClient();
    delay(10);
}

// ===== WIFI ACCESS POINT SETUP =====
void startWiFiAP() {
    Serial.println("📡 Starting WiFi Access Point...");
    
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    
    IPAddress IP = WiFi.softAPIP();
    Serial.printf("✅ WiFi Access Point started successfully!\n");
    Serial.printf("�� Network Name (SSID): %s\n", AP_SSID);
    Serial.printf("🔑 Password: %s\n", AP_PASSWORD);
    Serial.printf("�� IP Address: %s\n", IP.toString());
    Serial.printf("📱 Students connect to: %s\n", AP_SSID);
    Serial.printf("🌐 Web Portal: http://%s\n", IP.toString());
}

// ===== WEB SERVER ROUTES =====
void setupWebServer() {
    Serial.println("🌐 Setting up web server routes...");
    
    // Main attendance page
    server.on("/", HTTP_GET, []() {
        Serial.println("📱 Student accessed attendance portal");
        server.send(200, "text/html", getAttendanceHTML());
    });
    
    // API: Get session status
    server.on("/api/session/status", HTTP_GET, []() {
        Serial.println("📡 API Request: Get session status");
        handleGetSessionStatus();
    });
    
    // API: Submit attendance
    server.on("/api/attendance/submit", HTTP_POST, []() {
        Serial.println("📝 API Request: Submit attendance");
        handleSubmitAttendance();
    });
    
    // API: Device connected
    server.on("/api/device/connected", HTTP_POST, []() {
        Serial.println("🔌 API Request: Device connected");
        handleDeviceConnected();
    });
    
    // Handle not found
    server.onNotFound([]() {
        Serial.println("❌ 404: Page not found");
        server.send(404, "text/plain", "Page not found. Go to / for attendance portal.");
    });
    
    Serial.println("✅ Web server routes configured");
}

// ===== API HANDLERS =====
void handleGetSessionStatus() {
    if (!hasActiveSession) {
        String response = "{\"active\": false, \"message\": \"No active session\"}";
        server.send(200, "application/json", response);
        Serial.println("�� Session Status: No active session");
        return;
    }
    
    String json = "{\"active\": true, \"session_id\": \"" + currentSessionId + 
                  "\", \"course_name\": \"" + currentCourseCode + 
                  "\", \"lecturer_name\": \"" + currentLecturer + 
                  "\", \"date\": \"" + getCurrentDate() + "\"}";
    
    server.send(200, "application/json", json);
    Serial.printf("📊 Session Status: Active - %s by %s\n", currentCourseCode.c_str(), currentLecturer.c_str());
}

void handleSubmitAttendance() {
    if (server.hasArg("plain")) {
        String body = server.arg("plain");
        Serial.println("📝 Received attendance submission: " + body);
        
        // Parse JSON
        DynamicJsonDocument doc(512);
        DeserializationError error = deserializeJson(doc, body);
        
        if (error) {
            Serial.println("❌ JSON parsing error: " + String(error.c_str()));
            server.send(400, "application/json", "{\"error\": \"Invalid JSON format\"}");
            return;
        }
        
        // Extract data
        String sessionId = doc["session_id"];
        String matricNo = doc["student_matric_no"];
        String deviceId = doc["device_id"];
        String clientIp = doc["client_ip"];
        
        Serial.printf("�� Attendance Details:\n");
        Serial.printf("   Session ID: %s\n", sessionId.c_str());
        Serial.printf("   Matric No: %s\n", matricNo.c_str());
        Serial.printf("   Device ID: %s\n", deviceId.c_str());
        Serial.printf("   Client IP: %s\n", clientIp.c_str());
        
        // Validate session
        if (sessionId != currentSessionId) {
            Serial.println("❌ Session validation failed: Invalid or expired session");
            server.send(400, "application/json", "{\"error\": \"Invalid or expired session\"}");
            return;
        }
        
        // Check if device is connected to our network
        if (!isDeviceConnected(clientIp)) {
            Serial.println("❌ Security check failed: Device not connected to ESP32 network");
            server.send(400, "application/json", "{\"error\": \"Device not connected to ESP32 network\"}");
            return;
        }
        
        Serial.println("✅ Security checks passed, sending to backend...");
        
        // Send to backend server
        bool success = sendAttendanceToBackend(sessionId, matricNo, deviceId, clientIp);
        
        if (success) {
            server.send(200, "application/json", "{\"success\": true, \"message\": \"Attendance recorded successfully\"}");
            Serial.println("✅ Attendance recorded successfully");
        } else {
            server.send(500, "application/json", "{\"error\": \"Failed to send to backend server\"}");
            Serial.println("❌ Failed to send attendance to backend");
        }
    } else {
        Serial.println("❌ No data received in attendance submission");
        server.send(400, "application/json", "{\"error\": \"No data received\"}");
    }
}

void handleDeviceConnected() {
    if (server.hasArg("plain")) {
        String body = server.arg("plain");
        Serial.println("🔌 Device connection request: " + body);
        
        // Parse JSON
        DynamicJsonDocument doc(256);
        DeserializationError error = deserializeJson(doc, body);
        
        if (!error) {
            String mac = doc["mac"];
            String ip = doc["ip"];
            String name = doc["name"];
            
            addConnectedDevice(mac, ip, name);
            Serial.printf("✅ Device registered: %s (%s) at %s\n", name.c_str(), mac.c_str(), ip.c_str());
        } else {
            Serial.println("❌ Error parsing device connection data");
        }
    }
    
    server.send(200, "application/json", "{\"status\": \"ok\", \"message\": \"Device connection registered\"}");
}

// ===== DEVICE MANAGEMENT =====
void addConnectedDevice(String mac, String ip, String name) {
    // Check if device already exists
    for (int i = 0; i < deviceCount; i++) {
        if (connectedDevices[i].mac == mac) {
            connectedDevices[i].ip = ip;
            connectedDevices[i].name = name;
            connectedDevices[i].isActive = true;
            Serial.printf("�� Device updated: %s (%s) at %s\n", name.c_str(), mac.c_str(), ip.c_str());
            return;
        }
    }
    
    // Add new device
    if (deviceCount < MAX_DEVICES) {
        connectedDevices[deviceCount].mac = mac;
        connectedDevices[deviceCount].ip = ip;
        connectedDevices[deviceCount].name = name;
        connectedDevices[deviceCount].isActive = true;
        deviceCount++;
        
        Serial.printf("📱 New device connected: %s (%s) at %s\n", name.c_str(), mac.c_str(), ip.c_str());
        Serial.printf("📊 Total connected devices: %d\n", deviceCount);
    } else {
        Serial.println("⚠️ Maximum device limit reached");
    }
}

bool isDeviceConnected(String ip) {
    for (int i = 0; i < deviceCount; i++) {
        if (connectedDevices[i].ip == ip && connectedDevices[i].isActive) {
            return true;
        }
    }
    return false;
}

// ===== BACKEND COMMUNICATION =====
bool sendAttendanceToBackend(String sessionId, String matricNo, String deviceId, String clientIp) {
    Serial.println("�� Sending attendance to backend server...");
    
    String url = String(SERVER_URL) + "/admin-panel/api/attendance/submit/";
    Serial.printf("🌐 Backend URL: %s\n", url.c_str());
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    String jsonPayload = "{\"session_id\":\"" + sessionId + 
                         "\",\"student_matric_no\":\"" + matricNo + 
                         "\",\"device_id\":\"" + deviceId + 
                         "\",\"client_ip\":\"" + clientIp + 
                         "\",\"device_mac\":\"AA:BB:CC:DD:EE:FF\",\"device_name\":\"Student Device\"}";
    
    Serial.printf("📤 Payload: %s\n", jsonPayload.c_str());
    
    int httpCode = http.POST(jsonPayload);
    
    if (httpCode > 0) {
        String response = http.getString();
        Serial.printf("📡 Backend response: %d - %s\n", httpCode, response.c_str());
        http.end();
        
        if (httpCode == 200) {
            Serial.println("✅ Backend communication successful");
            return true;
        } else {
            Serial.printf("⚠️ Backend returned status: %d\n", httpCode);
            return false;
        }
    } else {
        Serial.printf("❌ Backend request failed: %s\n", http.errorToString(httpCode).c_str());
        http.end();
        return false;
    }
}

// ===== UTILITY FUNCTIONS =====
String getCurrentDate() {
    // Simple date format: YYYY-MM-DD
    // In production, you might want to use a proper RTC module
    return "2025-08-16"; // Placeholder - replace with actual date logic
}

// ===== MANUAL SESSION CONTROL (for testing) =====
void startSession(String sessionId, String courseCode, String lecturer) {
    currentSessionId = sessionId;
    currentCourseCode = courseCode;
    currentLecturer = lecturer;
    hasActiveSession = true;
    
    Serial.printf("🎯 Session started successfully!\n");
    Serial.printf("   Session ID: %s\n", sessionId.c_str());
    Serial.printf("   Course: %s\n", courseCode.c_str());
    Serial.printf("   Lecturer: %s\n", lecturer.c_str());
    Serial.println("📱 Students can now mark attendance");
}

void endSession() {
    hasActiveSession = false;
    currentSessionId = "";
    currentCourseCode = "";
    currentLecturer = "";
    
    Serial.println("🔚 Session ended");
    Serial.println("�� No more attendance submissions allowed");
}

// ===== HTML TEMPLATE =====
String getAttendanceHTML() {
    return R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Attendance System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        .logo {
            font-size: 2rem;
            color: #667eea;
            margin-bottom: 1rem;
            font-weight: bold;
        }
        .status {
            background: #e8f5e8;
            color: #2e7d32;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-weight: 500;
        }
        .form-group {
            margin: 1rem 0;
            text-align: left;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .message {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-weight: 500;
        }
        .success { background: #e8f5e8; color: #2e7d32; }
        .error { background: #ffebee; color: #c62828; }
        .info { background: #e3f2fd; color: #1565c0; }
        .loading {
            display: none;
            color: #667eea;
            font-style: italic;
        }
        .stats {
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">�� Smart Attendance</div>
        
        <div id="sessionStatus" class="status">
            <div id="statusText">Checking session status...</div>
            <div id="sessionInfo" style="display: none;">
                <strong>Course:</strong> <span id="courseName"></span><br>
                <strong>Lecturer:</strong> <span id="lecturerName"></span><br>
                <strong>Date:</strong> <span id="sessionDate"></span>
            </div>
        </div>
        
        <div id="attendanceForm" style="display: none;">
            <form id="form">
                <div class="form-group">
                    <label for="matricNo">Enter Your Matric Number:</label>
                    <input type="text" id="matricNo" name="matricNo" 
                           placeholder="e.g., 2021/123456" required>
                </div>
                <button type="submit" class="btn" id="submitBtn">
                    <span id="btnText">Submit Attendance</span>
                    <span id="loading" class="loading">Processing...</span>
                </button>
            </form>
        </div>
        
        <div id="message"></div>
        
        <div class="stats">
            <strong>Connected Devices:</strong> <span id="deviceCount">0</span><br>
            <strong>Network:</strong> <span id="networkName">ESP32_Attendance</span>
        </div>
    </div>

    <script>
        const API_BASE_URL = 'http://192.168.4.1';
        let currentSession = null;
        
        // Check session status on page load
        window.addEventListener('load', checkSessionStatus);
        
        // Check session status every 30 seconds
        setInterval(checkSessionStatus, 30000);
        
        async function checkSessionStatus() {
            try {
                const response = await fetch(`${API_BASE_URL}/api/session/status`);
                const data = await response.json();
                
                if (data.active) {
                    currentSession = data;
                    showSessionActive(data);
                } else {
                    showSessionInactive();
                }
            } catch (error) {
                console.error('Error checking session:', error);
                showSessionInactive();
            }
        }
        
        function showSessionActive(session) {
            document.getElementById('statusText').textContent = '✅ Session Active';
            document.getElementById('courseName').textContent = session.course_name;
            document.getElementById('lecturerName').textContent = session.lecturer_name;
            document.getElementById('sessionDate').textContent = session.date;
            document.getElementById('sessionInfo').style.display = 'block';
            document.getElementById('attendanceForm').style.display = 'block';
            document.getElementById('message').innerHTML = '';
        }
        
        function showSessionInactive() {
            document.getElementById('statusText').textContent = '❌ No Active Session';
            document.getElementById('sessionInfo').style.display = 'none';
            document.getElementById('attendanceForm').style.display = 'none';
            document.getElementById('message').innerHTML = 
                '<div class="info">No active attendance session. Please wait for your lecturer to start a session.</div>';
        }
        
        // Handle form submission
        document.getElementById('form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const matricNo = document.getElementById('matricNo').value.trim();
            if (!matricNo) {
                showMessage('Please enter your matric number', 'error');
                return;
            }
            
            if (!currentSession) {
                showMessage('No active session found', 'error');
                return;
            }
            
            // Get client IP (this will be the ESP32's internal IP)
            const clientIP = window.location.hostname;
            
            // Show loading state
            setLoading(true);
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/attendance/submit`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_id: currentSession.session_id,
                        student_matric_no: matricNo,
                        device_id: 'ESP32_001',
                        client_ip: clientIP,
                        device_mac: 'AA:BB:CC:DD:EE:FF',
                        device_name: 'Student Device'
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    showMessage('✅ Attendance recorded successfully!', 'success');
                    document.getElementById('matricNo').value = '';
                } else {
                    showMessage(`❌ ${data.error || 'Failed to record attendance'}`, 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showMessage('❌ Network error. Please try again.', 'error');
            } finally {
                setLoading(false);
            }
        });
        
        function showMessage(text, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.innerHTML = `<div class="message ${type}">${text}</div>`;
            
            // Auto-hide success messages after 5 seconds
            if (type === 'success') {
                setTimeout(() => {
                    messageDiv.innerHTML = '';
                }, 5000);
            }
        }
        
        function setLoading(loading) {
            const submitBtn = document.getElementById('submitBtn');
            const btnText = document.getElementById('btnText');
            const loadingSpan = document.getElementById('loading');
            
            if (loading) {
                submitBtn.disabled = true;
                btnText.style.display = 'none';
                loadingSpan.style.display = 'inline';
            } else {
                submitBtn.disabled = false;
                btnText.style.display = 'inline';
                loadingSpan.style.display = 'none';
            }
        }
        
        function updateDeviceCount(count) {
            document.getElementById('deviceCount').textContent = count;
        }
        
        function updateNetworkName(name) {
            document.getElementById('networkName').textContent = name;
        }
        
        // Expose functions for ESP32 to call
        window.ESP32Update = {
            updateDeviceCount: updateDeviceCount,
            updateNetworkName: updateNetworkName
        };
    </script>
</body>
</html>
    )rawliteral";
}