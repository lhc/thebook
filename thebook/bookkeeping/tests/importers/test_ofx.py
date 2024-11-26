import datetime
import decimal
import io

import pytest
from model_bakery import baker

from django.contrib.auth import get_user_model

from thebook.bookkeeping.importers import InvalidOFXFile
from thebook.bookkeeping.importers.constants import UNCATEGORIZED
from thebook.bookkeeping.importers.ofx import OFXImporter
from thebook.bookkeeping.models import CashBook, Category, Transaction


@pytest.fixture
def cash_book():
    return CashBook.objects.create(name="Cash Book 1")


@pytest.fixture
def user():
    return baker.make(get_user_model())


@pytest.fixture
def uncategorized():
    _uncategorized, _ = Category.objects.get_or_create(name=UNCATEGORIZED)
    return _uncategorized


def test_raise_error_when_providing_invalid_ofx_file(db, cash_book, user):
    with pytest.raises(InvalidOFXFile):
        invalid_ofx_file = io.BytesIO(b"NOT_A_VALID_OFX")
        ofx_importer = OFXImporter(invalid_ofx_file, cash_book, user)


def test_cora_ofx_file_with_one_transaction(
    db, request, cash_book, user, uncategorized
):
    ofx_file_path = request.path.parent / "data" / "cora-one-transaction.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)

        transactions = ofx_importer.run()

        assert len(transactions) == 1
        transaction = transactions[0]
        assert transaction.reference == "16b3dab5-d1ca-41e1-87c2-a26920ae70ac"
        assert transaction.date == datetime.date(2024, 8, 19)
        assert transaction.description == "Debito em Conta"
        assert transaction.amount == decimal.Decimal("-2500.50")
        assert transaction.notes == ""
        assert transaction.cash_book == cash_book
        assert transaction.created_by == user
        assert transaction.category == uncategorized


def test_bradesco_ofx_file_with_one_transaction(
    db, request, cash_book, user, uncategorized
):
    ofx_file_path = request.path.parent / "data" / "bradesco-one-transaction.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)

        transactions = ofx_importer.run()

        assert len(transactions) == 1
        transaction = transactions[0]
        assert transaction.reference == "N10235-106"
        assert transaction.date == datetime.date(2024, 8, 2)
        assert transaction.description == "PAGTO ELETRON  COBRANCA ALUGUEL"
        assert transaction.amount == decimal.Decimal("-1798.60")
        assert transaction.notes == ""
        assert transaction.cash_book == cash_book
        assert transaction.created_by == user
        assert transaction.category == uncategorized


def test_ofx_file_with_multiple_transactions(db, request, cash_book, user):
    ofx_file_path = request.path.parent / "data" / "cora-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)

        transactions = ofx_importer.run()

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
        assert Transaction.objects.count() == 5
        assert references == expected_references


def test_bradesco_ofx_file_with_multiple_transactions(db, request, cash_book, user):
    ofx_file_path = request.path.parent / "data" / "bradesco-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)

        transactions = ofx_importer.run()

        assert len(transactions) == 57
        assert Transaction.objects.count() == 57


def test_import_same_ofx_file_twice_will_not_duplicate_transactions(
    db, request, cash_book, user
):
    ofx_file_path = request.path.parent / "data" / "cora-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)
        transactions = ofx_importer.run()
        assert Transaction.objects.all().count() == 5

    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)
        transactions = ofx_importer.run()
        assert Transaction.objects.all().count() == 5


def test_import_ofx_file_that_overlaps_other_already_imported_do_not_duplicate_transactions(
    db, request, cash_book, user
):
    ofx_file_path = request.path.parent / "data" / "cora-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)
        _ = ofx_importer.run()
        assert Transaction.objects.all().count() == 5

    ofx_file_path = (
        request.path.parent / "data" / "cora-multiple-transactions-extended.ofx"
    )
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)
        transactions = ofx_importer.run()
    assert Transaction.objects.all().count() == 7

    references = sorted([transaction.reference for transaction in transactions])
    expected_references = sorted(
        [
            "3825c888-1017-497d-bee2-c0737d5dafc0",
            "63c41497-5e0b-4a3c-ada1-d9abebb0af39",
            "69b66fe5-0360-466c-b2e5-08efc1768389",
            "39221b44-f648-44ec-b6d1-1d8eefe54e02",
            "6b01e19f-fc2f-4ea7-b524-6f6c634aea63",
            "b3950c28-8b64-49ed-bdfb-d83a4df39c96",
            "f5098c7d-81f0-44d9-b0f7-3b8eadee5c34",
        ]
    )

    assert len(transactions) == 7
    assert references == expected_references


def test_ofx_file_with_multiple_transactions_filter_by_start_date(
    db, request, cash_book, user
):
    ofx_file_path = request.path.parent / "data" / "cora-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)

        transactions = ofx_importer.run(start_date=datetime.date(2024, 8, 25))

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
    db, request, cash_book, user
):
    ofx_file_path = request.path.parent / "data" / "cora-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)

        transactions = ofx_importer.run(end_date=datetime.date(2024, 8, 25))

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
    db, request, cash_book, user
):
    ofx_file_path = request.path.parent / "data" / "cora-multiple-transactions.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)

        transactions = ofx_importer.run(
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
    db, request, cash_book, user, ignored_memos, expected_references
):
    ofx_file_path = request.path.parent / "data" / "bradesco-with-memos-to-ignore.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)

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
    db, request, cash_book, user, default_ignored_memos, expected_references, mocker
):
    mocker.patch(
        "thebook.bookkeeping.importers.ofx.DEFAULT_IGNORED_MEMOS", default_ignored_memos
    )
    ofx_file_path = request.path.parent / "data" / "bradesco-with-memos-to-ignore.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)

        transactions = ofx_importer.run()

        references = sorted([transaction.reference for transaction in transactions])
        assert references == sorted(expected_references)


@pytest.mark.xfail(
    reason="current version of ofxparser does not process UTF-8 characters correctly"
)
def test_utf_8_transactions_content(db, request, cash_book, user):
    ofx_file_path = request.path.parent / "data" / "ofx-utf-8.ofx"
    with open(ofx_file_path, "r") as ofx_file:
        ofx_importer = OFXImporter(ofx_file, cash_book, user)

        transactions = ofx_importer.run()

        assert len(transactions) == 1
