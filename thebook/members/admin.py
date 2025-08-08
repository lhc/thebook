from django.contrib import admin

from thebook.members.models import (
    Member,
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


@admin.register(ReceivableFee)
class ReceivableFeeAdmin(admin.ModelAdmin):
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
    ]


@admin.register(ReceivableFeeTransactionMatchRule)
class ReceivableFeeTransactionMatchRuleAdmin(admin.ModelAdmin):
    list_display = [
        "membership",
        "pattern",
    ]
