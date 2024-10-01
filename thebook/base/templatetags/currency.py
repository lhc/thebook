import numbers

from django import template

register = template.Library()


@register.filter
def money(value):
    if isinstance(value, numbers.Number):
        return f"(R$ {-1 * value:.2f})" if value < 0 else f"R$ {value:.2f}"
    return "-"
