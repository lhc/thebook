import logging

from django.conf import settings
from django.utils.translation import gettext as _

from thebook.bookkeeping.importers.csv import CSVImporter
from thebook.bookkeeping.models import BankAccount, Transaction
from thebook.integrations.bradesco.importers.ofx import OFXImporter
from thebook.integrations.cora.constants import CORA_BANK_ACCOUNT
from thebook.integrations.cora.importers.credit_card_invoice import (
    CoraCreditCardInvoiceImporter,
)
from thebook.integrations.cora.importers.ofx import CoraOFXImporter

logger = logging.getLogger(__name__)


class ImportTransactionsError(Exception): ...


class InvalidOFXFile(Exception):
    default_message = "Not a valid OFX File"

    def __init__(self, message=None):
        super().__init__(message or self.default_message)


def import_transactions(
    transactions_file, file_type, bank_account, user, start_date, end_date
):
    cora_bank_account, _ = BankAccount.objects.get_or_create(name=CORA_BANK_ACCOUNT)

    importer = None
    if file_type == "csv":
        importer = CSVImporter
    elif file_type == "csv_cora_credit_card":
        importer = CoraCreditCardInvoiceImporter
    elif file_type == "ofx":
        if bank_account == cora_bank_account:
            importer = CoraOFXImporter
        else:
            importer = OFXImporter

    if importer is None:
        raise ImportTransactionsError(
            _("Unable to find a suitable file importer for this file.")
        )

    try:
        if file_type == "csv_cora_credit_card":
            csv_importer = importer(transactions_file)
            transactions = csv_importer.get_transactions(
                start_date, end_date, exclude_existing=True
            )
            Transaction.objects.bulk_create(
                transactions,
                update_conflicts=True,
                update_fields=["description", "amount"],
                unique_fields=["reference"],
            )
        elif file_type == "ofx" and bank_account == cora_bank_account:
            ofx_importer = importer(transactions_file)
            transactions = ofx_importer.get_transactions(
                start_date, end_date, exclude_existing=True
            )
            Transaction.objects.bulk_create(
                transactions,
                update_conflicts=True,
                update_fields=["description", "amount"],
                unique_fields=["reference"],
            )
        else:
            importer(transactions_file, bank_account, user).run(start_date, end_date)
    except Exception as err:
        logger.exception(err)
        raise ImportTransactionsError(_("Something wrong happened during file import."))
