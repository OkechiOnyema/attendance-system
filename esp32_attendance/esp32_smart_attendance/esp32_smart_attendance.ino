#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DNSServer.h>

// ESP32 connects to your laptop hotspot for internet access
const char* WIFI_SSID = "AttendanceWiFi";        // Your laptop hotspot name
const char* WIFI_PASSWORD = "attendance123";      // Your laptop hotspot password

// ESP32 creates its own network for students (NO INTERNET ACCESS)
const char* AP_SSID = "ESP32_Attendance";
const char* AP_PASSWORD = "esp32pass123";
const char* AP_IP = "192.168.5.1";

// Django Server (Your live system)
const char* DJANGO_SERVER = "https://attendance-system-muqs.onrender.com";
const char* DEVICE_ID = "ESP32_Smart_001";
const char* DEVICE_NAME = "CS101_Smart_Attendance";

// Web Server for ESP32
WebServer server(80);
DNSServer dnsServer;

// Connected devices tracking
int deviceCount = 0;
bool hotspotConnected = false;

// Active course session data
String activeCourseCode = "";
String activeCourseName = "";
String activeSessionId = "";
bool hasActiveSession = false;

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("ESP32 Smart Attendance System Starting...");
    Serial.println("This system fetches active course sessions and validates enrollment");
    Serial.println("Students must connect to ESP32 to mark attendance");
    
    // First, connect ESP32 to your laptop hotspot (for internet access)
    connectToHotspot();
    
    // Then create ESP32's own network for students (NO INTERNET)
    setupAccessPoint();
    
    // Setup Web Server
    setupWebServer();
    
    // Setup DNS Server (for captive portal - blocks all external access)
    dnsServer.start(53, "*", AP_IP);
    
    Serial.println("ESP32 Smart Attendance System Ready!");
    Serial.println("Students connect to ESP32 WiFi (NO INTERNET)");
    Serial.println("Laptop keeps internet access through hotspot");
    Serial.println("ESP32 will fetch active course sessions from Django");
}

void connectToHotspot() {
    Serial.println("Connecting to laptop hotspot...");
    
    WiFi.mode(WIFI_AP_STA); // ESP32 acts as both Station (connects to hotspot) and Access Point
    
    // Connect to your laptop hotspot
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println();
        Serial.println("Connected to laptop hotspot!");
        Serial.print("Hotspot IP: ");
        Serial.println(WiFi.localIP());
        hotspotConnected = true;
        
        // Fetch active course session immediately
        fetchActiveCourseSession();
    } else {
        Serial.println();
        Serial.println("Failed to connect to laptop hotspot!");
        Serial.println("ESP32 will work in Access Point mode only");
        hotspotConnected = false;
    }
}

void setupAccessPoint() {
    Serial.println("Setting up ESP32 WiFi network (NO INTERNET ACCESS)...");
    
    // Configure ESP32's own WiFi network
    WiFi.softAPConfig(IPAddress(192, 168, 5, 1), IPAddress(192, 168, 5, 1), IPAddress(255, 255, 255, 0));
    
    // Start ESP32's Access Point
    if (WiFi.softAP(AP_SSID, AP_PASSWORD)) {
        Serial.println("ESP32 WiFi Network Started Successfully!");
        Serial.print("SSID: ");
        Serial.println(AP_SSID);
        Serial.print("Password: ");
        Serial.println(AP_PASSWORD);
        Serial.print("IP Address: ");
        Serial.println(WiFi.softAPIP());
        Serial.println("Connected devices will have NO INTERNET ACCESS");
    } else {
        Serial.println("Failed to start ESP32 WiFi network!");
    }
}

void setupWebServer() {
    Serial.println("Setting up Web Server...");
    
    // Main attendance page
    server.on("/", HTTP_GET, handleAttendancePage);
    
    // API endpoints
    server.on("/api/mark-attendance", HTTP_POST, handleAttendanceSubmission);
    server.on("/api/active-course", HTTP_GET, handleActiveCourse);
    server.on("/api/status", HTTP_GET, handleStatus);
    server.on("/api/refresh-course", HTTP_GET, handleRefreshCourse);
    
    // Captive portal - redirect ALL other requests to main page
    server.onNotFound(handleCaptivePortal);
    
    server.begin();
    Serial.println("Web Server started on port 80");
    Serial.println("All external requests will be blocked");
}

void fetchActiveCourseSession() {
    if (!hotspotConnected) {
        Serial.println("ESP32 not connected to internet - cannot fetch active course");
        return;
    }
    
    Serial.println("Fetching active course session from Django...");
    
    HTTPClient http;
    String url = String(DJANGO_SERVER) + "/admin-panel/api/esp32/active-course/";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    // Send request to get active course
    int httpResponseCode = http.GET();
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println("Django response: " + response);
        
        // Parse the response to get active course info
        parseActiveCourseResponse(response);
        
        http.end();
    } else {
        Serial.println("Failed to fetch active course: " + http.errorToString(httpResponseCode));
        http.end();
    }
}

