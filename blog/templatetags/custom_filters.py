from django import template

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
