from django.contrib import admin

from thebook.bookkeeping.models import CashBook, Category, Document, Transaction


@admin.action(description="Mark selected transactions as donations")
def make_donation(modeladmin, request, queryset):
    DONATION = "Doação"
    donation, _ = Category.objects.get_or_create(name=DONATION)
    queryset.update(category=donation)


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
    actions = [make_donation]
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
