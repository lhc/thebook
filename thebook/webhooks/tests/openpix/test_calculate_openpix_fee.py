from decimal import Decimal

import pytest

from thebook.webhooks.openpix.services import calculate_openpix_fee


@pytest.mark.parametrize(
    "openpix_plan,transaction_type,amount,expected_fee",
    [
        ("PERCENTUAL", "OPENPIX:TRANSACTION_RECEIVED", 20, -0.5),
        ("PERCENTUAL", "PAYMENT", 62.5, -0.5),
        ("PERCENTUAL", "PAYMENT", 64, -0.51),
        ("PERCENTUAL", "PAYMENT", 100, -0.8),
        ("PERCENTUAL", "PAYMENT", 625, -5),
        ("PERCENTUAL", "PAYMENT", 630, -5),
        ("FIXO", "OPENPIX:TRANSACTION_RECEIVED", 20, -0.85),
        ("FIXO", "PAYMENT", 62.50, -0.85),
        ("FIXO", "PAYMENT", 64, -0.85),
        ("FIXO", "PAYMENT", 100, -0.85),
        ("FIXO", "PAYMENT", 625, -0.85),
        ("FIXO", "PAYMENT", 630, -0.85),
        ("PERCENTUAL", "WITHDRAW", 630, -1),
        ("FIXO", "WITHDRAW", 630, -1),
        ("FIXO", "REFUND", 630, 0.0),
        ("PERCENTUAL", "REFUND", 630, 0.0),
    ],
)
def test_calculate_openpix_fee_based_on_selected_plan(
    settings, openpix_plan, transaction_type, amount, expected_fee
):
    settings.OPENPIX_PLAN = openpix_plan
    assert calculate_openpix_fee(amount, transaction_type) == round(
        Decimal(expected_fee), 2
    )
