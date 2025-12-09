from django.contrib import admin

from thebook.webhooks.models import OpenPixWebhookPayload, PaypalWebhookPayload


@admin.action(description="Process Webhook Payload")
def process_payload(modeladmin, request, queryset):
    OpenPixWebhookPayload.objects.process_received_payloads()


@admin.register(OpenPixWebhookPayload)
class OpenPixWebhookPayloadAdmin(admin.ModelAdmin):
    actions = [
        process_payload,
    ]
    list_display = [
        "status",
        "created_at",
    ]
    list_filter = [
        "status",
    ]


@admin.register(PaypalWebhookPayload)
class PaypalWebhookPayloadAdmin(admin.ModelAdmin):
    list_display = [
        "status",
        "created_at",
    ]
    list_filter = [
        "status",
    ]
