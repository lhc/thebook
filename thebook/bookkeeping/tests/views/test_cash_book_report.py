import datetime
import decimal
from http import HTTPStatus

import pytest
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from thebook.bookkeeping.models import Transaction


@pytest.fixture
def user(scope="module"):
    return baker.make(get_user_model())


def test_unauthenticated_access_to_cash_book_report_redirect_to_login_page(db, client):
    cash_book_report_url = reverse("bookkeeping:report-cash-book")

    response = client.get(cash_book_report_url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{settings.LOGIN_URL}?next={cash_book_report_url}"


def test_allowed_access_to_bank_account_details_authenticated(db, client, user):
    client.force_login(user)

    cash_book_report_url = reverse("bookkeeping:report-cash-book")

    response = client.get(cash_book_report_url)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.freeze_time("2026-02-03")
def test_return_current_month_transactions_by_default(db, client, user):
    transaction_1 = baker.make(Transaction, date=datetime.date(2026, 1, 31))
    transaction_2 = baker.make(Transaction, date=datetime.date(2026, 2, 6))
    transaction_3 = baker.make(Transaction, date=datetime.date(2026, 2, 28))
    transaction_4 = baker.make(Transaction, date=datetime.date(2026, 3, 1))

    client.force_login(user)

    cash_book_report_url = reverse("bookkeeping:report-cash-book")

    response = client.get(cash_book_report_url)

    assert "transactions" in response.context
    assert transaction_1 not in response.context["transactions"]
    assert transaction_2 in response.context["transactions"]
    assert transaction_3 in response.context["transactions"]
    assert transaction_4 not in response.context["transactions"]


@pytest.mark.freeze_time("2026-02-03")
def test_returned_transactions_have_income_and_expense_properties(db, client, user):
    transaction_1 = baker.make(
        Transaction, date=datetime.date(2026, 2, 6), amount=decimal.Decimal("100")
    )
    transaction_2 = baker.make(
        Transaction, date=datetime.date(2026, 2, 10), amount=decimal.Decimal("-50.42")
    )
    transaction_3 = baker.make(
        Transaction, date=datetime.date(2026, 2, 28), amount=decimal.Decimal("12.5")
    )

    client.force_login(user)

    cash_book_report_url = reverse("bookkeeping:report-cash-book")

    response = client.get(cash_book_report_url)

    assert "transactions" in response.context

    assert response.context["transactions"][0].id == transaction_1.id
    assert response.context["transactions"][0].income == decimal.Decimal("100")
    assert response.context["transactions"][0].expense is None

    assert response.context["transactions"][1].id == transaction_2.id
    assert response.context["transactions"][1].income is None
    assert response.context["transactions"][1].expense == decimal.Decimal("-50.42")

    assert response.context["transactions"][2].id == transaction_3.id
    assert response.context["transactions"][2].income == decimal.Decimal("12.5")
    assert response.context["transactions"][2].expense is None


@pytest.mark.freeze_time("2026-02-03")
def test_has_opening_balance_with_transactions_before_period(db, client, user):
    transaction_1 = baker.make(
        Transaction, date=datetime.date(2026, 1, 31), amount=decimal.Decimal("258.45")
    )
    transaction_1 = baker.make(
        Transaction, date=datetime.date(2026, 2, 6), amount=decimal.Decimal("100")
    )
    transaction_2 = baker.make(
        Transaction, date=datetime.date(2026, 2, 10), amount=decimal.Decimal("-50.42")
    )
    transaction_3 = baker.make(
        Transaction, date=datetime.date(2026, 2, 28), amount=decimal.Decimal("12.5")
    )

    client.force_login(user)

    cash_book_report_url = reverse("bookkeeping:report-cash-book")

    response = client.get(cash_book_report_url)

    assert "opening_balance" in response.context
    assert response.context["opening_balance"] == decimal.Decimal("258.45")


@pytest.mark.freeze_time("2026-02-03")
def test_has_start_and_end_date_of_current_month(db, client, user):
    client.force_login(user)

    cash_book_report_url = reverse("bookkeeping:report-cash-book")

    response = client.get(cash_book_report_url)

    assert "start_date" in response.context
    assert response.context["start_date"] == datetime.date(2026, 2, 1)

    assert "end_date" in response.context
    assert response.context["end_date"] == datetime.date(2026, 3, 1)


@pytest.mark.freeze_time("2026-02-03")
def test_has_start_and_end_date_provided_as_argument(db, client, user):
    client.force_login(user)

    cash_book_report_url = reverse("bookkeeping:report-cash-book")

    response = client.get(
        cash_book_report_url,
        query_params={"start_date": "2026-01-10", "end_date": "2026-03-01"},
    )

    assert "start_date" in response.context
    assert response.context["start_date"] == datetime.date(2026, 1, 10)

    assert "end_date" in response.context
    assert response.context["end_date"] == datetime.date(2026, 3, 1)
