from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножает значение на аргумент."""
    return value * arg

@register.filter
def divide(value, arg):
    """Делит значение на аргумент."""
    try:
        return value / arg
    except (ValueError, ZeroDivisionError):
        return None