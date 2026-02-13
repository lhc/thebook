from decimal import Decimal

import pytest
from model_bakery import baker

from thebook.bookkeeping.models import Category, CategoryMatchRule, Transaction


@pytest.fixture
def accountant():
    return Category.objects.create(name="Contabilidade")


@pytest.fixture
def bank_fees():
    return Category.objects.create(name="Tarifas Bancárias")


@pytest.fixture
def donation():
    return Category.objects.create(name="Doação")


@pytest.fixture
def recurring():
    return Category.objects.create(name="Recorrente")


@pytest.fixture
def expected_category(request, accountant, bank_fees, donation, recurring):
    return {
        "accountant": accountant,
        "bank_fees": bank_fees,
        "donation": donation,
        "recurring": recurring,
    }.get(request.param)


@pytest.mark.parametrize(
    "transaction_amount,donation_threshold,expected_category",
    [
        (Decimal("50.0"), Decimal("50.0"), "donation"),
        (Decimal("50.0"), Decimal("40.0"), None),
        (Decimal("49.99"), Decimal("50.0"), "donation"),
        (Decimal("5"), Decimal("50.0"), "donation"),
        (Decimal("50.01"), Decimal("50.0"), None),
        (Decimal("100"), Decimal("50.0"), None),
        (Decimal("-0.01"), Decimal("50.0"), None),
        (Decimal("-50.0"), Decimal("50.0"), None),
    ],
    indirect=["expected_category"],
)
def test_transactions_below_certain_positive_value_set_as_donation(
    db,
    settings,
    transaction_amount,
    donation_threshold,
    expected_category,
):
    settings.DONATION_THRESHOLD = donation_threshold

    transaction = baker.make(Transaction, amount=transaction_amount)

    transaction.categorize()

    transaction.refresh_from_db()
    assert transaction.category == expected_category


def test_transactions_description_rules_over_donation_threshold(
    db, mocker, settings, accountant
):
    CategoryMatchRule.objects.create(
        pattern="NOT DONATION",
        category=accountant,
    ),

    settings.DONATION_THRESHOLD = Decimal("50")

    transaction = baker.make(
        Transaction,
        description="NOT DONATION",
        amount=Decimal("49.99"),
    )

    transaction.categorize()

    transaction.refresh_from_db()
    assert transaction.category == accountant


def test_consider_match_rule_priority_when_categorizing(
    db, mocker, settings, accountant, bank_fees
):
    CategoryMatchRule.objects.create(
        pattern="PAYMENT",
        category=accountant,
    )
    CategoryMatchRule.objects.create(
        pattern="PAYMENT",
        category=bank_fees,
    )

    transaction = baker.make(
        Transaction,
        description="PAYMENT",
        amount=Decimal("49.99"),
    )

    transaction.categorize()

    transaction.refresh_from_db()
    assert transaction.category == bank_fees
