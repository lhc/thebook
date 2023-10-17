from django.contrib import admin

from moneybook.bookkeeping.models import Account, Category, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    ...


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    ...


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    ...