void parseActiveCourseResponse(String response) {
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, response);
    
    if (error) {
        Serial.println("JSON parsing failed: " + String(error.c_str()));
        return;
    }
    
    // Check if there's an active course
    if (doc.containsKey("active_course") && doc["active_course"] == true) {
        hasActiveSession = true;
        activeCourseCode = doc["course_code"].as<String>();
        activeCourseName = doc["course_title"].as<String>();
        activeSessionId = doc["session"].as<String>();
        
        Serial.println("Active Course Found!");
        Serial.println("Course Code: " + activeCourseCode);
        Serial.println("Course Name: " + activeCourseName);
        Serial.println("Session: " + activeSessionId);
    } else {
        hasActiveSession = false;
        activeCourseCode = "";
        activeCourseName = "";
        activeSessionId = "";
        
        Serial.println("No active course session found");
    }
}

void handleAttendancePage() {
    String html = "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>Smart Attendance System</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px}.container{max-width:600px;margin:0 auto;background:white;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);overflow:hidden}.header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:30px;text-align:center}.header h1{font-size:28px;margin-bottom:10px}.header p{opacity:0.9;font-size:16px}.course-info{background:#e8f4fd;padding:20px;margin:20px;border-radius:10px;border-left:4px solid #2196f3;text-align:center}.course-info h3{color:#1976d2;margin-bottom:10px}.no-course{background:#fff3cd;color:#856404;padding:20px;margin:20px;border-radius:10px;border:1px solid #ffeaa7;text-align:center}.form-container{padding:30px}.form-group{margin-bottom:20px}.form-label{display:block;margin-bottom:8px;font-weight:600;color:#333;font-size:14px}.form-input{width:100%;padding:15px;border:2px solid #e1e8ed;border-radius:10px;font-size:16px;transition:all 0.3s ease}.form-input:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}.submit-btn{width:100%;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;padding:15px;border-radius:10px;font-size:16px;font-weight:600;cursor:pointer;transition:transform 0.2s ease}.submit-btn:hover{transform:translateY(-2px)}.submit-btn:disabled{background:#ccc;cursor:not-allowed;transform:none}.status{padding:15px;border-radius:10px;margin:20px 0;text-align:center;font-weight:600}.status.success{background:#d4edda;color:#155724;border:1px solid #c3e6cb}.status.error{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb}.status.info{background:#d1ecf1;color:#0c5460;border:1px solid #bee5eb}.refresh-btn{background:#28a745;color:white;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;margin-top:10px}.refresh-btn:hover{background:#218838}</style></head><body><div class='container'><div class='header'><h1>Smart Attendance</h1><p>Physical Presence Authentication System</p></div><div id='courseInfo'></div><div id='attendanceForm' class='form-container' style='display:none'><h2 style='text-align:center;margin-bottom:20px'>Mark Attendance</h2><form id='attendanceFormElement'><div class='form-group'><label class='form-label' for='matricNumber'>Matric Number</label><input type='text' id='matricNumber' class='form-input' placeholder='Enter your matric number' required></div><button type='submit' class='submit-btn' id='submitBtn'>Mark Attendance</button></form><div id='status' class='status' style='display:none'></div></div></div><script>window.onload=function(){loadActiveCourse()};async function loadActiveCourse(){try{const response=await fetch('/api/active-course');const data=await response.json();const courseInfoDiv=document.getElementById('courseInfo');const attendanceForm=document.getElementById('attendanceForm');if(data.has_active_session){courseInfoDiv.innerHTML='<div class=\"course-info\"><h3>Active Course Session</h3><p><strong>Course Code:</strong> '+data.course_code+'</p><p><strong>Course Name:</strong> '+data.course_name+'</p><p><strong>Session:</strong> '+data.session_id+'</p><p><strong>Status:</strong> <span style=\"color:#28a745\">Active</span></p><button class=\"refresh-btn\" onclick=\"loadActiveCourse()\">Refresh Course Info</button></div>';attendanceForm.style.display='block'}else{courseInfoDiv.innerHTML='<div class=\"no-course\"><h3>Warning: No Active Course Session</h3><p>There is currently no active course session for attendance marking.</p><p>Please wait for a lecturer to start a session.</p><button class=\"refresh-btn\" onclick=\"loadActiveCourse()\">Refresh</button></div>';attendanceForm.style.display='none'}}catch(error){console.error('Error loading course info:',error)}}document.getElementById('attendanceFormElement').addEventListener('submit',async function(e){e.preventDefault();const submitBtn=document.getElementById('submitBtn');const statusDiv=document.getElementById('status');const matricNumber=document.getElementById('matricNumber').value;submitBtn.disabled=true;submitBtn.innerHTML='Marking Attendance...';statusDiv.style.display='none';try{const response=await fetch('/api/mark-attendance',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({matric_number:matricNumber})});const result=await response.json();if(result.success){showStatus('Attendance marked successfully!','success');document.getElementById('matricNumber').value=''}else{showStatus('Error: '+result.message,'error')}}catch(error){showStatus('Error: '+error.message,'error')}finally{submitBtn.disabled=false;submitBtn.innerHTML='Mark Attendance'}});function showStatus(message,type){const statusDiv=document.getElementById('status');statusDiv.textContent=message;statusDiv.className='status '+type;statusDiv.style.display='block';if(type==='success'){setTimeout(function(){statusDiv.style.display='none'},5000)}}</script></body></html>";
    
    server.send(200, "text/html", html);
}

