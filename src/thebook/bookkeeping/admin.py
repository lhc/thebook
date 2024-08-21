from django.contrib import admin

from thebook.bookkeeping.models import CashBook, Category, Transaction


@admin.register(CashBook)
class CashBookAdmin(admin.ModelAdmin): ...


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): ...


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "date",
        "description",
        "amount",
        "cash_book",
    ]
    list_filter = [
        "cash_book",
        "category",
    ]
