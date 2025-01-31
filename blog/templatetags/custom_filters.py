from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def add_class(field, class_name):
    """
    Adds a CSS class to a form field.
    """
    return field.as_widget(attrs={'class': class_name})

@register.filter
def get_selected_object(field):
    if hasattr(field, 'field') and hasattr(field.field, 'choices'):
        for value, label in field.field.choices:
            if str(value) == str(field.value()):
                return label
    return None

@register.filter
def subtract(value, arg):
    """
    Subtracts the arg from the value.
    Usage: {{ show.location.max_capacity|subtract:show.credits }}
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divides the value by the argument."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def timeuntil_weeks(value, weeks):
    """Returns a date that's a certain number of weeks before the given date"""
    target_date = value - timedelta(weeks=int(weeks))
    return target_date.strftime("%B %d, %Y")
