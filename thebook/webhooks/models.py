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

from thebook.bookkeeping.models import BankAccount, Category, Transaction
from thebook.webhooks.constants import ProcessingStatus
from thebook.webhooks.managers import (
    OpenPixWebhookPayloadManager,
    PayPalWebhookPayloadManager,
)
from thebook.webhooks.openpix.services import calculate_openpix_fee
from thebook.webhooks.paypal.services import process_webhook_payload

logger = structlog.get_logger(__name__)


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
            self.internal_notes = "webhooks.openpix.jsondecodeerror"
            self.save()
            return

        transaction_type = jmespath.search("event", payload)
        if transaction_type != "OPENPIX:TRANSACTION_RECEIVED":
            self.status = ProcessingStatus.UNPARSABLE
            self.internal_notes = "webhooks.paypal.unparsable_event"
            self.save()
            return

        amount = jmespath.search("pix.charge.value || pix.value", payload) / 100
        openpix_fee = calculate_openpix_fee(amount, transaction_type)

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
            bank_fee_category, _ = Category.objects.get_or_create(
                name="Tarifas Bancárias"
            )

            Transaction.objects.create(
                reference=reference,
                date=utc_transaction_date,
                description=description,
                amount=amount,
                bank_account=bank_account,
                source="openpix-webhook",
                created_by=user,
            )
            Transaction.objects.create(
                reference=f"{reference}-T",
                date=utc_transaction_date,
                description="Taxa OpenPix - " + description,
                amount=openpix_fee,
                bank_account=bank_account,
                category=bank_fee_category,
                source="openpix-webhook",
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
    webhook_id = models.CharField()
    internal_notes = models.CharField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PayPalWebhookPayloadManager()

    def process(self):
        process_webhook_payload(self)
