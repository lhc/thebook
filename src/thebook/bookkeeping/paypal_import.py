import csv
import datetime
import decimal
import io

from django.conf import settings
from django.db import IntegrityError

from thebook.bookkeeping.models import Category, Transaction
from thebook.categorizer import (
    BANK_FEES,
    CASH_BOOK_TRANSFER,
    DONATION,
    MEMBERSHIP_FEE,
    RECURRING_DONATION,
)


def import_transactions(paypal_csvfile, cash_book, user):
    for transaction in get_all_paypal_transactions(paypal_csvfile, cash_book, user):
        try:
            transaction.save()
        except IntegrityError:
            # Avoid importing same transaction more than once
            pass


def get_all_paypal_transactions(paypal_csvfile, cash_book, user):
    uncategorized, _ = Category.objects.get_or_create(
        name=settings.BOOKKEEPING_UNCATEGORIZED
    )
    donation, _ = Category.objects.get_or_create(name=DONATION)
    recurring_donation, _ = Category.objects.get_or_create(name=RECURRING_DONATION)
    bank_fees, _ = Category.objects.get_or_create(name=BANK_FEES)
    cash_book_transfer, _ = Category.objects.get_or_create(name=CASH_BOOK_TRANSFER)
    membership_fee, _ = Category.objects.get_or_create(name=MEMBERSHIP_FEE)

    csv_content = paypal_csvfile.read().decode()
    if csv_content[0] == "\ufeff":
        csv_content = csv_content[1:]

    reader = csv.DictReader(io.StringIO(csv_content))
    for paypal_transaction in reader:
        transactions_to_create = []

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
            transactions_to_create.append(
                Transaction(
                    reference=transaction_reference,
                    date=transaction_date,
                    description=description,
                    amount=transaction_amount,
                    cash_book=cash_book,
                    category=cash_book_transfer,
                    created_by=user,
                )
            )
        elif (
            transaction_type == "Conversão de moeda em geral"
            and transaction_currency == "BRL"
        ):
            # Marcio is the only payment in USD
            transactions_to_create.append(
                Transaction(
                    reference=transaction_reference,
                    date=transaction_date,
                    description="Mensalidade LHC - USD50 - Marcio Paduan Donadio",
                    amount=transaction_amount,
                    cash_book=cash_book,
                    category=membership_fee,
                    created_by=user,
                )
            )
        elif transaction_type == "Pagamento de doação":
            transactions_to_create.append(
                Transaction(
                    reference=transaction_reference,
                    date=transaction_date,
                    description=f"Doação Recebida de {transaction_name}",
                    amount=transaction_amount,
                    cash_book=cash_book,
                    category=donation,
                    created_by=user,
                )
            )
            transactions_to_create.append(
                Transaction(
                    reference=transaction_reference,
                    date=transaction_date,
                    description=f"Taxa Intermediação - Doação Recebida de {transaction_name}",
                    amount=transaction_tax,
                    cash_book=cash_book,
                    category=bank_fees,
                    created_by=user,
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
                membership_fee
                if transaction_amount in current_membership_fees
                else recurring_donation
            )

            transactions_to_create.append(
                Transaction(
                    reference=transaction_reference,
                    date=transaction_date,
                    description=f"{recurring_fee_type} - {transaction_name}",
                    amount=transaction_amount,
                    cash_book=cash_book,
                    category=category,
                    created_by=user,
                )
            )
            transactions_to_create.append(
                Transaction(
                    reference=transaction_reference,
                    date=transaction_date,
                    description=f"Taxa Intermediação - {recurring_fee_type} - {transaction_name}",
                    amount=transaction_tax,
                    cash_book=cash_book,
                    category=bank_fees,
                    created_by=user,
                )
            )

        for paypal_transaction in transactions_to_create:
            yield paypal_transaction
