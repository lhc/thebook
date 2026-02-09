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
def bank_account(scope="module"):
    return BankAccount.objects.create(name="Test Bank Account")


@pytest.fixture
def user(scope="module"):
    return baker.make(get_user_model())


def test_unauthenticated_access_to_bank_account_absolute_url_redirect_to_login_page(
    db, client, bank_account
):
    bank_account_url = reverse("bookkeeping:bank-account", args=(bank_account.slug,))

    response = client.get(bank_account_url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{settings.LOGIN_URL}?next={bank_account_url}"


def test_allowed_access_to_bank_account_details_authenticated(
    db, client, user, bank_account
):
    client.force_login(user)

    bank_account_url = reverse("bookkeeping:bank-account", args=(bank_account.slug,))

    response = client.get(bank_account_url)

    assert response.status_code == HTTPStatus.OK


def test_not_found_with_invalid_bank_account_slug(db, client, user):
    client.force_login(user)

    bank_account_url = reverse("bookkeeping:bank-account", args=("i-do-not-exist",))

    response = client.get(bank_account_url)

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_bank_account_returns_bank_account_instance_in_context(
    db, client, bank_account, user
):
    client.force_login(user)

    bank_account_url = reverse("bookkeeping:bank-account", args=(bank_account.slug,))

    response = client.get(bank_account_url)

    assert "bank_account" in response.context
    assert response.context["bank_account"] == bank_account


def test_bank_account_returns_bank_account_instance_in_context(
    db, client, bank_account, user
):
    client.force_login(user)

    bank_account_url = reverse("bookkeeping:bank-account", args=(bank_account.slug,))

    response = client.get(bank_account_url)

    assert "bank_account" in response.context
    assert response.context["bank_account"] == bank_account


def test_returns_bank_account_instance_in_context(db, client, bank_account, user):
    client.force_login(user)

    bank_account_url = reverse("bookkeeping:bank-account", args=(bank_account.slug,))

    response = client.get(bank_account_url)

    assert "bank_account" in response.context
    assert response.context["bank_account"] == bank_account


@pytest.mark.freeze_time("2026-02-03")
def test_returns_bank_account_transactions_of_current_month_in_context(
    db, client, bank_account, user
):
    # fmt: off
    t_1 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 1, 31))
    t_2 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 1))
    t_3 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 15))
    t_4 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 28))
    t_5 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 3, 1))
    # fmt: on

    client.force_login(user)

    bank_account_url = reverse("bookkeeping:bank-account", args=(bank_account.slug,))

    response = client.get(bank_account_url)

    assert "transactions" in response.context
    assert t_1 not in response.context["transactions"]
    assert t_2 in response.context["transactions"]
    assert t_3 in response.context["transactions"]
    assert t_4 in response.context["transactions"]
    assert t_5 not in response.context["transactions"]


@pytest.mark.freeze_time("2026-02-03")
def test_returns_transactions_date_range_in_context(db, client, bank_account, user):
    client.force_login(user)

    bank_account_url = reverse("bookkeeping:bank-account", args=(bank_account.slug,))

    response = client.get(bank_account_url)

    assert "start_date" in response.context
    assert response.context["start_date"] == datetime.date(2026, 2, 1)
    assert "end_date" in response.context
    assert response.context["end_date"] == datetime.date(2026, 2, 28)


@pytest.mark.freeze_time("2026-02-03")
def test_returns_bank_account_transactions_filtered_by_date_range(
    db, client, bank_account, user
):
    # fmt: off
    t_1 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 1, 31))
    t_2 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 1))
    t_3 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 15))
    t_4 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 28))
    t_5 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 3, 1))
    # fmt: on

    client.force_login(user)

    bank_account_url = reverse(
        "bookkeeping:bank-account",
        args=(bank_account.slug,),
        query={"start_date": "2026-02-10", "end_date": "2026-02-28"},
    )

    response = client.get(bank_account_url)

    assert "transactions" in response.context
    assert t_1 not in response.context["transactions"]
    assert t_2 not in response.context["transactions"]
    assert t_3 in response.context["transactions"]
    assert t_4 in response.context["transactions"]
    assert t_5 not in response.context["transactions"]


@pytest.mark.freeze_time("2026-02-03")
def test_returns_bank_account_transactions_current_month_if_missing_start_date(
    db, client, bank_account, user
):
    # fmt: off
    t_1 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 1, 31))
    t_2 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 1))
    t_3 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 15))
    t_4 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 28))
    t_5 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 3, 1))
    # fmt: on

    client.force_login(user)

    bank_account_url = reverse(
        "bookkeeping:bank-account",
        args=(bank_account.slug,),
        query={
            "end_date": "2026-02-28",
        },
    )

    response = client.get(bank_account_url)

    assert "transactions" in response.context
    assert t_1 not in response.context["transactions"]
    assert t_2 in response.context["transactions"]
    assert t_3 in response.context["transactions"]
    assert t_4 in response.context["transactions"]
    assert t_5 not in response.context["transactions"]


@pytest.mark.freeze_time("2026-02-03")
def test_returns_bank_account_transactions_current_month_if_missing_end_date(
    db, client, bank_account, user
):
    # fmt: off
    t_1 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 1, 31))
    t_2 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 1))
    t_3 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 15))
    t_4 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 2, 28))
    t_5 = baker.make(Transaction, bank_account=bank_account, date=datetime.date(2026, 3, 1))
    # fmt: on

    client.force_login(user)

    bank_account_url = reverse(
        "bookkeeping:bank-account",
        args=(bank_account.slug,),
        query={
            "start_date": "2026-02-10",
        },
    )

    response = client.get(bank_account_url)

    assert "transactions" in response.context
    assert t_1 not in response.context["transactions"]
    assert t_2 in response.context["transactions"]
    assert t_3 in response.context["transactions"]
    assert t_4 in response.context["transactions"]
    assert t_5 not in response.context["transactions"]


@pytest.mark.freeze_time("2026-02-03")
def test_bank_account_has_summary_in_context(db, client, bank_account, user):
    client.force_login(user)

    bank_account_url = reverse(
        "bookkeeping:bank-account",
        args=(bank_account.slug,),
    )

    response = client.get(bank_account_url)

    assert "bank_account" in response.context

    assert hasattr(response.context["bank_account"], "incomes")
    assert hasattr(response.context["bank_account"], "expenses")
    assert hasattr(response.context["bank_account"], "period_balance")
    assert hasattr(response.context["bank_account"], "overall_balance")
    assert hasattr(response.context["bank_account"], "summary_start_date")
    assert hasattr(response.context["bank_account"], "summary_end_date")
