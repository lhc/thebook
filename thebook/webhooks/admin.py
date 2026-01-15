from django.contrib import admin

from thebook.webhooks.models import OpenPixWebhookPayload, PaypalWebhookPayload


@admin.action(description="Process OpenPix Webhook Payload")
def process_openpix_payload(modeladmin, request, queryset):
    OpenPixWebhookPayload.objects.process_received_payloads()


@admin.action(description="Process PayPal Webhook Payload")
def process_paypal_payload(modeladmin, request, queryset):
    PaypalWebhookPayload.objects.process_received_payloads()


@admin.register(OpenPixWebhookPayload)
class OpenPixWebhookPayloadAdmin(admin.ModelAdmin):
    actions = [
        process_openpix_payload,
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
    actions = [
        process_paypal_payload,
    ]
    list_display = [
        "status",
        "created_at",
    ]
    list_filter = [
        "status",
    ]
