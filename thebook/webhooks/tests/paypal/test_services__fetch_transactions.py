import datetime
from decimal import Decimal
from pathlib import Path

import pytest
import responses
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model

from thebook.bookkeeping.models import BankAccount, Category, Transaction
from thebook.webhooks.paypal.services import fetch_transactions

SAMPLE_PAYLOADS_DIR = Path(__file__).parent / "sample_payloads"


@pytest.fixture
def bank_fee_category(db):
    return Category.objects.create(name=settings.BANK_FEE_CATEGORY_NAME)


@pytest.fixture
def bank_account_transfer_category(db):
    category, _ = Category.objects.get_or_create(
        name="Transferência entre contas bancárias"
    )
    return category


@pytest.fixture
def paypal_bank_account():
    bank_account, _ = BankAccount.objects.get_or_create(
        name=settings.PAYPAL_BANK_ACCOUNT
    )
    return bank_account


@pytest.fixture
def user():
    return get_user_model().objects.get_or_create_automation_user()


@pytest.fixture
def paypal__oauth2_token():
    return {"access_token": "test-access-token"}


@pytest.fixture
def reporting_transactions__one_transaction():
    with open(
        Path(SAMPLE_PAYLOADS_DIR / "reporting_transactions__one_transaction.json"), "r"
    ) as payload:
        return payload.read()


@pytest.fixture
def reporting_transactions__multiple_transactions():
    with open(
        Path(
            SAMPLE_PAYLOADS_DIR / "reporting_transactions__multiple_transactions.json"
        ),
        "r",
    ) as payload:
        return payload.read()


@pytest.fixture
def reporting_transactions__usd_transaction():
    with open(
        Path(SAMPLE_PAYLOADS_DIR / "reporting_transactions__usd_transaction.json"), "r"
    ) as payload:
        return payload.read()


@pytest.fixture(params=["T0400", "T0403"])
def reporting_transactions__one_bank_account_transfer_transaction(
    request,
):
    with open(
        Path(
            SAMPLE_PAYLOADS_DIR
            / "reporting_transactions__one_bank_account_transfer_transaction.json"
        ),
        "r",
    ) as payload:
        return payload.read().replace("<TRANSACTION_EVENT_CODE>", request.param)


@responses.activate
def test_fetch_one_transaction(
    db,
    paypal_bank_account,
    user,
    bank_fee_category,
    paypal__oauth2_token,
    reporting_transactions__one_transaction,
):
    responses.add(
        responses.POST,
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        json=paypal__oauth2_token,
    )
    responses.add(
        responses.GET,
        f"{settings.PAYPAL_API_BASE_URL}/v1/reporting/transactions",
        body=reporting_transactions__one_transaction,
        content_type="application/json",
    )

    transactions = fetch_transactions(
        start_date=datetime.date(2026, 2, 1), end_date=datetime.date(2026, 2, 2)
    )

    assert len(transactions) == 2

    assert transactions[0].id is None
    assert transactions[0].reference == "5EM753922G985452E"
    assert transactions[0].date == datetime.date(2026, 2, 1)
    assert transactions[0].description == "Regular Donation"
    assert transactions[0].amount == Decimal("102.36")
    assert transactions[0].bank_account == paypal_bank_account
    assert transactions[0].category is None
    assert transactions[0].created_by == user

    assert transactions[1].id is None
    assert transactions[1].reference == "5EM753922G985452E-T"
    assert transactions[1].date == datetime.date(2026, 2, 1)
    assert transactions[1].description == "Taxa Paypal - Regular Donation"
    assert transactions[1].amount == Decimal("-7.64")
    assert transactions[1].bank_account == paypal_bank_account
    assert transactions[1].category == bank_fee_category
    assert transactions[1].created_by == user


