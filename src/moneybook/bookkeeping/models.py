from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

from moneybook.bookkeeping.managers import TransactionManager


class Account(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.name


class Document(models.Model):
    transaction = models.ForeignKey(
        "bookkeeping.Transaction", on_delete=models.CASCADE, related_name="documents"
    )
    document_file = models.FileField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Transaction(models.Model):
    ACCOUNT_TRANSFER = 1
    EXPENSE = 2
    INCOME = 3
    TRANSACTION_TYPE_CHOICES = [
        (ACCOUNT_TRANSFER, _("Account Transfer")),
        (EXPENSE, _("Expense")),
        (INCOME, _("Income")),
    ]

    reference = models.CharField(max_length=32, unique=True)
    date = models.DateField()
    description = models.CharField(max_length=256)
    transaction_type = models.SmallIntegerField(choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    account = models.ForeignKey(
        "bookkeeping.Account", on_delete=models.SET_NULL, null=True
    )
    category = models.ForeignKey(
        "bookkeeping.Category", on_delete=models.SET_NULL, null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    objects = TransactionManager()

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.description} ({self.amount:.2f})"
