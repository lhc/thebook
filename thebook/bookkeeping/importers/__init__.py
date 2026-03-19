import logging

from django.utils.translation import gettext as _

from thebook.bookkeeping.importers.csv import CSVImporter
from thebook.bookkeeping.importers.ofx import OFXImporter
from thebook.bookkeeping.models import Transaction
from thebook.integrations.cora.credit_card_invoice import CoraCreditCardInvoiceImporter

logger = logging.getLogger(__name__)


class ImportTransactionsError(Exception): ...


class InvalidOFXFile(Exception):
    default_message = "Not a valid OFX File"

    def __init__(self, message=None):
        super().__init__(message or self.default_message)


def import_transactions(
    transactions_file, file_type, bank_account, user, start_date, end_date
):
    importers = {
        "csv": CSVImporter,
        "csv_cora_credit_card": CoraCreditCardInvoiceImporter,
        "ofx": OFXImporter,
    }
    importer = importers.get(file_type) or None
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
        else:
            importer(transactions_file, bank_account, user).run(start_date, end_date)
    except Exception as err:
        logger.exception(err)
        raise ImportTransactionsError(_("Something wrong happened during file import."))
