import logging

from django.utils.translation import gettext as _

from thebook.bookkeeping.importers.csv import CSVImporter
from thebook.bookkeeping.importers.ofx import OFXImporter

logger = logging.getLogger(__name__)


class ImportTransactionsError(Exception):
    ...


def import_transactions(transactions_file, file_type, cash_book, user):
    importers = {
        "csv": CSVImporter,
        "ofx": OFXImporter,
    }
    importer = importers.get(file_type) or None
    if importer is None:
        raise ImportTransactionsError(
            _("Unable to find a suitable file importer for this file.")
        )

    try:
        importer(transactions_file, cash_book, user).run()
    except Exception as err:
        logger.exception(err)
        raise ImportTransactionsError(_('Something wrong happened during file import.'))
