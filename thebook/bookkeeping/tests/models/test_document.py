import datetime
import re

import pytest
from model_bakery import baker

from django.contrib.contenttypes.models import ContentType

from thebook.bookkeeping.models import (
    BankAccount,
    Document,
    Transaction,
    document_upload_path,
)


@pytest.fixture
def document():
    bank_account = BankAccount(name="test_bank_account", slug="test_bank_account")
    transaction = Transaction(bank_account=bank_account)
    return Document(transaction=transaction)


def test_document_upload_path_generate_different_results_even_if_filename_is_the_same(
    document,
):
    filename = "invoice.pdf"

    first_file = document_upload_path(document, filename)
    second_file = document_upload_path(document, filename)

    assert first_file != second_file


@pytest.mark.parametrize("bank_account_slug", ["bank_account_1", "bank_account_2"])
def test_document_upload_path_put_file_inside_bank_account_slug_directory(
    bank_account_slug,
):
    bank_account = BankAccount(name=bank_account_slug, slug=bank_account_slug)
    transaction = Transaction(bank_account=bank_account)
    document = Document(transaction=transaction)

    filename = "invoice.pdf"

    upload_path = document_upload_path(document, filename)

    assert upload_path.parts[0] == bank_account_slug


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


@pytest.mark.parametrize("model_class", [Transaction, BankAccount])
def test_document_can_be_linked_to_any_models(db, model_class):
    content_object = baker.make(model_class)
    contenty_type = ContentType.objects.get_for_model(model_class)

    document = Document.objects.create(
        document_date=datetime.date(2026, 2, 11),
        content_object=content_object,
    )

    assert document.content_type == contenty_type
    assert document.object_id == content_object.id
    assert document.content_object == content_object
