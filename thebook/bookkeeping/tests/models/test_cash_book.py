import datetime
from decimal import Decimal

import pytest
from model_bakery import baker

from django.utils.text import slugify

from thebook.bookkeeping.models import CashBook, Transaction


@pytest.fixture
def cash_book():
    return CashBook.objects.create(name="Test Cash Book")


@pytest.fixture
def cash_book_with_transactions(cash_book):
    # fmt: off
    baker.make(Transaction, cash_book=cash_book, date=datetime.date(2020, 1, 1), amount=Decimal("15.5"))
    baker.make(Transaction, cash_book=cash_book, date=datetime.date(2020, 1, 1), amount=Decimal("-16.5"))
    baker.make(Transaction, cash_book=cash_book, date=datetime.date(2020, 2, 1), amount=Decimal("300.26"))
    baker.make(Transaction, cash_book=cash_book, date=datetime.date(2024, 11, 1), amount=Decimal("25.5"))
    baker.make(Transaction, cash_book=cash_book, date=datetime.date(2024, 12, 1), amount=Decimal("-26.73"))
    baker.make(Transaction, cash_book=cash_book, date=datetime.date(2024, 12, 1), amount=Decimal("-100.37"))
    # fmt: on
    return cash_book


@pytest.mark.parametrize("cash_book_name", ["Paypal Account", "Bank", "Cash Account"])
def test_set_cash_book_slug_based_in_name_if_not_provided(db, cash_book_name):
    cash_book = CashBook(name=cash_book_name)

    cash_book.save()

    assert cash_book.slug == slugify(cash_book_name)


def test_cash_book_summary(db, cash_book):
    assert cash_book.summary() == {
        "id": cash_book.id,
        "name": cash_book.name,
        "slug": cash_book.slug,
        "withdraws": Decimal("0"),
        "deposits": Decimal("0"),
        "balance": Decimal("0"),
        "year": None,
        "month": None,
    }


@pytest.mark.parametrize("year", [2020, 2024])
def test_cash_book_summary_for_year(db, cash_book, year):
    assert cash_book.summary(year=year) == {
        "id": cash_book.id,
        "name": cash_book.name,
        "slug": cash_book.slug,
        "withdraws": Decimal("0"),
        "deposits": Decimal("0"),
        "balance": Decimal("0"),
        "year": year,
        "month": None,
    }


@pytest.mark.parametrize("year,month", [(2020, 1), (2024, 12)])
def test_cash_book_summary_for_year_and_month(db, cash_book, year, month):
    assert cash_book.summary(month=month, year=year) == {
        "id": cash_book.id,
        "name": cash_book.name,
        "slug": cash_book.slug,
        "withdraws": Decimal("0"),
        "deposits": Decimal("0"),
        "balance": Decimal("0"),
        "year": year,
        "month": month,
    }


@pytest.mark.parametrize("month", [0, -1, 13, 9999])
def test_cash_book_summary_for_invalid_month(db, cash_book, month):
    with pytest.raises(ValueError):
        cash_book_summary = cash_book.summary(month=month, year=2024)


@pytest.mark.parametrize("month", [1, 5, 11])
def test_cash_book_summary_value_error_if_valid_month_provided_without_year(
    db, cash_book, month
):
    with pytest.raises(ValueError):
        cash_book_summary = cash_book.summary(month=month)


def test_cash_book_summary_with_transactions(db, cash_book_with_transactions):
    cash_book_summary = cash_book_with_transactions.summary()

    assert cash_book_summary == {
        "id": cash_book_with_transactions.id,
        "name": cash_book_with_transactions.name,
        "slug": cash_book_with_transactions.slug,
        "deposits": Decimal("341.26"),
        "withdraws": Decimal("-143.60"),
        "balance": Decimal("197.66"),
        "month": None,
        "year": None,
    }


@pytest.mark.parametrize(
    "year,deposits,withdraws,balance",
    [
        (2020, Decimal("315.76"), Decimal("-16.5"), Decimal("299.26")),
        (2022, Decimal("0"), Decimal("0"), Decimal("0")),
        (2024, Decimal("25.5"), Decimal("-127.1"), Decimal("-101.6")),
    ],
)
def test_cash_book_summary_with_transactions_filter_by_year(
    db, cash_book_with_transactions, year, deposits, withdraws, balance
):
    cash_book_summary = cash_book_with_transactions.summary(year=year)

    assert cash_book_summary == {
        "id": cash_book_with_transactions.id,
        "name": cash_book_with_transactions.name,
        "slug": cash_book_with_transactions.slug,
        "deposits": deposits,
        "withdraws": withdraws,
        "balance": balance,
        "month": None,
        "year": year,
    }


@pytest.mark.parametrize(
    "year,month,deposits,withdraws,balance",
    [
        (2020, 1, Decimal("15.5"), Decimal("-16.5"), Decimal("-1")),
        (2020, 2, Decimal("300.26"), Decimal("0"), Decimal("300.26")),
        (2020, 10, Decimal("0"), Decimal("0"), Decimal("0")),
        (2024, 12, Decimal("0"), Decimal("-127.1"), Decimal("-127.1")),
    ],
)
def test_cash_book_summary_with_transactions_filter_by_year_and_month(
    db, cash_book_with_transactions, year, month, deposits, withdraws, balance
):
    cash_book_summary = cash_book_with_transactions.summary(year=year, month=month)

    assert cash_book_summary == {
        "id": cash_book_with_transactions.id,
        "name": cash_book_with_transactions.name,
        "slug": cash_book_with_transactions.slug,
        "deposits": deposits,
        "withdraws": withdraws,
        "balance": balance,
        "month": month,
        "year": year,
    }
