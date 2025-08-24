#!/usr/bin/env python3
"""
Quick fix for ESP32 JSON serialization issue in views.py
"""

import re

def fix_esp32_json_issue():
    """Fix the ESP32 device JSON serialization issue in views.py"""
    
    # Read the views.py file
    with open('admin_ui/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the problematic line
    old_pattern = r"'esp32_device': record\.esp32_device\.device_name if record\.esp32_device else '-'"
    new_pattern = "'esp32_device': record.esp32_device.device_name if record.esp32_device else '-'"
    
    # Also add esp32_device to select_related
    old_select = r"select_related\('student', 'attendance_session', 'marked_by'\)"
    new_select = "select_related('student', 'attendance_session', 'marked_by', 'esp32_device')"
    
    # Apply fixes
    content = re.sub(old_pattern, new_pattern, content)
    content = re.sub(old_select, new_select, content)
    
    # Write back to file
    with open('admin_ui/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed ESP32 JSON serialization issue in views.py")
    print("✅ Added esp32_device to select_related")

if __name__ == "__main__":
    fix_esp32_json_issue()
