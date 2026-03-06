from django.contrib import admin, messages
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from thebook.webhooks.models import OpenPixWebhookPayload, PaypalWebhookPayload


@admin.register(OpenPixWebhookPayload)
class OpenPixWebhookPayloadAdmin(admin.ModelAdmin):
    actions = [
        "process_payload",
    ]
    list_display = [
        "status",
        "created_at",
    ]
    list_filter = [
        "status",
    ]

    @admin.action(description=_("Process selected webhook payloads"))
    def process_payload(self, request, queryset):
        for processed, payload in enumerate(queryset, start=1):
            payload.process()

        self.message_user(
            request,
            ngettext(
                "%(processed)d webhook payload processed.",
                "%(processed)d webhook payloads processed.",
                processed,
            )
            % {"processed": processed},
            messages.SUCCESS,
        )


@admin.register(PaypalWebhookPayload)
class PaypalWebhookPayloadAdmin(admin.ModelAdmin):
    actions = [
        "process_payload",
    ]
    list_display = [
        "status",
        "created_at",
    ]
    list_filter = [
        "status",
    ]

    @admin.action(description=_("Process selected webhook payloads"))
    def process_payload(self, request, queryset):
        for processed, payload in enumerate(queryset, start=1):
            payload.process()

        self.message_user(
            request,
            ngettext(
                "%(processed)d webhook payload processed.",
                "%(processed)d webhook payloads processed.",
                processed,
            )
            % {"processed": processed},
            messages.SUCCESS,
        )
