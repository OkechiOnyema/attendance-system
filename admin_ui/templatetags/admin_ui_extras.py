from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get item from dictionary by key
    Usage: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key)

@register.filter
def add(value, arg):
    """
    Template filter to add two numbers
    Usage: {{ value|add:arg }}
    """
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value
