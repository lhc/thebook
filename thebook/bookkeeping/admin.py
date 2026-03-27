from django.contrib import admin

from thebook.bookkeeping.models import (
    BankAccount,
    Category,
    CategoryMatchRule,
    Document,
    Transaction,
)


@admin.action(description="Mark selected transactions as donations")
def make_donation(modeladmin, request, queryset):
    DONATION = "Doação"
    donation, _ = Category.objects.get_or_create(name=DONATION)
    queryset.update(category=donation)


@admin.action(description="Mark selected transactions as membership fee")
def make_membership_fee(modeladmin, request, queryset):
    MEMBERSHIP_FEE = "Contribuição Associativa"
    membership_fee, _ = Category.objects.get_or_create(name=MEMBERSHIP_FEE)
    queryset.update(category=membership_fee)


@admin.action(description="Mark selected transactions as cash book transfer")
def make_bank_account_transfer(modeladmin, request, queryset):
    BANK_ACCOUNT_TRANSFER = "Transferência entre contas bancárias"
    bank_account_transfer, _ = Category.objects.get_or_create(
        name=BANK_ACCOUNT_TRANSFER
    )
    queryset.update(category=bank_account_transfer)


@admin.action(description="Automatically categorize transactions")
def categorize_transactions(modeladmin, request, queryset):
    for transaction in queryset:
        transaction.categorize()


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin): ...


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): ...


@admin.register(CategoryMatchRule)
class CategoryMatchRuleAdmin(admin.ModelAdmin):
    list_display = [
        "priority",
        "pattern",
        "category",
    ]


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
        make_bank_account_transfer,
        categorize_transactions,
    ]
    list_display = [
        "ref",
        "date",
        "description",
        "amount",
        "category",
        "bank_account",
        "fornecedor",
        "tag_list",
    ]
    list_filter = [
        "bank_account",
        "category",
        "date",
        "fornecedor",
    ]
    list_select_related = [
        "bank_account",
        "category",
        "fornecedor",
    ]
    inlines = [
        DocumentInline,
    ]
    search_fields = [
        "id",
        "date",
        "description",
    ]

    def ref(self, obj):
        return obj.reference.split("-").pop()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tags")

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())
