from django.contrib import admin

from thebook.members.models import Membership, Member, ReceivableFee


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "membership_fee_amount",
        "payment_interval",
        "active",
    ]
    list_select_related = [
        "member",
    ]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "has_key",
        "membership__active",
    ]
    list_select_related = [
        "membership",
    ]


@admin.register(ReceivableFee)
class ReceivableFeeAdmin(admin.ModelAdmin): ...
