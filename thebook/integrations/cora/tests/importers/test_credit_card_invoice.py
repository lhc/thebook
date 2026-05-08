import datetime
import decimal
from uuid import UUID

import pytest
from model_bakery import baker

from django.conf import settings
from django.contrib.auth import get_user_model

from thebook.bookkeeping.models import BankAccount, Transaction
from thebook.integrations.cora.constants import CORA_CREDIT_CARD_BANK_ACCOUNT
from thebook.integrations.cora.importers.credit_card_invoice import (
    CoraCreditCardInvoiceImporter,
    InvalidCoraCreditCardInvoice,
)


def valid_uuid(value):
    try:
        uuid_obj = UUID(str(value))
    except ValueError:
        return False
    return str(uuid_obj) == str(value)


class TestCoraCreditCardInvoiceImporter:

    @pytest.fixture
    def cora_credit_card_bank_account(self, db):
        bank_account, _ = BankAccount.objects.get_or_create(
            name=CORA_CREDIT_CARD_BANK_ACCOUNT
        )
        return bank_account

    @pytest.fixture
    def user(self, db):
        return get_user_model().objects.get_or_create_automation_user()

    def test_valid_but_empty_invoice_file(
        self, db, request, cora_credit_card_bank_account, user
    ):
        invoice_file_path = (
            request.path.parent / "data" / "credit-card-invoice-empty.csv"
        )
        with open(invoice_file_path, "rb") as invoice_file:
            importer = CoraCreditCardInvoiceImporter(invoice_file)
            transactions = importer.get_transactions()
            assert transactions == []

    def test_invalid_invoice_file(self, db, request):
        invoice_file_path = (
            request.path.parent / "data" / "credit-card-invoice-invalid.csv"
        )
        with open(invoice_file_path, "rb") as invoice_file:
            importer = CoraCreditCardInvoiceImporter(invoice_file)

            with pytest.raises(InvalidCoraCreditCardInvoice):
                transactions = importer.get_transactions()

    def test_one_transaction_excluding_existing_false(
        self, db, request, cora_credit_card_bank_account, user
    ):
        invoice_file_path = (
            request.path.parent / "data" / "credit-card-invoice-one-transaction.csv"
        )
        with open(invoice_file_path, "rb") as invoice_file:
            importer = CoraCreditCardInvoiceImporter(invoice_file)
            transactions = importer.get_transactions()

            assert len(transactions) == 1

            assert transactions[0].id is None
            assert valid_uuid(transactions[0].reference)
            assert transactions[0].date == datetime.date(2026, 2, 21)
            assert transactions[0].description == "BACKBLAZE INC"
            assert transactions[0].amount == decimal.Decimal("-8.91")
            assert transactions[0].notes == "BACKBLAZE INC - USD1,50"
            assert transactions[0].bank_account == cora_credit_card_bank_account
            assert transactions[0].source == "cora.importers.credit_card_invoice"
            assert transactions[0].created_by == user

    def test_one_transaction_excluding_existing_true(
        self, db, request, cora_credit_card_bank_account
    ):
        baker.make(
            Transaction,
            date=datetime.date(2026, 2, 21),
            description="BACKBLAZE INC",
            amount=decimal.Decimal("-8.91"),
            bank_account=cora_credit_card_bank_account,
        )

        invoice_file_path = (
            request.path.parent / "data" / "credit-card-invoice-one-transaction.csv"
        )
        with open(invoice_file_path, "rb") as invoice_file:
            importer = CoraCreditCardInvoiceImporter(invoice_file)
            transactions = importer.get_transactions(exclude_existing=True)
            assert len(transactions) == 0

    def test_one_transaction_from_different_bank_account(
        self, db, request, cora_credit_card_bank_account
    ):
        baker.make(
            Transaction,
            date=datetime.date(2026, 2, 21),
            description="BACKBLAZE INC",
            amount=decimal.Decimal("-8.91"),
        )

        invoice_file_path = (
            request.path.parent / "data" / "credit-card-invoice-one-transaction.csv"
        )
        with open(invoice_file_path, "rb") as invoice_file:
            importer = CoraCreditCardInvoiceImporter(invoice_file)
            transactions = importer.get_transactions(exclude_existing=True)
            assert len(transactions) == 1

    def test_two_transactions_excluding_existing_true(
        self, db, request, cora_credit_card_bank_account
    ):
        baker.make(
            Transaction,
            date=datetime.date(2026, 2, 21),
            description="BACKBLAZE INC",
            amount=decimal.Decimal("-8.91"),
            bank_account=cora_credit_card_bank_account,
        )

        invoice_file_path = (
            request.path.parent / "data" / "credit-card-invoice-two-transactions.csv"
        )
        with open(invoice_file_path, "rb") as invoice_file:
            importer = CoraCreditCardInvoiceImporter(invoice_file)
            transactions = importer.get_transactions(exclude_existing=True)

            assert len(transactions) == 1
            assert transactions[0].description == "VULTR BY CONSTANT"

    def test_two_transactions_excluding_existing_false(
        self, db, request, cora_credit_card_bank_account
    ):
        baker.make(
            Transaction,
            date=datetime.date(2026, 2, 21),
            description="BACKBLAZE INC",
            amount=decimal.Decimal("-8.91"),
            bank_account=cora_credit_card_bank_account,
        )

        invoice_file_path = (
            request.path.parent / "data" / "credit-card-invoice-two-transactions.csv"
        )
        with open(invoice_file_path, "rb") as invoice_file:
            importer = CoraCreditCardInvoiceImporter(invoice_file)
            transactions = importer.get_transactions(exclude_existing=False)

            assert len(transactions) == 2
            assert sorted(
                [transaction.description for transaction in transactions]
            ) == ["BACKBLAZE INC", "VULTR BY CONSTANT"]

    @pytest.mark.parametrize(
        "start_date,end_date,expected",
        [
            (None, None, ["FIRST", "SECOND", "THIRD", "FOURTH"]),
            (datetime.date(2026, 3, 20), None, ["SECOND", "THIRD", "FOURTH"]),
            (datetime.date(2026, 3, 21), None, ["SECOND", "THIRD", "FOURTH"]),
            (
                datetime.date(2026, 3, 20),
                datetime.date(2026, 4, 10),
                ["SECOND", "THIRD"],
            ),
            (None, datetime.date(2026, 4, 10), ["FIRST", "SECOND", "THIRD"]),
            (
                datetime.date(2026, 4, 1),
                datetime.date(2026, 4, 21),
                ["THIRD", "FOURTH"],
            ),
            (
                datetime.date(2026, 4, 1),
                datetime.date(2026, 4, 22),
                ["THIRD", "FOURTH"],
            ),
        ],
    )
    def test_transactions_filtered_by_date_range(
        self, db, request, start_date, end_date, expected
    ):
        invoice_file_path = (
            request.path.parent
            / "data"
            / "credit-card-invoice-multiple-transactions.csv"
        )
        with open(invoice_file_path, "rb") as invoice_file:
            importer = CoraCreditCardInvoiceImporter(invoice_file)
            transactions = importer.get_transactions(
                start_date=start_date, end_date=end_date
            )

            assert len(transactions) == len(expected)
            assert sorted(
                [transaction.description for transaction in transactions]
            ) == sorted(expected)
