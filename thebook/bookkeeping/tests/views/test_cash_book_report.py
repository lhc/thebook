from http import HTTPStatus

import pytest
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse


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
