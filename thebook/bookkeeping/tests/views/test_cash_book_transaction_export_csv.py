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


def test_unauthenticated_access_to_export_cash_book_transactions_redirect_to_login_page(
    db, client, cash_book
):
    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions-export-csv", args=(cash_book.slug,)
    )

    response = client.get(cash_book_transactions_url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{settings.LOGIN_URL}?next={cash_book_transactions_url}"


def test_allowed_access_to_export_cash_book_transactions_authenticated(
    db, client, cash_book
):
    user = baker.make(get_user_model())
    client.force_login(user)

    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions-export-csv", args=(cash_book.slug,)
    )

    response = client.get(cash_book_transactions_url)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["Content-Type"] == "text/csv"


def test_not_found_with_invalid_cash_book_slug(db, client):
    user = baker.make(get_user_model())
    client.force_login(user)

    cash_book_transactions_url = reverse(
        "bookkeeping:cash-book-transactions-export-csv", args=("i-do-not-exist",)
    )

    response = client.get(cash_book_transactions_url)

    assert response.status_code == HTTPStatus.NOT_FOUND
