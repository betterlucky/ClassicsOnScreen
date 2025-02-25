from django import template
from datetime import datetime, timedelta
from django.conf import settings
from django.template.defaultfilters import stringfilter

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

@register.filter
def htmx_attrs(field, attrs_dict):
    """
    Adds HTMX attributes to a form field.
    Usage: {{ form.field|htmx_attrs:{'hx-post': '/validate/', 'hx-trigger': 'change'} }}
    """
    if isinstance(attrs_dict, str):
        import json
        attrs_dict = json.loads(attrs_dict)
    
    existing_attrs = field.field.widget.attrs
    existing_attrs.update(attrs_dict)
    return field.as_widget(attrs=existing_attrs)

@register.filter
@stringfilter
def replace_settings(value):
    """
    Replaces settings placeholders in text with their actual values.
    Usage: {{ text|replace_settings }}
    """
    return value.replace('{{MAX_FILM_VOTES}}', str(settings.MAX_FILM_VOTES))
