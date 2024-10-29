import numbers

from django import template

register = template.Library()


@register.filter
def money(value):
    if not isinstance(value, numbers.Number):
        return "-"

    integer_value = str(abs(int(value)))
    integer_part = ".".join(
        [integer_value[::-1][i : i + 3][::-1] for i in range(0, len(integer_value), 3)][
            ::-1
        ]
    )
    decimal_part = int((abs(value) % 1) * 100)

    return (
        f"(R$ {integer_part},{decimal_part:02})"
        if value < 0
        else f"R$ {integer_part},{decimal_part:02}"
    )
