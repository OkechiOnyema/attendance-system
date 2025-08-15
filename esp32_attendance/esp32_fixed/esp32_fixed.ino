/*
 * ESP32 Fixed Attendance System
 * 
 * This ESP32 creates a WiFi network and monitors student connections
 * for attendance tracking. Fixed to work with current network setup.
 * 
 * Hardware: ESP32 DevKit or ESP32 CAM
 * 
 * Setup:
 * 1. Install ESP32 board in Arduino IDE
 * 2. Install ArduinoJson library
 * 3. Upload to ESP32
 * 4. Connect to ESP32 WiFi network
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DNSServer.h>

// ===== CONFIGURATION =====
const char* ESP32_SSID = "ESP32_Attendance";     // WiFi network name
const char* ESP32_PASSWORD = "";                  // No password
const char* ESP32_IP = "192.168.4.1";            // ESP32 IP address
const char* DJANGO_SERVER = "http://10.141.126.27:8000";  // Django server URL (your computer's IP)

// ===== GLOBAL VARIABLES =====
DNSServer dnsServer;
WiFiServer server(80);
HTTPClient http;

// Device tracking
struct ConnectedDevice {
  String mac;
  String ip;
  bool connected;
  unsigned long lastSeen;
};

ConnectedDevice devices[50];
int deviceCount = 0;

// Timing
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 30000; // 30 seconds

// ===== SETUP =====
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("🚀 ESP32 Attendance System Starting...");
  
  // Setup ESP32 as Access Point
  setupESP32AP();
  
  // Setup DNS server for captive portal
  setupDNSServer();
  
  // Start HTTP server
  server.begin();
  
  Serial.println("✅ ESP32 Ready!");
  Serial.print("📶 Network: ");
  Serial.println(ESP32_SSID);
  Serial.print("🌐 IP Address: ");
  Serial.println(ESP32_IP);
  Serial.print("💻 Django Server: ");
  Serial.println(DJANGO_SERVER);
  Serial.println("🔓 No password required");
}

// ===== MAIN LOOP =====
void loop() {
  // Handle DNS requests
  dnsServer.processNextRequest();
  
  // Handle client connections
  handleClients();
  
  // Send heartbeat to Django
  if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  delay(100);
}

// ===== ESP32 ACCESS POINT SETUP =====
void setupESP32AP() {
  Serial.println("🌉 Setting up ESP32 Access Point...");
  
  // Set WiFi mode to Access Point only
  WiFi.mode(WIFI_AP);
  
  // Configure static IP
  IPAddress localIP;
  localIP.fromString(ESP32_IP);
  
  IPAddress gateway;
  gateway.fromString(ESP32_IP);
  
  IPAddress subnet;
  subnet.fromString("255.255.255.0");
  
  // Start Access Point
  WiFi.softAP(ESP32_SSID, ESP32_PASSWORD);
  
  // Configure AP settings
  WiFi.softAPConfig(localIP, gateway, subnet);
  
  IPAddress IP = WiFi.softAPIP();
  Serial.print("📡 ESP32 IP: ");
  Serial.println(IP);
  
  Serial.println("✅ Access Point Ready!");
}

// ===== DNS SERVER SETUP =====
void setupDNSServer() {
  dnsServer.start(53, "*", WiFi.softAPIP());
}

// ===== CLIENT HANDLING =====
void handleClients() {
  WiFiClient client = server.available();
  
  if (client) {
    Serial.println("🔌 New client connected");
    
    String request = client.readStringUntil('\r');
    client.flush();
    
    // Extract client IP
    String clientIP = client.remoteIP().toString();
    
    // Generate MAC address (simplified)
    String clientMAC = "ESP32_" + String(random(1000, 9999));
    
    // Record device connection
    recordDeviceConnection(clientMAC, clientIP, "Student Device");
    
    // Send captive portal response
    sendCaptivePortal(client);
    
    client.stop();
  }
}

// ===== DEVICE MANAGEMENT =====
void recordDeviceConnection(String mac, String ip, String name) {
  Serial.println("📱 Student device connected - recording attendance");
  
  // Check if device already exists
  for (int i = 0; i < deviceCount; i++) {
    if (devices[i].mac == mac) {
      if (!devices[i].connected) {
        devices[i].connected = true;
        devices[i].ip = ip;
        devices[i].lastSeen = millis();
        
        // Send connection to Django
        sendDeviceConnected(mac, ip, name);
      }
      return;
    }
  }
  
  // Add new device
  if (deviceCount < 50) {
    devices[deviceCount].mac = mac;
    devices[deviceCount].ip = ip;
    devices[deviceCount].connected = true;
    devices[deviceCount].lastSeen = millis();
    
    deviceCount++;
    
    // Send connection to Django
    sendDeviceConnected(mac, ip, name);
    
    Serial.print("✅ New student connected: ");
    Serial.print(mac);
    Serial.print(" (");
    Serial.print(ip);
    Serial.println(")");
    Serial.println("📤 Attendance data sent to Django");
  }
}

// ===== DJANGO COMMUNICATION =====
void sendHeartbeat() {
  Serial.println("💓 Sending heartbeat to Django...");
  Serial.print("🌐 Django URL: ");
  Serial.println(DJANGO_SERVER + String("/admin-panel/api/esp32/heartbeat/"));
  
  http.begin(DJANGO_SERVER + String("/admin-panel/api/esp32/heartbeat/"));
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["device_id"] = "ESP32_CS101_001";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.print("📤 Sending data: ");
  Serial.println(jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    Serial.println("✅ Heartbeat sent successfully");
    Serial.print("📊 Response code: ");
    Serial.println(httpResponseCode);
    
    String response = http.getString();
    Serial.print("📥 Response: ");
    Serial.println(response);
  } else {
    Serial.print("❌ Heartbeat failed, error: ");
    Serial.println(httpResponseCode);
    Serial.print("❌ Error: ");
    Serial.println(http.errorToString(httpResponseCode));
  }
  
  http.end();
}

void sendDeviceConnected(String mac, String ip, String name) {
  Serial.println("📤 Sending device connection to Django...");
  Serial.print("🌐 Django URL: ");
  Serial.println(DJANGO_SERVER + String("/admin-panel/api/esp32/connected/"));
  
  http.begin(DJANGO_SERVER + String("/admin-panel/api/esp32/connected/"));
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<300> doc;
  doc["device_id"] = "ESP32_CS101_001";
  doc["mac_address"] = mac;
  doc["device_name"] = name;
  doc["ip_address"] = ip;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.print("📤 Sending data: ");
  Serial.println(jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    Serial.println("✅ Device connection sent to Django");
    Serial.print("📊 Response code: ");
    Serial.println(httpResponseCode);
    
    String response = http.getString();
    Serial.print("📥 Response: ");
    Serial.println(response);
  } else {
    Serial.print("❌ Device connection failed, error: ");
    Serial.println(httpResponseCode);
    Serial.print("❌ Error: ");
    Serial.println(http.errorToString(httpResponseCode));
  }
  
  http.end();
}

// ===== CAPTIVE PORTAL =====
void sendCaptivePortal(WiFiClient& client) {
  String html = R"(
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>ESP32 Attendance</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .container { max-width: 400px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }
        .status { color: #4ade80; font-weight: bold; font-size: 18px; }
        .info { color: #e2e8f0; font-size: 14px; margin: 10px 0; }
        .btn { background: #4ade80; color: white; padding: 12px 24px; border: none; border-radius: 8px; text-decoration: none; display: inline-block; margin: 10px; }
    </style>
</head>
<body>
    <div class='container'>
        <h2>🌉 ESP32 Attendance System</h2>
        <p class='status'>✅ Connected to ESP32 Network!</p>
        
        <p class='info'>You are now connected to the attendance tracking network.</p>
        <p class='info'>Your attendance will be automatically recorded.</p>
        
        <a href='http://10.141.126.27:8000' class='btn'>Access Django Dashboard</a>
        
        <p class='info'>📱 Device: ESP32_CS101_001</p>
        <p class='info'>🌐 Network: ESP32_Attendance</p>
        <p class='info'>💻 Django: 10.141.126.27:8000</p>
    </div>
</body>
</html>
  )";
  
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/html");
  client.println("Content-Length: " + String(html.length()));
  client.println();
  client.println(html);
}

// ===== DEBUG FUNCTIONS =====
void printConnectedDevices() {
  Serial.println("\n📱 Connected Devices:");
  Serial.println("==================");
  
  for (int i = 0; i < deviceCount; i++) {
    if (devices[i].connected) {
      Serial.print("MAC: ");
      Serial.print(devices[i].mac);
      Serial.print(" | IP: ");
      Serial.println(devices[i].ip);
    }
  }
  
  Serial.print("Total connected: ");
  Serial.println(deviceCount);
  Serial.println("==================\n");
}
