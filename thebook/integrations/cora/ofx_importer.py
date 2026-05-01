import csv
import datetime
import decimal
import io
import uuid

import structlog

from django.conf import settings
from django.contrib.auth import get_user_model

from thebook.bookkeeping.models import BankAccount, Category, Transaction
from thebook.utils.ofxparse import OfxParser

logger = structlog.get_logger(__name__)


class InvalidCoraOFXFile(Exception): ...


class CoraOFXImporter:
    def __init__(self, ofx_file):
        try:
            self.ofx_parser = OfxParser.parse(ofx_file)
        except (UnicodeDecodeError, TypeError, ValueError) as exc:
            logger.error(
                "CoraOFXImporter.__init__.invalid_cora_ofx_file",
            )
            raise InvalidCoraOFXFile() from exc

        self.cora_bank_account, _ = BankAccount.objects.get_or_create(
            name=settings.CORA_BANK_ACCOUNT
        )
        self.cora_credit_card_bank_account, _ = BankAccount.objects.get_or_create(
            name=settings.CORA_CREDIT_CARD_BANK_ACCOUNT
        )
        self.bank_account_transfer_category, _ = Category.objects.get_or_create(
            name="Transferência entre contas bancárias"
        )
        self.user = get_user_model().objects.get_or_create_automation_user()

    def _within_date_range(self, transaction_date, start_date, end_date):
        date_rules = []
        if start_date is not None:
            date_rules.append(transaction_date >= start_date)
        if end_date is not None:
            date_rules.append(transaction_date <= end_date)
        return all(date_rules)

    def get_transactions(
        self, start_date=None, end_date=None, exclude_existing: bool = True
    ):
        logger.info(
            "CoraOFXImporter.get_transactions.start",
            start_date=start_date,
            end_date=end_date,
            exclude_existing=exclude_existing,
        )

        transactions = []

        ofx_transactions = self.ofx_parser.account.statement.transactions
        for transaction in ofx_transactions:
            if (
                exclude_existing
                and Transaction.objects.filter(reference=transaction.id).exists()
            ):
                continue

            transaction_date = transaction.date.date()
            if not self._within_date_range(transaction_date, start_date, end_date):
                continue

            transaction_notes = ""
            transaction_category = None

            if "Pagamento da fatura" in transaction.memo:
                # Cora Credit Card invoice doesn't provide the information when the invoice
                # is paid, so we need to add it based on the payment that is provided in
                # the checking account OFX report
                bank_account_transfer_reference = uuid.uuid4()

                transaction_notes = notes = (
                    f"Transferência entre contas bancárias - {bank_account_transfer_reference}"
                )
                transaction_category = self.bank_account_transfer_category

                transactions.append(
                    Transaction(
                        reference=bank_account_transfer_reference,
                        date=transaction_date,
                        description=transaction.memo,
                        amount=-1 * transaction.amount,
                        notes=f"Transferência entre contas bancárias - {transaction.id}",
                        bank_account=self.cora_credit_card_bank_account,
                        category=transaction_category,
                        source="cora-ofx-importer",
                        created_by=self.user,
                    )
                )

            transactions.append(
                Transaction(
                    reference=transaction.id,
                    date=transaction_date,
                    description=transaction.memo,
                    notes=transaction_notes,
                    amount=transaction.amount,
                    bank_account=self.cora_bank_account,
                    category=transaction_category,
                    source="cora-ofx-importer",
                    created_by=self.user,
                )
            )

        logger.info(
            "CoraOFXImporter.get_transactions.completed",
            num_transactions=len(transactions),
        )
        return transactions
