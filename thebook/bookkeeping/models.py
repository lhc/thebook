import uuid
from decimal import Decimal
from pathlib import Path

from taggit.managers import TaggableManager

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.text import slugify
from django.utils.translation import gettext as _

from thebook.bookkeeping.categorizer import CategoryRule
from thebook.bookkeeping.managers import CashBookQuerySet, TransactionQuerySet

DONATION = "Doação"


def get_categorize_rules():
    donation, _ = Category.objects.get_or_create(name=DONATION)
    bank_fees, _ = Category.objects.get_or_create(name="Tarifas Bancárias")
    bank_income, _ = Category.objects.get_or_create(name="Investimentos")
    cash_book_transfer, _ = Category.objects.get_or_create(
        name="Transferência entre contas"
    )
    services, _ = Category.objects.get_or_create(name="Serviços")
    taxes, _ = Category.objects.get_or_create(name="Impostos")
    membership_fee, _ = Category.objects.get_or_create(name="Contribuição Associativa")

    return [
        CategoryRule(
            pattern="TARIFA BANCARIA Max Empresarial 1",
            category=bank_fees,
            tags=["recorrente"],
        ),
        CategoryRule(pattern="TARIFA BANCARIA", category=bank_fees),
        CategoryRule(
            pattern="CONTA DE TELEFONE", category=services, tags=["vivo", "recorrente"]
        ),
        CategoryRule(
            pattern="CONTA DE AGUA", category=services, tags=["sanasa", "recorrente"]
        ),
        CategoryRule(
            pattern="CONTA DE LUZ", category=services, tags=["cpfl", "recorrente"]
        ),
        CategoryRule(
            pattern="COBRANCA ALUGUEL",
            category=services,
            tags=["aluguel", "recorrente"],
        ),
        CategoryRule(pattern="RENTAB.INVEST FACILCRED", category=bank_income),
        CategoryRule(
            pattern="SYSTEN CONSULTORIA", category=services, tags=["contabilidade"]
        ),
        CategoryRule(pattern="CONTADOR", category=services),
        CategoryRule(pattern="PAYPAL DO BRASIL", category=cash_book_transfer),
        CategoryRule(
            pattern="PAGTO ELETRONICO TRIBUTO INTERNET --P.M CAMPINAS/SP",
            category=taxes,
        ),
        CategoryRule(pattern="PAGAMENTO DA FATURA", category=cash_book_transfer),
    ]


def document_upload_path(instance, filename):
    filepath = Path(filename)
    extension = filepath.suffix
    new_filename = "".join([uuid.uuid4().hex, extension])

    if instance.transaction is None:
        return Path(new_filename)

    return Path(instance.transaction.cash_book.slug, new_filename)


class CashBook(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    objects = CashBookQuerySet.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = [
            "name",
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def with_summary(self, *, month=None, year=None):
        def _valid_year_and_month(month, year):
            if month is not None:
                return all(
                    [
                        month in range(1, 13),
                        year is not None,
                    ]
                )
            return True

        if not _valid_year_and_month(month, year):
            raise ValueError("Invalid 'month' and 'year' arguments")

        transactions = self.transaction_set.all()

        overall_balance = (
            transactions.aggregate(overall_balance=Sum("amount")).get("overall_balance")
        ) or Decimal("0")

        if year is not None:
            transactions = transactions.filter(date__year=year)
        if month is not None:
            transactions = transactions.filter(date__month=month)

        deposits = (
            transactions.filter(amount__gte=Decimal("0"))
            .aggregate(deposits=Sum("amount"))
            .get("deposits")
        ) or Decimal("0")

        withdraws = (
            transactions.filter(amount__lt=Decimal("0"))
            .aggregate(withdraws=Sum("amount"))
            .get("withdraws")
        ) or Decimal("0")

        self.withdraws = withdraws
        self.deposits = deposits
        self.balance = deposits + withdraws
        self.overall_balance = overall_balance
        self.year = year
        self.month = month

        return self


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = [
            "name",
        ]
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.name


class Document(models.Model):
    transaction = models.ForeignKey(
        "bookkeeping.Transaction",
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
    )
    document_date = models.DateField()
    document_file = models.FileField(upload_to=document_upload_path)
    notes = models.CharField(max_length=128)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        document_notes = self.notes
        if not self.notes:
            document_notes = (
                self.transaction.description
                if self.transaction
                else "Document without notes"
            )
        return f"<{document_notes}>"

    def save(self, **kwargs):
        if not self.document_date and self.transaction:
            self.document_date = self.transaction.date
        super().save(**kwargs)


class Transaction(models.Model):
    reference = models.CharField(max_length=36, unique=True)
    date = models.DateField()
    description = models.CharField(max_length=256)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cash_book = models.ForeignKey(
        "bookkeeping.CashBook", on_delete=models.SET_NULL, null=True
    )
    category = models.ForeignKey(
        "bookkeeping.Category", on_delete=models.SET_NULL, null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    tags = TaggableManager(blank=True)

    objects = TransactionQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index("date", name="transaction_date_idx"),
        ]
        ordering = ["date", "description"]

    def __str__(self):
        return f"{self.description} ({self.amount:.2f})"

    @property
    def has_documents(self):
        return self.documents.exists()

    def categorize(self, rules=None):
        if rules is None:
            rules = get_categorize_rules()

        for rule in rules:
            self, applied = rule.apply_rule(self)
            if applied:
                self.save()
                return

        if Decimal("0") <= self.amount <= settings.DONATION_THRESHOLD:
            donation, _ = Category.objects.get_or_create(name=DONATION)
            self.category = donation
            self.save()
            return