void handleAttendanceSubmission() {
    if (server.method() != HTTP_POST) {
        server.send(405, "text/plain", "Method Not Allowed");
        return;
    }
    
    String body = server.arg("plain");
    Serial.println("Received attendance submission: " + body);
    
    // Parse JSON
    DynamicJsonDocument doc(512);
    DeserializationError error = deserializeJson(doc, body);
    
    if (error) {
        Serial.println("JSON parsing failed: " + String(error.c_str()));
        server.send(400, "application/json", "{\"success\":false,\"message\":\"Invalid JSON\"}");
        return;
    }
    
    // Extract matric number
    String matricNumber = doc["matric_number"].as<String>();
    
    // Validate matric number
    if (matricNumber.isEmpty()) {
        server.send(400, "application/json", "{\"success\":false,\"message\":\"Matric number is required\"}");
        return;
    }
    
    // Check if there's an active course session
    if (!hasActiveSession) {
        server.send(400, "application/json", "{\"success\":false,\"message\":\"No active course session found\"}");
        return;
    }
    
    // Send to Django server for enrollment validation and attendance recording
    bool success = markAttendanceWithValidation(matricNumber);
    
    if (success) {
        server.send(200, "application/json", "{\"success\":true,\"message\":\"Attendance recorded successfully\"}");
    } else {
        server.send(500, "application/json", "{\"success\":false,\"message\":\"Failed to record attendance\"}");
    }
}

bool markAttendanceWithValidation(String matricNumber) {
    // Only proceed if ESP32 is connected to internet (laptop hotspot)
    if (!hotspotConnected) {
        Serial.println("ESP32 not connected to internet - cannot send to Django");
        return false;
    }
    
    HTTPClient http;
    
    // Create JSON payload with course session info
    DynamicJsonDocument doc(1024);
    doc["matric_number"] = matricNumber;
    doc["course_code"] = activeCourseCode;
    doc["course_name"] = activeCourseName;
    doc["session_id"] = activeSessionId;
    doc["device_id"] = DEVICE_ID;
    doc["timestamp"] = millis();
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    Serial.println("Sending attendance with validation to Django: " + jsonString);
    
    // Send to Django server for enrollment validation and attendance recording
    String url = String(DJANGO_SERVER) + "/admin-panel/api/esp32/mark-attendance/";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    
    int httpResponseCode = http.POST(jsonString);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println("Django response: " + response);
        http.end();
        return true;
    } else {
        Serial.println("Django request failed: " + http.errorToString(httpResponseCode));
        http.end();
        return false;
    }
}

void handleActiveCourse() {
    // Return current active course information
    DynamicJsonDocument doc(512);
    doc["has_active_session"] = hasActiveSession;
    doc["course_code"] = activeCourseCode;
    doc["course_name"] = activeCourseName;
    doc["session_id"] = activeSessionId;
    doc["device_id"] = DEVICE_ID;
    
    String response;
    serializeJson(doc, response);
    
    server.send(200, "application/json", response);
}

void handleRefreshCourse() {
    // Refresh active course session from Django
    if (hotspotConnected) {
        fetchActiveCourseSession();
        server.send(200, "application/json", "{\"message\":\"Course session refreshed\"}");
    } else {
        server.send(500, "application/json", "{\"error\":\"ESP32 not connected to internet\"}");
    }
}

void handleStatus() {
    String status = "{\"device_name\":\"" + String(DEVICE_NAME) + "\",\"connected_devices\":" + String(deviceCount) + ",\"hotspot_connected\":" + (hotspotConnected ? "true" : "false") + ",\"has_active_session\":" + (hasActiveSession ? "true" : "false") + ",\"active_course\":\"" + activeCourseCode + "\",\"status\":\"active\"}";
    server.send(200, "application/json", status);
}

void handleCaptivePortal() {
    // Redirect ALL unknown requests to main page (blocks external access)
    server.sendHeader("Location", "http://192.168.5.1", true);
    server.send(302, "text/plain", "");
}

void loop() {
    // Handle web server
    server.handleClient();
    
    // Handle DNS server (blocks all external access)
    dnsServer.processNextRequest();
    
    // Update connected devices
    updateConnectedDevices();
    
    // Refresh course session every 5 minutes
    static unsigned long lastRefresh = 0;
    if (millis() - lastRefresh > 300000) { // 5 minutes
        if (hotspotConnected) {
            fetchActiveCourseSession();
        }
        lastRefresh = millis();
    }
    
    delay(100);
}

void updateConnectedDevices() {
    // Check for new connections to ESP32
    int currentDevices = WiFi.softAPgetStationNum();
    if (currentDevices != deviceCount) {
        if (currentDevices > deviceCount) {
            Serial.println("New device connected to ESP32");
        } else {
            Serial.println("Device disconnected from ESP32");
        }
        deviceCount = currentDevices;
        Serial.println("Total connected devices: " + String(deviceCount));
    }
}