@responses.activate
def test_fetch_multiple_transactions(
    db,
    paypal_bank_account,
    user,
    bank_fee_category,
    bank_account_transfer_category,
    paypal__oauth2_token,
    reporting_transactions__multiple_transactions,
):
    responses.add(
        responses.POST,
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        json=paypal__oauth2_token,
    )
    responses.add(
        responses.GET,
        f"{settings.PAYPAL_API_BASE_URL}/v1/reporting/transactions",
        body=reporting_transactions__multiple_transactions,
        content_type="application/json",
    )

    transactions = fetch_transactions(
        start_date=datetime.date(2026, 2, 1), end_date=datetime.date(2026, 2, 2)
    )

    assert len(transactions) == 3

    assert transactions[0].id is None
    assert transactions[0].reference == "5EM753922G985452E"
    assert transactions[0].date == datetime.date(2026, 2, 1)
    assert transactions[0].description == "Regular Donation"
    assert transactions[0].amount == Decimal("102.36")
    assert transactions[0].bank_account == paypal_bank_account
    assert transactions[0].category is None
    assert transactions[0].created_by == user

    assert transactions[1].id is None
    assert transactions[1].reference == "5EM753922G985452E-T"
    assert transactions[1].date == datetime.date(2026, 2, 1)
    assert transactions[1].description == "Taxa Paypal - Regular Donation"
    assert transactions[1].amount == Decimal("-7.64")
    assert transactions[1].bank_account == paypal_bank_account
    assert transactions[1].category == bank_fee_category
    assert transactions[1].created_by == user

    assert transactions[2].id is None
    assert transactions[2].reference == "70Y35009P3781470Y"
    assert transactions[2].date == datetime.date(2026, 2, 2)
    assert (
        transactions[2].description
        == f"Transferência entre contas bancárias - 70Y35009P3781470Y"
    )
    assert transactions[2].amount == Decimal("-80.33")
    assert transactions[2].bank_account == paypal_bank_account
    assert transactions[2].category == bank_account_transfer_category
    assert transactions[2].created_by == user


@responses.activate
def test_fetch_one_bank_account_transfer_transaction(
    db,
    paypal_bank_account,
    user,
    bank_account_transfer_category,
    paypal__oauth2_token,
    reporting_transactions__one_bank_account_transfer_transaction,
):
    responses.add(
        responses.POST,
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        json=paypal__oauth2_token,
    )
    responses.add(
        responses.GET,
        f"{settings.PAYPAL_API_BASE_URL}/v1/reporting/transactions",
        body=reporting_transactions__one_bank_account_transfer_transaction,
        content_type="application/json",
    )

    transactions = fetch_transactions(
        start_date=datetime.date(2026, 2, 1), end_date=datetime.date(2026, 2, 2)
    )

    assert len(transactions) == 1

    assert transactions[0].id is None
    assert transactions[0].reference == "70Y35009P3781470Y"
    assert transactions[0].date == datetime.date(2026, 2, 2)
    assert (
        transactions[0].description
        == f"Transferência entre contas bancárias - 70Y35009P3781470Y"
    )
    assert transactions[0].amount == Decimal("-80.33")
    assert transactions[0].bank_account == paypal_bank_account
    assert transactions[0].category == bank_account_transfer_category
    assert transactions[0].created_by == user


@responses.activate
def test_fetch_one_existing_transaction(
    db,
    paypal_bank_account,
    user,
    bank_fee_category,
    paypal__oauth2_token,
    reporting_transactions__one_transaction,
):
    responses.add(
        responses.POST,
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        json=paypal__oauth2_token,
    )
    responses.add(
        responses.GET,
        f"{settings.PAYPAL_API_BASE_URL}/v1/reporting/transactions",
        body=reporting_transactions__one_transaction,
        content_type="application/json",
    )
    baker.make(Transaction, reference="5EM753922G985452E")

    transactions = fetch_transactions(
        start_date=datetime.date(2026, 2, 1), end_date=datetime.date(2026, 2, 2)
    )

    assert len(transactions) == 0


@responses.activate
def test_fetch_one_existing_bank_account_transfer_transaction(
    db,
    paypal_bank_account,
    user,
    bank_account_transfer_category,
    paypal__oauth2_token,
    reporting_transactions__one_bank_account_transfer_transaction,
):
    responses.add(
        responses.POST,
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        json=paypal__oauth2_token,
    )
    responses.add(
        responses.GET,
        f"{settings.PAYPAL_API_BASE_URL}/v1/reporting/transactions",
        body=reporting_transactions__one_bank_account_transfer_transaction,
        content_type="application/json",
    )
    baker.make(Transaction, reference="70Y35009P3781470Y")

    transactions = fetch_transactions(
        start_date=datetime.date(2026, 2, 1), end_date=datetime.date(2026, 2, 2)
    )

    assert len(transactions) == 0


@responses.activate
def test_fetch_usd_transaction(
    db,
    paypal_bank_account,
    user,
    bank_account_transfer_category,
    paypal__oauth2_token,
    reporting_transactions__usd_transaction,
):
    responses.add(
        responses.POST,
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        json=paypal__oauth2_token,
    )
    responses.add(
        responses.GET,
        f"{settings.PAYPAL_API_BASE_URL}/v1/reporting/transactions",
        body=reporting_transactions__usd_transaction,
        content_type="application/json",
    )

    transactions = fetch_transactions(
        start_date=datetime.date(2026, 2, 1), end_date=datetime.date(2026, 2, 2)
    )

    assert len(transactions) == 0
