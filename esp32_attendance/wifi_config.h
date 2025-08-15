/*
 * WiFi Configuration for ESP32 Bridge
 * 
 * SETUP: Use your laptop's WiFi hotspot for best results!
 * 
 * 1. Turn on WiFi hotspot on your laptop
 * 2. Update the credentials below
 * 3. Upload to ESP32
 * 4. Students connect to same hotspot
 */

// WiFi Network Credentials (Your Laptop Hotspot)
#define WIFI_SSID "AttendanceWiFi"         // Your laptop's hotspot network name
#define WIFI_PASSWORD "attendance123"       // Your laptop's hotspot password

// Django Server URL (your computer's IP address)
#define DJANGO_SERVER "http://10.141.126.27:8000"

// ESP32 Device Configuration
#define DEVICE_ID "ESP32_Bridge_001"
#define DEVICE_NAME "CS101_Classroom_Bridge"

// Optional: WiFi Connection Settings
#define WIFI_TIMEOUT 30000  // 30 seconds timeout
#define WIFI_RETRY_DELAY 5000  // 5 seconds between retries

/*
 * IMPORTANT NOTES:
 * 
 * 1. Make sure your laptop hotspot is ON before uploading ESP32 code
 * 2. ESP32 will connect to your laptop's hotspot automatically
 * 3. Students must connect to the SAME hotspot to access ESP32
 * 4. All devices will be on the same network = perfect communication!
 * 
 * TROUBLESHOOTING:
 * - If ESP32 won't connect, check hotspot is ON and credentials are correct
 * - If students can't access ESP32, make sure they're on the same hotspot
 * - Check Serial Monitor for connection status and IP address
 */
