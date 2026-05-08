import datetime
import decimal
import io
from uuid import UUID

import pytest
from model_bakery import baker

from django.contrib.auth import get_user_model

from thebook.bookkeeping.models import BankAccount, Category, Transaction
from thebook.integrations.cora.constants import (
    CORA_BANK_ACCOUNT,
    CORA_CREDIT_CARD_BANK_ACCOUNT,
)
from thebook.integrations.cora.importers.ofx import CoraOFXImporter, InvalidCoraOFXFile


def valid_uuid(value):
    try:
        uuid_obj = UUID(str(value))
    except ValueError:
        return False
    return str(uuid_obj) == str(value)


@pytest.fixture
def cora_bank_account(db):
    bank_account, _ = BankAccount.objects.get_or_create(name=CORA_BANK_ACCOUNT)
    return bank_account


@pytest.fixture
def cora_credit_card_bank_account(db):
    bank_account, _ = BankAccount.objects.get_or_create(
        name=CORA_CREDIT_CARD_BANK_ACCOUNT
    )
    return bank_account


@pytest.fixture
def bank_account_transfer_category(db):
    bank_account_transfer_category, _ = Category.objects.get_or_create(
        name="Transferência entre contas bancárias"
    )
    return bank_account_transfer_category


@pytest.fixture
def user(db):
    return get_user_model().objects.get_or_create_automation_user()


def test_raise_error_when_providing_invalid_ofx_file(db):
    with pytest.raises(InvalidCoraOFXFile):
        invalid_ofx_file = io.BytesIO(b"NOT_A_VALID_OFX")
        ofx_importer = CoraOFXImporter(invalid_ofx_file)


def test_ofx_file_with_one_transaction(db, request, cora_bank_account, user):
    ofx_file_path = request.path.parent / "data" / "ofx-one-transaction.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = CoraOFXImporter(ofx_file)

        transactions = ofx_importer.get_transactions()

        assert len(transactions) == 1
        assert transactions[0].id is None
        assert transactions[0].reference == "16b3dab5-d1ca-41e1-87c2-a26920ae70ac"
        assert transactions[0].date == datetime.date(2024, 8, 19)
        assert transactions[0].description == "Debito em Conta"
        assert transactions[0].amount == decimal.Decimal("-2500.50")
        assert transactions[0].notes == ""
        assert transactions[0].source == "cora.importers.ofx"
        assert transactions[0].bank_account == cora_bank_account
        assert transactions[0].created_by == user
        assert transactions[0].category is None


def test_ofx_file_with_multiple_transactions(db, request, cora_bank_account, user):
    ofx_file_path = request.path.parent / "data" / "ofx-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = CoraOFXImporter(ofx_file)

        transactions = ofx_importer.get_transactions()

        references = sorted([transaction.reference for transaction in transactions])
        expected_references = sorted(
            [
                "3825c888-1017-497d-bee2-c0737d5dafc0",
                "63c41497-5e0b-4a3c-ada1-d9abebb0af39",
                "69b66fe5-0360-466c-b2e5-08efc1768389",
                "39221b44-f648-44ec-b6d1-1d8eefe54e02",
                "6b01e19f-fc2f-4ea7-b524-6f6c634aea63",
            ]
        )

        assert len(transactions) == 5
        assert references == expected_references


def test_test_ofx_file_exclude_existing_true(db, request, cora_bank_account, user):
    baker.make(Transaction, reference="16b3dab5-d1ca-41e1-87c2-a26920ae70ac")

    ofx_file_path = request.path.parent / "data" / "ofx-one-transaction.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = CoraOFXImporter(ofx_file)

        transactions = ofx_importer.get_transactions(exclude_existing=True)

        assert len(transactions) == 0


def test_test_ofx_file_exclude_existing_false(db, request, cora_bank_account, user):
    baker.make(Transaction, reference="16b3dab5-d1ca-41e1-87c2-a26920ae70ac")

    ofx_file_path = request.path.parent / "data" / "ofx-one-transaction.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = CoraOFXImporter(ofx_file)

        transactions = ofx_importer.get_transactions(exclude_existing=False)

        assert len(transactions) == 1
        assert transactions[0].id is None
        assert transactions[0].reference == "16b3dab5-d1ca-41e1-87c2-a26920ae70ac"


