import datetime
from decimal import Decimal

import pytest
from model_bakery import baker

from django.utils.text import slugify

from thebook.bookkeeping.models import BankAccount, Transaction


@pytest.fixture
def bank_account():
    return BankAccount.objects.create(name="Test Bank Account")


@pytest.fixture
def bank_account_with_transactions(bank_account):
    # fmt: off
    baker.make(Transaction, bank_account=bank_account, date=datetime.date(2020, 1, 1), amount=Decimal("15.5"))
    baker.make(Transaction, bank_account=bank_account, date=datetime.date(2020, 1, 1), amount=Decimal("-16.5"))
    baker.make(Transaction, bank_account=bank_account, date=datetime.date(2020, 2, 1), amount=Decimal("300.26"))
    baker.make(Transaction, bank_account=bank_account, date=datetime.date(2024, 11, 1), amount=Decimal("25.5"))
    baker.make(Transaction, bank_account=bank_account, date=datetime.date(2024, 12, 1), amount=Decimal("-26.73"))
    baker.make(Transaction, bank_account=bank_account, date=datetime.date(2024, 12, 1), amount=Decimal("-100.37"))
    # fmt: on
    return bank_account


@pytest.mark.parametrize(
    "bank_account_name", ["Paypal Account", "Bank", "Cash Account"]
)
def test_set_bank_account_slug_based_in_name_if_not_provided(db, bank_account_name):
    bank_account = BankAccount(name=bank_account_name)

    bank_account.save()

    assert bank_account.slug == slugify(bank_account_name)


def test_bank_account_summary(db, bank_account):
    bank_account_with_summary = bank_account.with_summary()

    assert bank_account_with_summary.name == bank_account.name
    assert bank_account_with_summary.slug == bank_account.slug
    assert bank_account_with_summary.description == bank_account.description
    assert bank_account_with_summary.active == bank_account.active

    assert bank_account_with_summary.withdraws == Decimal("0")
    assert bank_account_with_summary.deposits == Decimal("0")
    assert bank_account_with_summary.balance == Decimal("0")
    assert bank_account_with_summary.overall_balance == Decimal("0")
    assert bank_account_with_summary.year is None
    assert bank_account_with_summary.month is None


@pytest.mark.parametrize("year", [2020, 2024])
def test_bank_account_summary_for_year(db, bank_account, year):
    bank_account_with_summary = bank_account.with_summary(year=year)

    assert bank_account_with_summary.name == bank_account.name
    assert bank_account_with_summary.slug == bank_account.slug
    assert bank_account_with_summary.description == bank_account.description
    assert bank_account_with_summary.active == bank_account.active

    assert bank_account_with_summary.withdraws == Decimal("0")
    assert bank_account_with_summary.deposits == Decimal("0")
    assert bank_account_with_summary.balance == Decimal("0")
    assert bank_account_with_summary.overall_balance == Decimal("0")
    assert bank_account_with_summary.year == year
    assert bank_account_with_summary.month is None


@pytest.mark.parametrize("year,month", [(2020, 1), (2024, 12)])
def test_bank_account_summary_for_year_and_month(db, bank_account, year, month):
    bank_account_with_summary = bank_account.with_summary(year=year, month=month)

    assert bank_account_with_summary.name == bank_account.name
    assert bank_account_with_summary.slug == bank_account.slug
    assert bank_account_with_summary.description == bank_account.description
    assert bank_account_with_summary.active == bank_account.active

    assert bank_account_with_summary.withdraws == Decimal("0")
    assert bank_account_with_summary.deposits == Decimal("0")
    assert bank_account_with_summary.balance == Decimal("0")
    assert bank_account_with_summary.overall_balance == Decimal("0")
    assert bank_account_with_summary.year == year
    assert bank_account_with_summary.month == month


@pytest.mark.parametrize("month", [0, -1, 13, 9999])
def test_bank_account_summary_for_invalid_month(db, bank_account, month):
    with pytest.raises(ValueError):
        bank_account_summary = bank_account.with_summary(month=month, year=2024)


