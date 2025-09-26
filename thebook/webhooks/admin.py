from django.contrib import admin

from thebook.webhooks.models import OpenPixWebhookPayload


@admin.register(OpenPixWebhookPayload)
class OpenPixWebhookPayloadAdmin(admin.ModelAdmin): ...
