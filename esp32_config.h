/*
 * ESP32 Configuration File
 * 
 * Update these settings for your network and Django server
 */

#ifndef ESP32_CONFIG_H
#define ESP32_CONFIG_H

// ===== WIFI CLIENT CONFIGURATION =====
// Your WiFi network credentials (for Django communication)
#define WIFI_NETWORK_NAME "AttendanceWiFi"  // Your WiFi network name
#define WIFI_NETWORK_PASSWORD "attendance123"  // Your WiFi password

// ===== DJANGO SERVER CONFIGURATION =====
// Django server URL (localhost - ESP32 will reach it via your computer)
#define DJANGO_SERVER_URL "http://10.66.19.27:8000"  // Your computer's IP on the network

// ===== DEVICE CONFIGURATION =====
#define DEVICE_ID_PREFIX "ESP32_001"  // Must match Django database ESP32 device ID

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
