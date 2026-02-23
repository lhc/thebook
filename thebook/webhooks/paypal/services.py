import datetime
import decimal

import requests

from django.conf import settings
from django.contrib.auth import get_user_model

from thebook.bookkeeping.models import BankAccount, Category, Transaction


def fetch_bank_account_transfer_transactions(
    start_date: datetime.date, end_date: datetime.date
):
    bank_account_transfer_category, _ = Category.objects.get_or_create(
        name="Transferência entre contas bancárias"
    )
    # https://developer.paypal.com/docs/transaction-search/transaction-event-codes/#t04nn-bank-withdrawal-from-paypal-account
    transaction_codes = (
        "T0400",
        "T0403",
    )

    for transaction_type in transaction_codes:
        transactions = fetch_transactions(start_date, end_date, transaction_type)

        references = [transaction.reference for transaction in transactions]
        existing_references = [
            transaction.reference
            for transaction in Transaction.objects.filter(reference__in=references)
        ]

        for transaction in transactions:
            if transaction.reference in existing_references:
                # Do not try to include a transaction already included
                continue

            transaction.description = (
                f"Transferência entre contas bancárias - {transaction.reference}",
            )
            transaction.category = bank_account_transfer_category
            transaction.save()


def fetch_transactions(
    start_date: datetime.date, end_date: datetime.date, transaction_type: str = None
):
    bank_account, _ = BankAccount.objects.get_or_create(name="PayPal")
    user = get_user_model().objects.get_or_create_automation_user()
    response = requests.post(
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        data={
            "grant_type": "client_credentials",
        },
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
    )
    auth_data = response.json()
    access_token = response.json().get("access_token") or ""

    params = {
        "start_date": start_date.strftime("%Y-%m-%dT00:00:00-00:00"),
        "end_date": end_date.strftime("%Y-%m-%dT23:59:59-00:00"),
    }
    if transaction_type is not None:
        params["transaction_type"] = transaction_type

    url = f"{settings.PAYPAL_API_BASE_URL}/v1/reporting/transactions"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
    )

    transactions = []
    transaction_details = response.json().get("transaction_details") or []
    for transaction in transaction_details:
        transaction_status = transaction["transaction_info"]["transaction_status"]
        if transaction_status != "S":
            # https://developer.paypal.com/docs/api/transaction-search/v1/#search_get!in=query&path=transaction_status&t=request
            continue

        raw_date = transaction["transaction_info"]["transaction_initiation_date"]
        utc_transaction_date = datetime.datetime.strptime(
            raw_date, "%Y-%m-%dT%H:%M:%SZ"
        )

        transaction_id = transaction["transaction_info"]["transaction_id"]
        amount = decimal.Decimal(
            transaction["transaction_info"]["transaction_amount"]["value"]
        )

        transactions.append(
            Transaction(
                reference=transaction_id,
                date=utc_transaction_date,
                description=transaction_id,
                amount=amount,
                bank_account=bank_account,
                created_by=user,
            )
        )

    return transactions
