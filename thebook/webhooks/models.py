import datetime
import json

import jmespath

from django.contrib.auth import get_user_model
from django.db import DatabaseError, models, transaction
from django.utils.functional import classproperty
from django.utils.translation import gettext as _

from thebook.bookkeeping.models import CashBook, Transaction
from thebook.webhooks.managers import OpenPixWebhookPayloadManager


class ProcessingStatus:
    RECEIVED = 1
    PROCESSED = 2

    @classproperty
    def choices(cls):
        return (
            (cls.RECEIVED, _("Received")),
            (cls.PROCESSED, _("Processed")),
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

    def process(self, cash_book=None, user=None):
        if self.status == ProcessingStatus.PROCESSED:
            return

        if cash_book is None:
            cash_book = CashBook.objects.get(name="OpenPix")

        if user is None:
            user = get_user_model().objects.get(email="renne@rocha.dev.br")

        payload = json.loads(self.payload)

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
                cash_book=cash_book,
                created_by=user,
            )
            Transaction.objects.create(
                reference="T" + reference,
                date=utc_transaction_date,
                description="Taxa OpenPix - " + description,
                amount=fee,
                cash_book=cash_book,
                created_by=user,
            )

            self.status = ProcessingStatus.PROCESSED
            self.save()
