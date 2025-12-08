from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext as _


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
