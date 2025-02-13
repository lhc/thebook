import uuid
from decimal import Decimal
from pathlib import Path

from taggit.managers import TaggableManager

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.text import slugify
from django.utils.translation import gettext as _

from thebook.bookkeeping.managers import CashBookQuerySet, TransactionQuerySet

DONATION = "Doação"
RECURRING_DONATION = "Doação Recorrente"
BANK_FEES = "Tarifas Bancárias"
BANK_INCOME = "Investimentos"
CREDIT_CARD_BILL = "Fatura Cartão de Crédito"
RECURRING = "Recorrente"
MEMBERSHIP_FEE = "Mensalidade"
CASH_BOOK_TRANSFER = "Transferência entre contas"
ACCOUNTANT = "Contabilidade"
TAXES = "Impostos"
UNCATEGORIZED = "Uncategorized"


def get_categorize_rules():
    uncategorized, _ = Category.objects.get_or_create(name=UNCATEGORIZED)
    donation, _ = Category.objects.get_or_create(name=DONATION)
    recurring_donation, _ = Category.objects.get_or_create(name=RECURRING_DONATION)
    bank_fees, _ = Category.objects.get_or_create(name=BANK_FEES)
    bank_income, _ = Category.objects.get_or_create(name=BANK_INCOME)
    credit_card_bill, _ = Category.objects.get_or_create(name=CREDIT_CARD_BILL)
    recurring, _ = Category.objects.get_or_create(name=RECURRING)
    cash_book_transfer, _ = Category.objects.get_or_create(name=CASH_BOOK_TRANSFER)
    accountant, _ = Category.objects.get_or_create(name=ACCOUNTANT)
    taxes, _ = Category.objects.get_or_create(name=TAXES)
    membership_fee, _ = Category.objects.get_or_create(name=MEMBERSHIP_FEE)

    return {
        "TARIFA BANCARIA": bank_fees,
        "CONTA DE TELEFONE": recurring,
        "CONTA DE AGUA": recurring,
        "CONTA DE LUZ": recurring,
        "COBRANCA ALUGUEL": recurring,
        "RENTAB.INVEST FACILCRED": bank_income,
        "SYSTEN CONSULTORIA": accountant,
        "CONTADOR": accountant,
        "PAYPAL DO BRASIL": cash_book_transfer,
        "PAGTO ELETRONICO TRIBUTO INTERNET --P.M CAMPINAS/SP": taxes,
        "PAGAMENTO DA FATURA": credit_card_bill,
    }


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

        for description, category in rules.items():
            if description.lower() in self.description.lower():
                self.category = category
                self.save()
                return

        if Decimal("0") <= self.amount <= settings.DONATION_THRESHOLD:
            donation, _ = Category.objects.get_or_create(name=DONATION)
            self.category = donation
            self.save()
            return
