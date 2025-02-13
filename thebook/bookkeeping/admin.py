from django.contrib import admin

from thebook.bookkeeping.models import CashBook, Category, Document, Transaction


@admin.action(description="Mark selected transactions as donations")
def make_donation(modeladmin, request, queryset):
    DONATION = "Doação"
    donation, _ = Category.objects.get_or_create(name=DONATION)
    queryset.update(category=donation)


@admin.action(description="Mark selected transactions as membership fee")
def make_membership_fee(modeladmin, request, queryset):
    MEMBERSHIP_FEE = "Mensalidade"
    membership_fee, _ = Category.objects.get_or_create(name=MEMBERSHIP_FEE)
    queryset.update(category=membership_fee)


@admin.action(description="Mark selected transactions as cash book transfer")
def make_cash_book_transfer(modeladmin, request, queryset):
    CASH_BOOK_TRANSFER = "Transferência entre contas"
    cash_book_transfer, _ = Category.objects.get_or_create(name=CASH_BOOK_TRANSFER)
    queryset.update(category=cash_book_transfer)


@admin.action(description="Automatically categorize transactions")
def categorize_transactions(modeladmin, request, queryset):
    for transaction in queryset:
        transaction.categorize()


@admin.register(CashBook)
class CashBookAdmin(admin.ModelAdmin): ...


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): ...


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "document_date",
    ]
    list_filter = [
        "document_date",
    ]


class DocumentInline(admin.TabularInline):
    model = Document


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    actions = [
        make_donation,
        make_membership_fee,
        make_cash_book_transfer,
        categorize_transactions,
    ]
    list_display = [
        "ref",
        "date",
        "description",
        "amount",
        "category",
        "cash_book",
        "tag_list",
    ]
    list_filter = [
        "cash_book",
        "category",
        "date",
    ]
    list_select_related = [
        "cash_book",
        "category",
    ]
    inlines = [
        DocumentInline,
    ]

    def ref(self, obj):
        return obj.reference.split("-").pop()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tags")

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())
