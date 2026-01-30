import datetime
import io
from http import HTTPStatus

import pytest
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from django.utils.functional import SimpleLazyObject

from thebook.bookkeeping.importers import ImportTransactionsError
from thebook.bookkeeping.models import BankAccount, Transaction
from thebook.bookkeeping.views import _get_bank_account_transactions_context


@pytest.fixture
def bank_account():
    return BankAccount.objects.create(name="Bank Account 1")


@pytest.fixture
def user():
    return baker.make(get_user_model())


def test_unauthenticated_access_to_cb_import_transactions_not_allowed(
    db, client, mocker, bank_account
):
    import_transactions_mock = mocker.patch(
        "thebook.bookkeeping.views.import_transactions"
    )

    import_url = reverse(
        "bookkeeping:bank-account-import-transactions", args=(bank_account.slug,)
    )

    response = client.post(
        import_url,
        {
            "csv_file": io.StringIO(),
            "file_type": "csv",
            "next_url": "",
        },
    )

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{settings.LOGIN_URL}?next={import_url}"


def test_allowed_access_to_cb_import_transactions_authenticated(
    db, client, mocker, user, bank_account
):
    import_transactions_mock = mocker.patch(
        "thebook.bookkeeping.views.import_transactions"
    )

    client.force_login(user)

    import_url = reverse(
        "bookkeeping:bank-account-import-transactions", args=(bank_account.slug,)
    )
    next_url = reverse(
        "bookkeeping:bank-account-transactions", args=(bank_account.slug,)
    )

    response = client.post(
        import_url,
        {
            "csv_file": io.StringIO(),
            "file_type": "csv",
            "next_url": next_url,
        },
    )

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == next_url


def test_not_found_with_invalid_bank_account_slug(db, client, mocker, user):
    import_transactions_mock = mocker.patch(
        "thebook.bookkeeping.views.import_transactions"
    )

    client.force_login(user)

    import_url = reverse(
        "bookkeeping:bank-account-import-transactions",
        args=("not-a-valid-bank-account",),
    )

    response = client.post(
        import_url,
        {
            "csv_file": io.StringIO(),
            "file_type": "csv",
            "next_url": "",
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_import_transactions_csv_called_when_provided_valid_data(
    db, client, mocker, user, bank_account
):
    import_transactions_mock = mocker.patch(
        "thebook.bookkeeping.views.import_transactions"
    )

    client.force_login(user)

    import_url = reverse(
        "bookkeeping:bank-account-import-transactions", args=(bank_account.slug,)
    )
    next_url = reverse(
        "bookkeeping:bank-account-transactions", args=(bank_account.slug,)
    )
    file_type = "csv"

    response = client.post(
        import_url,
        {
            "csv_file": io.StringIO(),
            "file_type": file_type,
            "next_url": next_url,
        },
    )

    import_transactions_mock.assert_called_once()


def test_import_transactions_add_error_message_when_failed(
    db, client, mocker, user, bank_account
):
    expected_error_message = "An error happened."
    import_transactions_mock = mocker.patch(
        "thebook.bookkeeping.views.import_transactions",
        side_effect=ImportTransactionsError(expected_error_message),
    )

    client.force_login(user)

    import_url = reverse(
        "bookkeeping:bank-account-import-transactions", args=(bank_account.slug,)
    )
    next_url = reverse(
        "bookkeeping:bank-account-transactions", args=(bank_account.slug,)
    )
    file_type = "csv"

    response = client.post(
        import_url,
        {
            "csv_file": io.StringIO(),
            "file_type": file_type,
            "next_url": next_url,
        },
    )

    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert str(messages[0]) == expected_error_message
