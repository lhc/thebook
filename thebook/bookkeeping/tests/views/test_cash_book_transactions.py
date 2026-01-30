import datetime
from http import HTTPStatus

import pytest
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse

from thebook.bookkeeping.models import BankAccount, Category, Document, Transaction
from thebook.bookkeeping.views import (
    _get_bank_account_transactions_context,
    bank_account_transactions,
)


@pytest.fixture
def bank_account_1():
    return BankAccount.objects.create(name="Bank Account 1")


@pytest.fixture
def bank_account_2():
    return BankAccount.objects.create(name="Bank Account 2")


@pytest.fixture
def user():
    return baker.make(get_user_model())


def test_unauthenticated_access_to_cb_transactions_redirect_to_login_page(
    db, client, bank_account_1
):
    bank_account_transactions_url = reverse(
        "bookkeeping:bank-account-transactions", args=(bank_account_1.slug,)
    )

    response = client.get(bank_account_transactions_url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{settings.LOGIN_URL}?next={bank_account_transactions_url}"


def test_allowed_access_to_cb_transactions_authenticated(
    db, client, user, bank_account_1
):
    client.force_login(user)

    bank_account_transactions_url = reverse(
        "bookkeeping:bank-account-transactions", args=(bank_account_1.slug,)
    )

    response = client.get(bank_account_transactions_url)

    assert response.status_code == HTTPStatus.OK


def test_not_found_with_invalid_bank_account_slug(db, client, user):
    client.force_login(user)

    bank_account_transactions_url = reverse(
        "bookkeeping:bank-account-transactions", args=("i-do-not-exist",)
    )

    response = client.get(bank_account_transactions_url)

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_return_transactions_only_for_selected_bank_account(
    db, client, user, bank_account_1, bank_account_2
):
    client.force_login(user)

    transaction_1 = baker.make(Transaction, bank_account=bank_account_1)
    transaction_2 = baker.make(Transaction, bank_account=bank_account_2)
    transaction_3 = baker.make(Transaction, bank_account=bank_account_1)

    bank_account_transactions_url = reverse(
        "bookkeeping:bank-account-transactions", args=(bank_account_1.slug,)
    )

    response = client.get(bank_account_transactions_url)

    assert transaction_1 in response.context["transactions"]
    assert transaction_2 not in response.context["transactions"]
    assert transaction_3 in response.context["transactions"]


def test_providing_year_retrieve_context_with_year(
    db, client, user, bank_account_1, mocker
):
    get_context_mock = mocker.patch(
        "thebook.bookkeeping.views._get_bank_account_transactions_context",
        return_value={
            "bank_account": bank_account_1,
            "transactions": [],
        },
    )
    client.force_login(user)

    bank_account_transactions_url = reverse(
        "bookkeeping:bank-account-transactions",
        args=(bank_account_1.slug,),
    )
    response = client.get(bank_account_transactions_url, query_params={"year": "2024"})

    get_context_mock.assert_called_once_with(bank_account_1, year="2024", month=None)


def test_providing_year_and_month_retrieve_context_with_year_and_month(
    db, client, user, bank_account_1, mocker
):
    get_context_mock = mocker.patch(
        "thebook.bookkeeping.views._get_bank_account_transactions_context",
        return_value={
            "bank_account": bank_account_1,
            "transactions": [],
        },
    )
    client.force_login(user)

    bank_account_transactions_url = reverse(
        "bookkeeping:bank-account-transactions",
        args=(bank_account_1.slug,),
    )
    response = client.get(
        bank_account_transactions_url, query_params={"year": "2024", "month": "11"}
    )

    get_context_mock.assert_called_once_with(bank_account_1, year="2024", month="11")


def test_bank_account_transactions_context(db, bank_account_1):
    transaction_1 = baker.make(Transaction, bank_account=bank_account_1)
    transaction_2 = baker.make(Transaction, bank_account=bank_account_1)

    context = _get_bank_account_transactions_context(bank_account_1)

    assert context["bank_account"] == bank_account_1.with_summary()
    assert len(context["transactions"]) == 2
    assert transaction_1 in context["transactions"]
    assert transaction_2 in context["transactions"]


def test_bank_account_transactions_context_with_year(db, bank_account_1):
    transaction_1 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2024, 1, 1)
    )
    transaction_2 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2023, 1, 1)
    )
    transaction_3 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2024, 1, 1)
    )

    context = _get_bank_account_transactions_context(bank_account_1, year=2024)

    assert context["bank_account"] == bank_account_1.with_summary(year=2024)
    assert len(context["transactions"]) == 2
    assert transaction_1 in context["transactions"]
    assert transaction_2 not in context["transactions"]
    assert transaction_3 in context["transactions"]


