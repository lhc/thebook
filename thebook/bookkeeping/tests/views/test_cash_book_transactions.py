from http import HTTPStatus

import pytest
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from thebook.bookkeeping.views import _get_cash_book_transactions_context
from thebook.bookkeeping.models import CashBook, Transaction


@pytest.fixture
def cash_book():
    return CashBook.objects.create(name="Cash Book 1")


def test_unauthenticated_access_to_dashboard_redirect_to_login_page(
    db, client, cash_book
):
    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions", args=(cash_book.slug,)
    )

    response = client.get(cash_book_transactions_url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{settings.LOGIN_URL}?next={cash_book_transactions_url}"


def test_allowed_access_dashboard_authenticated(db, client, cash_book):
    user = baker.make(get_user_model())
    client.force_login(user)

    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions", args=(cash_book.slug,)
    )

    response = client.get(cash_book_transactions_url)

    assert response.status_code == HTTPStatus.OK


def test_not_found_with_invalid_cash_book_slug(db, client):
    user = baker.make(get_user_model())
    client.force_login(user)

    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions", args=("i-do-not-exist",)
    )

    response = client.get(cash_book_transactions_url)

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_cash_book_transactions_context(db):
    cash_book_1 = CashBook.objects.create(name="Cash Book 1")
    cash_book_2 = CashBook.objects.create(name="Cash Book 2")

    transaction_1 = baker.make(Transaction, cash_book=cash_book_1)
    transaction_2 = baker.make(Transaction, cash_book=cash_book_1)
    transaction_3 = baker.make(Transaction, cash_book=cash_book_2)

    context = _get_cash_book_transactions_context(cash_book_1)

    assert context["cash_book"] == cash_book_1
    assert len(context["transactions"]) == 2
    assert transaction_1 in context["transactions"]
    assert transaction_2 in context["transactions"]
