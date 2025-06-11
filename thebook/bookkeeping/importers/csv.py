import csv
import datetime
import decimal
import io
import uuid

from django.db import IntegrityError

from thebook.bookkeeping.importers.constants import (
    ACCOUNTANT,
    BANK_FEES,
    BANK_INCOME,
    CASH_BOOK_TRANSFER,
    DONATION,
    MEMBERSHIP_FEE,
    RECURRING,
    RECURRING_DONATION,
    TAXES,
)
from thebook.bookkeeping.models import Category, Transaction


def get_categories():
    accountant, _ = Category.objects.get_or_create(name=ACCOUNTANT)
    bank_fees, _ = Category.objects.get_or_create(name=BANK_FEES)
    bank_income, _ = Category.objects.get_or_create(name=BANK_INCOME)
    cash_book_transfer, _ = Category.objects.get_or_create(name=CASH_BOOK_TRANSFER)
    donation, _ = Category.objects.get_or_create(name=DONATION)
    membership_fee, _ = Category.objects.get_or_create(name=MEMBERSHIP_FEE)
    recurring, _ = Category.objects.get_or_create(name=RECURRING)
    recurring_donation, _ = Category.objects.get_or_create(name=RECURRING_DONATION)
    taxes, _ = Category.objects.get_or_create(name=TAXES)

    return {
        ACCOUNTANT: accountant,
        BANK_FEES: bank_fees,
        BANK_INCOME: bank_income,
        CASH_BOOK_TRANSFER: cash_book_transfer,
        DONATION: donation,
        MEMBERSHIP_FEE: membership_fee,
        RECURRING: recurring,
        RECURRING_DONATION: recurring_donation,
        TAXES: taxes,
    }


