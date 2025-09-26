from django.db import models


class OpenPixWebhookPayload(models.Model):
    thebook_token = models.CharField()
    payload = models.CharField()
    created_at = models.DateTimeField(auto_now_add=True)
