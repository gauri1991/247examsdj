from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Replace occurrences of a string in a value.
    Usage: {{ value|replace:"old,new" }}
    """
    if not arg:
        return value
    
    if ',' in arg:
        old, new = arg.split(',', 1)
        return str(value).replace(old, new)
    return value

@register.filter  
def underscore_to_space(value):
    """
    Replace underscores with spaces and title case.
    Usage: {{ value|underscore_to_space }}
    """
    return str(value).replace('_', ' ').title()