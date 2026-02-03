import re
import uuid
from decimal import Decimal
from pathlib import Path

from taggit.managers import TaggableManager

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _

from thebook.bookkeeping.managers import BankAccountQuerySet, TransactionQuerySet


def document_upload_path(instance, filename):
    filepath = Path(filename)
    extension = filepath.suffix
    new_filename = "".join([uuid.uuid4().hex, extension])

    if instance.transaction is None:
        return Path(new_filename)

    return Path(instance.transaction.bank_account.slug, new_filename)


class BankAccount(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    objects = BankAccountQuerySet.as_manager()

    class Meta:
        ordering = [
            "name",
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("bookkeeping:bank-account", args=(self.slug,))

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

        transactions = self.transactions.all()

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


class CategoryMatchRule(models.Model):
    priority = models.IntegerField(unique=True)
    pattern = models.CharField(max_length=512)
    category = models.ForeignKey("bookkeeping.Category", on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    comparison_function = models.CharField(
        max_length=3,
        choices={
            "EQ": "EQ",
            "NEQ": "NEQ",
            "LTE": "LTE",
            "GTE": "GTE",
        },
        blank=True,
        null=True,
    )
    tags = models.CharField(max_length=512, blank=True, null=True)

    def __str__(self):
        return f"{self.pattern} ({self.priority})"

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(value__isnull=True)
                        & models.Q(comparison_function__isnull=True)
                    )
                    | (
                        models.Q(value__isnull=False)
                        & models.Q(comparison_function__isnull=False)
                    )
                ),
                name="value_and_comparison_function_are_required_together",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(comparison_function__isnull=True)
                    | (
                        models.Q(comparison_function__isnull=False)
                        & models.Q(comparison_function__in=["EQ", "NEQ", "LTE", "GTE"])
                    )
                ),
                name="valid_comparison_function",
            ),
        ]

    def apply_rule(self, transaction):
        applied = False
        if self.tags and not transaction.id:
            raise ValueError(
                "You need to save the transaction before adding tags to it."
            )

        string_pattern_matched = bool(
            re.match(self.pattern, transaction.description, re.IGNORECASE)
        )

        if self.value:
            value_matched = False
            if self.comparison_function == "EQ" and transaction.amount == self.value:
                value_matched = True
            elif self.comparison_function == "NEQ" and transaction.amount != self.value:
                value_matched = True
            elif self.comparison_function == "LTE" and transaction.amount <= self.value:
                value_matched = True
            elif self.comparison_function == "GTE" and transaction.amount >= self.value:
                value_matched = True
        else:
            value_matched = True

        applied = all(
            [
                string_pattern_matched,
                value_matched,
            ]
        )
        if applied:
            transaction.category = self.category
            if self.tags:
                transaction.tags.add(*self.tags.split(","))
            transaction.save()

        return transaction, applied


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

    bank_account = models.ForeignKey(
        "bookkeeping.BankAccount",
        on_delete=models.SET_NULL,
        related_name="transactions",
        related_query_name="transaction",
        null=True,
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
            rules = CategoryMatchRule.objects.order_by("priority")

        for rule in rules:
            self, applied = rule.apply_rule(self)
            if applied:
                self.save()
                return

        if Decimal("0") <= self.amount <= settings.DONATION_THRESHOLD:
            donation, _ = Category.objects.get_or_create(name="Doação")
            self.category = donation
            self.save()
            return
