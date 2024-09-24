from django.contrib import admin

from thebook.bookkeeping.models import CashBook, Category, Document, Transaction


@admin.register(CashBook)
class CashBookAdmin(admin.ModelAdmin): ...


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): ...


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin): ...


class DocumentInline(admin.TabularInline):
    model = Document


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "ref",
        "date",
        "description",
        "amount",
        "category",
        "cash_book",
    ]
    list_filter = [
        "cash_book",
        "category",
        "date",
    ]
    inlines = [
        DocumentInline,
    ]

    def ref(self, obj):
        return obj.reference.split("-").pop()
