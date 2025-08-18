/*
 * ESP32 Configuration Header File
 * 
 * This file contains all the configurable settings for your ESP32 devices.
 * Update these values according to your network and device setup.
 * 
 * Author: Attendance System Team
 * Date: 2025
 */

#ifndef ESP32_CONFIG_H
#define ESP32_CONFIG_H

// ========================================
// DJANGO SERVER CONFIGURATION
// ========================================

// Your Django server IP address
// Change this to match your Django server's IP address
const char* DJANGO_SERVER = "192.168.4.100";  // UPDATE THIS IP ADDRESS

// Django server port (usually 8000 for development)
const int DJANGO_PORT = 8000;

// ========================================
// ESP32 DEVICE CONFIGURATION
// ========================================

// Device identification - MUST BE UNIQUE for each ESP32
const char* DEVICE_ID = "ESP32_001";          // UPDATE: Make unique per device

// Human-readable device name
const char* DEVICE_NAME = "Classroom_ESP32";  // UPDATE: Descriptive name

// Physical location of the device
const char* LOCATION = "Main Building Room 101"; // UPDATE: Actual location

// ========================================
// WIFI CONFIGURATION
// ========================================

// WiFi network name prefix (will be combined with DEVICE_ID)
const char* WIFI_PREFIX = "Attendance_";      // UPDATE: Network name prefix

// WiFi password (leave empty for open network)
const char* WIFI_PASSWORD = "";               // UPDATE: Add password if needed

// ========================================
// TIMING CONFIGURATION
// ========================================

// How often to send heartbeat to Django (in milliseconds)
const unsigned long HEARTBEAT_INTERVAL = 30000;    // 30 seconds

// How often to check for active sessions (in milliseconds)
const unsigned long SESSION_CHECK_INTERVAL = 60000; // 1 minute

// ========================================
// MULTIPLE DEVICE SETUP EXAMPLES
// ========================================

/*
 * For multiple classrooms, create different config files or use these examples:
 * 
 * // Classroom 1 - Computer Science
 * const char* DEVICE_ID = "ESP32_CS101_001";
 * const char* DEVICE_NAME = "CS101_Classroom";
 * const char* LOCATION = "Computer Science Building Room 101";
 * const char* WIFI_PREFIX = "CS101_Attendance_";
 * 
 * // Classroom 2 - Mathematics
 * const char* DEVICE_ID = "ESP32_MATH201_001";
 * const char* DEVICE_NAME = "MATH201_Classroom";
 * const char* LOCATION = "Mathematics Building Room 201";
 * const char* WIFI_PREFIX = "MATH201_Attendance_";
 * 
 * // Classroom 3 - Engineering
 * const char* DEVICE_ID = "ESP32_ENG301_001";
 * const char* DEVICE_NAME = "ENG301_Classroom";
 * const char* LOCATION = "Engineering Building Room 301";
 * const char* WIFI_PREFIX = "ENG301_Attendance_";
 */

// ========================================
// ADVANCED CONFIGURATION
// ========================================

// Maximum number of WiFi clients (ESP32 can handle up to 8)
const int MAX_WIFI_CLIENTS = 8;

// WiFi channel (1-13, leave as 0 for auto)
const int WIFI_CHANNEL = 0;

// WiFi power (0-84, higher = more power)
const int WIFI_POWER = 84;

// ========================================
// DEBUG CONFIGURATION
// ========================================

// Enable/disable debug output
#define DEBUG_ENABLED true

// Serial baud rate
#define SERIAL_BAUD 115200

// ========================================
// SECURITY CONFIGURATION
// ========================================

// Enable basic WiFi authentication (if WIFI_PASSWORD is set)
#define WIFI_AUTH_ENABLED false

// Rate limiting for attendance submissions (in milliseconds)
const unsigned long SUBMISSION_COOLDOWN = 5000; // 5 seconds between submissions

// ========================================
// NETWORK CONFIGURATION
// ========================================

// Static IP configuration (optional, leave as 0 for DHCP)
const int STATIC_IP_1 = 192;
const int STATIC_IP_2 = 168;
const int STATIC_IP_3 = 4;
const int STATIC_IP_4 = 1;

// Gateway IP (usually your router's IP)
const int GATEWAY_IP_1 = 192;
const int GATEWAY_IP_2 = 168;
const int GATEWAY_IP_3 = 4;
const int GATEWAY_IP_4 = 1;

// Subnet mask
const int SUBNET_1 = 255;
const int SUBNET_2 = 255;
const int SUBNET_3 = 255;
const int SUBNET_4 = 0;

// ========================================
// PERSISTENCE CONFIGURATION
// ========================================

// Enable persistent storage of session data
#define PERSISTENCE_ENABLED true

// Preferences namespace
#define PREFERENCES_NAMESPACE "attendance"

// ========================================
// ERROR HANDLING CONFIGURATION
// ========================================

// Maximum retry attempts for HTTP requests
const int MAX_RETRY_ATTEMPTS = 3;

// Retry delay between attempts (in milliseconds)
const unsigned long RETRY_DELAY = 5000;

// ========================================
// FEATURE FLAGS
// ========================================

// Enable OLED display support
#define OLED_DISPLAY_ENABLED false

// Enable LED indicators
#define LED_INDICATORS_ENABLED false

// Enable buzzer/sound notifications
#define SOUND_NOTIFICATIONS_ENABLED false

// Enable deep sleep mode for power saving
#define DEEP_SLEEP_ENABLED false

// ========================================
// CUSTOMIZATION NOTES
// ========================================

/*
 * IMPORTANT: Before uploading to ESP32, update these values:
 * 
 * 1. DJANGO_SERVER: Set to your Django server's actual IP address
 * 2. DEVICE_ID: Make unique for each ESP32 device
 * 3. DEVICE_NAME: Give a descriptive name for the device
 * 4. LOCATION: Specify the actual physical location
 * 5. WIFI_PREFIX: Choose a prefix for WiFi network names
 * 
 * Example for a computer science classroom:
 * - DJANGO_SERVER = "192.168.1.100"
 * - DEVICE_ID = "ESP32_CS101_001"
 * - DEVICE_NAME = "CS101_Computer_Science"
 * - LOCATION = "Computer Science Building, Room 101"
 * - WIFI_PREFIX = "CS101_Attendance_"
 * 
 * This will create a WiFi network named: "CS101_Attendance_ESP32_CS101_001"
 */

#endif // ESP32_CONFIG_H
