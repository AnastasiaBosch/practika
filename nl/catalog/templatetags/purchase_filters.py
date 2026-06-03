from django import template

register = template.Library()

@register.filter
def status_count(queryset, status_code):
    """Подсчет количества записей с определенным статусом"""
    return queryset.filter(status=status_code).count()