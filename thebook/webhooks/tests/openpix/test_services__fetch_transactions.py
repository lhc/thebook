import datetime
from decimal import Decimal
from pathlib import Path

import pytest
import responses
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model

from thebook.bookkeeping.models import BankAccount, Category, Transaction
from thebook.webhooks.openpix.services import fetch_transactions

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
def openpix_bank_account():
    bank_account, _ = BankAccount.objects.get_or_create(
        name=settings.OPENPIX_BANK_ACCOUNT
    )
    return bank_account


@pytest.fixture
def user():
    return get_user_model().objects.get_or_create_automation_user()


@pytest.fixture
def openpix__transactions():
    with open(Path(SAMPLE_PAYLOADS_DIR / "openpix__transactions.json"), "r") as payload:
        return payload.read()


@responses.activate
def test_fetch_multiple_transactions(
    db,
    settings,
    openpix_bank_account,
    user,
    bank_fee_category,
    bank_account_transfer_category,
    openpix__transactions,
):
    settings.OPENPIX_PLAN = "PERCENTUAL"
    responses.add(
        responses.GET,
        f"{settings.OPENPIX_API_BASE_URL}/api/v1/transaction",
        body=openpix__transactions,
        content_type="application/json",
    )

    transactions = fetch_transactions(
        start_date=datetime.date(2026, 2, 1), end_date=datetime.date(2026, 2, 28)
    )

    assert len(transactions) == 5

    assert transactions[0].reference == "E54843980984242151500EqEkgXhBQPb"
    assert transactions[0].date == datetime.date(2026, 2, 15)
    assert transactions[0].description == "NED LUDD - 12345678910"
    assert transactions[0].amount == Decimal("110")
    assert transactions[0].bank_account == openpix_bank_account
    assert transactions[0].category is None
    assert transactions[0].created_by == user

    assert transactions[1].reference == "E54843980984242151500EqEkgXhBQPb-T"
    assert transactions[1].date == datetime.date(2026, 2, 15)
    assert transactions[1].description == "Taxa OpenPix - NED LUDD - 12345678910"
    assert transactions[1].amount == Decimal("-0.88")
    assert transactions[1].bank_account == openpix_bank_account
    assert transactions[1].category == bank_fee_category
    assert transactions[1].created_by == user

    assert transactions[2].reference == "E54811417202602091301r0gglTvTqLN"
    assert transactions[2].date == datetime.date(2026, 2, 20)
    assert (
        transactions[2].description
        == "Transferência entre contas bancárias - E54811417202602091301r0gglTvTqLN"
    )
    assert transactions[2].amount == Decimal("511.87")
    assert transactions[2].bank_account == openpix_bank_account
    assert transactions[2].category == bank_account_transfer_category
    assert transactions[2].created_by == user

    assert transactions[3].reference == "E00416968202602281512zy3bbOcj3IJ"
    assert transactions[3].date == datetime.date(2026, 2, 28)
    assert transactions[3].description == "LUIZ ANTONIO - 12345678910"
    assert transactions[3].amount == Decimal("42")
    assert transactions[3].bank_account == openpix_bank_account
    assert transactions[3].category == None
    assert transactions[3].created_by == user

    assert transactions[4].reference == "E00416968202602281512zy3bbOcj3IJ-T"
    assert transactions[4].date == datetime.date(2026, 2, 28)
    assert transactions[4].description == "Taxa OpenPix - LUIZ ANTONIO - 12345678910"
    assert transactions[4].amount == Decimal("-0.50")
    assert transactions[4].bank_account == openpix_bank_account
    assert transactions[4].category == bank_fee_category
    assert transactions[4].created_by == user


@responses.activate
def test_fetch_already_existing_transactions(
    db,
    openpix__transactions,
):
    responses.add(
        responses.GET,
        f"{settings.OPENPIX_API_BASE_URL}/api/v1/transaction",
        body=openpix__transactions,
        content_type="application/json",
    )
    baker.make(Transaction, reference="E54843980984242151500EqEkgXhBQPb")
    baker.make(Transaction, reference="E54811417202602091301r0gglTvTqLN")
    baker.make(Transaction, reference="E00416968202602281512zy3bbOcj3IJ")

    transactions = fetch_transactions(
        start_date=datetime.date(2026, 2, 1), end_date=datetime.date(2026, 2, 28)
    )

    assert len(transactions) == 0


@responses.activate
def test_only_fetch_new_transactions(
    db,
    openpix__transactions,
):
    responses.add(
        responses.GET,
        f"{settings.OPENPIX_API_BASE_URL}/api/v1/transaction",
        body=openpix__transactions,
        content_type="application/json",
    )
    baker.make(Transaction, reference="E54843980984242151500EqEkgXhBQPb")
    baker.make(Transaction, reference="E54811417202602091301r0gglTvTqLN")

    transactions = fetch_transactions(
        start_date=datetime.date(2026, 2, 1), end_date=datetime.date(2026, 2, 28)
    )

    assert len(transactions) == 2

    assert transactions[0].reference == "E00416968202602281512zy3bbOcj3IJ"
    assert transactions[1].reference == "E00416968202602281512zy3bbOcj3IJ-T"