class CSVImporter:
    new_transactions = []

    def __init__(self, transactions_file, cash_book, user):
        self.categories = get_categories()

        self.transactions_file = transactions_file
        self.cash_book = cash_book
        self.user = user

    def run(self, start_date=None, end_date=None, ignored_memos=None):
        csv_content = self.transactions_file.read().decode()

        # PayPal export adds this character in the beginning of the exported file
        # breaking Python CSV reader library, so we need to get rid of this character
        # if it exists
        if csv_content[0] == "\ufeff":
            csv_content = csv_content[1:]

        reader = csv.DictReader(io.StringIO(csv_content))
        for paypal_transaction in reader:
            transaction_date = datetime.datetime.strptime(
                paypal_transaction["Data"], "%d/%m/%Y"
            ).date()
            transaction_amount = decimal.Decimal(
                paypal_transaction["Bruto "].replace(".", "").replace(",", ".")
            )
            transaction_currency = paypal_transaction["Moeda"]
            transaction_tax = decimal.Decimal(
                paypal_transaction["Tarifa "].replace(".", "").replace(",", ".")
            )
            transaction_reference = paypal_transaction["ID da transação"]

            transaction_type = paypal_transaction["Descrição"]
            transaction_name = paypal_transaction["Nome"]

            if transaction_type == "Retirada geral - Conta bancária":
                transaction_bank_name = paypal_transaction["Nome do banco"]
                description = f"{transaction_type} - {transaction_bank_name}"
                self.new_transactions.append(
                    Transaction(
                        reference=transaction_reference,
                        date=transaction_date,
                        description=description,
                        amount=transaction_amount,
                        cash_book=self.cash_book,
                        category=self.categories[CASH_BOOK_TRANSFER],
                        created_by=self.user,
                    )
                )
            elif (
                transaction_type == "Conversão de moeda em geral"
                and transaction_currency == "BRL"
            ):
                # Marcio is the only payment in USD
                self.new_transactions.append(
                    Transaction(
                        reference=transaction_reference,
                        date=transaction_date,
                        description="Mensalidade LHC - USD50 - Marcio Paduan Donadio",
                        amount=transaction_amount,
                        cash_book=self.cash_book,
                        category=self.categories[MEMBERSHIP_FEE],
                        created_by=self.user,
                    )
                )
            elif transaction_type == "Pagamento de doação":
                self.new_transactions.append(
                    Transaction(
                        reference=transaction_reference,
                        date=transaction_date,
                        description=f"Doação Recebida de {transaction_name}",
                        amount=transaction_amount,
                        cash_book=self.cash_book,
                        category=self.categories[DONATION],
                        created_by=self.user,
                    )
                )
                self.new_transactions.append(
                    Transaction(
                        reference=f"{transaction_reference}T",
                        date=transaction_date,
                        description=f"Taxa Intermediação - Doação Recebida de {transaction_name}",
                        amount=transaction_tax,
                        cash_book=self.cash_book,
                        category=self.categories[BANK_FEES],
                        created_by=self.user,
                    )
                )
            elif transaction_type == "Pagamento de assinaturas":
                if transaction_currency == "USD":
                    # We don't process USD recurring here
                    continue

                current_membership_fees = (75, 85, 110)
                recurring_fee_type = (
                    "Mensalidade"
                    if transaction_amount in current_membership_fees
                    else "Contribuição"
                )
                category = (
                    self.categories[MEMBERSHIP_FEE]
                    if transaction_amount in current_membership_fees
                    else self.categories[RECURRING_DONATION]
                )
                self.new_transactions.append(
                    Transaction(
                        reference=transaction_reference,
                        date=transaction_date,
                        description=f"{recurring_fee_type} - {transaction_name}",
                        amount=transaction_amount,
                        cash_book=self.cash_book,
                        category=category,
                        created_by=self.user,
                    )
                )
                self.new_transactions.append(
                    Transaction(
                        reference=f"{transaction_reference}T",
                        date=transaction_date,
                        description=f"Taxa Intermediação - {recurring_fee_type} - {transaction_name}",
                        amount=transaction_tax,
                        cash_book=self.cash_book,
                        category=self.categories[BANK_FEES],
                        created_by=self.user,
                    )
                )
            else:
                if transaction_currency == "USD":
                    # We don't process USD recurring here
                    continue

                self.new_transactions.append(
                    Transaction(
                        reference=transaction_reference,
                        date=transaction_date,
                        description=f"{transaction_type} - {transaction_name}",
                        amount=transaction_amount,
                        cash_book=self.cash_book,
                        created_by=self.user,
                    )
                )
                self.new_transactions.append(
                    Transaction(
                        reference=f"{transaction_reference}T",
                        date=transaction_date,
                        description=f"Taxa Intermediação - {transaction_type} - {transaction_name}",
                        amount=transaction_tax,
                        cash_book=self.cash_book,
                        category=self.categories[BANK_FEES],
                        created_by=self.user,
                    )
                )

        Transaction.objects.bulk_create(
            self.new_transactions,
            update_conflicts=True,
            update_fields=["description", "amount"],
            unique_fields=["reference"],
        )


class CSVCoraCreditCardImporter:
    def __init__(self, transactions_file, cash_book, user):
        self.categories = get_categories()
        self.new_transactions = []

        self.transactions_file = transactions_file
        self.cash_book = cash_book
        self.user = user

    def run(self, start_date=None, end_date=None, ignored_memos=None):
        csv_content = self.transactions_file.read().decode()

        reader = csv.DictReader(io.StringIO(csv_content))
        for transaction in reader:
            transaction_date = datetime.datetime.strptime(
                transaction["Data"], "%d/%m/%Y"
            ).date()
            transaction_amount = -1 * decimal.Decimal(
                transaction["Valor"].replace(".", "").replace(",", ".")
            )
            transaction_notes = "".join(
                [
                    transaction["Moeda"],
                    transaction["Valor Moeda Local"],
                ]
            )

            self.new_transactions.append(
                Transaction(
                    reference=uuid.uuid4(),
                    date=transaction_date,
                    description=transaction["Descrição"].strip(),
                    amount=transaction_amount,
                    notes=transaction_notes,
                    cash_book=self.cash_book,
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
