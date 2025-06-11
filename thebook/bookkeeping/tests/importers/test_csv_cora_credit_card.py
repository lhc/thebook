import datetime
import decimal
import io

import pytest
from model_bakery import baker

from django.contrib.auth import get_user_model

from thebook.bookkeeping.importers import InvalidOFXFile
from thebook.bookkeeping.importers.csv import CSVCoraCreditCardImporter
from thebook.bookkeeping.models import CashBook, Category, Transaction


@pytest.fixture
def cash_book():
    return CashBook.objects.create(name="Cash Book 1")


@pytest.fixture
def user():
    return baker.make(get_user_model())


@pytest.mark.xfail(reason="need to pass the correct data to the importer")
def test_cora_csv_credit_card_file_with_one_transaction(
    mocker, db, request, cash_book, user
):
    mocker.patch(
        "thebook.bookkeeping.importers.csv.uuid.uuid4",
        return_value="16b3dab5-d1ca-41e1-87c2-a26920ae70ac",
    )

    csv_file_path = (
        request.path.parent / "data" / "cora-credit-card-one-transaction.csv"
    )
    with open(csv_file_path, "r") as csv_file:
        csv_importer = CSVCoraCreditCardImporter(csv_file, cash_book, user)

        transactions = csv_importer.run()

        assert len(transactions) == 1
        transaction = transactions[0]
        assert transaction.reference == "16b3dab5-d1ca-41e1-87c2-a26920ae70ac"
        assert transaction.date == datetime.date(2024, 9, 25)
        assert transaction.description == "MIGADU.COM EMAIL SRVC."
        assert transaction.amount == decimal.Decimal("-112.83")
        assert transaction.notes == "USD19,00"
        assert transaction.cash_book == cash_book
        assert transaction.created_by == user
        assert transaction.category is None
