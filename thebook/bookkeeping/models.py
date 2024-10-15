import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.text import slugify
from django.utils.translation import gettext as _

from thebook.bookkeeping.managers import CashBookQuerySet, TransactionQuerySet


def document_upload_path(instance, filename):
    cash_book_slug = instance.transaction.cash_book.slug

    filepath = Path(filename)
    extension = filepath.suffix

    new_filename = "".join([uuid.uuid4().hex, extension])

    return Path(cash_book_slug, new_filename)


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

    def summary(self, *, month=None, year=None):
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

        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "withdraws": withdraws,
            "deposits": deposits,
            "balance": deposits + withdraws,
            "year": year,
            "month": month,
        }


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
        "bookkeeping.Transaction", on_delete=models.CASCADE, related_name="documents"
    )
    document_file = models.FileField(upload_to=document_upload_path)
    notes = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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

    objects = TransactionQuerySet.as_manager()

    class Meta:
        ordering = ["date", "description"]

    def __str__(self):
        return f"{self.description} ({self.amount:.2f})"

    @property
    def has_documents(self):
        return self.documents.exists()