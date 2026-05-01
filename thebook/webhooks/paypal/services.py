import datetime
import decimal
import json

import jmespath
import requests
import structlog

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from thebook.bookkeeping.models import BankAccount, Category, Transaction
from thebook.webhooks.constants import ProcessingStatus

logger = structlog.get_logger(__name__)


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


def _get_subscription(billing_agreement_id, access_token=None):
    if access_token is None:
        access_token = _get_paypal_access_token()
    response = requests.get(
        f"{settings.PAYPAL_API_BASE_URL}/v1/billing/subscriptions/{billing_agreement_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    subscription = response.json()
    return subscription


def _extract_amount(payload):
    currency = jmespath.search("resource.amount.currency", payload)

    if currency == "BRL":
        amount = float(jmespath.search("resource.amount.total", payload))
    elif currency == "USD":
        amount = float(jmespath.search("resource.receivable_amount.value", payload))

    return amount


def _extract_transaction_fee(payload):
    currency = jmespath.search("resource.transaction_fee.currency", payload)

    if currency == "BRL":
        transaction_fee = -1 * float(
            jmespath.search("resource.transaction_fee.value", payload)
        )
    elif currency == "USD":
        transaction_fee = None

    return transaction_fee


def process_webhook_payload(webhook):
    from thebook.webhooks.models import PaypalWebhookPayload

    logger.info("webhooks.paypal.services.process_webhook_payload.start", id=webhook.id)

    if webhook.status == ProcessingStatus.PROCESSED:
        logger.info(
            "webhooks.paypal.services.process_webhook_payload.already_processed",
            id=webhook.id,
        )
        return

    bank_account, _ = BankAccount.objects.get_or_create(
        name=settings.PAYPAL_BANK_ACCOUNT
    )
    user = get_user_model().objects.get_or_create_automation_user()

    try:
        payload = json.loads(webhook.payload)
    except json.decoder.JSONDecodeError:
        logger.warning(
            "webhooks.paypal.services.process_webhook_payload.unparsable_event",
            id=webhook.id,
        )
        webhook.status = ProcessingStatus.UNPARSABLE
        webhook.internal_notes = (
            "webhooks.paypal.services.process_webhook_payload.unparsable_event"
        )
        webhook.save()
        return

    reference = jmespath.search("resource.id", payload)
    if Transaction.objects.filter(reference=reference).exists():
        logger.info(
            "webhooks.paypal.services.process_webhook_payload.duplicated_transaction",
            id=webhook.id,
        )
        webhook.status = ProcessingStatus.DUPLICATED
        webhook.internal_notes = (
            "webhooks.paypal.services.process_webhook_payload.duplicated_transaction",
        )
        webhook.save()
        return

    webhook.webhook_id = payload.get("id") or ""
    if PaypalWebhookPayload.objects.filter(webhook_id=webhook.webhook_id).exists():
        logger.warning(
            "webhooks.paypal.services.process_webhook_payload.duplicated_event",
            id=webhook.id,
        )
        webhook.status = ProcessingStatus.DUPLICATED
        webhook.internal_notes = "webhooks.paypal.duplicated_event"
        webhook.save()
        return

    event_type = payload.get("event_type")
    if event_type != "PAYMENT.SALE.COMPLETED":
        logger.warning(
            "webhooks.paypal.services.process_webhook_payload.unparsable_event",
            id=webhook.id,
        )
        webhook.status = ProcessingStatus.UNPARSABLE
        webhook.internal_notes = "webhooks.paypal.unparsable_event"
        webhook.save()
        return

    billing_agreement_id = (
        jmespath.search("resource.billing_agreement_id", payload) or ""
    )
    if not billing_agreement_id:
        logger.warning(
            "webhooks.paypal.services.process_webhook_payload.missing_billing_agreement_id",
            id=webhook.id,
        )
        webhook.status = ProcessingStatus.UNPARSABLE
        webhook.internal_notes = "webhooks.paypal.missing_billing_agreement_id"
        webhook.save()
        return

    subscription = _get_subscription(billing_agreement_id)
    logger.info(
        "webhooks.paypal.services.process_webhook_payload.subscription",
        id=webhook.id,
        subscription=subscription,
    )

    amount = _extract_amount(payload)
    transaction_fee = _extract_transaction_fee(payload)

    fee = -1 * float(jmespath.search("resource.transaction_fee.value", payload))

    paid_at = jmespath.search("resource.create_time", payload)
    utc_transaction_date = datetime.datetime.strptime(paid_at, "%Y-%m-%dT%H:%M:%SZ")

    given_name = jmespath.search("subscriber.name.given_name", subscription) or ""
    surname = jmespath.search("subscriber.name.surname", subscription) or ""
    full_name = " ".join([given_name, surname]).strip()
    payer_id = jmespath.search("subscriber.payer_id", subscription) or ""

    description_parts = (full_name, payer_id)
    currency = jmespath.search("resource.amount.currency", payload)
    if currency == "USD":
        usd_amount = jmespath.search("resource.amount.total", payload)
        description_parts = (full_name, f"USD {usd_amount}", payer_id)

    description = " - ".join([part for part in description_parts if part])

    with transaction.atomic():
        bank_fee_category, _ = Category.objects.get_or_create(name="Tarifas Bancárias")

        Transaction.objects.create(
            reference=reference,
            date=utc_transaction_date,
            description=description,
            amount=amount,
            bank_account=bank_account,
            source="paypal-webhook",
            created_by=user,
        )

        if transaction_fee is not None:
            Transaction.objects.create(
                reference=f"{reference}-T",
                date=utc_transaction_date,
                description="Taxa PayPal - " + description,
                amount=fee,
                bank_account=bank_account,
                category=bank_fee_category,
                source="paypal-webhook",
                created_by=user,
            )

        webhook.status = ProcessingStatus.PROCESSED
        webhook.save()

    logger.info(
        "webhooks.paypal.services.process_webhook_payload.finished", id=webhook.id
    )
