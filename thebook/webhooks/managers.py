import calendar
import datetime

from django.db import models


class OpenPixWebhookPayloadManager(models.Manager):

    def process_received_payloads(self):
        from thebook.webhooks.models import ProcessingStatus

        for payload in self.filter(status=ProcessingStatus.RECEIVED):
            payload.process()


class PayPalWebhookPayloadManager(models.Manager):

    def process_received_payloads(self):
        from thebook.webhooks.models import ProcessingStatus

        for payload in self.filter(status=ProcessingStatus.RECEIVED):
            payload.process()


def fetch_transactions(start_date: datetime.date, end_date: datetime.date):
    bank_account, _ = BankAccount.objects.get_or_create(name="PayPal")
    user = get_user_model().objects.get_or_create_automation_user()
    bank_account_transfer_category, _ = Category.objects.get_or_create(
        name="Transferência entre contas bancárias"
    )

    response = requests.post(
        f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
        data={
            "grant_type": "client_credentials",
        },
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
    )
    auth_data = response.json()
    access_token = response.json().get("access_token") or ""

    # https://developer.paypal.com/docs/transaction-search/transaction-event-codes/#t04nn-bank-withdrawal-from-paypal-account
    transaction_codes = (
        "T0400",
        "T0403",
    )
    params = {
        "start_date": start_date.strftime("%Y-%m-%dT00:00:00-00:00"),
        "end_date": end_date.strftime("%Y-%m-%dT00:00:00-00:00"),
    }
    for transaction_code in transaction_codes:
        params["transaction_type"] = transaction_code
        url = f"{settings.PAYPAL_API_BASE_URL}/v1/reporting/transactions"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )

        transaction_details = response.json.get("transaction_details") or []
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

            Transaction.objects.create(
                reference=transaction_id,
                date=utc_transaction_date,
                description=f"Transferência entre contas bancárias - {transaction_id}",
                amount=amount,
                bank_account=bank_account,
                category=bank_account_transfer_category,
                created_by=user,
            )
