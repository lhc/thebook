import csv
import datetime
import decimal
import io
import uuid

import structlog

from django.conf import settings
from django.contrib.auth import get_user_model

from thebook.bookkeeping.models import BankAccount, Transaction

logger = structlog.get_logger(__name__)


class InvalidCoraCreditCardInvoice(Exception): ...


class CoraCreditCardInvoiceImporter:

    _expected_field_names = set(
        [
            "Data",
            "Nome no Cartão",
            "Final do Cartão",
            "Categoria",
            "Descrição",
            "Moeda",
            "Valor Moeda Local",
            "Conversão Dólar na Data",
            "Valor em Dólar",
            "IOF",
            "Valor",
        ]
    )  # Fields that must appear in the file content to be considered a valid Cora Credit Card Invoice file

    def __init__(self, invoice_file):
        self.invoice_file = invoice_file
        self.bank_account, _ = BankAccount.objects.get_or_create(
            name=settings.CORA_CREDIT_CARD_BANK_ACCOUNT
        )
        self.user = get_user_model().objects.get_or_create_automation_user()

    def _within_range(
        self,
        transaction_date: datetime.date,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> bool:
        checks = []
        if start_date is not None:
            checks.append(transaction_date >= start_date)
        if end_date is not None:
            checks.append(transaction_date <= end_date)
        return all(checks)

    def get_transactions(
        self,
        start_date: datetime.date = None,
        end_date: datetime.date = None,
        exclude_existing: bool = True,
    ) -> list[Transaction]:
        logger.info(
            "CoraCreditCardInvoiceImporter.get_transactions.start",
            start_date=start_date,
            end_date=end_date,
            exclude_existing=exclude_existing,
        )

        transactions = []

        csv_content = self.invoice_file.read().decode()
        reader = csv.DictReader(io.StringIO(csv_content))

        if set(reader.fieldnames) != self._expected_field_names:
            logger.error(
                "CoraCreditCardInvoiceImporter.get_transactions.invalid_cora_credit_card_invoice",
                start_date=start_date,
                end_date=end_date,
                exclude_existing=exclude_existing,
            )
            raise InvalidCoraCreditCardInvoice

        for transaction in reader:
            transaction_date = datetime.datetime.strptime(
                transaction["Data"], "%d/%m/%Y"
            ).date()
            if not self._within_range(transaction_date, start_date, end_date):
                continue

            amount = -1 * decimal.Decimal(
                transaction["Valor"].replace(".", "").replace(",", ".")
            )
            description = transaction["Descrição"].strip()
            currency = transaction["Moeda"]
            amount_in_local_currency = transaction["Valor Moeda Local"]

            if (
                exclude_existing
                and Transaction.objects.filter(
                    date=transaction_date,
                    description=description,
                    amount=amount,
                    bank_account=self.bank_account,
                ).exists()
            ):
                continue

            transactions.append(
                Transaction(
                    reference=uuid.uuid4(),
                    date=transaction_date,
                    description=description,
                    amount=amount,
                    notes=f"{description} - {currency}{amount_in_local_currency}",
                    bank_account=self.bank_account,
                    source="cora-credit-card-invoice-importer",
                    created_by=self.user,
                )
            )

        logger.info(
            "CoraCreditCardInvoiceImporter.get_transactions.completed",
            num_transactions=len(transactions),
        )
        return transactions
