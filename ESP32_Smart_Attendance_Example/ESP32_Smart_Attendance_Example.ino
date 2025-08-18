/*
 * ESP32 Smart Attendance System
 * Network-Based Access Control Example
 * 
 * This sketch demonstrates how to:
 * 1. Create a WiFi access point
 * 2. Monitor device connections/disconnections
 * 3. Serve the attendance web page
 * 4. Validate attendance submissions
 * 5. Ensure only connected devices can mark attendance
 */

#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Configuration
const char* ssid = "ESP32_Attendance";  // WiFi network name
const char* password = "12345678";       // WiFi password
const char* deviceId = "ESP32_001";      // Unique device ID
const char* serverUrl = "http://your-server.com"; // Django server URL

// Web server on port 80
WebServer server(80);

// Store connected devices
struct ConnectedDevice {
  String ip;
  String mac;
  String name;
  unsigned long connectedAt;
};

#define MAX_DEVICES 50
ConnectedDevice connectedDevices[MAX_DEVICES];
int deviceCount = 0;

// HTML page for attendance
const char* attendancePage = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <title>Smart Attendance</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 400px; margin: 0 auto; }
        input, button { width: 100%; padding: 10px; margin: 10px 0; }
        .message { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Smart Attendance</h1>
        <p>Enter your matric number to mark attendance</p>
        
        <div id="sessionInfo">
            <h3>Session Details</h3>
            <p><strong>Course:</strong> <span id="courseCode">Loading...</span></p>
            <p><strong>Lecturer:</strong> <span id="lecturerName">Loading...</span></p>
        </div>
        
        <form id="attendanceForm">
            <input type="text" id="matricNo" placeholder="Enter matric number" required>
            <button type="submit">Mark Attendance</button>
        </form>
        
        <div id="message" class="message" style="display: none;"></div>
    </div>

    <script>
        const DEVICE_ID = 'ESP32_001';
        const API_BASE_URL = 'http://your-server.com/admin-panel';
        let currentSession = null;
        
        // Load session info
        async function loadSession() {
            try {
                const response = await fetch(`${API_BASE_URL}/api/session/active/?device_id=${DEVICE_ID}`);
                const data = await response.json();
                
                if (data.active) {
                    currentSession = data;
                    document.getElementById('courseCode').textContent = data.course_code;
                    document.getElementById('lecturerName').textContent = data.lecturer_name;
                } else {
                    showMessage('No active session found', 'error');
                }
            } catch (error) {
                showMessage('Error loading session', 'error');
            }
        }
        
        // Submit attendance
        document.getElementById('attendanceForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const matricNo = document.getElementById('matricNo').value.trim();
            if (!matricNo) {
                showMessage('Please enter matric number', 'error');
                return;
            }
            
            if (!currentSession) {
                showMessage('No active session', 'error');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/attendance/submit/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: currentSession.session_id,
                        student_matric_no: matricNo,
                        device_id: DEVICE_ID,
                        client_ip: window.location.hostname
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showMessage(result.message, 'success');
                    document.getElementById('matricNo').value = '';
                } else {
                    showMessage(result.error, 'error');
                }
            } catch (error) {
                showMessage('Error submitting attendance', 'error');
            }
        });
        
        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = `message ${type}`;
            msg.style.display = 'block';
            setTimeout(() => msg.style.display = 'none', 5000);
        }
        
        // Load session on page load
        loadSession();
    </script>
</body>
</html>
)rawliteral";

void setup() {
  Serial.begin(115200);
  
  // Create WiFi access point
  WiFi.softAP(ssid, password);
  
  Serial.println("ESP32 Smart Attendance System");
  Serial.print("SSID: ");
  Serial.println(ssid);
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());
  
  // Set up web server routes
  server.on("/", HTTP_GET, handleRoot);
  server.on("/connect", HTTP_POST, handleDeviceConnect);
  server.on("/disconnect", HTTP_POST, handleDeviceDisconnect);
  
  // Start web server
  server.begin();
  Serial.println("Web server started");
  
  // Start monitoring task
  xTaskCreate(monitorConnections, "MonitorConnections", 4096, NULL, 1, NULL);
}

void loop() {
  server.handleClient();
  delay(10);
}

// Serve attendance page
void handleRoot() {
  server.send(200, "text/html", attendancePage);
}

