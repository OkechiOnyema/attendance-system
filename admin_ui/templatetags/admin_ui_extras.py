from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter to get item from dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def format_timestamp(timestamp):
    """Format timestamp for display"""
    if timestamp:
        try:
            from datetime import datetime
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return str(timestamp)
    return "Unknown"

@register.filter
def device_status_class(device):
    """Get CSS class for device status"""
    if device.is_active:
        return "status-active"
    return "status-inactive"

@register.filter
def presence_status_text(presence_data):
    """Get text for presence status"""
    if presence_data and presence_data.get('device_count', 0) > 0:
        return "Live"
    return "No Data"
