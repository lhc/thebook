import datetime
import decimal

import jmespath
import requests

from django.conf import settings
from django.contrib.auth import get_user_model

from thebook.bookkeeping.models import BankAccount, Category, Transaction


def calculate_openpix_fee(amount):
    """OpenPix doesn't provide the fee in the Webhook payload so we need to calculate it based on the amount received and the active account plan"""
    fee = 0.0

    if settings.OPENPIX_PLAN == "FIXO":
        fee = -0.85
    elif settings.OPENPIX_PLAN == "PERCENTUAL":
        fee = -1 * round(min(max(0.008 * amount, 0.5), 5), 2)

    return round(decimal.Decimal(fee), 2)


def fetch_transactions(start_date: datetime.date, end_date: datetime.date):
    results = []

    bank_account, _ = BankAccount.objects.get_or_create(
        name=settings.OPENPIX_BANK_ACCOUNT
    )
    bank_fee_category, _ = Category.objects.get_or_create(
        name=settings.BANK_FEE_CATEGORY_NAME
    )
    bank_account_transfer_category, _ = Category.objects.get_or_create(
        name="Transferência entre contas bancárias"
    )
    user = get_user_model().objects.get_or_create_automation_user()

    response = requests.get(
        f"{settings.OPENPIX_API_BASE_URL}/api/v1/transaction",
        params={
            "start": start_date.strftime("%Y-%m-%dT00:00:00Z"),
            "end": end_date.strftime("%Y-%m-%dT00:00:00Z"),
        },
        headers={
            "Authorization": settings.OPENPIX_APP_ID,
        },
    )
    data = response.json()

    transactions = jmespath.search("transactions", data) or []
    for transaction in transactions:
        transaction_id = jmespath.search("endToEndId", transaction)
        if Transaction.objects.filter(reference=transaction_id).exists():
            continue

        transaction_date = datetime.datetime.strptime(
            jmespath.search("time", transaction), "%Y-%m-%dT%H:%M:%S.%fZ"
        ).date()
        transaction_amount = jmespath.search("value", transaction) / 100

        transaction_type = jmespath.search("type", transaction)
        is_bank_account_transfer = transaction_type == "WITHDRAW"
        if is_bank_account_transfer:
            transaction_category = bank_account_transfer_category
            transaction_description = (
                f"Transferência entre contas bancárias - {transaction_id}"
            )
        else:
            transaction_category = None
            payer_name = jmespath.search("payer.name", transaction) or ""
            payer_tax_id = jmespath.search("payer.taxID.taxID", transaction)
            transaction_description = f"{payer_name} - {payer_tax_id}"

        results.append(
            Transaction(
                reference=transaction_id,
                date=transaction_date,
                description=transaction_description,
                amount=decimal.Decimal(str(transaction_amount)),
                bank_account=bank_account,
                category=transaction_category,
                created_by=user,
            )
        )

        if not is_bank_account_transfer:
            transaction_fee_amount = calculate_openpix_fee(transaction_amount)

            results.append(
                Transaction(
                    reference=f"{transaction_id}-T",
                    date=transaction_date,
                    description=f"Taxa OpenPix - {transaction_description}",
                    amount=transaction_fee_amount,
                    bank_account=bank_account,
                    category=bank_fee_category,
                    created_by=user,
                )
            )

    return results
