# BankAccount.objects.summary(year=year, month=month)  # all history of year/month
# raise valueerror if month alone / month out of range


import datetime
from decimal import Decimal

import pytest
from model_bakery import baker

from django.utils.text import slugify

from thebook.bookkeeping.models import BankAccount, Transaction


@pytest.fixture
def transactions(cash_book_1, cash_book_2):
    # fmt: off
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2020, 11, 1), amount=Decimal("15.5"))
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2020, 11, 1), amount=Decimal("-16.5"))
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2020, 2, 1), amount=Decimal("300.26"))
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2022, 2, 1), amount=Decimal("42.87"))
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2024, 11, 1), amount=Decimal("25.5"))
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2024, 12, 1), amount=Decimal("-26.73"))
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2024, 12, 1), amount=Decimal("-100.37"))

    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2020, 1, 1), amount=Decimal("289.04"))
    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2020, 1, 1), amount=Decimal("-285.57"))
    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2020, 2, 1), amount=Decimal("384.32"))
    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2022, 5, 1), amount=Decimal("226.67"))
    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2024, 11, 1), amount=Decimal("190.39"))
    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2024, 12, 1), amount=Decimal("-181.52"))
    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2024, 12, 1), amount=Decimal("-366.61"))
    # fmt: on

    return cash_book_1, cash_book_2


@pytest.fixture
def cash_book_1():
    return BankAccount.objects.create(name="Cash Book 1")


@pytest.fixture
def cash_book_2():
    return BankAccount.objects.create(name="Cash Book 2")


def test_cash_books_summary(db, cash_book_1, cash_book_2):
    cash_books = BankAccount.objects.summary()

    assert cash_books.count() == 2

    assert cash_books[0].id == cash_book_1.id
    assert cash_books[0].withdraws == Decimal("0")
    assert cash_books[0].deposits == Decimal("0")
    assert cash_books[0].balance == Decimal("0")
    assert cash_books[0].year is None
    assert cash_books[0].month is None

    assert cash_books[1].id == cash_book_2.id
    assert cash_books[1].withdraws == Decimal("0")
    assert cash_books[1].deposits == Decimal("0")
    assert cash_books[1].balance == Decimal("0")
    assert cash_books[1].year is None
    assert cash_books[1].month is None


def test_cash_books_summary_with_transactions(
    db, transactions, cash_book_1, cash_book_2
):
    cash_books = BankAccount.objects.summary()

    assert cash_books.count() == 2

    assert cash_books[0].id == cash_book_1.id
    assert cash_books[0].withdraws == Decimal("-143.6")
    assert cash_books[0].deposits == Decimal("384.13")
    assert cash_books[0].balance == Decimal("240.53")
    assert cash_books[0].year is None
    assert cash_books[0].month is None
    assert cash_books[0].overall_balance == Decimal("240.53")

    assert cash_books[1].id == cash_book_2.id
    assert cash_books[1].withdraws == Decimal("-833.7")
    assert cash_books[1].deposits == Decimal("1090.42")
    assert cash_books[1].balance == Decimal("256.72")
    assert cash_books[1].year is None
    assert cash_books[1].month is None
    assert cash_books[1].overall_balance == Decimal("256.72")


@pytest.mark.parametrize("year", [2020, 2024])
def test_cash_books_summary_for_year_no_transactions(
    db, cash_book_1, cash_book_2, year
):
    cash_books = BankAccount.objects.summary(year=year)

    assert cash_books.count() == 2

    assert cash_books[0].id == cash_book_1.id
    assert cash_books[0].year == year
    assert cash_books[0].month is None

    assert cash_books[1].id == cash_book_2.id
    assert cash_books[1].year == year
    assert cash_books[1].month is None


@pytest.mark.parametrize("year,month", [(2020, 1), (2024, 12)])
def test_cash_books_summary_for_year_and_month_no_transactions(
    db, cash_book_1, cash_book_2, year, month
):
    cash_books = BankAccount.objects.summary(year=year, month=month)

    assert cash_books.count() == 2

    assert cash_books[0].id == cash_book_1.id
    assert cash_books[0].year == year
    assert cash_books[0].month == month

    assert cash_books[1].id == cash_book_2.id
    assert cash_books[1].year == year
    assert cash_books[1].month == month


