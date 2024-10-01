import pytest

from decimal import Decimal

from django.template import Context, Template, TemplateSyntaxError


@pytest.mark.parametrize(
    "value,expected",
    [
        (Decimal("0"), "R$ 0.00"),
        (Decimal("1"), "R$ 1.00"),
        (Decimal("12.5"), "R$ 12.50"),
        (Decimal("142.56"), "R$ 142.56"),
        (Decimal("12.500001"), "R$ 12.50"),
        (Decimal("1202.500001"), "R$ 1202.50"),
        (Decimal("-1"), "(R$ 1.00)"),
        (Decimal("-12.5"), "(R$ 12.50)"),
        (Decimal("-142.56"), "(R$ 142.56)"),
        (Decimal("-12.500001"), "(R$ 12.50)"),
        (Decimal("-1202.500001"), "(R$ 1202.50)"),
        (15.98, "R$ 15.98"),
        (-15.98, "(R$ 15.98)"),
        (None, "-"),
        ("", "-"),
        ("    ", "-"),
    ],
)
def test_format_values_as_money(value, expected):
    output = Template("""{% load currency %}{{ value|money }}""").render(
        Context({"value": value})
    )
    assert output == expected
