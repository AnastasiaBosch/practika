from django import template

register = template.Library()

@register.filter
def get_list(value, arg):
    """Получить список значений GET-параметра"""
    return value.getlist(arg)

@register.filter
def status_count(queryset, status_code):
    """Подсчет количества записей с определенным статусом"""
    return queryset.filter(status=status_code).count()

@register.filter
def sum_delivery(queryset):
    """Сумма стоимости доставки"""
    return sum(p.delivery_cost for p in queryset)

@register.filter
def total_with_delivery(queryset, total_spent):
    """Общая сумма с учетом доставки"""
    delivery_sum = sum(p.delivery_cost for p in queryset)
    return total_spent + delivery_sum