@pytest.mark.parametrize(
    [
        "year",
        "deposits_1",
        "withdraws_1",
        "balance_1",
        "deposits_2",
        "withdraws_2",
        "balance_2",
    ],
    [
        (
            2020,
            Decimal("315.76"),
            Decimal("-16.5"),
            Decimal("299.26"),
            Decimal("673.36"),
            Decimal("-285.57"),
            Decimal("387.79"),
        ),
        (
            2024,
            Decimal("25.5"),
            Decimal("-127.1"),
            Decimal("-101.6"),
            Decimal("190.39"),
            Decimal("-548.13"),
            Decimal("-357.74"),
        ),
    ],
)
def test_cash_books_summary_for_year_with_transactions(
    db,
    transactions,
    cash_book_1,
    cash_book_2,
    year,
    deposits_1,
    withdraws_1,
    balance_1,
    deposits_2,
    withdraws_2,
    balance_2,
):
    cash_books = BankAccount.objects.summary(year=year)

    assert cash_books.count() == 2

    assert cash_books[0].id == cash_book_1.id
    assert cash_books[0].deposits == deposits_1
    assert cash_books[0].withdraws == withdraws_1
    assert cash_books[0].balance == balance_1

    assert cash_books[1].id == cash_book_2.id
    assert cash_books[1].deposits == deposits_2
    assert cash_books[1].withdraws == withdraws_2
    assert cash_books[1].balance == balance_2


@pytest.mark.parametrize(
    [
        "year",
        "month",
        "deposits_1",
        "withdraws_1",
        "balance_1",
        "deposits_2",
        "withdraws_2",
        "balance_2",
    ],
    [
        (
            2020,
            11,
            Decimal("15.5"),
            Decimal("-16.5"),
            Decimal("-1"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        ),
        (
            2024,
            12,
            Decimal("0"),
            Decimal("-127.1"),
            Decimal("-127.1"),
            Decimal("0"),
            Decimal("-548.13"),
            Decimal("-548.13"),
        ),
        (
            2022,
            11,
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        ),
    ],
)
def test_cash_books_summary_for_year_and_month_with_transactions(
    db,
    transactions,
    cash_book_1,
    cash_book_2,
    year,
    month,
    deposits_1,
    withdraws_1,
    balance_1,
    deposits_2,
    withdraws_2,
    balance_2,
):
    cash_books = BankAccount.objects.summary(year=year, month=month)

    assert cash_books.count() == 2

    assert cash_books[0].id == cash_book_1.id
    assert cash_books[0].deposits == deposits_1
    assert cash_books[0].withdraws == withdraws_1
    assert cash_books[0].balance == balance_1

    assert cash_books[1].id == cash_book_2.id
    assert cash_books[1].deposits == deposits_2
    assert cash_books[1].withdraws == withdraws_2
    assert cash_books[1].balance == balance_2


def test_cash_books_summary_for_year_include_overall_balance(
    db, transactions, cash_book_1, cash_book_2
):
    cash_books = BankAccount.objects.summary(year=2020)

    assert cash_books.count() == 2

    assert cash_books[0].id == cash_book_1.id
    assert cash_books[0].year == 2020
    assert cash_books[0].month is None
    assert cash_books[0].overall_balance == Decimal("240.53")

    assert cash_books[1].id == cash_book_2.id
    assert cash_books[1].year == 2020
    assert cash_books[1].month is None
    assert cash_books[1].overall_balance == Decimal("256.72")


def test_cash_books_summary_for_year_and_month_include_overall_balance(
    db, transactions, cash_book_1, cash_book_2
):
    cash_books = BankAccount.objects.summary(year=2020, month=11)

    assert cash_books.count() == 2

    assert cash_books[0].id == cash_book_1.id
    assert cash_books[0].year == 2020
    assert cash_books[0].month == 11
    assert cash_books[0].overall_balance == Decimal("240.53")

    assert cash_books[1].id == cash_book_2.id
    assert cash_books[1].year == 2020
    assert cash_books[1].month == 11
    assert cash_books[1].overall_balance == Decimal("256.72")


@pytest.mark.parametrize("month", [0, -1, 13, 9999])
def test_cash_books_summary_for_invalid_month(db, month):
    with pytest.raises(ValueError):
        cash_books = BankAccount.objects.summary(year=2024, month=month)


@pytest.mark.parametrize("month", [1, 5, 11])
def test_cash_books_summary_value_error_if_valid_month_provided_without_year(db, month):
    with pytest.raises(ValueError):
        cash_book_summary = BankAccount.objects.summary(month=month)
