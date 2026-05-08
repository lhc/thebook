import datetime
import decimal
import io

import pytest
from model_bakery import baker

from django.contrib.auth import get_user_model

from thebook.bookkeeping.importers import InvalidOFXFile
from thebook.bookkeeping.models import BankAccount, Category, Transaction
from thebook.integrations.bradesco.importers.ofx import OFXImporter


@pytest.fixture
def bank_account():
    return BankAccount.objects.create(name="Bank Account 1")


@pytest.fixture
def user():
    return baker.make(get_user_model())


def test_raise_error_when_providing_invalid_ofx_file(db, bank_account, user):
    with pytest.raises(InvalidOFXFile):
        invalid_ofx_file = io.BytesIO(b"NOT_A_VALID_OFX")
        ofx_importer = OFXImporter(invalid_ofx_file, bank_account, user)


def test_bradesco_ofx_file_with_one_transaction(db, request, bank_account, user):
    ofx_file_path = request.path.parent / "data" / "ofx-one-transaction.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, bank_account, user)

        transactions = ofx_importer.run()

        assert len(transactions) == 1
        transaction = transactions[0]
        assert transaction.reference == "N10235-106"
        assert transaction.date == datetime.date(2024, 8, 2)
        assert transaction.description == "PAGTO ELETRON  COBRANCA ALUGUEL"
        assert transaction.amount == decimal.Decimal("-1798.60")
        assert transaction.notes == ""
        assert transaction.bank_account == bank_account
        assert transaction.created_by == user
        assert transaction.category is None


def test_bradesco_ofx_file_with_multiple_transactions(db, request, bank_account, user):
    ofx_file_path = request.path.parent / "data" / "ofx-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, bank_account, user)

        transactions = ofx_importer.run()

        assert len(transactions) == 57
        assert Transaction.objects.count() == 57


@pytest.mark.parametrize(
    "ignored_memos,expected_references",
    [
        (
            [
                "TRANSFERENCIA PIX",
                "APLIC.INVEST FACIL",
            ],
            [
                "N1013F-701353",
                "N1016B-13",
                "N10597-1561275",
            ],
        ),
        (
            [
                "TRANSFERENCIA PIX REM: CPS1 TECNOLOGIA LTDA  01/08",
                "TARIFA BANCARIA LIQUIDACAO QRCODE PIX",
            ],
            [
                "N10155-1517476",
                "N10181-1023199",
                "N10597-1561275",
            ],
        ),
    ],
)
def test_ofx_file_ignoring_transactions_by_exact_description(
    db, request, bank_account, user, ignored_memos, expected_references
):
    ofx_file_path = request.path.parent / "data" / "ofx-with-memos-to-ignore.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, bank_account, user)

        transactions = ofx_importer.run(ignored_memos=ignored_memos)

        references = sorted([transaction.reference for transaction in transactions])
        assert references == sorted(expected_references)


@pytest.mark.parametrize(
    "default_ignored_memos,expected_references",
    [
        (
            [
                "TRANSFERENCIA PIX",
                "APLIC.INVEST FACIL",
            ],
            [
                "N1013F-701353",
                "N1016B-13",
                "N10597-1561275",
            ],
        ),
        (
            [
                "TRANSFERENCIA PIX REM: CPS1 TECNOLOGIA LTDA  01/08",
                "TARIFA BANCARIA LIQUIDACAO QRCODE PIX",
            ],
            [
                "N10155-1517476",
                "N10181-1023199",
                "N10597-1561275",
            ],
        ),
    ],
)
def test_use_default_list_of_ignored_descriptions_if_not_provided(
    db, request, bank_account, user, default_ignored_memos, expected_references, mocker
):
    mocker.patch(
        "thebook.integrations.bradesco.importers.ofx.DEFAULT_IGNORED_MEMOS",
        default_ignored_memos,
    )
    ofx_file_path = request.path.parent / "data" / "ofx-with-memos-to-ignore.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, bank_account, user)

        transactions = ofx_importer.run()

        references = sorted([transaction.reference for transaction in transactions])
        assert references == sorted(expected_references)


@pytest.mark.xfail(
    reason="current version of ofxparser does not process UTF-8 characters correctly"
)
def test_utf_8_transactions_content(db, request, bank_account, user):
    ofx_file_path = request.path.parent / "data" / "ofx-utf-8.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, bank_account, user)

        transactions = ofx_importer.run()

        assert len(transactions) == 1
