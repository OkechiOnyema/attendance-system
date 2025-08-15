/*
 * ESP32 Configuration File for Access Point Mode
 * 
 * Update these settings for your ESP32 access point network
 */

#ifndef ESP32_CONFIG_H
#define ESP32_CONFIG_H

// ===== ESP32 ACCESS POINT CONFIGURATION =====
// ESP32 creates its own network for all devices
#define ESP32_AP_SSID "ESP32_Attendance"     // Network name ESP32 creates
#define ESP32_AP_PASSWORD ""                  // No password - open network
#define ESP32_AP_IP "192.168.4.1"            // ESP32's IP address
#define ESP32_AP_GATEWAY "192.168.4.1"       // Gateway for connected devices
#define ESP32_AP_SUBNET "255.255.255.0"      // Subnet mask

// ===== DJANGO SERVER CONFIGURATION =====
// Django will run on ESP32 network IP
#define DJANGO_SERVER_URL "http://192.168.4.1:8000"  // Django on ESP32 network

// ===== DEVICE CONFIGURATION =====
#define DEVICE_ID_PREFIX "ESP32_"  // Base device ID prefix

// ===== TIMING CONFIGURATION =====
#define HEARTBEAT_INTERVAL 30000      // 30 seconds
#define COURSE_CHECK_INTERVAL 60000   // 1 minute
#define DEVICE_TIMEOUT 300000         // 5 minutes

// ===== NETWORK CONFIGURATION =====
#define MAX_CONNECTED_DEVICES 50      // Maximum number of student devices
#define AP_CHANNEL 1                  // WiFi channel for Access Point
#define AP_MAX_CONNECTIONS 10         // Maximum WiFi connections

// ===== DEBUG CONFIGURATION =====
#define DEBUG_SERIAL true             // Enable serial debugging
#define DEBUG_HTTP true               // Enable HTTP request/response logging

#endif // ESP32_CONFIG_H