@pytest.mark.parametrize("month", [1, 5, 11])
def test_bank_account_summary_value_error_if_valid_month_provided_without_year(
    db, bank_account, month
):
    with pytest.raises(ValueError):
        bank_account_summary = bank_account.with_summary(month=month)


def test_bank_account_summary_with_transactions(db, bank_account_with_transactions):
    bank_account_with_summary = bank_account_with_transactions.with_summary()

    assert bank_account_with_summary.name == bank_account_with_transactions.name
    assert bank_account_with_summary.slug == bank_account_with_transactions.slug
    assert (
        bank_account_with_summary.description
        == bank_account_with_transactions.description
    )
    assert bank_account_with_summary.active == bank_account_with_transactions.active

    assert bank_account_with_summary.withdraws == Decimal("-143.60")
    assert bank_account_with_summary.deposits == Decimal("341.26")
    assert bank_account_with_summary.balance == Decimal("197.66")
    assert bank_account_with_summary.overall_balance == Decimal("197.66")
    assert bank_account_with_summary.year is None
    assert bank_account_with_summary.month is None


@pytest.mark.parametrize(
    "year,deposits,withdraws,balance",
    [
        (2020, Decimal("315.76"), Decimal("-16.5"), Decimal("299.26")),
        (2022, Decimal("0"), Decimal("0"), Decimal("0")),
        (2024, Decimal("25.5"), Decimal("-127.1"), Decimal("-101.6")),
    ],
)
def test_bank_account_summary_with_transactions_filter_by_year(
    db, bank_account_with_transactions, year, deposits, withdraws, balance
):
    bank_account_with_summary = bank_account_with_transactions.with_summary(year=year)

    assert bank_account_with_summary.name == bank_account_with_transactions.name
    assert bank_account_with_summary.slug == bank_account_with_transactions.slug
    assert (
        bank_account_with_summary.description
        == bank_account_with_transactions.description
    )
    assert bank_account_with_summary.active == bank_account_with_transactions.active

    assert bank_account_with_summary.withdraws == withdraws
    assert bank_account_with_summary.deposits == deposits
    assert bank_account_with_summary.balance == balance
    assert bank_account_with_summary.overall_balance == Decimal("197.66")
    assert bank_account_with_summary.year == year
    assert bank_account_with_summary.month is None


@pytest.mark.parametrize(
    "year,month,deposits,withdraws,balance",
    [
        (2020, 1, Decimal("15.5"), Decimal("-16.5"), Decimal("-1")),
        (2020, 2, Decimal("300.26"), Decimal("0"), Decimal("300.26")),
        (2020, 10, Decimal("0"), Decimal("0"), Decimal("0")),
        (2024, 12, Decimal("0"), Decimal("-127.1"), Decimal("-127.1")),
    ],
)
def test_bank_account_summary_with_transactions_filter_by_year_and_month(
    db, bank_account_with_transactions, year, month, deposits, withdraws, balance
):
    bank_account_with_summary = bank_account_with_transactions.with_summary(
        year=year, month=month
    )

    assert bank_account_with_summary.name == bank_account_with_transactions.name
    assert bank_account_with_summary.slug == bank_account_with_transactions.slug
    assert (
        bank_account_with_summary.description
        == bank_account_with_transactions.description
    )
    assert bank_account_with_summary.active == bank_account_with_transactions.active

    assert bank_account_with_summary.withdraws == withdraws
    assert bank_account_with_summary.deposits == deposits
    assert bank_account_with_summary.balance == balance
    assert bank_account_with_summary.overall_balance == Decimal("197.66")
    assert bank_account_with_summary.year == year
    assert bank_account_with_summary.month == month


def test_bank_account_default_fetch_order_by_name(db):
    bank_account_1 = BankAccount.objects.create(name="Bank Account C")
    bank_account_2 = BankAccount.objects.create(name="Bank Account A")
    bank_account_3 = BankAccount.objects.create(name="Bank Account B")

    bank_accounts = BankAccount.objects.all()

    assert bank_accounts[0].name == bank_account_2.name
    assert bank_accounts[1].name == bank_account_3.name
    assert bank_accounts[2].name == bank_account_1.name
