from django import forms
from django.contrib import admin

from thebook.members.models import (
    Member,
    MemberMetadata,
    Membership,
    ReceivableFee,
    ReceivableFeeTransactionMatchRule,
)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "membership_fee_amount",
        "payment_interval",
        "start_date",
        "active",
    ]
    list_select_related = [
        "member",
    ]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user__email",
        "has_key",
        "membership__active",
    ]
    list_select_related = [
        "membership",
        "user",
    ]


@admin.register(MemberMetadata)
class MemberMetadataAdmin(admin.ModelAdmin): ...


@admin.register(ReceivableFee)
class ReceivableFeeAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        "transaction",
    ]
    list_display = [
        "membership__member",
        "start_date",
        "due_date",
        "amount",
        "status",
        "due_date",
    ]
    list_filter = [
        "status",
        "membership__member__name",
    ]
    list_select_related = [
        "membership",
        "membership__member",
    ]


@admin.register(ReceivableFeeTransactionMatchRule)
class ReceivableFeeTransactionMatchRuleAdmin(admin.ModelAdmin):
    list_display = [
        "membership",
        "pattern",
    ]
