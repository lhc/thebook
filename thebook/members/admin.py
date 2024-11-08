from django.contrib import admin

from thebook.members.models import Membership, Member, ReceivableFee


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin): ...


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin): ...


@admin.register(ReceivableFee)
class ReceivableFeeAdmin(admin.ModelAdmin): ...
