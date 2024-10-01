import datetime
from decimal import Decimal
from http import HTTPStatus

import pytest
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from thebook.base.views import _get_dashboard_context
from thebook.bookkeeping.models import CashBook, Transaction


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
    cash_book_1 = CashBook.objects.create(name="Cash Book 1")
    cash_book_2 = CashBook.objects.create(name="Cash Book 2")

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

    assert context == {
        "deposits": Decimal("89.74"),
        "withdraws": Decimal("-73.89"),
        "balance": Decimal("15.85"),
        "overall_balance": Decimal("213.96"),
    }
