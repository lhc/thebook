from datetime import date, datetime
from decimal import Decimal

from ofxparse import OfxParser
from ofxtools.Parser import OFXTree

from django.conf import settings
from django.db import IntegrityError

from thebook.bookkeeping.importers.constants import UNCATEGORIZED
from thebook.bookkeeping.models import Category, Transaction

# Default List of transactions descriptions that we
# can ignore and not insert into the system
DEFAULT_IGNORED_MEMOS = [
    "APLIC.INVEST FACIL",
    "APLIC.AUTOM.INVESTFACIL*",
    "RESGATE INVEST FACIL",
    "RESG.AUTOM.INVEST FACIL*",
]


class OFXImporter:
    def __init__(self, transactions_file, cash_book, user):
        self.uncategorized, _ = Category.objects.get_or_create(name=UNCATEGORIZED)
        self.new_transactions = []

        self.transactions_file = transactions_file
        self.cash_book = cash_book
        self.user = user

        try:
            self.ofx_parser = OfxParser.parse(self.transactions_file)
        except (UnicodeDecodeError, TypeError, ValueError):
            from thebook.bookkeeping.importers import InvalidOFXFile

            raise InvalidOFXFile()

    def _get_reference(self, fitid, checknum):
        return "-".join([field for field in (fitid, checknum) if field])

    def _within_date_range(self, transaction_date, start_date, end_date):
        date_rules = []
        if start_date is not None:
            date_rules.append(transaction_date >= start_date)
        if end_date is not None:
            date_rules.append(transaction_date <= end_date)
        return all(date_rules)

    def run(self, start_date=None, end_date=None, ignored_memos=None):
        if ignored_memos is None:
            ignored_memos = DEFAULT_IGNORED_MEMOS

        ofx_transactions = self.ofx_parser.account.statement.transactions
        for transaction in ofx_transactions:
            if transaction.memo in ignored_memos:
                continue

            transaction_date = transaction.date.date()
            if not self._within_date_range(transaction_date, start_date, end_date):
                continue

            self.new_transactions.append(
                Transaction(
                    reference=self._get_reference(transaction.id, transaction.checknum),
                    date=transaction_date,
                    description=transaction.memo,
                    amount=transaction.amount,
                    cash_book=self.cash_book,
                    category=self.uncategorized,
                    created_by=self.user,
                )
            )

        transactions = Transaction.objects.bulk_create(
            self.new_transactions,
            update_conflicts=True,
            update_fields=["description", "amount"],
            unique_fields=["reference"],
        )

        return transactions
