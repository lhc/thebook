from decimal import Decimal

import pytest
from model_bakery import baker

from thebook.bookkeeping.models import Category, Transaction


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
def uncategorized():
    return Category.objects.create(name="Uncategorized")


@pytest.fixture
def expected_category(
    request, accountant, bank_fees, donation, recurring, uncategorized
):
    return {
        "accountant": accountant,
        "bank_fees": bank_fees,
        "donation": donation,
        "recurring": recurring,
        "uncategorized": uncategorized,
    }.get(request.param)


@pytest.fixture
def category_description_rules(accountant, bank_fees, recurring):
    return {
        "TARIFA BANCARIA": bank_fees,
        "CONTA DE TELEFONE": recurring,
        "CONTADOR": accountant,
    }


@pytest.mark.parametrize(
    "transaction_amount,donation_threshold,expected_category",
    [
        (Decimal("50.0"), Decimal("50.0"), "donation"),
        (Decimal("50.0"), Decimal("40.0"), "uncategorized"),
        (Decimal("49.99"), Decimal("50.0"), "donation"),
        (Decimal("5"), Decimal("50.0"), "donation"),
        (Decimal("50.01"), Decimal("50.0"), "uncategorized"),
        (Decimal("100"), Decimal("50.0"), "uncategorized"),
        (Decimal("-0.01"), Decimal("50.0"), "uncategorized"),
        (Decimal("-50.0"), Decimal("50.0"), "uncategorized"),
    ],
    indirect=["expected_category"],
)
def test_transactions_below_certain_positive_value_set_as_donation(
    db,
    settings,
    uncategorized,
    transaction_amount,
    donation_threshold,
    expected_category,
):
    settings.DONATION_THRESHOLD = donation_threshold

    transaction = baker.make(
        Transaction, category=uncategorized, amount=transaction_amount
    )

    transaction.categorize()

    transaction.refresh_from_db()
    assert transaction.category == expected_category


def test_transactions_description_rules_over_donation_threshold(
    db, mocker, settings, uncategorized, accountant
):
    test_rules = {
        "NOT DONATION": accountant,
    }
    mocker.patch(
        "thebook.bookkeeping.models.get_categorize_rules", return_value=test_rules
    )
    settings.DONATION_THRESHOLD = Decimal("50")

    transaction = baker.make(
        Transaction,
        description="NOT DONATION",
        category=uncategorized,
        amount=Decimal("49.99"),
    )

    transaction.categorize()

    transaction.refresh_from_db()
    assert transaction.category == accountant
