import datetime
import decimal

import requests

from django.conf import settings
from django.contrib.auth import get_user_model

from thebook.bookkeeping.models import BankAccount, Category, Transaction


def fetch_transactions(start_date: datetime.date, end_date: datetime.date):
    bank_account, _ = BankAccount.objects.get_or_create(
        name=settings.OPENPIX_BANK_ACCOUNT
    )
    user = get_user_model().objects.get_or_create_automation_user()
    bank_account_transfer_category, _ = Category.objects.get_or_create(
        name="Transferência entre contas bancárias"
    )

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

    transactions = jmespath("transactions", data)
    for transaction in transactions:
        transaction_type = jmespath.search("type", transaction)
        if transaction_type != "WITHDRAW":
            continue

        transaction_id = jmespath.search("endToEndId", transaction)
        transaction_date = datetime.datetime.strptime(
            jmespath.search("time", transaction), "%Y-%m-%dT%H:%M:%S.%fZ"
        ).date()
        transaction_amount = -1 * jmespath.search("value", transaction) / 100

        utc_transaction_date = datetime.datetime.strptime(
            raw_date, "%Y-%m-%dT%H:%M:%SZ"
        )

        Transaction.objects.create(
            reference=transaction_id,
            date=transaction_date,
            description=f"Transferência entre contas bancárias - {transaction_id}",
            amount=transaction_amount,
            bank_account=bank_account,
            category=bank_account_transfer_category,
            created_by=user,
        )
