import datetime
import json

import jmespath
import requests
import structlog

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DatabaseError, models, transaction
from django.utils.functional import classproperty
from django.utils.translation import gettext as _

from thebook.bookkeeping.models import BankAccount, Transaction
from thebook.webhooks.managers import (
    OpenPixWebhookPayloadManager,
    PayPalWebhookPayloadManager,
)

logger = structlog.get_logger(__name__)


class ProcessingStatus:
    RECEIVED = 1
    PROCESSED = 2
    UNPARSABLE = 3

    @classproperty
    def choices(cls):
        return (
            (cls.RECEIVED, _("Received")),
            (cls.PROCESSED, _("Processed")),
            (cls.UNPARSABLE, _("Unparsable")),
        )


class OpenPixWebhookPayload(models.Model):
    thebook_token = models.CharField()
    payload = models.CharField()
    status = models.IntegerField(
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.RECEIVED,
        verbose_name=_("Processing Status"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OpenPixWebhookPayloadManager()

    def process(self, bank_account=None, user=None):
        if self.status == ProcessingStatus.PROCESSED:
            return

        if bank_account is None:
            bank_account, _ = BankAccount.objects.get_or_create(name="OpenPix")

        if user is None:
            user = get_user_model().objects.get_or_create_automation_user()

        try:
            payload = json.loads(self.payload)
        except json.decoder.JSONDecodeError:
            self.status = ProcessingStatus.UNPARSABLE
            self.save()
            return

        if jmespath.search("event", payload) != "OPENPIX:TRANSACTION_RECEIVED":
            return

        amount = jmespath.search("pix.charge.value || pix.value", payload) / 100

        raw_fee = jmespath.search("pix.charge.fee", payload)
        if not raw_fee:
            raw_fee = round(amount * 100 * 0.0080, 2)
        fee = (-1 * raw_fee) / 100

        # Original in UTC time
        paid_at = jmespath.search("pix.charge.paidAt || pix.time", payload)
        utc_transaction_date = datetime.datetime.strptime(
            paid_at, "%Y-%m-%dT%H:%M:%S.%fZ"
        )

        comment = jmespath.search("pix.charge.comment", payload) or ""
        payer_name = (
            jmespath.search("pix.charge.payer.name || pix.payer.name", payload) or ""
        )
        payer_tax_id = (
            jmespath.search(
                "pix.charge.payer.taxID.taxID || pix.payer.taxID.taxID", payload
            )
            or ""
        )
        description = " - ".join(
            [part for part in (comment, payer_name, payer_tax_id) if part]
        )

        reference = jmespath.search(
            "pix.charge.transactionID || pix.transactionID", payload
        )

        with transaction.atomic():
            Transaction.objects.create(
                reference=reference,
                date=utc_transaction_date,
                description=description,
                amount=amount,
                bank_account=bank_account,
                created_by=user,
            )
            Transaction.objects.create(
                reference="T" + reference,
                date=utc_transaction_date,
                description="Taxa OpenPix - " + description,
                amount=fee,
                bank_account=bank_account,
                created_by=user,
            )

            self.status = ProcessingStatus.PROCESSED
            self.save()


class PaypalWebhookPayload(models.Model):
    paypal_transmission_time = models.CharField()
    paypal_auth_version = models.CharField()
    paypal_cert_url = models.CharField()
    paypal_auth_algo = models.CharField()
    paypal_transmission_sig = models.CharField()
    paypal_transmission_id = models.CharField()
    correlation_id = models.CharField()

    payload = models.CharField()
    status = models.IntegerField(
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.RECEIVED,
        verbose_name=_("Processing Status"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PayPalWebhookPayloadManager()

    def process(self, bank_account=None, user=None):
        if self.status == ProcessingStatus.PROCESSED:
            return

        if bank_account is None:
            bank_account = BankAccount.objects.get(name="PayPal")

        if user is None:
            user = get_user_model().objects.get_or_create_automation_user()

        payload = json.loads(self.payload)

        event_type = payload.get("event_type")
        if event_type != "PAYMENT.SALE.COMPLETED":
            return

        billing_agreement_id = (
            jmespath.search("resource.billing_agreement_id", payload) or ""
        )
        if not billing_agreement_id:
            return

        response = requests.post(
            f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
            data={
                "grant_type": "client_credentials",
            },
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        )
        auth_data = response.json()
        logger.info(f"{auth_data=}")
        logger.info(f"{settings.PAYPAL_CLIENT_ID=}")
        logger.info(f"{settings.PAYPAL_CLIENT_SECRET=}")
        logger.info(f"{settings.PAYPAL_API_BASE_URL=}")
        logger.info(f"{billing_agreement_id=}")

        access_token = response.json().get("access_token") or ""

        response = requests.get(
            f"{settings.PAYPAL_API_BASE_URL}/v1/billing/subscriptions/{billing_agreement_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        subscription = response.json()

        amount = float(jmespath.search("resource.amount.total", payload))
        fee = -1 * float(jmespath.search("resource.transaction_fee.value", payload))
        paid_at = jmespath.search("resource.create_time", payload)
        utc_transaction_date = datetime.datetime.strptime(paid_at, "%Y-%m-%dT%H:%M:%SZ")

        logger.info(f"{subscription=}")
        given_name = jmespath.search("subscriber.name.given_name", subscription) or ""
        surname = jmespath.search("subscriber.name.surname", subscription) or ""
        full_name = " ".join([given_name, surname]).strip()
        payer_id = jmespath.search("subscriber.name.payer_id", subscription) or ""

        description = " - ".join([part for part in (payer_id, full_name) if part])
        logger.info(f"{description=}")

        reference = jmespath.search("resource.id", payload)

        with transaction.atomic():
            Transaction.objects.create(
                reference=reference,
                date=utc_transaction_date,
                description=description,
                amount=amount,
                bank_account=bank_account,
                created_by=user,
            )
            Transaction.objects.create(
                reference="T" + reference,
                date=utc_transaction_date,
                description="Taxa PayPal - " + description,
                amount=fee,
                bank_account=bank_account,
                created_by=user,
            )

            self.status = ProcessingStatus.PROCESSED
            self.save()