// Handle device connection
void handleDeviceConnect() {
  if (server.hasArg("plain")) {
    String body = server.arg("plain");
    
    // Parse JSON
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, body);
    
    if (!error) {
      String clientIP = doc["client_ip"].as<String>();
      String clientMAC = doc["client_mac"].as<String>();
      String clientName = doc["client_name"].as<String>();
      
      // Add to connected devices
      addConnectedDevice(clientIP, clientMAC, clientName);
      
      // Notify Django server
      notifyServerDeviceConnected(clientIP, clientMAC, clientName);
      
      server.send(200, "application/json", "{\"status\":\"connected\"}");
    } else {
      server.send(400, "application/json", "{\"error\":\"Invalid JSON\"}");
    }
  } else {
    server.send(400, "application/json", "{\"error\":\"No data\"}");
  }
}

// Handle device disconnection
void handleDeviceDisconnect() {
  if (server.hasArg("plain")) {
    String body = server.arg("plain");
    
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, body);
    
    if (!error) {
      String clientIP = doc["client_ip"].as<String>();
      
      // Remove from connected devices
      removeConnectedDevice(clientIP);
      
      // Notify Django server
      notifyServerDeviceDisconnected(clientIP);
      
      server.send(200, "application/json", "{\"status\":\"disconnected\"}");
    } else {
      server.send(400, "application/json", "{\"error\":\"Invalid JSON\"}");
    }
  } else {
    server.send(400, "application/json", "{\"error\":\"No data\"}");
  }
}

// Add connected device
void addConnectedDevice(String ip, String mac, String name) {
  if (deviceCount < MAX_DEVICES) {
    connectedDevices[deviceCount].ip = ip;
    connectedDevices[deviceCount].mac = mac;
    connectedDevices[deviceCount].name = name;
    connectedDevices[deviceCount].connectedAt = millis();
    deviceCount++;
    
    Serial.printf("Device connected: %s (%s) at %s\n", name.c_str(), mac.c_str(), ip.c_str());
  }
}

// Remove disconnected device
void removeConnectedDevice(String ip) {
  for (int i = 0; i < deviceCount; i++) {
    if (connectedDevices[i].ip == ip) {
      Serial.printf("Device disconnected: %s (%s)\n", 
                   connectedDevices[i].name.c_str(), 
                   connectedDevices[i].ip.c_str());
      
      // Shift remaining devices
      for (int j = i; j < deviceCount - 1; j++) {
        connectedDevices[j] = connectedDevices[j + 1];
      }
      deviceCount--;
      break;
    }
  }
}

// Notify Django server about device connection
void notifyServerDeviceConnected(String ip, String mac, String name) {
  HTTPClient http;
  http.begin(String(serverUrl) + "/admin-panel/api/device/connected-smart/");
  http.addHeader("Content-Type", "application/json");
  
  String payload = "{\"device_id\":\"" + String(deviceId) + 
                   "\",\"client_ip\":\"" + ip + 
                   "\",\"client_mac\":\"" + mac + 
                   "\",\"client_name\":\"" + name + "\"}";
  
  int httpCode = http.POST(payload);
  
  if (httpCode == 200) {
    Serial.println("Server notified of device connection");
  } else {
    Serial.printf("Failed to notify server: %d\n", httpCode);
  }
  
  http.end();
}

// Notify Django server about device disconnection
void notifyServerDeviceDisconnected(String ip) {
  HTTPClient http;
  http.begin(String(serverUrl) + "/admin-panel/api/device/disconnected-smart/");
  http.addHeader("Content-Type", "application/json");
  
  String payload = "{\"device_id\":\"" + String(deviceId) + 
                   "\",\"client_ip\":\"" + ip + "\"}";
  
  int httpCode = http.POST(payload);
  
  if (httpCode == 200) {
    Serial.println("Server notified of device disconnection");
  } else {
    Serial.printf("Failed to notify server: %d\n", httpCode);
  }
  
  http.end();
}

// Monitor WiFi connections (runs in separate task)
void monitorConnections(void * parameter) {
  while (true) {
    // Check for new connections (this is a simplified approach)
    // In practice, you might use WiFi events or DHCP lease monitoring
    
    delay(5000); // Check every 5 seconds
  }
}

// Print connected devices info
void printConnectedDevices() {
  Serial.printf("\nConnected Devices: %d\n", deviceCount);
  for (int i = 0; i < deviceCount; i++) {
    Serial.printf("%d: %s (%s) - %s\n", 
                 i + 1,
                 connectedDevices[i].name.c_str(),
                 connectedDevices[i].mac.c_str(),
                 connectedDevices[i].ip.c_str());
  }
  Serial.println();
}
