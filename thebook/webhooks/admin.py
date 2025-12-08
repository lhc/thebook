from django.contrib import admin

from thebook.webhooks.models import OpenPixWebhookPayload


@admin.action(description="Process Webhook Payload")
def process_payload(modeladmin, request, queryset):
    for payload in queryset:
        payload.process()


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
