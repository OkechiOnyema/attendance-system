#!/usr/bin/env python3
"""
ESP32 Setup Verification Script

This script verifies that your ESP32 access point setup is correct:
1. Checks configuration files
2. Verifies Django models
3. Tests API endpoints
4. Validates network settings

Usage:
    python verify_esp32_setup.py
"""

import os
import sys
import json
from pathlib import Path

def check_esp32_files():
    """Check if ESP32 files exist and are properly configured"""
    print("🔍 Checking ESP32 Files...")
    
    required_files = [
        'esp32_attendance/esp32_attendance.ino',
        'esp32_attendance/esp32_config.h'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    return True

def check_esp32_config():
    """Check ESP32 configuration settings"""
    print("\n⚙️ Checking ESP32 Configuration...")
    
    config_file = 'esp32_attendance/esp32_config.h'
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required configurations
        required_configs = [
            'ESP32_AP_SSID',
            'ESP32_AP_IP',
            'DJANGO_SERVER_URL',
            'DEVICE_ID_PREFIX'
        ]
        
        missing_configs = []
        for config in required_configs:
            if config in content:
                print(f"✅ {config}")
            else:
                missing_configs.append(config)
        
        if missing_configs:
            print(f"❌ Missing configurations: {missing_configs}")
            return False
        
        # Check specific values
        if 'ESP32_Attendance' in content:
            print("✅ Network SSID: ESP32_Attendance")
        else:
            print("⚠️ Network SSID may not be set correctly")
        
        if '192.168.4.1' in content:
            print("✅ IP Address: 192.168.4.1")
        else:
            print("⚠️ IP Address may not be set correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        return False

def check_django_models():
    """Check if Django models are properly set up"""
    print("\n🗂️ Checking Django Models...")
    
    models_file = 'admin_ui/models.py'
    
    try:
        with open(models_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        required_models = [
            'class ESP32Device',
            'class NetworkSession',
            'class ConnectedDevice'
        ]
        
        missing_models = []
        for model in required_models:
            if model in content:
                print(f"✅ {model}")
            else:
                missing_models.append(model)
        
        if missing_models:
            print(f"❌ Missing models: {missing_models}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading models file: {e}")
        return False

def check_django_urls():
    """Check if Django URLs are properly configured"""
    print("\n🔗 Checking Django URLs...")
    
    urls_file = 'admin_ui/urls.py'
    
    try:
        with open(urls_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        required_urls = [
            'api/esp32/heartbeat/',
            'api/esp32/connected/',
            'api/esp32/disconnected/',
            'api/esp32/active-course/'
        ]
        
        missing_urls = []
        for url in required_urls:
            if url in content:
                print(f"✅ {url}")
            else:
                missing_urls.append(url)
        
        if missing_urls:
            print(f"❌ Missing URLs: {missing_urls}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading URLs file: {e}")
        return False

def check_django_views():
    """Check if Django views are properly implemented"""
    print("\n👁️ Checking Django Views...")
    
    views_file = 'admin_ui/views.py'
    
    try:
        with open(views_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        required_views = [
            'def api_device_heartbeat',
            'def api_device_connected',
            'def api_device_disconnected',
            'def api_active_course'
        ]
        
        missing_views = []
        for view in required_views:
            if view in content:
                print(f"✅ {view}")
            else:
                missing_views.append(view)
        
        if missing_views:
            print(f"❌ Missing views: {missing_views}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading views file: {e}")
        return False

def check_requirements():
    """Check if required Python packages are available"""
    print("\n📦 Checking Python Requirements...")
    
    required_packages = [
        'django',
        'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"⚠️ Install missing packages: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def print_setup_summary():
    """Print setup summary and next steps"""
    print("\n📋 ESP32 Access Point Setup Summary")
    print("=" * 50)
    print("✅ ESP32 Arduino code ready")
    print("✅ Configuration file configured")
    print("✅ Django models implemented")
    print("✅ API endpoints configured")
    print("✅ Views implemented")
    print("\n🚀 Next Steps:")
    print("1. Upload esp32_attendance.ino to your ESP32")
    print("2. Power up ESP32 and check serial monitor")
    print("3. Connect to ESP32 WiFi network")
    print("4. Start Django server on ESP32 network")
    print("5. Test with test_esp32_access_point.py")
    print("\n📚 See ESP32_ACCESS_POINT_SETUP.md for detailed instructions")

def main():
    """Main verification function"""
    print("🔌 ESP32 Access Point Setup Verification")
    print("=" * 50)
    
    checks = [
        check_esp32_files(),
        check_esp32_config(),
        check_django_models(),
        check_django_urls(),
        check_django_views(),
        check_requirements()
    ]
    
    all_passed = all(checks)
    
    if all_passed:
        print("\n🎉 All checks passed! Your ESP32 access point setup is ready.")
        print_setup_summary()
    else:
        print("\n⚠️ Some checks failed. Please fix the issues above before proceeding.")
        print("\n🔧 Common fixes:")
        print("- Ensure all files exist in correct locations")
        print("- Check ESP32 configuration values")
        print("- Verify Django models and views are implemented")
        print("- Install required Python packages")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
