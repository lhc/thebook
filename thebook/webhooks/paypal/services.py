import datetime
import decimal

import jmespath
import requests

from django.conf import settings
from django.contrib.auth import get_user_model

from thebook.bookkeeping.models import BankAccount, Category, Transaction


def _get_paypal_access_token():
    response = requests.post(
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        data={
            "grant_type": "client_credentials",
        },
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
    )
    auth_data = response.json()
    return response.json().get("access_token") or ""


def fetch_transactions(start_date: datetime.date, end_date: datetime.date):
    results = []

    bank_account, _ = BankAccount.objects.get_or_create(
        name=settings.PAYPAL_BANK_ACCOUNT
    )
    bank_fee_category, _ = Category.objects.get_or_create(
        name=settings.BANK_FEE_CATEGORY_NAME
    )
    bank_account_transfer_category, _ = Category.objects.get_or_create(
        name="Transferência entre contas bancárias"
    )

    user = get_user_model().objects.get_or_create_automation_user()
    access_token = _get_paypal_access_token()

    params = {
        "start_date": start_date.strftime("%Y-%m-%dT00:00:00-00:00"),
        "end_date": end_date.strftime("%Y-%m-%dT23:59:59-00:00"),
    }
    url = f"{settings.PAYPAL_API_BASE_URL}/v1/reporting/transactions"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
    )
    data = response.json()

    for transaction in jmespath.search("transaction_details", data) or []:
        transaction_status = jmespath.search(
            "transaction_info.transaction_status", transaction
        )
        if transaction_status != "S":
            # https://developer.paypal.com/docs/api/transaction-search/v1/#search_get!in=query&path=transaction_status&t=request
            continue

        transaction_id = jmespath.search("transaction_info.transaction_id", transaction)
        if Transaction.objects.filter(reference=transaction_id).exists():
            continue

        transaction_currency_code = jmespath.search(
            "transaction_info.transaction_amount.currency_code", transaction
        )
        if transaction_currency_code == "USD":
            continue
        transaction_amount = decimal.Decimal(
            jmespath.search("transaction_info.transaction_amount.value", transaction)
        )

        raw_date = jmespath.search(
            "transaction_info.transaction_initiation_date", transaction
        )
        transaction_date = datetime.datetime.strptime(
            raw_date, "%Y-%m-%dT%H:%M:%SZ"
        ).date()
        transaction_fee_amount = decimal.Decimal(
            jmespath.search("transaction_info.fee_amount.value", transaction) or "0"
        )

        transaction_type = jmespath.search(
            "transaction_info.transaction_event_code", transaction
        )
        is_bank_account_transfer = transaction_type in ("T0400", "T0403")
        if is_bank_account_transfer:
            transaction_category = bank_account_transfer_category
            transaction_description = (
                f"Transferência entre contas bancárias - {transaction_id}"
            )
        else:
            transaction_category = None
            transaction_description = jmespath.search(
                "transaction_info.transaction_subject", transaction
            )

        results.append(
            Transaction(
                reference=transaction_id,
                date=transaction_date,
                description=transaction_description,
                amount=transaction_amount + transaction_fee_amount,
                bank_account=bank_account,
                category=transaction_category,
                created_by=user,
            )
        )

        if not is_bank_account_transfer:
            results.append(
                Transaction(
                    reference=f"{transaction_id}-T",
                    date=transaction_date,
                    description=f"Taxa Paypal - {transaction_description}",
                    amount=transaction_fee_amount,
                    bank_account=bank_account,
                    category=bank_fee_category,
                    created_by=user,
                )
            )

    return results
