from django import template

register = template.Library()

@register.filter
def add_class(field, class_name):
    """
    Adds a CSS class to a form field.
    """
    return field.as_widget(attrs={'class': class_name})
