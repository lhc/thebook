from decimal import Decimal

import pytest

from thebook.webhooks.openpix.services import calculate_openpix_fee


@pytest.mark.parametrize(
    "openpix_plan,amount,expected_fee",
    [
        ("PERCENTUAL", 20, -0.5),
        ("PERCENTUAL", 62.5, -0.5),
        ("PERCENTUAL", 64, -0.51),
        ("PERCENTUAL", 100, -0.8),
        ("PERCENTUAL", 625, -5),
        ("PERCENTUAL", 630, -5),
        ("FIXO", 20, -0.85),
        ("FIXO", 62.50, -0.85),
        ("FIXO", 64, -0.85),
        ("FIXO", 100, -0.85),
        ("FIXO", 625, -0.85),
        ("FIXO", 630, -0.85),
    ],
)
def test_calculate_openpix_fee_based_on_selected_plan(
    settings, openpix_plan, amount, expected_fee
):
    settings.OPENPIX_PLAN = openpix_plan
    assert calculate_openpix_fee(amount) == round(Decimal(expected_fee), 2)