def test_ofx_file_with_multiple_transactions_filter_by_start_date(
    db, request, cora_bank_account, user
):
    ofx_file_path = request.path.parent / "data" / "ofx-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = CoraOFXImporter(ofx_file)

        transactions = ofx_importer.get_transactions(
            start_date=datetime.date(2024, 8, 25)
        )

        references = sorted([transaction.reference for transaction in transactions])
        expected_references = sorted(
            [
                "69b66fe5-0360-466c-b2e5-08efc1768389",
                "39221b44-f648-44ec-b6d1-1d8eefe54e02",
                "6b01e19f-fc2f-4ea7-b524-6f6c634aea63",
            ]
        )

        assert len(transactions) == 3
        assert references == expected_references


def test_ofx_file_with_multiple_transactions_filter_by_end_date(
    db, request, cora_bank_account, user
):
    ofx_file_path = request.path.parent / "data" / "ofx-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = CoraOFXImporter(ofx_file)

        transactions = ofx_importer.get_transactions(
            end_date=datetime.date(2024, 8, 25)
        )

        references = sorted([transaction.reference for transaction in transactions])
        expected_references = sorted(
            [
                "3825c888-1017-497d-bee2-c0737d5dafc0",
                "63c41497-5e0b-4a3c-ada1-d9abebb0af39",
            ]
        )

        assert len(transactions) == 2
        assert references == expected_references


def test_ofx_file_with_multiple_transactions_filter_by_start_date_and_end_date(
    db, request, cora_bank_account, user
):
    ofx_file_path = request.path.parent / "data" / "ofx-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = CoraOFXImporter(ofx_file)

        transactions = ofx_importer.get_transactions(
            start_date=datetime.date(2024, 8, 24), end_date=datetime.date(2024, 9, 15)
        )

        references = sorted([transaction.reference for transaction in transactions])
        expected_references = sorted(
            [
                "63c41497-5e0b-4a3c-ada1-d9abebb0af39",
                "69b66fe5-0360-466c-b2e5-08efc1768389",
                "39221b44-f648-44ec-b6d1-1d8eefe54e02",
            ]
        )

        assert len(transactions) == 3
        assert references == expected_references


def test_ofx_file_with_credit_card_invoice_pay(
    db,
    request,
    cora_bank_account,
    cora_credit_card_bank_account,
    bank_account_transfer_category,
    user,
):
    ofx_file_path = request.path.parent / "data" / "ofx-one-pay-credit-card-invoice.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = CoraOFXImporter(ofx_file)

        transactions = ofx_importer.get_transactions()

        assert len(transactions) == 2

        assert transactions[0].id is None
        assert valid_uuid(transactions[0].reference)
        assert transactions[0].date == datetime.date(2026, 2, 18)
        assert (
            transactions[0].description
            == "Pagamento da fatura - Cora SCFI - 37.880.206/0001-63"
        )
        assert transactions[0].amount == decimal.Decimal("104.73")
        assert (
            transactions[0].notes
            == f"Transferência entre contas bancárias - 3db4aa9c-af0d-4cf4-ba4f-fc4c3be4deae"
        )
        assert transactions[0].source == "cora.importers.ofx"
        assert transactions[0].bank_account == cora_credit_card_bank_account
        assert transactions[0].created_by == user
        assert transactions[0].category == bank_account_transfer_category

        assert transactions[1].id is None
        assert transactions[1].reference == "3db4aa9c-af0d-4cf4-ba4f-fc4c3be4deae"
        assert transactions[1].date == datetime.date(2026, 2, 18)
        assert (
            transactions[1].description
            == "Pagamento da fatura - Cora SCFI - 37.880.206/0001-63"
        )
        assert transactions[1].amount == decimal.Decimal("-104.73")
        assert (
            transactions[1].notes
            == f"Transferência entre contas bancárias - {transactions[0].reference}"
        )
        assert transactions[1].source == "cora.importers.ofx"
        assert transactions[1].bank_account == cora_bank_account
        assert transactions[1].created_by == user
        assert transactions[1].category == bank_account_transfer_category
