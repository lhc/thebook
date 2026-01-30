import datetime
from http import HTTPStatus

import pytest
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse

from thebook.bookkeeping.models import BankAccount, Category, Document, Transaction


@pytest.fixture
def transaction():
    return baker.make(Transaction)


@pytest.fixture
def user():
    return baker.make(get_user_model())


def test_access_to_transaction_details(db, client, user, transaction):
    client.force_login(user)

    response = client.get(
        reverse(
            "bookkeeping:partial-transaction-details",
            args=(transaction.id,),
        )
    )

    assert response.status_code == HTTPStatus.OK
    assert "transaction" in response.context
    assert response.context["transaction"] == transaction


def test_access_to_invalid_transaction_details(db, client, user, transaction):
    client.force_login(user)

    response = client.get(
        reverse(
            "bookkeeping:partial-transaction-details",
            args=(99999,),
        )
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_unauthenticated_access_to_transactions_details_redirect_to_login_page(
    db, client, transaction
):
    transaction_details_url = reverse(
        "bookkeeping:partial-transaction-details",
        args=(transaction.id,),
    )

    response = client.get(transaction_details_url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{settings.LOGIN_URL}?next={transaction_details_url}"
