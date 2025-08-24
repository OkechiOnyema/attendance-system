#!/usr/bin/env python3
"""
Script to replace the ESP32 function in views.py
"""

def replace_function():
    """Replace the ESP32 function in views.py"""
    
    # Read the fixed function
    with open('fixed_esp32_function.py', 'r') as f:
        fixed_function = f.read()
    
    # Read the views.py file
    with open('admin_ui/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start and end of the function
    start_marker = "@csrf_exempt\ndef esp32_student_verification_api(request):"
    end_marker = "    return JsonResponse({\n        'success': False,\n        'message': 'Method not allowed'\n    }, status=405)"
    
    # Find the start position
    start_pos = content.find(start_marker)
    if start_pos == -1:
        print("❌ Could not find function start")
        return
    
    # Find the end position (after the function)
    end_pos = content.find(end_marker, start_pos)
    if end_pos == -1:
        print("❌ Could not find function end")
        return
    
    # Include the end marker in the replacement
    end_pos = end_pos + len(end_marker)
    
    # Create new content
    before_function = content[:start_pos]
    after_function = content[end_pos:]
    
    # Remove the @csrf_exempt and def line from fixed function since we already have it
    fixed_function_lines = fixed_function.split('\n')
    # Skip the first 3 lines (comment, @csrf_exempt, def line)
    fixed_function_content = '\n'.join(fixed_function_lines[3:])
    
    new_content = before_function + start_marker + "\n" + fixed_function_content + after_function
    
    # Write back to file
    with open('admin_ui/views.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Function replaced successfully!")

if __name__ == "__main__":
    replace_function()
