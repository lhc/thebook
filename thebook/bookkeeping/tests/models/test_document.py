import datetime
import re

import pytest
from model_bakery import baker

from thebook.bookkeeping.models import (
    BankAccount,
    Document,
    Transaction,
    document_upload_path,
)


@pytest.fixture
def document():
    cash_book = BankAccount(name="test_cash_book", slug="test_cash_book")
    transaction = Transaction(cash_book=cash_book)
    return Document(transaction=transaction)


def test_document_upload_path_generate_different_results_even_if_filename_is_the_same(
    document,
):
    filename = "invoice.pdf"

    first_file = document_upload_path(document, filename)
    second_file = document_upload_path(document, filename)

    assert first_file != second_file


@pytest.mark.parametrize("cash_book_slug", ["cash_book_1", "cash_book_2"])
def test_document_upload_path_put_file_inside_cash_book_slug_directory(
    cash_book_slug,
):
    cash_book = BankAccount(name=cash_book_slug, slug=cash_book_slug)
    transaction = Transaction(cash_book=cash_book)
    document = Document(transaction=transaction)

    filename = "invoice.pdf"

    upload_path = document_upload_path(document, filename)

    assert upload_path.parts[0] == cash_book_slug


def test_document_upload_path_create_uuid_name_for_file(document):
    UUID_PATTERN = r"^[0-9a-fA-F]{32}$"
    filename = "invoice"

    upload_path = document_upload_path(document, filename)

    assert re.match(UUID_PATTERN, upload_path.name)


@pytest.mark.parametrize("file_extension", [".pdf", ".docx"])
def test_document_upload_path_keep_file_extension(document, file_extension):
    UUID_PATTERN_WITH_FILE_EXTENSION = rf"^[0-9a-fA-F]{{32}}{file_extension}$"

    filename = f"invoice{file_extension}"

    upload_path = document_upload_path(document, filename)

    assert re.match(UUID_PATTERN_WITH_FILE_EXTENSION, upload_path.name)


def test_document_without_date_gets_transaction_date_by_default(db):
    transaction = baker.make(Transaction, date=datetime.date(2023, 2, 13))
    document = Document(transaction=transaction)

    document.save()

    assert document.document_date == transaction.date


@pytest.mark.parametrize("notes", ["", None])
def test_document_representation_with_empty_notes(notes):
    document = Document(
        document_date=datetime.date(2025, 2, 13),
        notes=notes,
    )
    assert str(document) == "<Document without notes>"


def test_document_representation_with_empty_notes_and_transaction(db):
    transaction = baker.make(
        Transaction,
        description="Transaction Description",
    )
    document = Document(
        document_date=datetime.date(2025, 2, 13),
        transaction=transaction,
    )
    assert str(document) == "<Transaction Description>"


def test_document_representation():
    document = Document(
        document_date=datetime.date(2023, 2, 13),
        notes="Document Notes",
    )
    assert str(document) == "<Document Notes>"
