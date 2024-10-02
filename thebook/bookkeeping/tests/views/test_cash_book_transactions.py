import datetime
from http import HTTPStatus

import pytest
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from thebook.bookkeeping.views import _get_cash_book_transactions_context
from thebook.bookkeeping.models import CashBook, Transaction


@pytest.fixture
def cash_book_1():
    return CashBook.objects.create(name="Cash Book 1")


@pytest.fixture
def cash_book_2():
    return CashBook.objects.create(name="Cash Book 2")


@pytest.fixture
def user():
    return baker.make(get_user_model())


def test_unauthenticated_access_to_cb_transactions_redirect_to_login_page(
    db, client, cash_book_1
):
    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions", args=(cash_book_1.slug,)
    )

    response = client.get(cash_book_transactions_url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{settings.LOGIN_URL}?next={cash_book_transactions_url}"


def test_allowed_access_to_cb_transactions_authenticated(db, client, user, cash_book_1):
    client.force_login(user)

    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions", args=(cash_book_1.slug,)
    )

    response = client.get(cash_book_transactions_url)

    assert response.status_code == HTTPStatus.OK


def test_not_found_with_invalid_cash_book_slug(db, client, user):
    client.force_login(user)

    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions", args=("i-do-not-exist",)
    )

    response = client.get(cash_book_transactions_url)

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_return_transactions_only_for_selected_cash_book(
    db, client, user, cash_book_1, cash_book_2
):
    client.force_login(user)

    transaction_1 = baker.make(Transaction, cash_book=cash_book_1)
    transaction_2 = baker.make(Transaction, cash_book=cash_book_2)
    transaction_3 = baker.make(Transaction, cash_book=cash_book_1)

    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions", args=(cash_book_1.slug,)
    )

    response = client.get(cash_book_transactions_url)

    assert transaction_1 in response.context["transactions"]
    assert transaction_2 not in response.context["transactions"]
    assert transaction_3 in response.context["transactions"]


def test_providing_year_retrieve_context_with_year(
    db, client, user, cash_book_1, mocker
):
    get_context_mock = mocker.patch(
        "thebook.bookkeeping.views._get_cash_book_transactions_context",
        return_value={
            "cash_book": cash_book_1,
            "transactions": [],
        },
    )
    client.force_login(user)

    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions",
        args=(cash_book_1.slug,),
    )
    response = client.get(cash_book_transactions_url, query_params={"year": "2024"})

    get_context_mock.assert_called_once_with(cash_book_1, year="2024", month=None)


def test_providing_year_and_month_retrieve_context_with_year_and_month(
    db, client, user, cash_book_1, mocker
):
    get_context_mock = mocker.patch(
        "thebook.bookkeeping.views._get_cash_book_transactions_context",
        return_value={
            "cash_book": cash_book_1,
            "transactions": [],
        },
    )
    client.force_login(user)

    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions",
        args=(cash_book_1.slug,),
    )
    response = client.get(
        cash_book_transactions_url, query_params={"year": "2024", "month": "11"}
    )

    get_context_mock.assert_called_once_with(cash_book_1, year="2024", month="11")


def test_cash_book_transactions_context(db, cash_book_1):
    transaction_1 = baker.make(Transaction, cash_book=cash_book_1)
    transaction_2 = baker.make(Transaction, cash_book=cash_book_1)

    context = _get_cash_book_transactions_context(cash_book_1)

    assert context["cash_book"] == cash_book_1
    assert len(context["transactions"]) == 2
    assert transaction_1 in context["transactions"]
    assert transaction_2 in context["transactions"]


def test_cash_book_transactions_context_with_year(db, cash_book_1):
    transaction_1 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2024, 1, 1)
    )
    transaction_2 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2023, 1, 1)
    )
    transaction_3 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2024, 1, 1)
    )

    context = _get_cash_book_transactions_context(cash_book_1, year=2024)

    assert context["cash_book"] == cash_book_1
    assert len(context["transactions"]) == 2
    assert transaction_1 in context["transactions"]
    assert transaction_2 not in context["transactions"]
    assert transaction_3 in context["transactions"]


def test_cash_book_transactions_context_with_year_and_month(db, cash_book_1):
    transaction_1 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2024, 1, 1)
    )
    transaction_2 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2023, 1, 1)
    )
    transaction_3 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2024, 3, 1)
    )

    context = _get_cash_book_transactions_context(cash_book_1, year=2024, month=1)

    assert context["cash_book"] == cash_book_1
    assert len(context["transactions"]) == 1
    assert transaction_1 in context["transactions"]
    assert transaction_2 not in context["transactions"]
    assert transaction_3 not in context["transactions"]


def test_cash_book_transactions_context_with_year_and_invalid_month(db, cash_book_1):
    transaction_1 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2024, 1, 1)
    )
    transaction_2 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2023, 1, 1)
    )
    transaction_3 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2024, 3, 1)
    )

    context = _get_cash_book_transactions_context(cash_book_1, year=2024, month=13)

    assert context["cash_book"] == cash_book_1
    assert len(context["transactions"]) == 2
    assert transaction_1 in context["transactions"]
    assert transaction_2 not in context["transactions"]
    assert transaction_3 in context["transactions"]


def test_cash_book_transactions_context_without_year_and_valid_month(db, cash_book_1):
    transaction_1 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2024, 1, 1)
    )
    transaction_2 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2023, 1, 1)
    )
    transaction_3 = baker.make(
        Transaction, cash_book=cash_book_1, date=datetime.date(2024, 3, 1)
    )

    context = _get_cash_book_transactions_context(cash_book_1, month=1)

    assert context["cash_book"] == cash_book_1
    assert len(context["transactions"]) == 3
    assert transaction_1 in context["transactions"]
    assert transaction_2 in context["transactions"]
    assert transaction_3 in context["transactions"]


@pytest.mark.parametrize(
    "year,month,expected_year,expected_month",
    [
        (2024, 1, 2024, 1),
        (2024, None, 2024, None),
        (None, None, None, None),
        (2024, 13, 2024, None),  # Invalid month
        (None, 11, None, None),  # Missing year
        ("2024", "10", 2024, 10),
        ("2024", None, 2024, None),
        ("2024", None, 2024, None),
        (None, "11", None, None),
    ],
)
def test_cash_book_transactions_context_return_appropriate_year_and_month(
    db, cash_book_1, year, month, expected_year, expected_month
):
    context = _get_cash_book_transactions_context(cash_book_1, year=year, month=month)

    assert context["year"] == expected_year
    assert context["month"] == expected_month


@pytest.mark.parametrize(
    "year,month",
    [
        ("", ""),
        ("2024", "A"),
        ("A", "B"),
        ("A2024", "A11"),
    ],
)
def test_cash_book_transactions_context_non_numeric_input_for_year_and_month(
    db, cash_book_1, year, month
):
    with pytest.raises(ValueError):
        context = _get_cash_book_transactions_context(
            cash_book_1, year=year, month=month
        )


def test_cb_transactions_with_format(db, client, user, cash_book_1):
    client.force_login(user)

    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions", args=(cash_book_1.slug,)
    )

    response = client.get(cash_book_transactions_url, query_params={"format": "csv"})

    assert response.status_code == HTTPStatus.OK
    assert response.headers["Content-Type"] == "text/csv"
