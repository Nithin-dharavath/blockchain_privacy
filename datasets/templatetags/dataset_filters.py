from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Template filter to look up dictionary values by key
    Usage: {{ dict|lookup:key }}
    """
    if dictionary is None:
        return ''
    
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    
    # Handle list of dicts (like DataFrame rows)
    try:
        return dictionary.get(key, '')
    except (AttributeError, KeyError):
        return ''

@register.filter
def get_item(dictionary, key):
    """
    Alternative filter for dictionary lookup
    Usage: {{ dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