def test_bank_account_transactions_context_with_year_and_month(db, bank_account_1):
    transaction_1 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2024, 1, 1)
    )
    transaction_2 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2023, 1, 1)
    )
    transaction_3 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2024, 3, 1)
    )

    context = _get_bank_account_transactions_context(bank_account_1, year=2024, month=1)

    assert context["bank_account"] == bank_account_1.with_summary(year=2024, month=1)
    assert len(context["transactions"]) == 1
    assert transaction_1 in context["transactions"]
    assert transaction_2 not in context["transactions"]
    assert transaction_3 not in context["transactions"]


def test_bank_account_transactions_context_with_year_and_invalid_month(
    db, bank_account_1
):
    transaction_1 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2024, 1, 1)
    )
    transaction_2 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2023, 1, 1)
    )
    transaction_3 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2024, 3, 1)
    )

    context = _get_bank_account_transactions_context(
        bank_account_1, year=2024, month=13
    )

    assert context["bank_account"] == bank_account_1.with_summary(year=2024)
    assert len(context["transactions"]) == 2
    assert transaction_1 in context["transactions"]
    assert transaction_2 not in context["transactions"]
    assert transaction_3 in context["transactions"]


def test_bank_account_transactions_context_without_year_and_valid_month(
    db, bank_account_1
):
    transaction_1 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2024, 1, 1)
    )
    transaction_2 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2023, 1, 1)
    )
    transaction_3 = baker.make(
        Transaction, bank_account=bank_account_1, date=datetime.date(2024, 3, 1)
    )

    context = _get_bank_account_transactions_context(bank_account_1, month=1)

    assert context["bank_account"] == bank_account_1.with_summary()
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
def test_bank_account_transactions_context_return_appropriate_year_and_month(
    db, bank_account_1, year, month, expected_year, expected_month
):
    context = _get_bank_account_transactions_context(
        bank_account_1, year=year, month=month
    )

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
def test_bank_account_transactions_context_non_numeric_input_for_year_and_month(
    db, bank_account_1, year, month
):
    with pytest.raises(ValueError):
        context = _get_bank_account_transactions_context(
            bank_account_1, year=year, month=month
        )


def test_cb_transactions_with_format(db, client, user, bank_account_1):
    client.force_login(user)

    bank_account_transactions_url = reverse(
        "bookkeeping:bank-account-transactions", args=(bank_account_1.slug,)
    )

    response = client.get(bank_account_transactions_url, query_params={"format": "csv"})

    assert response.status_code == HTTPStatus.OK
    assert response.headers["Content-Type"] == "text/csv"


@pytest.mark.parametrize(
    "year,month,previous_period,next_period",
    [
        ("2024", None, "year=2023", "year=2025"),
        ("2020", None, "year=2019", "year=2021"),
        ("2024", "1", "year=2023&month=12", "year=2024&month=2"),
        ("2023", "12", "year=2023&month=11", "year=2024&month=1"),
        ("2024", "6", "year=2024&month=5", "year=2024&month=7"),
    ],
)
def test_cb_transactions_next_and_previous_period_query_params_in_context(
    db, bank_account_1, year, month, previous_period, next_period
):
    context = _get_bank_account_transactions_context(
        bank_account_1, year=year, month=month
    )

    assert context["previous_period"] == previous_period
    assert context["next_period"] == next_period


def test_return_transactions_does_not_execute_excessive_amount_of_queries(
    db, django_assert_num_queries, client, user, bank_account_1
):
    baker.make(
        Transaction,
        bank_account=bank_account_1,
        category=baker.make(Category),
        _quantity=20,
    )
    baker.make(
        Document,
        transaction__bank_account=bank_account_1,
        _quantity=20,
        _create_files=True,
    )

    bank_account_transactions_url = reverse(
        "bookkeeping:bank-account-transactions", args=(bank_account_1.slug,)
    )
    request = RequestFactory().get(bank_account_transactions_url)

    with django_assert_num_queries(6) as captured:
        response = bank_account_transactions(request, bank_account_1.slug)
