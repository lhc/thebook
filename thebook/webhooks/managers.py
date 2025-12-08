import calendar
import datetime

from django.db import models


class OpenPixWebhookPayloadManager(models.Manager):

    def process_received_payloads(self):
        from thebook.webhooks.models import ProcessingStatus

        for payload in self.filter(status=ProcessingStatus.RECEIVED):
            payload.process()
