import datetime
from decimal import Decimal
from http import HTTPStatus

import pytest
from model_bakery import baker
from pytest_django.asserts import assertQuerySetEqual

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from thebook.base.views import _get_dashboard_context
from thebook.bookkeeping.models import BankAccount, Transaction
from thebook.members.models import Membership


def test_unauthenticated_access_to_dashboard_redirect_to_login_page(db, client):
    dashboard_url = reverse("base:dashboard")

    response = client.get(dashboard_url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{settings.LOGIN_URL}?next={dashboard_url}"


def test_allowed_access_dashboard_authenticated(db, client):
    user = baker.make(get_user_model())
    client.force_login(user)

    response = client.get(reverse("base:dashboard"))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.freeze_time("2024-09-15")
def test_dashboard_context(db):
    cash_book_1 = BankAccount.objects.create(name="Cash Book 1")
    cash_book_2 = BankAccount.objects.create(name="Cash Book 2")

    # fmt: off
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2023, 11, 1), amount=Decimal("100"))
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2024, 9, 1), amount=Decimal("12.53"))
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2024, 9, 10), amount=Decimal("-15.5"))
    baker.make(Transaction, cash_book=cash_book_1, date=datetime.date(2024, 9, 12), amount=Decimal("19.23"))

    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2023, 11, 1), amount=Decimal("98.11"))
    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2024, 9, 1), amount=Decimal("15.4"))
    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2024, 9, 10), amount=Decimal("42.58"))
    baker.make(Transaction, cash_book=cash_book_2, date=datetime.date(2024, 9, 12), amount=Decimal("-58.39"))
    # fmt: on

    context = _get_dashboard_context()

    assert context["deposits"] == Decimal("89.74")
    assert context["withdraws"] == Decimal("-73.89")
    assert context["balance"] == Decimal("15.85")
    assert context["overall_balance"] == Decimal("213.96")
    assert context["today"] == datetime.date(2024, 9, 15)
    assertQuerySetEqual(
        context["cash_books_summary"], BankAccount.objects.summary(year=2024, month=9)
    )


def test_dashboard_list_only_active_cash_books(db):
    cash_book_1 = BankAccount.objects.create(name="Cash Book 1", active=True)
    cash_book_2 = BankAccount.objects.create(name="Cash Book 2", active=False)
    cash_book_3 = BankAccount.objects.create(name="Cash Book 3", active=True)
    cash_book_4 = BankAccount.objects.create(name="Cash Book 4", active=False)

    context = _get_dashboard_context()

    assert len(context["cash_books_summary"]) == 2

    assert cash_book_1 in context["cash_books_summary"]
    assert cash_book_2 not in context["cash_books_summary"]
    assert cash_book_3 in context["cash_books_summary"]
    assert cash_book_4 not in context["cash_books_summary"]


def test_dashboard_context_has_number_of_active_memberships(db):
    baker.make(Membership, active=True, _quantity=4)
    baker.make(Membership, active=False, _quantity=10)

    context = _get_dashboard_context()

    assert context["active_memberships"] == 4
