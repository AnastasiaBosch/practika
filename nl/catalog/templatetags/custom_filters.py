from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножает value на arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def filter_attr(items, attr_string):
    """Фильтр по атрибуту вида 'status=assembled'"""
    if not items:
        return []
    
    attr_name, value = attr_string.split('=')
    return [item for item in items if getattr(item, attr_name) == value]